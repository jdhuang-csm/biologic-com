from numpy import ndarray
from typing import Optional

from .technique import TechniqueParameters, pad_text, value2str
from ...utils import isiterable
from ... import units




def process_list_values(vals: list, base_unit: Optional[str], replace_none=None):
    scaled_vals = [units.get_scaled_value(v) for v in vals]
    unit = [units.get_prefix_char(v) + base_unit for v in vals]
    
    if replace_none is not None:
        # Replace Nones with specified value
        scaled_vals = [v or replace_none for v in scaled_vals]
        
    return scaled_vals, unit
    
    
# class ChronoParametersBase(object):
#     step_durations: list
    
#     @property
#     def num_steps(self):
#         return len(self.step_durations)
    
#     def listify_attr(self, name: str, base_unit: str = None, replace_none=None):
#         """Format stepwise attribute as list.

#         :param str name: Attribute name.
#         :param str base_unit: base unit (e.g. V, A, C). If provided, 
#             appropriate unit prefixes will be selected and values
#             will be scaled accordingly. The scaled values and prefixed
#             units will be stored in _{name}_scaled and _{name}_units,
#             respectively. Defaults to None (no scaling).
#         :param Any replace_none: If provided, replace None with this 
#             value. Defaults to None (no replacement).
#         """
#         vals = getattr(self, name)
        
#         if not isiterable(vals) or isinstance(vals, str):
#             # Convert scalar to list
#             vals = [vals or replace_none] * self.num_steps
#         elif replace_none is not None:
#             # Replace Nones
#             vals = [v or replace_none for v in vals]
            
#         setattr(self, name, vals)
        
#         if base_unit is not None:
#             # Scale values and get units
#             scaled_vals, unit = process_list_values(vals, base_unit)
#             setattr(self, f"_{name}_scaled", scaled_vals)
#             setattr(self, f"_{name}_unit", unit)
            
            
class StepwiseTechniqueParameters(TechniqueParameters):
    """Base class for stepwise techniques like chronoamperometry, 
    chronopotentiometry, etc."""
    num_steps: int

    @property
    def step_index(self):
        return list(range(self.num_steps))

    def key2str(self, key):
        attr = self._param_map[key]
        values = getattr(self, attr)

        # Convert single values to lists
        if not (isinstance(values, list) or isinstance(values, ndarray)):
            values = [values] * self.num_steps

        str_list = [f'{pad_text(key)}'] + [f'{value2str(v)}' for v in values]
        return ''.join(str_list)
    
    
    def listify_attr(self, name: str, base_unit: str = None, replace_none=None):
        """Format stepwise attribute as list.

        :param str name: Attribute name.
        :param str base_unit: base unit (e.g. V, A, C). If provided, 
            appropriate unit prefixes will be selected and values
            will be scaled accordingly. The scaled values and prefixed
            units will be stored in _{name}_scaled and _{name}_units,
            respectively. Defaults to None (no scaling).
        :param Any replace_none: If provided, replace None with this 
            value. Defaults to None (no replacement).
        """
        vals = getattr(self, name)
        
        if not isiterable(vals) or isinstance(vals, str):
            # Convert scalar to list
            vals = [vals or replace_none] * self.num_steps
        elif replace_none is not None:
            # Replace Nones
            vals = [v if v is not None else replace_none for v in vals]
            
        setattr(self, name, vals)
        
        if base_unit is not None:
            # Scale values and get units
            scaled_vals, unit = process_list_values(vals, base_unit)
            setattr(self, f"_{name}_scaled", scaled_vals)
            setattr(self, f"_{name}_unit", unit)