from typing import Tuple, Optional

class UnitPrefix(object):
    scale_map = {
        'G': 1e9,
        'M': 1e6,
        'k': 1e3,
        '': 1,
        'm': 1e-3,
        'mu': 1e-6,
        'n': 1e-9
    }

    reverse_scale_map = {v: k for k, v in scale_map.items()}

    chr_map = {
        'mu': 181
    }
    
    reverse_char_map = {chr(v): k for k, v in chr_map.items()}

    def __init__(self, prefix):
        if prefix not in self.scale_map.keys():
            try:
                # Look up special characters
                prefix = self.reverse_char_map[prefix]
            except KeyError:
                raise ValueError(f"Unrecognized unit prefix: {prefix}")
        self.prefix = prefix

    @classmethod
    def from_value(cls, value, min_factor=None, max_factor=None):
        """
        Select appropriate prefix from value
        """
        # Get scale options from largest to smallest
        scales = list(reversed(sorted(list(cls.reverse_scale_map.keys()))))
        
        # Limit available scales
        if min_factor is not None:
            scales = [s for s in scales if s >= min_factor]
        if max_factor is not None:
            scales = [s for s in scales if s <= max_factor]

        if value == 0 or value is None:
            scale = 1
        else:
            # Set floor on magnitude to ensure that a matching scale is found
            value = max(abs(value), min(scales))
            
            # Get largest scale that is less than value
            scale = next(s for s in scales if value >= s)

        # Get corresponding prefix
        prefix = cls.reverse_scale_map[scale]

        return cls(prefix)


    def set_prefix(self, prefix):
        if prefix not in self.scale_map.keys():
            raise ValueError(f'Invalid prefix {prefix}. Options: {list(self.scale_map.values())}')

        self._prefix = prefix

    def get_prefix(self):
        return self._prefix

    prefix = property(get_prefix, set_prefix)

    @property
    def scale(self):
        return self.scale_map[self.prefix]

    @property
    def char(self):
        if self.chr_map.get(self.prefix, None) is not None:
            return chr(self.chr_map[self.prefix])
        return self.prefix

    def raw_to_scaled(self, raw_value):
        if raw_value is None:
            return None
        return raw_value / self.scale

    def scaled_to_raw(self, scaled_value):
        if scaled_value is None:
            return None
        return scaled_value * self.scale
    

def get_scaled_value(value):
    try:
        return UnitPrefix.from_value(value).raw_to_scaled(value)
    except TypeError:
        return value

def get_prefix_char(value):
    try:
        return UnitPrefix.from_value(value).char
    except TypeError:
        return ""
    
    
def get_scaled_value_and_prefix(value, min_factor: float = None, max_factor: float = None) -> Tuple[float, str]:
    unit = UnitPrefix.from_value(value, min_factor=min_factor, max_factor=max_factor)
    return unit.raw_to_scaled(value), unit.char
    
# Enumerate all possible prefix characters
_all_prefixes = [get_prefix_char(v) for v in UnitPrefix.scale_map.values()]

 
class TimeUnit(object):
    
    unit_values = {
        "d": 3600. * 24,
        "h": 3600.,
        "mn": 60.,
        "s": 1.,
        "ms": 1e-3
    }
    
    reverse_value_map = {v: k for k, v in unit_values.items()}
    
    def __init__(self, unit):
        self.unit = unit
        
    def set_unit(self, unit):
        if unit not in self.unit_values.keys():
            raise ValueError(f"Unrecognized unit: {unit}. Options: {list(self.unit_values.keys())}")
        self._unit = unit
        
    def get_unit(self):
        return self._unit
    
    unit = property(get_unit, set_unit)
    
    @property
    def value(self):
        return self.unit_values[self.unit]
        
    def convert(self, value: float, output_unit: str):
        input_val = self.value
        output_val = self.unit_values[output_unit]
        
        return value * input_val / output_val
        
    @classmethod
    def from_value(cls, value: float, input_unit: str = "s"):
        # Convert to seconds
        value_s = cls(input_unit).convert(value, "s")
        
        # Get scale options from largest to smallest
        values = reversed(sorted(list(cls.unit_values.values())))

        if value_s == 0 or value_s is None:
            unit_val = 1
        else:
            # Set floor on magnitude
            value_s = max(abs(value_s), 1e-3)
            
            # Get largest scale that is less than value
            unit_val = next(v for v in values if value_s >= v)

        # Get corresponding prefix
        unit = cls.reverse_value_map[unit_val]

        return cls(unit)
    
    def split_duration(duration: float):
        """Convert duration in seconds to hours, minutes, seconds, and milliseconds

        :param float duration: Duration in seconds
        :return Tuple[float, float, float, float]: hours, minutes, seconds, milliseconds
        """
        # Get hours, minutes, seconds
        h = int(duration / 3600.)
        m = int((duration % 3600.) / 60.)
        s = int(duration % 60.)

        # Get milliseconds
        ms = duration % 1
        ms = ms * 1000
        
        return h, m, s, ms
    

def get_scaled_time(t: float, input_unit: str = "s") -> Tuple[float, str]:
    output_unit = TimeUnit.from_value(t, input_unit).unit
    output_value = TimeUnit(input_unit).convert(t, output_unit)
    return output_value, output_unit


# Constants
Faraday = 96485 # C / mol


def coulombs2mAh(q: float) -> float:
    """
    Coulombs to milliamp-hours
    
    :param float q: Charge in Coulombs
    :return float: Charge in mAh
    """
    return q * 1000. / 3600.


def calculate_dqdx(mass: float, mol_wt: float, ne: int) -> float:
    """Calculate change in battery capacity (dq) vs. 
    stoichiometry change (dx).

    :param float mass: Mass of active material in g.
    :param float mol_wt: Molecular weight of active material in g/mol.
    :param int ne: Number of electrons transferred.
    :return float: dq/dx in mAh
    """
    dq = (mass / mol_wt) * ne * Faraday
    return coulombs2mAh(dq)

