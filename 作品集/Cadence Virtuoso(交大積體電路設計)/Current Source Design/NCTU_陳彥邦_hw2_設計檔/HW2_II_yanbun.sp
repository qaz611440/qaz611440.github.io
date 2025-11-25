************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW2_II
* View Name:     schematic
* Netlisted on:  Nov 12 00:16:42 2024
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
* Cell Name:    HW2_II
* View Name:    schematic
************************************************************************

.SUBCKT HW2_II
*.PININFO
*.CONNECT net1 gnd! 
MM5 M3M4M7GATE_M5D M5M6GATE_M4M6D M5_S gnd! N_33 m=1 l=M5_L w=M5_W
MM6 M5M6GATE_M4M6D M5M6GATE_M4M6D gnd! gnd! N_33 m=1 l=M6_L w=M6_W
MM4 M5M6GATE_M4M6D M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M4_L w=M4_W
MM3 M3M4M7GATE_M5D M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M3_L w=M3_W
MM7 gnd! M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M7_L w=M7_W
RRs2 M5_S gnd! gnd! 972.1 $[RNHR1000] l=Rs2_L w=Rs2_W
.ENDS

