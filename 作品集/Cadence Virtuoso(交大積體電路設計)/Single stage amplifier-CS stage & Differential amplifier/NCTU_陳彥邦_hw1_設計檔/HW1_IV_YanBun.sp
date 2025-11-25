************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW1_IV
* View Name:     schematic
* Netlisted on:  Oct 27 23:39:00 2024
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
.PARAM

*.GLOBAL gnd!

*.PIN gnd!

************************************************************************
* Library Name: Yanbun_library
* Cell Name:    HW1_IV
* View Name:    schematic
************************************************************************

.SUBCKT HW1_IV
*.PININFO
*.CONNECT net1 gnd! 
*.CONNECT net3 gnd! 
*.CONNECT VIN1 gnd! 
*.CONNECT net4 gnd! 
*.CONNECT VIN2 gnd! 
MM4 M1_M2_SOURCE M3_M4_GATE gnd! gnd! N_33 m=1 l=M4_L w=M4_W
MM3 M3_M4_GATE M3_M4_GATE gnd! gnd! N_33 m=1 l=M3_L w=M3_W
MM2 VOUT2 gnd! M1_M2_SOURCE M1_M2_SOURCE N_33 m=1 l=M2_L w=M2_W
MM1 VOUT1 gnd! M1_M2_SOURCE M1_M2_SOURCE N_33 m=1 l=M1_L w=M1_W
RRD2 gnd! VOUT2 RD2 $[RP]
RRD1 gnd! VOUT1 RD1 $[RP]
CC1 VOUT2 gnd! 5p $[CP]
CC0 VOUT1 gnd! 5p $[CP]
.ENDS

