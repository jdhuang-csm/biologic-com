EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.50 (software)
Internet server v11.50 (firmware)
Command interpretor v11.50 (firmware)

Filename : C:\Users\jhuang2\python\biologic-com\OCV-CA_olecom.mps

Device : SP-150
CE vs. WE compliance from -10 V to 10 V
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -1,00 V, max = 1,00 V
Safety Limits :
	Do not start on E overload
Electrode material : 
Initial state : 
Electrolyte : 
Comments : 
Electrode surface area : 0,001 cm²
Characteristic mass : 0,001 g
Equivalent Weight : 0,000 g/eq.
Density : 0,000 g/cm3
Volume (V) : 0,001 cm³
Cycle Definition : Charge/Discharge alternance
Do not turn to OCV between techniques

Technique : 1
Open Circuit Voltage
tR (h:m:s)          00:00:10,0000       
dER/dt (mV/h)       0,000               
record              Ewe                 
dER (mV)            0,000               
dtR (s)             0,100               
E range min (V)     -1,000              
E range max (V)     1,000               

Technique : 2
Chronoamperometry / Chronocoulometry
Ns                  0                   1                   2                   
Ei (V)              0                   -0,010              0,010               
vs.                 Ref                 Ref                 Ref                 
ts (h:m:s)          00:00:01,0000       00:00:05,0000       00:00:05,0000       
Imax                pass                pass                pass                
unit Imax           A                   A                   A                   
Imin                pass                pass                pass                
unit Imin           A                   A                   A                   
dQM                 pass                pass                pass                
unit dQM            A.h                 A.h                 A.h                 
record              I                   I                   I                   
dI                  0,000               0,000               0,000               
unit dI             A                   A                   A                   
dQ                  0,000               0,000               0,000               
unit dQ             A.h                 A.h                 A.h                 
dt (s)              0,001               0,001               0,001               
dta (s)             0,001               0,001               0,001               
E range min (V)     -1,000              -1,000              -1,000              
E range max (V)     1,000               1,000               1,000               
I Range             Auto                Auto                Auto                
I Range min         None                None                None                
I Range max         None                None                None                
I Range init        None                None                None                
Bandwidth           7                   7                   7                   
goto Ns'            0                   0                   0                   
nc cycles           0                   0                   0                   