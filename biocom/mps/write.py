from pathlib import Path
from typing import Union, Optional, List

from .techniques.sequence import TechniqueSequence


from .config import (
    BasicConfig, HardwareSettings, CellCharacteristics, 
    BatteryCharacteristics, CorrosionCharacteristics,  MaterialsCharacteristics, 
    RecordingOptions, SafetySettings, MiscOptions
)
from . import headerfields
from .common import (
    CycleDefinition, TurnToOCV
)
from ..units import calculate_dqdx
from .techniques.technique import TechniqueParameters
from .config import FullConfiguration


# Included in TechniqueSequence
# def get_technique_header(index: int, technique):
#     # TODO: technique enum?
#     header_lines = [
#         f"Technique : {index}",
#         f"{technique}"
#     ]

#     return '\n'.join(header_lines)


def make_header(
        configuration: FullConfiguration
    ):

    basic_config = configuration.basic
    hardware_settings = configuration.hardware
    safety_settings = configuration.safety
    recording_options = configuration.recording
    cell_characteristics = configuration.cell
    sample_characteristics = configuration.sample
    misc_options = configuration.misc
    
    if not any(
        [isinstance(sample_characteristics, c) 
         for c in [
             BatteryCharacteristics, 
             CorrosionCharacteristics, 
             MaterialsCharacteristics
            ]
         ]
    ):
        raise TypeError("sample_characteristics must be an instance of BatteryCharacteristics, "
                        "CorrosionCharacteristics, or MaterialsCharacteristics. "
                        f"Got type {type(sample_characteristics)}")
    
    device = basic_config.device
    
    # Get basic config block
    basic_fields = [
        headerfields.NumTechniques(basic_config.num_techniques, device),
        headerfields.SoftwareVersion(basic_config.software_version, device),
        headerfields.InternetServerVersion(basic_config.server_version, device),
        headerfields.CommandInterpreterVersion(basic_config.interpreter_version, device),
        headerfields.SettingsFilename(basic_config.settings_filename, device),
        headerfields.DeviceField(device, device)
    ]
    
    # Hardware config block
    hardware_fields = [
        headerfields.ComplianceVoltage(hardware_settings.v_comp_min, hardware_settings.v_comp_max, device),
        headerfields.ElectrodeConnectionField(hardware_settings.electrode_connection, device),
        headerfields.PotentialControlField(hardware_settings.potential_control, device),
        headerfields.EweControlRange(hardware_settings.v_range_min, hardware_settings.v_range_max, device),
        headerfields.Filtering(hardware_settings.filtering, device)
    ]
    
    # Get safety limits block
    safety_limits = [
        headerfields.SafetyEweMin(safety_settings.ewe_min, device),
        headerfields.SafetyEweMax(safety_settings.ewe_max, device),
        headerfields.SafetyIabs(safety_settings.iabs_mA, device),
        headerfields.SafetyDQ(safety_settings.dq_mAh, device),
        headerfields.SafetyAux1Min(safety_settings.aux1_min, device),
        headerfields.SafetyAux1Max(safety_settings.aux1_max, device),
        headerfields.SafetyAux2Min(safety_settings.aux2_min, device),
        headerfields.SafetyAux2Max(safety_settings.aux2_max, device),
        headerfields.SafetyDuration(safety_settings.duration_ms, device),
        headerfields.SafetyNoStartOnOverload(safety_settings.no_start_on_overload, device)
    ]
    
    # Cell fields 
    generic_cell_fields = [
        headerfields.ChannelGroundingField(hardware_settings.grounding, device),
        headerfields.ElectrodeMaterial(cell_characteristics.electrode_material, device),
        headerfields.InitialState(cell_characteristics.initial_state, device),
        headerfields.Electrolyte(cell_characteristics.electrolyte, device),
        headerfields.Comments(cell_characteristics.comments, device),
    ]
    
    # Sample-type-specific fields
    if isinstance(sample_characteristics, BatteryCharacteristics):
        dqdx = calculate_dqdx(sample_characteristics.active_mass_mg * 1e-3,
                              sample_characteristics.active_mol_wt_g,
                              sample_characteristics.num_electrons
                              )
        specific_cell_fields = [
            headerfields.ActiveMass([sample_characteristics.active_mass_mg, sample_characteristics.active_x], device),
            headerfields.MolecularWeight(sample_characteristics.active_mol_wt_g, device),
            headerfields.AtomicWeight(sample_characteristics.ion_at_wt_g, device),
            headerfields.AcquisitionStart(sample_characteristics.x0, device),
            headerfields.NumElectrons(sample_characteristics.num_electrons, device),
            headerfields.DxDq(dqdx, device),
            headerfields.BatteryCapacity(sample_characteristics.capacity_mAh, device),
            headerfields.CableTypeField(cell_characteristics.cable, device),
            headerfields.ReferenceElectrodeField(cell_characteristics.ref_electrode, device),
            headerfields.ElectrodeSurfaceArea(cell_characteristics.surface_area, device),
            headerfields.CharacteristicMass(cell_characteristics.char_mass, device),
            headerfields.Volume(cell_characteristics.volume, device),
        ]
    elif isinstance(sample_characteristics, CorrosionCharacteristics):
        specific_cell_fields = [
            headerfields.CableTypeField(cell_characteristics.cable, device),
            headerfields.ReferenceElectrodeField(cell_characteristics.ref_electrode, device),
            headerfields.ElectrodeSurfaceArea(cell_characteristics.surface_area, device),
            headerfields.CharacteristicMass(cell_characteristics.char_mass, device),
            headerfields.EquivalentWeight(sample_characteristics.equiv_wt, device),
            headerfields.Density(sample_characteristics.density, device),
            headerfields.Volume(cell_characteristics.volume, device),
        ]
    elif isinstance(sample_characteristics, MaterialsCharacteristics):
        specific_cell_fields = [
            headerfields.CableTypeField(cell_characteristics.cable, device),
            headerfields.ReferenceElectrodeField(cell_characteristics.ref_electrode, device),
            headerfields.ElectrodeSurfaceArea(cell_characteristics.surface_area, device),
            headerfields.CharacteristicMass(cell_characteristics.char_mass, device),
            headerfields.Volume(cell_characteristics.volume, device),
            headerfields.Thickness(sample_characteristics.thickness, device),
            headerfields.Diameter(sample_characteristics.diameter, device),
            headerfields.CellConstant(sample_characteristics.cell_constant, device)
        ]
        
    # Trailing fields
    trailing_fields = [
        headerfields.RecordEce(recording_options.ece, device),
        headerfields.RecordAux1(recording_options.aux1, device),
        headerfields.RecordAux2(recording_options.aux2, device),
        headerfields.RecordPower(recording_options.power, device),
        headerfields.RecordEISQuality(recording_options.eis_quality, device),
        headerfields.CreateOneFilePerLoop(misc_options.one_file_per_loop, device),
        headerfields.CycleDefinitionField(misc_options.cycle_definition, device),
        headerfields.TurnToOCV(misc_options.turn_to_ocv, device)
    ]
    
    def join_fields(field_list, sep: str = "\n"):
        # Remove Nones
        field_list = [f for f in field_list if f is not None]
        return sep.join(field_list)
    
    # Safety limits must be an indented block
    safety_limits_text =  join_fields(safety_limits, sep="\n\t")
    if len(safety_limits_text) > 0:
        safety_limits_text = "Safety Limits :\n\t" + safety_limits_text
    else:
        safety_limits_text = None
        
    
    # Fixed first line
    field_text = ['EC-LAB SETTING FILE\n']
    
    # Add all fields
    field_text += [
        join_fields(f) for f in [
            basic_fields,
            hardware_fields,
            generic_cell_fields,
            specific_cell_fields,
            trailing_fields
        ]
    ]
    
    # Safety limits goes between hardware and cell fields
    field_text = field_text[:3] + [safety_limits_text] + field_text[3:]
        
    return join_fields(field_text)
    

def write_techniques(
        techniques: TechniqueSequence,
        configuration: FullConfiguration,
        mps_file: Union[str, Path]
    ):  
    # if not isinstance(techniques, TechniqueParameters):
    #     if not isinstance(techniques, list):
    #         # Single technique provided - place in list
    #         techniques = [techniques]
        
    #     # Convert list of techniques to TechniqueSequence
    #     techniques = TechniqueSequence(techniques)
    
    # Update filename
    configuration.basic.settings_filename = mps_file
        
    header_text = make_header(configuration)
    
    # Apply the configuration to any techniques that need the corresponding info
    techniques.apply_configuration(configuration)
    
    with open(mps_file, 'w') as f:
        f.write(header_text)
        f.write("\n\n" + techniques.sequence_text())
    
    