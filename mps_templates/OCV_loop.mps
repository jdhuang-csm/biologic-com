EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\OCV_loop.mps

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
Electrode surface area : 0.000 cm²
Characteristic mass : 0.001 g
Equivalent Weight : 0.000 g/eq.
Density : 0.000 g/cm3
Volume (V) : 0.001 cm³
Cycle Definition : Charge/Discharge alternance
Turn to OCV between techniques

Technique : 1
Open Circuit Voltage
tR (h:m:s)          0:00:30.0000        
dER/dt (mV/h)       1.0                 
record              <Ewe>               
dER (mV)            0.00                
dtR (s)             0.5000              
E range min (V)     -10.000             
E range max (V)     10.000              

Technique : 2
Loop
goto Ne             1                   
nt times            2                   
