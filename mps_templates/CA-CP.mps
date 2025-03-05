EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v0.00 (firmware)
Command interpretor v0.00 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\CA-CP.mps

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
Turn to OCV between techniques

Technique : 1
Chronoamperometry / Chronocoulometry
Ns                  0                   1                   
Ei (V)              0.350               0.350               
vs.                 Ref                 Ref                 
ti (h:m:s)          0:00:10.0000        0:00:10.0000        
Imax                pass                pass                
unit Imax           mA                  mA                  
Imin                pass                pass                
unit Imin           mA                  mA                  
dQM                 0.000               0.000               
unit dQM            mA.h                mA.h                
record              I                   I                   
dI                  5.000               5.000               
unit dI             µA                  µA                  
dQ                  0.000               0.000               
unit dQ             mA.h                mA.h                
dt (s)              0.1000              0.5000              
dta (s)             0.1000              0.1000              
E range min (V)     -2.500              -2.500              
E range max (V)     2.500               2.500               
I Range             Auto Limited        Auto Limited        
I Range min         10 µA               10 µA               
I Range max         1 A                 1 A                 
I Range init        10 µA               10 µA               
Bandwidth           5                   5                   
goto Ns'            0                   0                   
nc cycles           0                   0                   

Technique : 2
Chronopotentiometry
Is                  50.000              
unit Is             µA                  
vs.                 <None>              
ts (h:m:s)          0:00:10.0000        
EM (V)              pass                
dQM                 138.889             
unit dQM            nA.h                
record              <Ewe>               
dEs (mV)            0.00                
dts (s)             0.1000              
E range min (V)     -2.500              
E range max (V)     2.500               
I Range             100 µA              
Bandwidth           5                   
goto Ns'            0                   
nc cycles           0                   
