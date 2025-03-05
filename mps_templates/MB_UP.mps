EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\MB_UP.mps

Device : SP-150
CE vs. WE compliance from -10 V to 10 V
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -10.00 V, max = 10.00 V
Safety Limits :
	Do not start on E overload
Electrode material : 
Initial state : 
Electrolyte : 
Comments : 
Electrode surface area : 0.001 cm²
Characteristic mass : 0.001 g
Equivalent Weight : 0.000 g/eq.
Density : 0.000 g/cm3
Volume (V) : 0.001 cm³
Cycle Definition : Charge/Discharge alternance
Do not turn to OCV between techniques

Technique : 1
Potentio Electrochemical Impedance Spectroscopy
Mode                Single sine         
E (V)               0.0000              
vs.                 Eoc                 
tE (h:m:s)          0:00:0.0000         
record              0                   
dI                  0.000               
unit dI             A                   
dt (s)              1.000               
fi                  100.000             
unit fi             kHz                 
ff                  1.000               
unit ff             Hz                  
Nd                  10                  
Points              per decade          
spacing             Logarithmic         
Va (mV)             10.0                
pw                  0.10                
Na                  2                   
corr                0                   
E range min (V)     -10.000             
E range max (V)     10.000              
I Range             Auto                
Bandwidth           7                   
nc cycles           0                   
goto Ns'            0                   
nr cycles           0                   
inc. cycle          0                   

Technique : 2
Modulo Bat
ctrl_type           UP                  
Apply I/C           I                   
current/potential   current             
ctrl1_val                               
ctrl1_val_unit                          
ctrl1_val_vs                            
ctrl2_val                               
ctrl2_val_unit                          
ctrl2_val_vs                            
ctrl3_val                               
ctrl3_val_unit                          
ctrl3_val_vs                            
N                   0.00                
charge/discharge    Charge              
charge/discharge_1  Charge              
Apply I/C_1         I                   
N1                  0.00                
ctrl4_val                               
ctrl4_val_unit                          
ctrl5_val                               
ctrl5_val_unit                          
ctrl_tM             0                   
ctrl_seq            0                   
ctrl_repeat         0                   
ctrl_trigger        Rising Edge         
ctrl_TO_t           0.000               
ctrl_TO_t_unit      s                   
ctrl_Nd             6                   
ctrl_Na             2                   
ctrl_corr           0                   
lim_nb              1                   
lim1_type           Time                
lim1_comp           >                   
lim1_Q              Q limit             
lim1_value          10.000              
lim1_value_unit     s                   
lim1_action         Next sequence       
lim1_seq            1                   
rec_nb              1                   
rec1_type           Time                
rec1_value          0.001               
rec1_value_unit     s                   
E range min (V)     -10.000             
E range max (V)     10.000              
I Range             10 mA               
I Range min         Unset               
I Range max         Unset               
I Range init        Unset               
auto rest           1                   
Bandwidth           5                   

Urban Profile Table
Technique Number : 2
Sequence : 0
Number of Values : 101
Values : Time/s, E/V
0.00000	0.00000
0.00040	0.24485
0.00081	0.46213
0.00121	0.63947
0.00162	0.76768
0.00202	0.84107
0.00242	0.85774
0.00283	0.81944
0.00323	0.73131
0.00364	0.60138
0.00404	0.43992
0.00444	0.25869
0.00485	0.07009
0.00525	-0.11359
0.00566	-0.28101
0.00606	-0.42240
0.00646	-0.53013
0.00687	-0.59906
0.00727	-0.62676
0.00768	-0.61353
0.00808	-0.56223
0.00848	-0.47797
0.00889	-0.36772
0.00929	-0.23971
0.00970	-0.10290
0.01010	0.03362
0.01051	0.16127
0.01091	0.27241
0.01131	0.36086
0.01172	0.42215
0.01212	0.45376
0.01253	0.45516
0.01293	0.42776
0.01333	0.37471
0.01374	0.30064
0.01414	0.21125
0.01455	0.11296
0.01495	0.01240
0.01535	-0.08396
0.01576	-0.17025
0.01616	-0.24153
0.01657	-0.29403
0.01697	-0.32537
0.01737	-0.33462
0.01778	-0.32228
0.01818	-0.29022
0.01859	-0.24142
0.01899	-0.17980
0.01939	-0.10988
0.01980	-0.03649
0.02020	0.03557
0.02061	0.10183
0.02101	0.15837
0.02141	0.20212
0.02182	0.23094
0.02222	0.24376
0.02263	0.24056
0.02303	0.22233
0.02343	0.19097
0.02384	0.14910
0.02424	0.09990
0.02465	0.04683
0.02505	-0.00657
0.02545	-0.05692
0.02586	-0.10118
0.02626	-0.13686
0.02667	-0.16213
0.02707	-0.17592
0.02747	-0.17792
0.02788	-0.16859
0.02828	-0.14908
0.02869	-0.12113
0.02909	-0.08691
0.02949	-0.04891
0.02990	-0.00969
0.03030	0.02819
0.03071	0.06242
0.03111	0.09102
0.03152	0.11245
0.03192	0.12572
0.03232	0.13041
0.03273	0.12662
0.03313	0.11503
0.03354	0.09676
0.03394	0.07328
0.03434	0.04634
0.03475	0.01780
0.03515	-0.01044
0.03556	-0.03663
0.03596	-0.05921
0.03636	-0.07693
0.03677	-0.08892
0.03717	-0.09470
0.03758	-0.09422
0.03798	-0.08782
0.03838	-0.07619
0.03879	-0.06032
0.03919	-0.04143
0.03960	-0.02087
0.04000	0.00000
0.04040	0.00000
