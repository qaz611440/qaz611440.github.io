************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW2_I
* View Name:     schematic
* Netlisted on:  Nov 12 00:16:01 2024
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
* Cell Name:    HW2_I
* View Name:    schematic
************************************************************************

.SUBCKT HW2_I
*.PININFO
*.CONNECT VDD gnd! 
RRs1 gnd! MOS_GATE_Vol gnd! 972.1 $[RNHR1000] l=Rs1_L w=Rs1_W
MM1 MOS_GATE_Vol MOS_GATE_Vol gnd! gnd! N_33 m=1 l=M1_L w=M1_W
MM2 gnd! MOS_GATE_Vol gnd! gnd! N_33 m=1 l=M2_L w=M2_W
.ENDS

