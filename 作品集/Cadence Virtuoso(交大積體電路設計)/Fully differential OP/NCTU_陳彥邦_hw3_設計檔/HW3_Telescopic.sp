************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW3_Telescopic
* View Name:     schematic
* Netlisted on:  Dec 13 23:09:04 2024
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
* Cell Name:    HW2_II_finaldata
* View Name:    schematic
************************************************************************

.SUBCKT HW2_II_finaldata Vb1 Vb2
*.PININFO Vb1:O Vb2:O
*.CONNECT net1 gnd! 
RRs2 net3 gnd! gnd! 1.349649K $[RNHR1000] l=17.0u w=13.0u
MM5 Vb2 Vb1 net3 gnd! N_33 m=1 l=10.0u w=15.0u
MM6 Vb1 Vb1 gnd! gnd! N_33 m=1 l=10.0u w=15.0u
MM4 Vb1 Vb2 gnd! gnd! P_33 m=1 l=8.0u w=40.0u
MM3 Vb2 Vb2 gnd! gnd! P_33 m=1 l=8.0u w=30.0u
MM7 gnd! Vb2 gnd! gnd! P_33 m=1 l=1.0u w=1.0u
.ENDS

************************************************************************
* Library Name: Yanbun_library
* Cell Name:    HW3_Telescopic
* View Name:    schematic
************************************************************************

.SUBCKT HW3_Telescopic
*.PININFO
*.CONNECT net6 gnd! 
*.CONNECT net7 gnd! 
*.CONNECT VIN_M1_POS gnd! 
*.CONNECT net14 gnd! 
*.CONNECT VDD gnd! 
*.CONNECT VIN_M_NEG gnd! 
MM9 net3 gnd! gnd! gnd! N_33 m=1 l=M9_L w=M9_W
MMb1 gnd! gnd! gnd! gnd! N_33 m=1 l=Mb1_L w=Mb1_W
MM4 Vout_M2_NEG Vb1 net13 gnd! N_33 m=1 l=M3_L w=M3_W
MM3 Vout_M1_POS Vb1 net12 gnd! N_33 m=1 l=M3_L w=M3_W
MM2 net13 gnd! net3 gnd! N_33 m=1 l=M1_L w=M1_W
MM1 net12 gnd! net3 gnd! N_33 m=1 l=M1_L w=M1_W
MM8 net11 gnd! gnd! gnd! P_33 m=1 l=M7_L w=M7_W
MM7 net9 gnd! gnd! gnd! P_33 m=1 l=M7_L w=M7_W
MMb2 gnd! gnd! gnd! gnd! P_33 m=1 l=Mb2_L w=Mb2_W
MM5 Vout_M1_POS Vb2 net9 gnd! P_33 m=1 l=M5_L w=M5_W
MM6 Vout_M2_NEG Vb2 net11 gnd! P_33 m=1 l=M5_L w=M5_W
XI0 Vb1 Vb2 / HW2_II_finaldata
CC1 Vout_M2_NEG gnd! 500.0f $[CP]
CC0 Vout_M1_POS gnd! 500.0f $[CP]
.ENDS

