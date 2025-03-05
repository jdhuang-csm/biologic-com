import numpy as np
from numpy import ndarray
from typing import Optional, Union

class LinearIV(object):
    def __init__(self, i_mid: float, v_mid: float, dvdi: float):
        self.i_mid = i_mid
        self.v_mid = v_mid
        self.dvdi = dvdi
    
    def eval_v(self, i: Union[float, ndarray]) -> Union[float, ndarray]:
        if not np.isscalar(i):
            i = np.asarray(i)
        return self.v_mid + (i - self.i_mid) * self.dvdi


    def eval_i(self, v: Union[float, ndarray]):
        if not np.isscalar(v):
            v = np.asarray(v)
        return self.i_mid + (v - self.v_mid) * self.dvdi ** -1


    def _eval_ac(self, s_dc: float, s_ac: float, output: str):
        out = getattr(self, f'eval_{output}')(np.array([s_dc - s_ac, s_dc, s_dc + s_ac]))
        out_dc = out[1]
        out_ac = abs(out[-1] - out[0]) / 2
        
        return out_dc, out_ac
        
    def eval_iac(self, v_dc: float, v_ac: float):
        return self._eval_ac(v_dc, v_ac, 'i')
    
    def eval_vac(self, i_dc: float, i_ac: float):
        return self._eval_ac(i_dc, i_ac, 'v')
        