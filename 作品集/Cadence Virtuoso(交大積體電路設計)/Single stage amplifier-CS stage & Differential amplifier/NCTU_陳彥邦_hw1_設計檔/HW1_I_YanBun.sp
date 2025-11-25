************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW1_I_CS
* View Name:     schematic
* Netlisted on:  Oct 27 23:12:38 2024
************************************************************************

*.BIPOLAR
*.RESI = 2000 
*.RESVAL
*.CAPVAL
*.DIOPERI
*.DIOAREA
*.EQUATION
*.SCALE METER
*.MEGA
.PARAM VDD=
+ Vin_DC=
+ Vin_Pulse_H=
+ Vin_Pulse_L=
+ MOS_L=350n
+ MOS_W=1u
+ Period_Vin=10u
+ RD=80K
+ Vin_H=1.1
+ Vin_L=0.7
+ VDS=0
+ VGS=0

*.GLOBAL gnd!

*.PIN gnd!

************************************************************************
* Library Name: Yanbun_library
* Cell Name:    HW1_I_CS
* View Name:    schematic
************************************************************************

.SUBCKT HW1_I_CS
*.PININFO
*.CONNECT net1 gnd! 
*.CONNECT net9 gnd! 
*.CONNECT VIN gnd! 
RR2 gnd! VOUT RD $[RP]
CC0 VOUT gnd! 5p $[CP]
MM0 VOUT gnd! gnd! gnd! N_33 m=1 l=MOS_L w=MOS_W
.ENDS

