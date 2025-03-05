EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\cp-peis_batt.mps

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
Mass of active material : 0.001 mg
 at x = 0.000
Molecular weight of active material (at x = 0) : 0.001 g/mol
Atomic weight of intercalated ion : 0.001 g/mol
Acquisition started at : xo = 0.000
Number of e- transfered per intercalated ion : 1
for DX = 1, DQ = 26.802 mA.h
Battery capacity : 0.000 A.h
Electrode surface area : 0.001 cm²
Characteristic mass : 0.001 g
Volume (V) : 0.001 cm³
Cycle Definition : Charge/Discharge alternance
Turn to OCV between techniques

Technique : 1
Chronopotentiometry
Ns                  0                   1                   
Is                  0.000               50.000              
unit Is             A                   µA                  
vs.                 <None>              <None>              
ts (h:m:s)          0:00:10.0000        0:00:10.0000        
EM (V)              pass                pass                
dQM                 0.000               138.889             
unit dQM            mA.h                nA.h                
record              <Ewe>               <Ewe>               
dEs (mV)            0.00                0.00                
dts (s)             0.1000              0.1000              
E range min (V)     -10.000             -10.000             
E range max (V)     10.000              10.000              
I Range             10 mA               10 mA               
Bandwidth           7                   7                   
goto Ns'            0                   1                   
nc cycles           0                   0                   

Technique : 2
Potentio Electrochemical Impedance Spectroscopy
Mode                Single sine         
E (V)               0.0000              
vs.                 Eoc                 
tE (h:m:s)          0:00:0.0000         
record              0                   
dI                  0.000               
unit dI             mA                  
dt (s)              0.000               
fi                  200.000             
unit fi             kHz                 
ff                  100.000             
unit ff             mHz                 
Nd                  6                   
Points              per decade          
spacing             Logarithmic         
Va (mV)             10.0                
pw                  0.10                
Na                  2                   
corr                0                   
E range min (V)     -10.000             
E range max (V)     10.000              
I Range             Auto                
Bandwidth           5                   
nc cycles           3                   
goto Ns'            1                   
nr cycles           2                   
inc. cycle          1                   
