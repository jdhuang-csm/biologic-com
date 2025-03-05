import numpy as np
import warnings
from typing import List

from .technique import HardwareParameters, TechniqueParameters
from ..write_utils import FilePath
from .mb import MBSequence
from ..config import FullConfiguration



class TechniqueSequence(list):
    # def __init__(self, techniques: List[TechniqueParameters]) -> None:
    #     self.technique_list = techniques

    def __init__(self, techniques: List[TechniqueParameters]) -> None:
        super().__init__(techniques)

        self.set_v_limits()
        
        
    def apply_configuration(self, configuration: FullConfiguration):
        for t in self:
            t.apply_configuration(configuration)


    def set_v_limits(self):
        # Check v ranges: EC-Lab uses the same voltage range for all techniques
        for agg in ["min", "max"]:
            long_agg = "minimum" if agg == "min" else "maximum"
            v_lim = [getattr(t, f"v_range_{agg}") for t in self if hasattr(t, f"v_range_{agg}")]
            if len(np.unique(v_lim)) > 1:
                # Multiple voltage ranges provided. Set a single voltage range
                v_lim = getattr(np, agg)(v_lim)
                warnings.warn(f"Multiple {long_agg} voltage limits were provided in the technique "
                            "sequence, but EC-Lab requires a single voltage limit."
                            f"The {long_agg} voltage will be set to the {long_agg} provided value "
                            "across all techniques: {:.1f} V.".format(v_lim)
                            )
                for t in self:
                    setattr(t, f"v_range_{agg}", v_lim)

    def append(self, technique):
        super().append(technique)
        self.set_v_limits()

    @property
    def num_techniques(self) -> int:
        return len(self)

    @property
    def abbreviations(self):
        return [t.abbreviation for t in self]

    def technique_text(self, index, configuration):
        technique = self[index]

        # Header
        header = [
            f'Technique : {index + 1}',
            technique.technique_name
        ]

        # Parameter block
        param_text = technique.param_text(index + 1)

        return '\n'.join(header + [param_text])

    def sequence_text(self):
        # Get block for each technique
        text = [
            self.technique_text(i)
            for i in range(len(self))
        ]

        tables = []
        for i, technique in enumerate(self):
            if isinstance(technique, MBSequence):
                tables += technique.get_urban_tables(i + 1)

        # Separate techniques with double line breaks
        return '\n\n'.join(text + tables)

    def write_params(self, file: FilePath, append: bool = False):
        if append:
            mode = "a"
        else:
            mode = "w"

        with open(file, mode) as f:
            f.write(self.sequence_text())