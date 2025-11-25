************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW3_Folded-cascode
* View Name:     schematic
* Netlisted on:  Dec 13 23:08:24 2024
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
* Cell Name:    HW2_III_finaldata
* View Name:    schematic
************************************************************************

.SUBCKT HW2_III_finaldata Vb1 Vb2 Vb3 Vb4
*.PININFO Vb1:O Vb2:O Vb3:O Vb4:O
*.CONNECT net1 gnd! 
RRs3 net6 gnd! gnd! 1.119331K $[RNHR1000] l=1.2u w=1.0u
MM13 Vb4 Vb1 net7 gnd! N_33 m=1 l=1.0u w=1.0u
MM12 Vb3 Vb1 net4 gnd! N_33 m=1 l=1.0u w=1.0u
MM20 Vb2 Vb1 net2 gnd! N_33 m=1 l=1.0u w=2.0u
MM18 Vb1 Vb1 gnd! gnd! N_33 m=1 l=1.0u w=1.2u
MM15 net7 Vb4 gnd! gnd! N_33 m=1 l=1.0u w=1.0u
MM14 net4 Vb4 net6 gnd! N_33 m=1 l=1.0u w=1.0u
MM21 net2 Vb4 gnd! gnd! N_33 m=1 l=1.0u w=2.0u
MM9 net8 Vb3 gnd! gnd! P_33 m=1 l=1.0u w=1.0u
MM8 net5 Vb3 gnd! gnd! P_33 m=1 l=1.4u w=1.0u
MM22 net3 Vb3 gnd! gnd! P_33 m=1 l=1.0u w=3.0u
MM16 net9 Vb3 gnd! gnd! P_33 m=1 l=1.0u w=2.0u
MM11 Vb4 Vb2 net8 gnd! P_33 m=1 l=1.0u w=1.0u
MM10 Vb3 Vb2 net5 gnd! P_33 m=1 l=1.0u w=1.0u
MM23 gnd! Vb2 net3 gnd! P_33 m=1 l=1.0u w=5.0u
MM19 Vb2 Vb2 gnd! gnd! P_33 m=1 l=1.0u w=1.2u
MM17 Vb1 Vb2 net9 gnd! P_33 m=1 l=1.0u w=2.0u
.ENDS

************************************************************************
* Library Name: Yanbun_library
* Cell Name:    HW3_Folded-cascode
* View Name:    schematic
************************************************************************

.SUBCKT HW3_Folded-cascode
*.PININFO
*.CONNECT M1_VIN gnd! 
*.CONNECT net1 gnd! 
*.CONNECT net3 gnd! 
*.CONNECT VDD gnd! 
*.CONNECT net2 gnd! 
*.CONNECT M2_VIN gnd! 
XI7 Vb1 Vb2 Vb3 Vb4 / HW2_III_finaldata
MM2 M2_D gnd! gnd! gnd! P_33 m=1 l=M1_L w=M1_W
MM1 M1_D gnd! gnd! gnd! P_33 m=1 l=M1_L w=M1_W
MM8 Vout_- Vb2 M8_S gnd! P_33 m=1 l=M7_L w=M7_W
MM7 Vout_+ Vb2 M7_S gnd! P_33 m=1 l=M7_L w=M7_W
MM10 M8_S Vb3 gnd! gnd! P_33 m=1 l=M9_L w=M9_W
MM9 M7_S Vb3 gnd! gnd! P_33 m=1 l=M9_L w=M9_W
MM5 M1_D Vb4 gnd! gnd! N_33 m=1 l=M5_L w=M5_W
MM4 Vout_- Vb1 M2_D gnd! N_33 m=1 l=M3_L w=M3_W
MM6 M2_D Vb4 gnd! gnd! N_33 m=1 l=M5_L w=M5_W
MM3 Vout_+ Vb1 M1_D gnd! N_33 m=1 l=M3_L w=M3_W
CC1 Vout_- gnd! 500.0f $[CP]
CC0 Vout_+ gnd! 500.0f $[CP]
.ENDS

