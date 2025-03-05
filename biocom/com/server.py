import comtypes
from comtypes.client import CreateObject
from enum import Enum, auto
import time
import os
import numpy as np
import functools
import asyncio
from pathlib import Path
from typing import Union, Optional, Tuple, List
import warnings

from ..mps.techniques.sequence import TechniqueSequence
from ..mps.config import FullConfiguration
from ..mps.common import BLDeviceModel
from ..mps.write import write_techniques

# from ..mps.write_utils import FilePath
FilePath = Union[str, Path]



def validate_and_retry(func):
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        for i in range(obj.retries + 1):
            out = func(obj, *args, **kwargs)
            if out == 1:
                # Success 
                break
            elif i < obj.retries:
                # Wait before trying again    
                time.sleep(0.5)
                if obj.show_warnings:
                    warnings.warn(f"OLE-COM method {func.__name__} failed on attempt {i + 1}. Retrying...")
            
        if out != 1 and obj._validate_return_codes:
            raise RuntimeError(f"OLE-COM method {func.__name__} failed with code {out}. "
                               f"Args: {args}; kwargs: {kwargs}")
        return out
    return wrapper


class DeviceChannel(object):
    def __init__(self, device_id: int, channel: int, 
                 model: Optional[BLDeviceModel] = None,
                 name: Optional[str] = None,
                 data_path: Optional[Path] = None
                 ):
        self.device_id = device_id
        self.channel = channel
        self.model = model
        self.name = name
        self.data_path = data_path
        
        self.i_ac = None
        self.i_dc = None
        
        
    @property
    def key(self):
        return (self.device_id, self.channel)
    
    def __str__(self) -> str:
        return f"Device {self.device_id} (Model: {self.model}), Channel {self.channel} (Name: {self.name})"
    
    
# def parse_device_channel(device_channel: Union[DeviceChannel, Tuple[int, int]]):
#     if isinstance(device_channel, DeviceChannel):
#         return device_channel.key
#     return device_channel

def devchannel_input(func):
    # Decorator for OLECOM instance methods,
    # allowing a DeviceChannel instance to be provided instead of
    # device_id and channel
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        # print('args:', args)
        if isinstance(args[0], DeviceChannel):
            # Convert DeviceChannel instance to device_id, channel tuple
            device_id, channel = args[0].key
            out = func(obj, device_id, channel, *args[1:], **kwargs)
        else:
            out = func(obj, *args, **kwargs)
        return out
    return wrapper
    

class OLECOM(object):
    def __init__(self, validate_return_codes: bool = True, retries: int = 1,
                 show_warnings: bool = True, print_messages: bool = True):
        self.server = None
        self._validate_return_codes = validate_return_codes
        self.retries = retries
        self.show_warnings = show_warnings
        self.print_messages = print_messages
        
        # TODO: store configuration somewhere
        self.channel_sequences = {}
        self.channel_settings = {}
        self.channel_results = {}
        
    # def _register_sequence(
    #         self, 
    #         device_channel: Union[DeviceChannel, Tuple[int, int]], 
    #         sequence: TechniqueSequence):
    #     if device_id not in self.channel_sequences.keys():
    #         self.channel_sequences[device_id] = {}
            
    #     self.channel_sequences[device_id][channel] = sequence
        
    # def _register_settings(
    #         self, 
    #         device_channel: Union[DeviceChannel, Tuple[int, int]],
    #         mps_file: FilePath):
    #     if device_id not in self.channel_settings.keys():
    #         self.channel_settings[device_id] = {}
            
    #     self.channel_settings[device_id][channel] = mps_file
        
    # def set_channel_name(self, )
    
    def launch_server(self):
        prog_id = "EClabCOM.EClabExe"
        self.server = CreateObject(prog_id)
    
    def get_device_type(self, device_id: int):
        device_type, code = self.server.GetDeviceType(device_id)
        return device_type
    
    @validate_and_retry
    def connect_device(self, device_id: int):
        return self.server.ConnectDevice(device_id)
    
    @validate_and_retry
    def disconnect_device(self, device_id: int):
        return self.server.DisconnectDevice(device_id)
    
    @validate_and_retry
    def connect_device_by_ip(self, ip_address: str):
        return self.server.ConnectDeviceByIP(ip_address)
    
    @devchannel_input
    @validate_and_retry
    def select_channel(self, device_id: int, channel: int):
        return self.server.SelectChannel(device_id, channel)
    
    @devchannel_input
    @validate_and_retry
    def load_settings(self, device_id: int, channel: int, mps_file: FilePath, safe: bool = True):
        mps_file = Path(mps_file)
        abspath = mps_file.absolute().__str__()
        
        if safe:
            # Select the channel and wait briefly to avoid timing issues
            # Should solve:
            # 1. Inability to load settings while another channel is running
            self.select_channel(device_id, channel)
            time.sleep(1.0)
            
        out = self.server.LoadSettings(device_id, channel, abspath)
        
        if out == 1:
            # Store the settings only if successful
            self.channel_settings[(device_id, channel)] = mps_file
            
        return out
    
    @devchannel_input
    @validate_and_retry
    def run_channel(self, device_id: int, channel: int, output_file: FilePath):
        abspath = Path(output_file).absolute().__str__()
        code = self.server.RunChannel(device_id, channel, abspath)
        
        if code == 1:
            # If launched successfully, set channel status to running
            self.channel_results[(device_id, channel)] = ChannelResult.RUNNING
            
        return code
    
    @devchannel_input
    @validate_and_retry
    def stop_channel(self, device_id: int, channel: int):
        return self.server.StopChannel(device_id, channel)
    
    @devchannel_input
    def get_data_filename(self, device_id: int, channel: int, technique: int):
        if technique < 0:
            # Convert negative index to positive
            technique = len(self.get_sequence(device_id, channel)) + technique
            
        # GetDataFileName returns a tuple of length 1
        name = self.server.GetDataFileName(device_id, channel, technique)[0]
        return name
    
    @validate_and_retry
    def toggle_popups(self, enable: bool):
        # Not availabe for v11.50
        return self.server.EnableMessagesWindows(enable)
    
    @devchannel_input
    def get_channel_info(self, device_id: int, channel: int):
        # Not availabe for v11.50
        return self.server.GetChannelInfos(device_id, channel)
    
    @devchannel_input
    def check_measure_status(self, device_id: int, channel: int):
        return dict(zip(_measure_status_keys, self.server.MeasureStatus(device_id, channel)))
    
    @devchannel_input
    def channel_is_running(self, device_id: int, channel: int):
        stat = self.check_measure_status(device_id, channel)
        return all([
            # stat['Result code'] == 1,  # Valid return code
            int(stat['Connection']) == 0,  # Device is connected
            ChannelStatus(int(stat['Status'])) == ChannelStatus.RUN,  # Channel is running
        ])
        
    @devchannel_input
    def channel_is_stopped(self, device_id: int, channel: int):
        stat = self.check_measure_status(device_id, channel)
        return all([
            # stat['Result code'] == 1,  # Valid return code
            int(stat['Connection']) == 0,  # Device is connected
            ChannelStatus(int(stat['Status'])) == ChannelStatus.STOP,  # Channel is stopped
        ])
    
    @devchannel_input
    @validate_and_retry
    def load_techniques(
            self, 
            device_id: int,
            channel: int,
            sequence: TechniqueSequence, 
            config: FullConfiguration,
            mps_file: FilePath
        ):
        
        # Get device type and convert to enum
        channel_device = BLDeviceModel(self.get_device_type(device_id))
        
        # Compare devices 
        if channel_device != config.basic.device:
            raise ValueError(f"Detected device model {channel_device.value} at device_id {device_id}, "
                             f"but received settings for device model {config.basic.device.value}.")
            
        # Write settings file
        write_techniques(sequence, config, mps_file)
        
        # Load settings
        out = self.load_settings(device_id, channel, mps_file)
        
        if out == 1:
            # Store the sequence only if successful
            self.channel_sequences[(device_id, channel)] = sequence
            
        return out
    
    @devchannel_input
    def get_settings(self, device_id: int, channel: int) -> Path:
        return self.channel_settings[(device_id, channel)]
    
    @devchannel_input
    def get_sequence(self, device_id: int, channel: int) -> Path:
        return self.channel_sequences[(device_id, channel)]
        
    @devchannel_input
    def channel_is_done(self, device_id: int, channel: int, wait_for_buffer: bool = True) -> bool:
        # Check if data file exists for sequence
        # NOTE: all data files are created when measurement is launched, 
        # so this does not mean that the channel is done running.
        data_file = self.get_data_filename(device_id, channel, 0)
        if data_file is not None:
            # Data filename may come back as None - not yet sure in which cases this may happen
            data_status = os.path.exists(self.get_data_filename(device_id, channel, 0))    
            if not data_status:
                return data_status
        
        meas_status = self.check_measure_status(device_id, channel)
        
        # Check if channel is stopped
        is_stopped = all([
            int(meas_status['Connection']) == 0,  # Device is connected
            ChannelStatus(int(meas_status['Status'])) == ChannelStatus.STOP,  # Channel is stopped
        ])
        
        # PROBLEM: current point index seems to apply only to EIS.
        # E.g. for OCV, current point index and total point index are both frozen at values from last EIS measurement, and never get updated
        # # Check if channel has reached last point of last technique
        # # n_techniques = self.get_sequence(device_id, channel).num_techniques
        # all_points_done = all([
        #     # int(meas_status["Technique number"]) == n_techniques - 1,
        #     int(meas_status["Current point index"]) == int(meas_status["Total point index"])
        # ])
        
        # Check if the buffer is empty
        buffer_empty = (meas_status["Buffer size"] == 0 or not wait_for_buffer)
        
        # print(f"device {device_id} channel {channel}: data_status={data_status}, is_stopped={is_stopped}, buffer_empty={buffer_empty}")
        # for key in ["Current point index", "Total point index"]:
        #     print(key, meas_status[key])
        
        # return all([data_status, is_stopped, all_points_done, buffer_empty])
        return all([data_status, is_stopped, buffer_empty])
    
    def get_eis_value(self, mpr_file: Union[Path, str], index: int):
        abspath = Path(mpr_file).absolute().__str__()
        values, code = self.server.MeasureEisValue(abspath, index)
        if code == 1:
            t, f, zr, zi = values
            return {'time/s': t, 'freq/Hz': f, 'Re(Z)/Ohm': zr, '-Im(Z)/Ohm': zi}
        else:
            raise ValueError(f"Could not read EIS values at index {index} in file {mpr_file}")
    
    @devchannel_input
    async def wait_for_channel_async(
            self, 
            device_id: int, 
            channel: int, 
            min_wait: float,
            timeout: float,
            interval: float = 0.5,
            channel_status: Optional[dict] = None,
            cascading: bool = False
        ):
        start = time.monotonic()
        
        result = ChannelResult.RUNNING
        
        def log_status(res: ChannelResult):
            self.channel_results[(device_id, channel)] = res
            
            if channel_status is not None:
                # Log status in external dict for async control
                channel_status[(device_id, channel)] = res
                
        log_status(result)
        
        while not result_is_complete(result):
            await asyncio.sleep(interval)
            elapsed = time.monotonic() - start
            
            if cascading and channel_status is not None:
                # Only check the channel if all upstream channels are done
                query = should_query(device_id, channel, channel_status)
            else:
                query = True
                
            if query:
                if self.channel_is_done(device_id, channel) and elapsed > min_wait:
                    result = ChannelResult.DONE
            
            log_status(result)
                
            if elapsed > timeout and not result_is_complete(result):
                result = ChannelResult.TIMEOUT
                break
            
        if result == ChannelResult.TIMEOUT and self.print_messages:
            print(f"WARNING: Device {device_id} Channel {channel} timed out")
            
        log_status(result)
            
        if self.print_messages:
            print("Device {} Channel {} finished in {:.1f} s with result {}".format(device_id, channel, elapsed, result.name))
            
        return result
    
    @devchannel_input
    def wait_for_channel(
            self, 
            device_id: int, 
            channel: int, 
            min_wait: float,
            timeout: float,
            interval: float = 0.5
        ):
        return asyncio.run(self.wait_for_channel_async(device_id, channel, min_wait, timeout, interval))
        
    async def wait_for_channels_async(
            self,
            channels: List[DeviceChannel], 
            min_wait: float, 
            timeout: float, 
            interval: float = 0.5,
            channel_status: Optional[dict] = None,
            cascading: bool = False
            ):
        if cascading and channel_status is None:
            channel_status = {}
            
        return await asyncio.gather(
            *[
                self.wait_for_channel_async(c, min_wait, timeout, interval, channel_status, cascading)
                for c in channels
            ]
        )
    
    def wait_for_channels(
            self,
            channels: List[DeviceChannel], 
            min_wait: float, 
            timeout: float, 
            interval: float = 0.5):
        return asyncio.run(self.wait_for_channels_async(channels, min_wait, timeout, interval))
        
    @property
    def all_results_complete(self):
        return check_results(self.channel_results.values())
        
        
        

    

_measure_status_keys = [
    'Status',
    'Ox/Red',
    'OCV',
    'EIS',
    'Technique number',
    'Technique code',
    'Sequence number',
    'Current loop iteration number',
    'Curent sequence within loop number',
    'Loop experiment iteration number',
    'Cycle number',
    'Counter 1',
    'Counter 2',
    'Counter 3',
    'Buffer size',
    'Time',
    'Ewe',
    'Ece',
    'Eoc',
    'I',
    'Q-Q0',
    'Aux1',
    'Aux2',
    'Irange',
    'R compensation',
    'Frequency',
    '|Z|',
    'Current point index',
    'Total point index',
    'T (deg. C)',
    'Safety limit',
    'Connection',
    'Result code'
]

class ChannelStatus(Enum):
    STOP = 0
    RUN = 1
    PAUSE = 2
    SYNC = 3
    STOP_REC1 = 4
    STOP_REC2 = 5
    PAUSE_REC = 6
    

class ChannelResult(Enum):
    RUNNING = 0
    DONE = 1
    TIMEOUT = 2
    
    
def result_is_complete(result: ChannelResult):
    return result.value > 0

def check_results(results: List[ChannelResult]):
    return all([result_is_complete(r) for r in results])


def should_query(device_id: int, channel: int, channel_status: dict):
    # For cascading async channel status checks in wait_for_channels_async
    key = (device_id, channel)
    keys = list(channel_status.keys())
    # Get results of all upstream channels
    upstream_results = [channel_status[k] for k in keys[:keys.index(key)]]
    # If all upstream channels are done, we need to check this channel
    return check_results(upstream_results)
    