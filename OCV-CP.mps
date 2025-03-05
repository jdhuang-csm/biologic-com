EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v11.50 (firmware)
Command interpretor v11.50 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\OCV-CP.mps

Device : SP-300
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -10.00 V, max = 10.00 V
Ewe,I filtering : <None>
Safety Limits :
	Do not start on E overload
Channel : Floating
Electrode material : 
Initial state : 
Electrolyte : 
Comments : here is my comment
Comments : Line 2
Cable : Standard
Electrode surface area : 0.001 cm²
Characteristic mass : 0.001 g
Equivalent Weight : 0.000 g/eq.
Density : 0.000 g/cm3
Volume (V) : 0.001 cm³
Cycle Definition : Charge/Discharge alternance
Turn to OCV between techniques

Technique : 1
Open Circuit Voltage
tR (h:m:s)          00:00:10.0000       
dER/dt (mV/h)       0.000               
record              Ewe                 
dER (mV)            0.000               
dtR (s)             0.100               
E range min (V)     -10.000             
E range max (V)     10.000              

Technique : 2
Chronopotentiometry
Ns                  0                   1                   2                   
Is                  0.000               -1.000              1.000               
unit Is             A                   mA                  mA                  
vs.                 <None>              <None>              <None>              
ts (h:m:s)          00:00:01.0000       00:00:02.0000       00:00:02.0000       
EM (V)              pass                pass                pass                
dQM                 0.000               0.000               0.000               
unit dQM            A.h                 A.h                 A.h                 
record              Ewe                 Ewe                 Ewe                 
dEs (mV)            0.000               0.000               0.000               
dts (s)             0.001               0.001               0.001               
E range min (V)     -10.000             -10.000             -10.000             
E range max (V)     10.000              10.000              10.000              
I Range             10 mA               10 mA               10 mA               
Bandwidth           7                   7                   7                   
goto Ns'            0                   0                   0                   
nc cycles           0                   0                   0                   