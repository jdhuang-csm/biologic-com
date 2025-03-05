from pathlib import Path
from typing import Any, Union, Optional, List

from .common import BLDeviceModel, ReferenceElectrode
from .write_utils import format_value

class HeaderField(object):
    def __init__(
            self, 
            label: str, 
            units: Optional[str] = None,
            separator: str = ' : ', 
            precision: int = 3,
            add_linebreak: bool = False,
            devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        self.label = label
        self.units = units
        self.separator = separator
        self.precision = precision
        self.add_linebreak = add_linebreak
        self.devices = devices
        
    def check_device(self, device: BLDeviceModel):
        # Check if this field applies to the selected device
        if self.devices is not None:
            if device not in self.devices:
                return False
        return True
        
    def __call__(self, value, device: BLDeviceModel) -> str:
        # If the field is not relevant to the device type,
        # return None
        if not self.check_device(device):
            return None
            
        text = '{}{}{}'.format(self.label, self.separator, format_value(value, self.precision))
        
        if self.units is not None:
            text += f' {self.units}'
        
        if self.add_linebreak:
            text += "\n"
            
        return text
    
class OptionalField(HeaderField):
    # For fields that only appear if a non-default value is selected
    # Example: reference electrode
    def __init__(
            self, 
            label: str, 
            default_value,
            units: str | None = None, 
            separator: str = ' : ', 
            precision: int = 3, 
            add_linebreak: bool = False,
            devices: Optional[List[BLDeviceModel]] = None
            ) -> None:
        
        super().__init__(label, units, separator, precision, add_linebreak, devices)
        self.default_value = default_value
        
    def __call__(self, value, device: BLDeviceModel) -> str:
        if value == self.default_value:
            return None
        return super().__call__(value, device)
    
class CheckboxField(HeaderField):
    # For fields that appear only if a box is checked
    # and specify a variable value
    def __call__(self, value, device: BLDeviceModel) -> str:
        if value is None:
            # value of None indicates that box is not checked
            return None
        return super().__call__(value, device)
    
class BooleanCheckboxField(HeaderField):
    # For fields that appear only if a box is checked,
    # and always have the same value if checked
    def __init__(self, 
            label: str, 
            add_linebreak: bool = False, 
            devices: List[BLDeviceModel] | None = None) -> None:
        super().__init__(label, None, "", 1, add_linebreak, devices)
        
    def __call__(self, value: bool, device: BLDeviceModel) -> str:
        if not value:
            # value of None of False indicates that box is not checked
            return None
        # Value of True indicates box is checked; 
        # no text should be added to label
        return super().__call__('', device)
    
    
class PathField(HeaderField):
    def __call__(self, value, device: BLDeviceModel) -> str:
        value = Path(value).absolute()
        return super().__call__(value, device)

    
class MultilineField(HeaderField):
    def __call__(self, value: Union[str, list], device: BLDeviceModel) -> str:
        """Value can either be a list of strings, each of which will
        appear on its own line, or a single string with line breaks.
        In either case, each line will begin with the header label.
        
        :param Union[str, list] value: String or list input
        :param BLDeviceModel device: Device model
        :return str: string to write
        """
        if not self.check_device(device):
            return None
        
        if isinstance(value, str):
            # If values is a string with line breaks, 
            # split at line breaks
            lines = value.split('\n')
        else:
            # If value is a list, each entry will appear on its own line
            lines = value
        lines = [super().__call__(l, device) for l in lines]
        return '\n'.join(lines)
    
class RangeField(HeaderField):
    def __init__(self, label: str, 
                 range_separator: str,
                 min_label: Optional[str] = None, 
                 max_label: Optional[str] = None,
                 separator: str = ' : ',
                 units: Optional[str] = None, 
                 precision: int = 3,
                 add_linebreak: bool = False,
                 devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        super().__init__(label, None, separator, precision, add_linebreak, devices)
        self.range_separator = range_separator
        self.min_label = min_label
        self.max_label = max_label
        self.range_units = units
        
    def __call__(self, min_val, max_val, device: BLDeviceModel) -> str:
        units = '' if self.range_units is None else f' {self.range_units}'
        
        value_text = "{}{}{}{}{}{}{}".format(
            self.min_label or '',
            format_value(min_val, self.precision), units, 
            self.range_separator,
            self.max_label or '',
            format_value(max_val, self.precision), units 
        )
        return super().__call__(value_text, device)
    
class MultivalueField(HeaderField):
    def __init__(self, label: str, 
                 value_labels: List[str],
                 value_separators: List[str],
                 value_units: List[str],
                 separator: str = ' : ',
                 precision: int = 3,
                 add_linebreak: bool = False,
                 devices: Optional[List[BLDeviceModel]] = None
                 ) -> None:
        if len(value_units) != len(value_labels):
            raise ValueError("Length of value_units must match length of value_labels")
        if len(value_separators) != len(value_labels) - 1:
            raise ValueError("Length of value_separators must be one less than length of value_labels")
            
        super().__init__(label, None, separator, precision, add_linebreak, devices)
        self.value_separators = value_separators
        self.value_labels = value_labels
        self.value_units = value_units
        
    def __call__(self, values: list, device: BLDeviceModel) -> str:
        if len(values) != len(self.value_labels):
            raise ValueError(f"Length of values must match value_labels ({len(self.value_labels)})")
        
        unit_list = ['' if u is None else f' {u}' for u in self.value_units]
        
        value_texts = [
           f"{l}{format_value(v, self.precision)}{u}" 
           for l, v, u in zip(self.value_labels, values, unit_list)
        ]
        
        seps = self.value_separators + ['']
        value_text = "".join([f"{vt}{s}" for vt, s in zip(value_texts, seps)])
        
        return super().__call__(value_text, device)
    
# -----------------------
# Define header fields
# -----------------------
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
    precision=0,
    devices=[BLDeviceModel.SP150] # TODO: which devices does this apply to?
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

# Filtering applies only to 300 series
Filtering = HeaderField(
    "Ewe,I filtering", 
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)

# Safety and advanced settings
# SafetyLimits
SafetyEweMin = CheckboxField("Ewe min", "V", separator=" = ")
SafetyEweMax = CheckboxField("Ewe max", "V", separator=" = ")
SafetyIabs = CheckboxField("|I|", "mA", separator=" = ")
SafetyDQ = CheckboxField("|Q-Qo|", "mA.h", separator=" = ")
SafetyAux1Min = CheckboxField("An In 1 min", separator=" = ")
SafetyAux1Max = CheckboxField("An In 1 max", separator=" = ")
SafetyAux2Min = CheckboxField("An In 2 min", separator=" = ")
SafetyAux2Max = CheckboxField("An In 2 max", separator=" = ")
SafetyDuration = CheckboxField("for t", "ms", separator=" > ")
SafetyNoStartOnOverload = BooleanCheckboxField("Do not start on E overload")

# Record additional variables
RecordEce = BooleanCheckboxField("Record ECE")
RecordAux1 = BooleanCheckboxField("Record Analogic IN 1")
RecordAux2 = BooleanCheckboxField("Record Analogic IN 2")
RecordPower = BooleanCheckboxField("Record Power")
RecordEISQuality = BooleanCheckboxField("Record EIS quality indicators")

# One data file per loop
CreateOneFilePerLoop = BooleanCheckboxField("Create one data file per loop")

# Cycle definition
CycleDefinitionField = HeaderField("Cycle Definition", units="alternance")


TurnToOCV = HeaderField("", separator="")

# Channel grounding applies only to 300 series (?)
ChannelGroundingField = HeaderField(
    "Channel",
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)

# Common metadata
ElectrodeMaterial = HeaderField("Electrode material")
InitialState = HeaderField("Initial state")
Electrolyte = HeaderField("Electrolyte")
Comments = MultilineField("Comments")

# Cable type applies only to 300 series (?)
CableTypeField = HeaderField(
    "Cable",
    devices=[
        BLDeviceModel.SP300, 
        BLDeviceModel.VMP300, 
        BLDeviceModel.VSP300
    ]
)
ReferenceElectrodeField = OptionalField("Reference electrode", 
                                        default_value=ReferenceElectrode.NONE)

# Battery fields
ActiveMass = MultivalueField(
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
