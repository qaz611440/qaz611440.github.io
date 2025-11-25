************************************************************************
* auCdl Netlist:
* 
* Library Name:  Yanbun_library
* Top Cell Name: HW2_IV
* View Name:     schematic
* Netlisted on:  Nov 12 00:17:51 2024
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
* Cell Name:    HW2_IV
* View Name:    schematic
************************************************************************

.SUBCKT HW2_IV
*.PININFO
*.CONNECT net1 gnd! 
RRs4 M5_S net3 gnd! 972.1 $[RNHR1000] l=Rs4_L w=Rs4_W
MM26 M24M25M28_GATE M26M27_GATE M5_S gnd! N_33 m=1 l=M26_L w=M26_W
MM27 M26M27_GATE M26M27_GATE net2 gnd! N_33 m=1 l=M27_L w=M27_W
MM25 M26M27_GATE M24M25M28_GATE gnd! gnd! P_33 m=1 l=M25_L w=M25_W
MM24 M24M25M28_GATE M24M25M28_GATE gnd! gnd! P_33 m=1 l=M24_L w=M24_W
MM28 gnd! M24M25M28_GATE gnd! gnd! P_33 m=1 l=M28_L w=M28_W
QQ2 gnd! gnd! net2 PNP_V50X50 AREA=2.5e-11
QQ1 gnd! gnd! net3 PNP_V50X50 AREA=2.5e-11
.ENDS

