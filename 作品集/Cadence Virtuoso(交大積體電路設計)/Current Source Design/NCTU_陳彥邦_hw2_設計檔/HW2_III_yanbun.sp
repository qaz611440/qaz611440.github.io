************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW2_III
* View Name:     schematic
* Netlisted on:  Nov 12 00:17:21 2024
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
* Cell Name:    HW2_III
* View Name:    schematic
************************************************************************

.SUBCKT HW2_III
*.PININFO
*.CONNECT net14 gnd! 
MM11 Over0.7v_M14M15M21_GATE SmallThan2.5v_M10M11M17M19M23_GATE net9 gnd! P_33 
+ m=1 l=M11_L w=M11_W
MM9 net9 SmallThan2.5v_M8M9M16M22_GATE gnd! gnd! P_33 m=1 l=M9_L w=M9_W
MM8 net6 SmallThan2.5v_M8M9M16M22_GATE gnd! gnd! P_33 m=1 l=M8_L w=M8_W
MM23 gnd! SmallThan2.5v_M10M11M17M19M23_GATE net13 gnd! P_33 m=1 l=M23_L 
+ w=M23_W
MM22 net13 SmallThan2.5v_M8M9M16M22_GATE gnd! gnd! P_33 m=1 l=M22_L w=M22_W
MM19 SmallThan2.5v_M10M11M17M19M23_GATE SmallThan2.5v_M10M11M17M19M23_GATE 
+ gnd! gnd! P_33 m=1 l=M19_L w=M19_W
MM17 Over0.7v_M12M13M18M20_GATE SmallThan2.5v_M10M11M17M19M23_GATE net11 gnd! 
+ P_33 m=1 l=M17_L w=M17_W
MM16 net11 SmallThan2.5v_M8M9M16M22_GATE gnd! gnd! P_33 m=1 l=M16_L w=M16_W
MM15 net10 Over0.7v_M14M15M21_GATE gnd! gnd! N_33 m=1 l=M15_L w=M15_W
MM14 net7 Over0.7v_M14M15M21_GATE net8 gnd! N_33 m=1 l=M14_L w=M14_W
MM13 Over0.7v_M14M15M21_GATE Over0.7v_M12M13M18M20_GATE net10 gnd! N_33 m=1 
+ l=M13_L w=M13_W
MM12 SmallThan2.5v_M8M9M16M22_GATE Over0.7v_M12M13M18M20_GATE net7 gnd! N_33 
+ m=1 l=M12_L w=M12_W
MM10 SmallThan2.5v_M8M9M16M22_GATE SmallThan2.5v_M10M11M17M19M23_GATE net6 
+ gnd! N_33 m=1 l=M10_L w=M10_W
MM21 net12 Over0.7v_M14M15M21_GATE gnd! gnd! N_33 m=1 l=M21_L w=M21_W
MM20 SmallThan2.5v_M10M11M17M19M23_GATE Over0.7v_M12M13M18M20_GATE net12 gnd! 
+ N_33 m=1 l=M20_L w=M20_W
MM18 Over0.7v_M12M13M18M20_GATE Over0.7v_M12M13M18M20_GATE gnd! gnd! N_33 m=1 
+ l=M18_L w=M18_W
RRs3 net8 gnd! gnd! 972.1 $[RNHR1000] l=Rs3_L w=Rs3_W
.ENDS

