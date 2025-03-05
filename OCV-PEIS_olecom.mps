EC-LAB SETTING FILE

Number of linked techniques : 2

EC-LAB for windows v11.52 (software)
Internet server v11.52 (firmware)
Command interpretor v11.52 (firmware)

Filename : C:\Users\AKZMESS002\python\biologic-com\OCV-PEIS_olecom.mps

Device : SP-300
Electrode connection : standard
Potential control : Ewe
Ewe ctrl range : min = -0,10 V, max = 0,10 V
Ewe,I filtering : <None>
Safety Limits :
	Do not start on E overload
Channel : Floating
Electrode material : 
Initial state : 
Electrolyte : 
Comments : 
Cable : standard
Electrode surface area : 0,001 cm²
Characteristic mass : 0,001 g
Equivalent Weight : 0,000 g/eq.
Density : 0,000 g/cm3
Volume (V) : 0,001 cm³
Cycle Definition : Charge/Discharge alternance
Turn to OCV between techniques

Technique : 1
Open Circuit Voltage
tR (h:m:s)          0:00:10,0000        
dER/dt (mV/h)       0,0                 
record              Ewe                 
dER (mV)            0,00                
dtR (s)             0,5000              
E range min (V)     -0,100              
E range max (V)     0,100               

Technique : 2
Potentio Electrochemical Impedance Spectroscopy
Mode                Single sine         
E (V)               0,0000              
vs.                 Eoc                 
tE (h:m:s)          0:00:0,0000         
record              0                   
dI                  0,000               
unit dI             A                   
dt (s)              1,000               
fi                  100,000             
unit fi             kHz                 
ff                  100,000             
unit ff             mHz                 
Nd                  10                  
Points              per decade          
spacing             Logarithmic         
Va (mV)             10,0                
pw                  0,10                
Na                  3                   
corr                0                   
E range min (V)     -0,100              
E range max (V)     0,100               
I Range             Auto                
Bandwidth           8                   
nc cycles           0                   
goto Ns'            0                   
nr cycles           0                   
inc. cycle          0                   
