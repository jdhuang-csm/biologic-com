EC-LAB SETTING FILE

Number of linked techniques : 1

EC-LAB for windows v11.50 (software)
Internet server v11.52 (firmware)
Command interpretor v11.50 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\mps_templates\CA_limit.mps

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
Chronoamperometry / Chronocoulometry
Ns                  0                   1                   2                   3                   
Ei (V)              0.000               0.010               -0.010              0.000               
vs.                 Ref                 Ref                 Ref                 Ref                 
ti (h:m:s)          0:00:0.5000         0:00:0.5000         0:00:0.5000         0:00:1.0000         
Imax                0.010               10.000              pass                pass                
unit Imax           mA                  µA                  mA                  mA                  
Imin                -0.010              -10.000             pass                pass                
unit Imin           mA                  µA                  mA                  mA                  
dQM                 0.000               0.000               0.000               0.000               
unit dQM            mA.h                mA.h                mA.h                mA.h                
record              I                   I                   I                   I                   
dI                  5.000               5.000               5.000               5.000               
unit dI             µA                  µA                  µA                  µA                  
dQ                  0.000               0.000               0.000               0.000               
unit dQ             mA.h                mA.h                mA.h                mA.h                
dt (s)              0.0100              0.0100              0.0100              0.0100              
dta (s)             0.0100              0.0100              0.0100              0.0100              
E range min (V)     -2.500              -2.500              -2.500              -2.500              
E range max (V)     2.500               2.500               2.500               2.500               
I Range             Auto                Auto                Auto                Auto                
I Range min         Unset               Unset               Unset               Unset               
I Range max         Unset               Unset               Unset               Unset               
I Range init        Unset               Unset               Unset               Unset               
Bandwidth           5                   5                   5                   5                   
goto Ns'            0                   0                   0                   0                   
nc cycles           0                   0                   0                   0                   
