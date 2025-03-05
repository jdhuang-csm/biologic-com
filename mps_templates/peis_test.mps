EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\peis_test.mps

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
Turn to OCV between techniques

Technique : 1
Chronopotentiometry
Ns                  0                   1                   
Is                  50.000              50.000              
unit Is             µA                  µA                  
vs.                 <None>              Ictrl               
ts (h:m:s)          0:00:10.0000        0:00:10.0000        
EM (V)              pass                pass                
dQM                 138.889             0.000               
unit dQM            nA.h                nA.h                
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
