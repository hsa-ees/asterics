EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:ov7670_pmod-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L CONN_02X06 Pmod_2
U 1 1 5A90C673
P 3600 3850
F 0 "Pmod_2" H 3600 4200 50  0000 C CNN
F 1 "CONN_02X06" V 3600 3850 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_2x06" H 3600 4400 50  0000 C CNN
F 3 "" H 3600 2650 50  0000 C CNN
	1    3600 3850
	1    0    0    -1  
$EndComp
$Comp
L CONN_02X06 Pmod_1
U 1 1 5A90C6F6
P 3600 2400
F 0 "Pmod_1" H 3600 2750 50  0000 C CNN
F 1 "CONN_02X06" V 3600 2400 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_2x06" H 3600 2850 50  0000 C CNN
F 3 "" H 3600 1200 50  0000 C CNN
	1    3600 2400
	1    0    0    -1  
$EndComp
$Comp
L CONN_02X09 OV7670
U 1 1 5A90C7CF
P 3600 5500
F 0 "OV7670" H 3600 6000 50  0000 C CNN
F 1 "CONN_02X09" V 3600 5500 50  0000 C CNN
F 2 "Socket_Strips:Socket_Strip_Angled_2x09" H 3800 6100 50  0000 C CNN
F 3 "" H 3600 4300 50  0000 C CNN
	1    3600 5500
	1    0    0    -1  
$EndComp
Text Label 3350 3700 2    60   ~ 0
GND
Text Label 3350 3600 2    60   ~ 0
VCC
Text Label 3350 4100 2    60   ~ 0
D6
Text Label 3350 4000 2    60   ~ 0
D4
Text Label 3350 3900 2    60   ~ 0
D2
Text Label 3350 3800 2    60   ~ 0
D0
Text Label 3850 3800 0    60   ~ 0
D1
Text Label 3850 3900 0    60   ~ 0
D3
Text Label 3850 4000 0    60   ~ 0
D5
Text Label 3850 4100 0    60   ~ 0
D7
Text Label 3350 5500 2    60   ~ 0
D7_r
Text Label 3850 5500 0    60   ~ 0
D6_r
Text Label 3850 3600 0    60   ~ 0
VCC
Text Label 3850 3700 0    60   ~ 0
GND
Text Label 3850 2150 0    60   ~ 0
VCC
Text Label 3350 2150 2    60   ~ 0
VCC
Text Label 3850 2250 0    60   ~ 0
GND
Text Label 3350 2250 2    60   ~ 0
GND
Text Label 3350 2350 2    60   ~ 0
VSYNC
Text Label 3350 2450 2    60   ~ 0
HREF
Text Label 3850 2550 0    60   ~ 0
RESET
Text Label 3850 2650 0    60   ~ 0
PWDN
Text Label 3850 2450 0    60   ~ 0
SIOC
Text Label 3850 2350 0    60   ~ 0
SIOD
Text Label 3350 2550 2    60   ~ 0
PCLK
Text Label 3350 2650 2    60   ~ 0
XCLK
Text Label 3850 5400 0    60   ~ 0
D4_r
Text Label 3850 5300 0    60   ~ 0
D2_r
Text Label 3850 5200 0    60   ~ 0
D0_r
Text Label 3350 5400 2    60   ~ 0
D5_r
Text Label 3350 5300 2    60   ~ 0
D3_r
Text Label 3350 5200 2    60   ~ 0
D1_r
Text Label 3350 5100 2    60   ~ 0
RESET_r
Text Label 3850 5100 0    60   ~ 0
PWDN_r
Text Label 3350 5600 2    60   ~ 0
PCLK_r
Text Label 3850 5600 0    60   ~ 0
XCLK_r
Text Label 3350 5700 2    60   ~ 0
VSYNC_r
Text Label 3850 5700 0    60   ~ 0
HREF_r
Text Label 3350 5800 2    60   ~ 0
SIOC_r
Text Label 3850 5800 0    60   ~ 0
SIOD_r
Text Label 3350 5900 2    60   ~ 0
VCC
Text Label 3850 5900 0    60   ~ 0
GND
$Comp
L R R1
U 1 1 5A92F9FF
P 6400 2350
F 0 "R1" V 6480 2350 50  0000 C CNN
F 1 "1k5" V 6400 2350 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6400 3250 50  0000 C CNN
F 3 "" H 6400 2350 50  0000 C CNN
	1    6400 2350
	0    1    1    0   
$EndComp
$Comp
L R R2
U 1 1 5A92FA44
P 6400 2750
F 0 "R2" V 6480 2750 50  0000 C CNN
F 1 "1k5" V 6400 2750 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6400 3650 50  0000 C CNN
F 3 "" H 6400 2750 50  0000 C CNN
	1    6400 2750
	0    1    1    0   
$EndComp
$Comp
L VCC #PWR01
U 1 1 5A92FA7D
P 6550 2350
F 0 "#PWR01" H 6550 2200 50  0001 C CNN
F 1 "VCC" H 6550 2500 50  0000 C CNN
F 2 "" H 6550 2350 50  0000 C CNN
F 3 "" H 6550 2350 50  0000 C CNN
	1    6550 2350
	1    0    0    -1  
$EndComp
$Comp
L VCC #PWR02
U 1 1 5A92FA9F
P 6550 2750
F 0 "#PWR02" H 6550 2600 50  0001 C CNN
F 1 "VCC" H 6550 2900 50  0000 C CNN
F 2 "" H 6550 2750 50  0000 C CNN
F 3 "" H 6550 2750 50  0000 C CNN
	1    6550 2750
	1    0    0    -1  
$EndComp
$Comp
L R R4
U 1 1 5AD5D350
P 8700 3850
F 0 "R4" V 8780 3850 50  0000 C CNN
F 1 "100" V 8700 3850 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 4050 50  0000 C CNN
F 3 "" H 8700 3850 50  0000 C CNN
	1    8700 3850
	0    1    1    0   
$EndComp
Text Label 8850 3850 0    60   ~ 0
D1_r
$Comp
L R R5
U 1 1 5AD5E928
P 8700 4100
F 0 "R5" V 8780 4100 50  0000 C CNN
F 1 "100" V 8700 4100 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 4300 50  0000 C CNN
F 3 "" H 8700 4100 50  0000 C CNN
	1    8700 4100
	0    1    1    0   
$EndComp
$Comp
L R R6
U 1 1 5AD5E95B
P 8700 4350
F 0 "R6" V 8780 4350 50  0000 C CNN
F 1 "100" V 8700 4350 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 4550 50  0000 C CNN
F 3 "" H 8700 4350 50  0000 C CNN
	1    8700 4350
	0    1    1    0   
$EndComp
$Comp
L R R7
U 1 1 5AD5E989
P 8700 4600
F 0 "R7" V 8780 4600 50  0000 C CNN
F 1 "100" V 8700 4600 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 4800 50  0000 C CNN
F 3 "" H 8700 4600 50  0000 C CNN
	1    8700 4600
	0    1    1    0   
$EndComp
$Comp
L R R8
U 1 1 5AD5EA33
P 8700 4850
F 0 "R8" V 8780 4850 50  0000 C CNN
F 1 "100" V 8700 4850 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 5050 50  0000 C CNN
F 3 "" H 8700 4850 50  0000 C CNN
	1    8700 4850
	0    1    1    0   
$EndComp
$Comp
L R R9
U 1 1 5AD5EADF
P 8700 5100
F 0 "R9" V 8780 5100 50  0000 C CNN
F 1 "100" V 8700 5100 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 5300 50  0000 C CNN
F 3 "" H 8700 5100 50  0000 C CNN
	1    8700 5100
	0    1    1    0   
$EndComp
$Comp
L R R10
U 1 1 5AD5EB14
P 8700 5350
F 0 "R10" V 8780 5350 50  0000 C CNN
F 1 "100" V 8700 5350 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 5550 50  0000 C CNN
F 3 "" H 8700 5350 50  0000 C CNN
	1    8700 5350
	0    1    1    0   
$EndComp
$Comp
L R R3
U 1 1 5AD5EB4C
P 8700 3600
F 0 "R3" V 8780 3600 50  0000 C CNN
F 1 "100" V 8700 3600 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 8600 3800 50  0000 C CNN
F 3 "" H 8700 3600 50  0000 C CNN
	1    8700 3600
	0    1    1    0   
$EndComp
Text Label 8850 4100 0    60   ~ 0
D2_r
Text Label 8850 4350 0    60   ~ 0
D3_r
Text Label 8850 4600 0    60   ~ 0
D4_r
Text Label 8850 4850 0    60   ~ 0
D5_r
Text Label 8850 5100 0    60   ~ 0
D6_r
Text Label 8850 5350 0    60   ~ 0
D7_r
Text Label 8850 3600 0    60   ~ 0
D0_r
Text Label 8550 3850 2    60   ~ 0
D1
Text Label 8550 4100 2    60   ~ 0
D2
Text Label 8550 4350 2    60   ~ 0
D3
Text Label 8550 4600 2    60   ~ 0
D4
Text Label 8550 4850 2    60   ~ 0
D5
Text Label 8550 5100 2    60   ~ 0
D6
Text Label 8550 5350 2    60   ~ 0
D7
Text Label 8550 3600 2    60   ~ 0
D0
$Comp
L R R13
U 1 1 5AD60FB9
P 6400 4100
F 0 "R13" V 6480 4100 50  0000 C CNN
F 1 "100" V 6400 4100 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 4300 50  0000 C CNN
F 3 "" H 6400 4100 50  0000 C CNN
	1    6400 4100
	0    1    1    0   
$EndComp
Text Label 6550 4100 0    60   ~ 0
PCLK_r
$Comp
L R R14
U 1 1 5AD60FC0
P 6400 4350
F 0 "R14" V 6480 4350 50  0000 C CNN
F 1 "100" V 6400 4350 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 4550 50  0000 C CNN
F 3 "" H 6400 4350 50  0000 C CNN
	1    6400 4350
	0    1    1    0   
$EndComp
$Comp
L R R11
U 1 1 5AD60FC6
P 6400 3600
F 0 "R11" V 6480 3600 50  0000 C CNN
F 1 "100" V 6400 3600 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 3800 50  0000 C CNN
F 3 "" H 6400 3600 50  0000 C CNN
	1    6400 3600
	0    1    1    0   
$EndComp
$Comp
L R R12
U 1 1 5AD60FCC
P 6400 3850
F 0 "R12" V 6480 3850 50  0000 C CNN
F 1 "100" V 6400 3850 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 4050 50  0000 C CNN
F 3 "" H 6400 3850 50  0000 C CNN
	1    6400 3850
	0    1    1    0   
$EndComp
$Comp
L R R17
U 1 1 5AD60FD2
P 6400 5100
F 0 "R17" V 6480 5100 50  0000 C CNN
F 1 "100" V 6400 5100 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 5300 50  0000 C CNN
F 3 "" H 6400 5100 50  0000 C CNN
	1    6400 5100
	0    1    1    0   
$EndComp
$Comp
L R R18
U 1 1 5AD60FD8
P 6400 5350
F 0 "R18" V 6480 5350 50  0000 C CNN
F 1 "100" V 6400 5350 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 5550 50  0000 C CNN
F 3 "" H 6400 5350 50  0000 C CNN
	1    6400 5350
	0    1    1    0   
$EndComp
$Comp
L R R16
U 1 1 5AD60FDE
P 6400 4850
F 0 "R16" V 6480 4850 50  0000 C CNN
F 1 "100" V 6400 4850 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 5050 50  0000 C CNN
F 3 "" H 6400 4850 50  0000 C CNN
	1    6400 4850
	0    1    1    0   
$EndComp
$Comp
L R R15
U 1 1 5AD60FE4
P 6400 4600
F 0 "R15" V 6480 4600 50  0000 C CNN
F 1 "100" V 6400 4600 50  0000 C CNN
F 2 "Resistors_SMD:R_0805_HandSoldering" V 6300 4800 50  0000 C CNN
F 3 "" H 6400 4600 50  0000 C CNN
	1    6400 4600
	0    1    1    0   
$EndComp
Text Label 6550 4350 0    60   ~ 0
XCLK_r
Text Label 6550 3600 0    60   ~ 0
VSYNC_r
Text Label 6550 3850 0    60   ~ 0
HREF_r
Text Label 6550 5100 0    60   ~ 0
SIOC_r
Text Label 6550 5350 0    60   ~ 0
SIOD_r
Text Label 6550 4850 0    60   ~ 0
RESET_r
Text Label 6550 4600 0    60   ~ 0
PWDN_r
Text Label 6250 4100 2    60   ~ 0
PCLK
Text Label 6250 4350 2    60   ~ 0
XCLk
Text Label 6250 3600 2    60   ~ 0
VSYNC
Text Label 6250 3850 2    60   ~ 0
HREF
Text Label 6250 5100 2    60   ~ 0
SIOC
Text Label 6250 5350 2    60   ~ 0
SIOD
Text Label 6250 4850 2    60   ~ 0
RESET
Text Label 6250 4600 2    60   ~ 0
PWDN
Text Label 6250 2350 2    60   ~ 0
SIOC_r
Text Label 6250 2750 2    60   ~ 0
SIOD_r
$EndSCHEMATC
