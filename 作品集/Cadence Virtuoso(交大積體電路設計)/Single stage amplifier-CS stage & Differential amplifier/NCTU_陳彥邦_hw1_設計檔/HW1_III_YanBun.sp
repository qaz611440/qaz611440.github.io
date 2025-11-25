************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW1__III
* View Name:     schematic
* Netlisted on:  Oct 27 23:38:34 2024
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
* Cell Name:    HW1__III
* View Name:    schematic
************************************************************************

.SUBCKT HW1__III
*.PININFO
*.CONNECT net2 gnd! 
*.CONNECT VIN gnd! 
*.CONNECT net4 gnd! 
MMP1 VOUT MP_GATE gnd! gnd! P_33 m=1 l=MP1_MOS_L w=MP1_MOS_W
MMP2 MP_GATE MP_GATE gnd! gnd! P_33 m=1 l=MP2_MOS_L w=MP2_MOS_W
MMN1 VOUT gnd! gnd! gnd! N_33 m=1 l=MN1_MOS_L w=MN1_MOS_W
CC0 VOUT gnd! 5p $[CP]
.ENDS

