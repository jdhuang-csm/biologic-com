from dataclasses import dataclass, replace
from pathlib import Path
from collections import namedtuple
from typing import Union, Optional

# from .techniques.sequence import TechniqueSequence

from .common import (
    BLDeviceModel, CableType, ChannelGrounding, ElectrodeConnection, 
    Filter, PotentialControl, ReferenceElectrode, TurnToOCV,
    SampleType, CycleDefinition
)


global SOFTWARE_VERSION
global SERVER_VERSION
global INTERPRETER_VERSION

SOFTWARE_VERSION = '11.50'
SERVER_VERSION = '11.50'
INTERPRETER_VERSION = '11.50'


# FullConfiguration = namedtuple(
#     'FullConfiguration', 
#     [
#         'basic',
#         'hardware',
#         'safety',
#         'recording',
#         'cell',
#         'sample',
#         'misc'
#     ]
#     )


def set_versions(
        software: str = '11.50',
        server: Optional[str] = None,
        interpreter: Optional[str] = None
    ):
    """
    Configure software, internet server, and command interpreter versions.
    This does NOT affect EC-Lab, but should be used only to inform 
    biocom of the versions that you are using to ensure that headers are
    written correctly.
    """
    global SOFTWARE_VERSION
    global SERVER_VERSION
    global INTERPRETER_VERSION 
    
    SOFTWARE_VERSION = software
    SERVER_VERSION = server or software
    INTERPRETER_VERSION = interpreter or software


@dataclass
class BasicConfig(object):
    num_techniques: int
    software_version: str
    server_version: str
    interpreter_version: str
    settings_filename: Union[str, Path]
    device: BLDeviceModel
    
    
@dataclass
class SafetySettings(object):
    duration_ms: Optional[float] = 10.0 # ms
    ewe_min: Optional[float] = None # V
    ewe_max: Optional[float] = None # V
    iabs_mA: Optional[float] = None # mA
    dq_mAh: Optional[float] = None  # mAh
    aux1_min: Optional[float] = None # V
    aux1_max: Optional[float] = None # V
    aux2_min: Optional[float] = None # V
    aux2_max: Optional[float] = None # V
    no_start_on_overload: bool = True


@dataclass
class HardwareSettings(object):
    v_range_min: float
    v_range_max: float
    filtering: Filter
    v_comp_min: int = -10
    v_comp_max: int = 10
    potential_control: PotentialControl = PotentialControl.EWE
    electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD
    grounding: ChannelGrounding = ChannelGrounding.FLOATING
    

@dataclass
class CellCharacteristics(object):
    electrode_material: str
    initial_state: str
    electrolyte: str
    comments: str
    cable: CableType = CableType.STANDARD
    ref_electrode: ReferenceElectrode = ReferenceElectrode.NONE
    surface_area: float = 0.001
    char_mass: float = 0.001
    volume: float = 0.001
    

@dataclass
class BatteryCharacteristics(object):
    active_mass_mg: float = 0.001
    active_x: float = 0.0
    active_mol_wt_g: float = 0.001
    ion_at_wt_g: float = 0.001
    x0: float = 0.0
    num_electrons: int = 1
    capacity_mAh: float = 0.0
    

@dataclass
class CorrosionCharacteristics(object):
    equiv_wt: float = 0.0
    density: float = 0.0
    

@dataclass
class MaterialsCharacteristics(object):
    thickness: float = 0.0
    diameter: float = 0.0
    cell_constant: float = 0.0
    

@dataclass
class RecordingOptions(object):
    ece: bool = False
    power: bool = False
    aux1: bool = False
    aux2: bool = False
    eis_quality: bool = False
    
@dataclass
class MiscOptions(object):
    turn_to_ocv: TurnToOCV = TurnToOCV.FALSE
    cycle_definition: CycleDefinition = CycleDefinition.CHARGE_DISCHARGE
    one_file_per_loop: bool = False
    
    
@dataclass
class FullConfiguration(object):
    basic: BasicConfig
    hardware: HardwareSettings
    sample: Union[CorrosionCharacteristics, BatteryCharacteristics, MaterialsCharacteristics]
    cell: CellCharacteristics
    safety: SafetySettings
    recording: RecordingOptions
    misc: MiscOptions
    
    # def __init__(self, 
    #              basic: BasicConfig,
    #              hardware: HardwareSettings,
    #              sample: Union[CorrosionCharacteristics, BatteryCharacteristics, MaterialsCharacteristics],
    #              cell: CellCharacteristics,
    #              safety: SafetySettings,
    #              recording: RecordingOptions,
    #              misc: MiscOptions
    #              ):
    #     self.basic = basic
    #     self.hardware = hardware
    #     self.sample = sample
    #     self.cell = cell
    #     self.safety = safety
    #     self.recording = recording
    #     self.misc = misc
        
    
_settings_classes = {
    'basic': BasicConfig,
    'hardware': HardwareSettings,
    'safety': SafetySettings,
    'recording': RecordingOptions,
    'cell': CellCharacteristics,
    'misc': MiscOptions
}




def make_or_update_config(
    current_settings: Union[FullConfiguration, None], 
    name: str, 
    kwargs: dict,
    sample_type: Optional[SampleType] = None
    ):  
    
    if current_settings is None:
        # Make a new settings instance
        if name == 'sample':
            if sample_type is None:
                raise ValueError("To create a new sample settings instance, "
                                 "sample_type must be provided")
            if sample_type == SampleType.CORROSION:
                cls = CorrosionCharacteristics
            elif sample_type == SampleType.BATTERY:
                cls = BatteryCharacteristics
            elif sample_type == SampleType.MATERIALS:
                cls = MaterialsCharacteristics
        else:
            cls = _settings_classes[name]
        return cls(**kwargs)
    else:
        # If a configuration object already exist, update the 
        # corresponding dataclass with the new kwargs.
        # Update the FullConfiguration instance in place
        new = replace(getattr(current_settings, name), **kwargs)
        setattr(current_settings, name, new)
    

def set_recording_options(
        ece: bool = False,
        power: bool = False,
        aux1: bool = False,
        aux2: bool = False,
        eis_quality: bool = False,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    
    return make_or_update_config(current_settings, 'recording', kwargs)
    # if current_settings is None:
    #     return RecordingOptions(**kwargs)
    # else:
    #     return replace(current_settings.recording, **kwargs)



def set_safety_limits(
        duration_ms: Optional[float] = 10.0,
        ewe_min: Optional[float] = None, # V
        ewe_max: Optional[float] = None, # V
        iabs_mA: Optional[float] = None, # mA
        dq_mAh: Optional[float] = None,  # mAh
        aux1_min: Optional[float] = None, # V
        aux1_max: Optional[float] = None, # V
        aux2_min: Optional[float] = None, # V
        aux2_max: Optional[float] = None, # V
        no_start_on_overload: bool = True,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # If there are no limits requiring a duration, 
    # remove the duration setting
    if not any([ewe_min, ewe_max, iabs_mA, dq_mAh, 
                aux1_min, aux1_max,
                aux2_min, aux2_max,
        ]):
        kwargs['duration_ms'] = None
        
        
    return make_or_update_config(current_settings, 'safety', kwargs)
    
    # if current_settings is None:
    #     return SafetySettings(**kwargs)
    # else:
    #     return replace(current_settings.safety, **kwargs)
 
    
    

def set_basic_config(
        num_techniques: int,
        software_version: str,
        server_version: str,
        interpreter_version: str,
        settings_filename: Union[str, Path],
        device: BLDeviceModel,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    return make_or_update_config(current_settings, 'basic', kwargs)
    
    # return BasicConfig(**locals())

def set_hardware(
        device: BLDeviceModel,
        v_range_min: float,
        v_range_max: float,
        filtering: Filter = Filter.NONE,
        v_comp_min: int = -10,
        v_comp_max: int = 10,
        potential_control: PotentialControl = PotentialControl.EWE,
        electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD,
        grounding: ChannelGrounding = ChannelGrounding.FLOATING,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k, v in locals().items() if k not in ['device', 'current_settings']}
    # print(kwargs)
    device.validate_filter(filtering)
    
    return make_or_update_config(current_settings, 'hardware', kwargs)
    
    
    # return HardwareSettings(
    #     v_range_min,
    #     v_range_max,
    #     filtering,
    #     v_comp_min,
    #     v_comp_max,
    #     potential_control,
    #     electrode_connection,
    #     grounding
    # )
    
def set_cell_characteristics(
        electrode_material: str = '',
        initial_state: str = '',
        electrolyte: str = '',
        comments: str = '',
        cable: CableType = CableType.STANDARD,
        ref_electrode: ReferenceElectrode = ReferenceElectrode.NONE,
        surface_area: float = 0.001,
        char_mass: float = 0.001,
        volume: float = 0.001,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return CellCharacteristics(**locals())
    return make_or_update_config(current_settings, 'cell', kwargs)
    

    
def set_battery_characteristics(
        active_mass_mg: float = 0.001,
        active_x: float = 0.0,
        active_mol_wt_g: float = 0.001,
        ion_at_wt_g: float = 0.001,
        x0: float = 0.0,
        num_electrons: int = 1,
        capacity_mAh: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return BatteryCharacteristics(**locals())
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.BATTERY)
    


def set_materials_characteristics(
        thickness: float = 0.0,
        diameter: float = 0.0,
        cell_constant: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    # return MaterialsCharacteristics(**locals())
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.MATERIALS)


def set_corrosion_characteristics(
        equiv_wt: float = 0.0,
        density: float = 0.0,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    return make_or_update_config(current_settings, 'sample', kwargs, SampleType.CORROSION)
    # return CorrosionCharacteristics(**locals())

def set_misc_options(
        turn_to_ocv: bool = True,
        cycle_definition: CycleDefinition = CycleDefinition.CHARGE_DISCHARGE,
        one_file_per_loop: bool = False,
        current_settings: Optional[FullConfiguration] = None
    ):
    kwargs = {k:v for k,v in locals().items() if k != 'current_settings'}
    kwargs['turn_to_ocv'] = TurnToOCV.from_bool(turn_to_ocv)
    return make_or_update_config(current_settings, 'misc', kwargs)
    # return MiscOptions(
    #     TurnToOCV.from_bool(turn_to_ocv),
    #     cycle_definition,
    #     one_file_per_loop
    # )
    
# def get_parameters_from_sequence(params: TechniqueSequence):
#     params = TechniqueSequence.technique_list[0]
    
#     # from hardwareparams subclass
#     params.v_range_min
#     params.v_range_max
#     params.i_range
#     params.bandwidth



def set_defaults(
        device: BLDeviceModel,
        technique_sequence,
        sample_type: SampleType
    ):
    
    global SOFTWARE_VERSION
    global SERVER_VERSION
    global INTERPRETER_VERSION

    basic = set_basic_config(
        technique_sequence.num_techniques,
        SOFTWARE_VERSION,
        SERVER_VERSION,
        INTERPRETER_VERSION,
        settings_filename=None,  # Placeholder
        device=device
    )
    
    recording = set_recording_options()
    safety = set_safety_limits()
    
    hardware = set_hardware(
        device,
        # Take v range from first technique
        technique_sequence[0].v_range_min,
        technique_sequence[0].v_range_max,
    )
    
    cell = set_cell_characteristics()
    
    misc = set_misc_options()
    
    if sample_type == SampleType.CORROSION:
        sample = set_corrosion_characteristics()
    elif sample_type == SampleType.BATTERY:
        sample = set_battery_characteristics()
    elif sample_type == SampleType.MATERIALS:
        sample = set_materials_characteristics()
        
    return FullConfiguration(
        basic,
        hardware,
        sample,
        cell,
        safety,
        recording,
        misc
    )
    
    
def validate_configuration(config: FullConfiguration):
    device: BLDeviceModel = config.basic.device
    
    device.validate_bandwidth(config.hardware.bandwidth)
    device.validate_filter(config.hardware.filtering)
    
    