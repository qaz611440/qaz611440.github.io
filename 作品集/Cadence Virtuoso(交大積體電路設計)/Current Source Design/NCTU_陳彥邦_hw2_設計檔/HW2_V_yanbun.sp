************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW2_V
* View Name:     schematic
* Netlisted on:  Nov 12 00:18:14 2024
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
* Cell Name:    HW2_V
* View Name:    schematic
************************************************************************

.SUBCKT HW2_V
*.PININFO
*.CONNECT net1 gnd! 
RRs2 M5_S gnd! gnd! 972.1 $[RNHR1000] l=Rs2_L w=Rs2_W
MM33 M35M36_GATE M32M33_GARE gnd! gnd! N_33 m=1 l=M33_L w=M33_W
MM32 M32M33_GARE M32M33_GARE gnd! gnd! N_33 m=1 l=M32_L w=M32_W
MM5 M3M4M7GATE_M5D M5M6GATE_M4M6D M5_S gnd! N_33 m=1 l=M5_L w=M5_W
MM6 M5M6GATE_M4M6D M5M6GATE_M4M6D gnd! gnd! N_33 m=1 l=M6_L w=M6_W
MM36 M5M6GATE_M4M6D M35M36_GATE gnd! gnd! P_33 m=1 l=M36_L w=M36_W
MM35 M35M36_GATE M35M36_GATE gnd! gnd! P_33 m=1 l=M35_L w=M35_W
MM34 M35M36_GATE M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M34_L w=M34_W
MM31 M32M33_GARE gnd! M31_Source gnd! P_33 m=1 l=M31_L w=M31_W
MM30 M31_Source gnd! M30_source gnd! P_33 m=1 l=M30_L w=M30_W
MM29 M30_source gnd! gnd! gnd! P_33 m=1 l=M29_L w=M29_W
MM4 M5M6GATE_M4M6D M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M4_L w=M4_W
MM3 M3M4M7GATE_M5D M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M3_L w=M3_W
MM7 gnd! M3M4M7GATE_M5D gnd! gnd! P_33 m=1 l=M7_L w=M7_W
.ENDS

