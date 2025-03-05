## TODO: this file should be obsolete; replaced by write_utils, headerfields, and header
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC
from typing import Any, Union, Optional, List

from .common import (
    ElectrodeConnection, PotentialControl, BLDeviceModel,
    ReferenceElectrode
)


FilePath = Union[Path, str]


_decimal_sep_comma = False


def set_decimal_separator(comma=False):
    global _decimal_sep_comma
    _decimal_sep_comma = comma
    
    
def float2str(value: float, precision: int):
    text = "{x:.{p}f}".format(x=value, p=precision)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text


def format_value(value, precision: int = 3):
    # Convert enums to values
    if isinstance(value, Enum):
        value = value.value
        
    # Convert bools to ints
    if isinstance(value, bool):
        return str(int(value))
    
    # Format floats with appropriate separator
    if isinstance(value, float):
        return float2str(value, precision)
        
    # Strings or ints: return raw value
    return str(value)

def format_duration(duration: float):
    """Format duration (in seconds) as text for mps file"""
    # Get hours, minutes, seconds
    h = int(duration / 3600)
    m = int(duration / 60)
    s = int(duration)
    
    # Get decimal seconds
    ds = round(duration % 1, 4)
    ds = '{:.4f}'.format(ds).split('.')[1]
    
    text = '{:02}:{:02}:{:02}.{}'.format(h, m, s, ds)
    if _decimal_sep_comma:
        return text.replace('.', ',')
    return text



    
def get_main_header(
    num_techniques: int,
    software_version: str,
    server_firmware: str,
    interpreter_firmware: str,
    mps_file: Union[str, Path],
    device_name: str,
    v_range_min: float,
    v_range_max: float,
    v_comp_min: int = -10,
    v_comp_max: int = 10,
    electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD,
    potential_control: PotentialControl = PotentialControl.EWE,
    electrode_material: str = '',
    initial_state: str = '',
    electrolyte: str = '',
    comments: str = '',
    surface_area: float = 1.0,
    characteristic_mass: float = 1.0,
    equiv_wt: float = 1.0,
    density: float = 1.0,
    volume: float = 1.0,
    record_ece: bool = False,
    record_pwr: bool = False,
    record_aux1: bool = False,
    record_aux2: bool = False,
    record_eis_quality: bool = False,
    return_to_ocv: bool = False
):
    
    mps_file = Path(mps_file).absolute()
    
    comment_block = [f"Comments : {c}" for c in comments.split('\n')]
    comment_block = "\n".join(comment_block)
    
    # TODO: incorporate GCPL header lines
    header_lines = [
        "EC-LAB SETTING FILE",
        "",
        f"Number of linked techniques : {num_techniques}",
        "",
        f"EC-LAB for windows v{software_version} (software)",
        f"Internet server v{server_firmware} (firmware)",
        f"Command interpretor v{interpreter_firmware} (firmware)",
        "",
        f"Filename : {mps_file}",
        "",
        f"Device : {device_name}",
        f"CE vs. WE compliance from {v_comp_min} V to {v_comp_max} V",
        f"Electrode connection : {electrode_connection.value}",
        f"Potential control : {potential_control.value}",
        # TODO: add filtering for VMP-300 series
        # "Ewe,I filtering : 50 kHz",
        "Ewe ctrl range : min = {} V, max = {} V".format(float2str(v_range_min, 2), float2str(v_range_max, 2)),
        # TODO: get safety limits from list arg?
        "Safety Limits :",
        "\tDo not start on E overload", #
        # TODO: add channel for VMP-300
        # "Channel : Grounded",
        f"Electrode material : {electrode_material}",
        f"Initial state : {initial_state}",
        f"Electrolyte : {electrolyte}",
        # f"Comments : {comments}",
        comment_block,
        "Electrode surface area : {} cm²".format(float2str(surface_area)), # TODO: handle superscript?
        "Characteristic mass : {} g".format(float2str(characteristic_mass)),
        "Equivalent Weight : {} g/eq.".format(float2str(equiv_wt)),
        "Density : {} g/cm3".format(float2str(density)),
        "Volume (V) : {} cm³".format(float2str(volume)), # TODO: superscript
        ""
    ]

    if record_ece:
        header_lines.append("Record Ece")
    if record_aux1:
        header_lines.append("Record Analogic IN 1")
    if record_aux2:
        header_lines.append("Record Analogic IN 2")
    if record_pwr:
        header_lines.append("Record Power")
    if record_eis_quality:
        header_lines.append("Record EIS quality indicators")

    if return_to_ocv:
        turn_to_ocv = 'Turn'
    else:
        turn_to_ocv = 'Do not turn'

    header_lines += [
        "Cycle Definition : Charge/Discharge alternance",
        f"{turn_to_ocv} to OCV between techniques"
    ]


    header = '\n'.join(header_lines)

    return header


def get_technique_header(index: int, technique):
    # TODO: technique enum?
    header_lines = [
        f"Technique : {index}",
        f"{technique}"
    ]

    return '\n'.join(header_lines)


class HeaderField(object):
    def __init__(self, label: str, units: Optional[str] = None,
                 separator: str = ' : ', precision: int = 3,
                 add_linebreak: bool=False
                 ) -> None:
        self.label = label
        self.units = units
        self.separator = separator
        self.precision = precision
        self.add_linebreak = add_linebreak
        
    def __call__(self, value) -> str:            
        text = '{}{}{}'.format(self.label, self.separator, format_value(value, self.precision))
        
        if self.units is not None:
            text += f' {self.units}'
        
        if self.add_linebreak:
            text += "\n"
            
        return text
    
class OptionalField(HeaderField):
    def __init__(
            self, 
            label: str, 
            default_value,
            units: str | None = None, 
            separator: str = ' : ', 
            precision: int = 3, 
            add_linebreak: bool = False) -> None:
        
        super().__init__(label, units, separator, precision, add_linebreak)
        self.default_value = default_value
        
    def __call__(self, value) -> str:
        if value == self.default_value:
            return None
        return super().__call__(value)
    

class MapField(ABC):
    value_map: dict
    def __call__(self, value) -> str:
        value = self.value_map[value]
        return super().__call__(value)
    
# MapField.register(HeaderField)
    
class PathField(HeaderField):
    def __call__(self, value) -> str:
        value = Path(value).absolute()
        return super().__call__(value)
    

    
class MultilineField(HeaderField):
    def __call__(self, value: str) -> str:
        lines = value.split('\n')
        lines = [super().__call__(l) for l in lines]
        return '\n'.join(lines)
    
class RangeField(HeaderField):
    def __init__(self, label: str, 
                 range_separator: str,
                 min_label: Optional[str] = None, 
                 max_label: Optional[str] = None,
                 separator: str = ' : ',
                 units: Optional[str] = None, 
                 precision: int = 3,
                 add_linebreak: bool = False
                 ) -> None:
        super().__init__(label, units, separator, precision, add_linebreak)
        self.range_separator = range_separator
        self.min_label = min_label
        self.max_label = max_label
        
    def __call__(self, min_val, max_val) -> str:
        units = '' if self.units is None else f' {self.units}'
        
        value_text = "{}{}{}{}{}".format(
            format_value(min_val, self.precision), units, 
            self.range_separator,
            format_value(max_val, self.precision), units 
        )
        return super().__call__(value_text)
    
class MultivalueField(HeaderField):
    def __init__(self, label: str, 
                 value_labels: List[str],
                 value_separators: List[str],
                 value_units: List[str],
                 separator: str = ' : ',
                 precision: int = 3,
                 add_linebreak: bool = False
                 ) -> None:
        if len(value_units) != len(value_labels):
            raise ValueError("Length of value_units must match length of value_labels")
        if len(value_separators) != len(value_labels) - 1:
            raise ValueError("Length of value_separators must be one less than length of value_labels")
            
        super().__init__(label, None, separator, precision, add_linebreak)
        self.value_separators = value_separators
        self.value_labels = value_labels
        self.value_units = value_units
        
    def __call__(self, values: list) -> str:
        if len(values) != len(self.value_labels):
            raise ValueError(f"Length of values must match value_labels ({len(self.value_labels)})")
        
        unit_list = ['' if u is None else f' {u}' for u in self.value_units]
        
        value_texts = [
           f"{l}{format_value(v, self.precision)}{u}" 
           for l, v, u in zip(self.value_labels, values, unit_list)
        ]
        
        seps = self.value_separators + ['']
        value_text = "".join([f"{vt}{s}" for vt, s in zip(value_texts, seps)])
        
        return super().__call__(value_text)
    
NumTechniques = HeaderField("Number of linked techniques", add_linebreak=True)

SoftwareVersion = HeaderField("EC-LAB for windows v", units="(software)", separator="")
InternetServerVersion = HeaderField("Internet server v", units="(firmware)", separator="")
CommandInterpreterVersion = HeaderField("Command interpretor v", units="(firmware)", separator="", add_linebreak=True)

SettingsFilename = PathField("Filename", add_linebreak=True)

DeviceField = HeaderField('Device')
ComplianceVoltage = RangeField(
    'CE vs. WE compliance from', 
    range_separator=" to ",
    units="V", 
    separator=" ",
    precision=0
)
ElectrodeConnectionField = HeaderField("Electrode connection")
PotentialControlField = HeaderField("Potential control")
                    
EweControlRange = RangeField(
    "Ewe ctrl range",
    range_separator=", ",
    min_label="min = ",
    max_label="max = ",
    units="V",
    precision=2
)

# TODO: filter only applies to 300-series.  
Filtering = HeaderField("Ewe,I filtering")
# SafetyLimits

# Common metadata
ElectrodeMaterial = HeaderField("Electrode material")
InitialState = HeaderField("Initial state")
Electrolyte = HeaderField("Electrolyte")
Comments = MultilineField("Comments")


# Battery fields
Mass = MultivalueField(
    "Mass of active material", 
    value_labels=["", "at x = "],
    value_separators=["\n "],
    value_units=["mg", None]
)
MolecularWeight = HeaderField("Molecular weight of active material (at x=0)", units="g/mol")
AtomicWeight = HeaderField("Atomic weight of intercalated ion", units="g/mol")
AcquisitionStart = HeaderField("Aquisition started at: x0 = ", separator="")
NumElectrons = HeaderField("Number of e- transfered per intercalated ion", precision=0)
DxDq = HeaderField("for DX = 1, DQ = ", units="mA.h", separator="")
BatteryCapacity = HeaderField("Battery Capacity", units="mA.h")
# TODO: handle superscript? chr(178); 178=int("0x00B2", 0)
ElectrodeSurfaceArea = HeaderField("Electrode surface area", units="cm²")
CharacteristicMass = HeaderField("Characteristic mass", units="g")
# TODO: handle superscript?: chr(179); 179=int("0x00B3", 0)
Volume = HeaderField("Volume (V)", units="cm³")

# Corrosion fields
EquivalentWeight = HeaderField("Equivalent Weight", units="g/eq.")
Density = HeaderField("Density", units="g/cm3")


# Materials fields
Thickness = HeaderField("Thickness (t)", units="cm")
Diameter = HeaderField("Diameter (d)", units="cm")
CellConstant = HeaderField("Cell constant (k=t/A)", units="cm-1")

# Variable position fields
ReferenceElectrodeField = OptionalField("Reference electrode", default_value=ReferenceElectrode.NONE)

# Common trailing fields
TurnToOCV = HeaderField("", separator="")
CycleDefinitionField = HeaderField("Cycle Definition", units="alternance")

common_preceding_fields = [
    NumTechniques,
    SoftwareVersion,
    InternetServerVersion,
    CommandInterpreterVersion,
    SettingsFilename,
    DeviceField,
    ComplianceVoltage,
    ElectrodeConnectionField,
    PotentialControlField,
    EweControlRange,
    # SafetyLimits,
    ElectrodeMaterial,
    InitialState,
    Electrolyte,
    Comments
]

@dataclass
class CommonPrecedingFields(object):
    num_techniques: int
    software_version: str
    server_version: str
    interpreter_version: str
    settings_filename: Union[str, Path]
    device: BLDeviceModel
    v_range_min: float
    v_range_max: float
    v_compliance_min: int = -10
    v_compliance_max: int = 10
    electrode_connection: ElectrodeConnection = ElectrodeConnection.STANDARD
    potential_control: PotentialControl = PotentialControl.EWE
        


battery_fields = [
    Mass,
    MolecularWeight,
    AtomicWeight,
    AcquisitionStart,
    NumElectrons,
    DxDq,
    BatteryCapacity,
    ElectrodeSurfaceArea,
    CharacteristicMass,
    Volume
]

corrosion_fields = [
    ElectrodeSurfaceArea,
    CharacteristicMass,
    EquivalentWeight,
    Density,
    Volume
]

materials_fields = [
    ElectrodeSurfaceArea,
    CharacteristicMass,
    Volume,
    Thickness,
    Diameter,
    CellConstant
]

common_trailing_fields = [
    CycleDefinitionField,
    # TurnToOCV
]

