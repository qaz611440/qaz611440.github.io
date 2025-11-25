************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW1_II
* View Name:     schematic
* Netlisted on:  Oct 27 23:38:06 2024
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
* Cell Name:    HW1_II
* View Name:    schematic
************************************************************************

.SUBCKT HW1_II
*.PININFO
*.CONNECT net1 gnd! 
*.CONNECT net2 gnd! 
*.CONNECT VIN gnd! 
MM0 VOUT gnd! VS gnd! N_33 m=1 l=MOS_L w=MOS_W
RR1 VS gnd! RS $[RP]
RR0 gnd! VOUT RD $[RP]
CC0 VOUT gnd! 5p $[CP]
.ENDS

