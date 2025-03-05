EC-LAB SETTING FILE

Number of linked techniques : 3

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\OCV-EIS_loop.mps

Device : SP-150
CE vs. WE compliance from -10 V to 10 V
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -2.50 V, max = 2.50 V
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
Open Circuit Voltage
tR (h:m:s)          0:00:30.0000        
dER/dt (mV/h)       1.0                 
record              <Ewe>               
dER (mV)            0.00                
dtR (s)             0.5000              
E range min (V)     -2.500              
E range max (V)     2.500               

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
E range min (V)     -2.500              
E range max (V)     2.500               
I Range             Auto                
Bandwidth           5                   
nc cycles           0                   
goto Ns'            1                   
nr cycles           2                   
inc. cycle          1                   

Technique : 3
Loop
goto Ne             1                   
nt times            2                   
