#!/usr/bin/env python3

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    startswith,
    any_of,
    all_of,
    contains,
    DiscoveryResult,
    Result,
    Service,
    SNMPSection,
    SimpleSNMPSection,
    SNMPTree,
    State,
    StringTable,
)
#Use this parse function if the device has 4 x radios
def parse_strings_4x(string_table):
    #print(string_table)
    result = {}
    result["wlan_0_freq"] = int(string_table[0][0])
    result["wlan_0_noise"] = int(string_table[0][1])
    result["wlan_1_freq"] = int(string_table[0][2])
    result["wlan_1_noise"] = int(string_table[0][3])
    result["wlan_2_freq"] = int(string_table[0][4])
    result["wlan_2_noise"] = int(string_table[0][5])
    result["wlan_3_freq"] = int(string_table[0][6])
    result["wlan_3_noise"] = int(string_table[0][7])
    result["easting"] = string_table[0][8]
    result["northing"] = string_table[0][9]
    result["altitude"] = string_table[0][10]
    return result
#Use this parse function if the device has 2 x radios
def parse_strings_2x(string_table):
    result = {}
    result["wlan_0_freq"] = int(string_table[0][0])
    result["wlan_0_noise"] = int(string_table[0][1])
    result["wlan_1_freq"] = int(string_table[0][2])
    result["wlan_1_noise"] = int(string_table[0][3])
    result["easting"] = string_table[0][4]
    result["northing"] = string_table[0][5]
    result["altitude"] = string_table[0][6]
    return result

def parse_strings_all(string_table):
    result = {}
    result["Temperature"] = string_table[0][0]
    result["Free Memory"] = string_table[0][1]
    result["Arp Dropped"] = string_table[0][2]
    result["Arp Requests"] = string_table[0][3]
    result["Arp Answered"] = string_table[0][4]
    result["Arp Total"] = string_table[0][5]
    result["Floods Dropped"] = string_table[0][6]
    result["Packes Dropped"] = string_table[0][7]
    result["Multicast Packets"] = string_table[0][8]
    result["Received Packets"] = string_table[0][9]
    result["Sent Packets"] = string_table[0][10]
    result["Floods Dropped"] = string_table[0][11]
    result["Instamesh Time Waited"] = string_table[0][12]
    #print(f"Parsine Function: {result}")
    return result
#
def discover_function(section):
    yield Service()

def discover_multiple_function(section):
    for row in section:
        try:
            print(f"Row Name: {row}")
            yield Service(row)
        except Exception as e:
            print(f"Truly Exceptional: {e}")
            continue

#This function is the meat in the check sandwich and the logic behind for threshold notifications
#Take the variable assigned in your 'parse' function, do whatever manipulations you want and 'yield' your results to the service
#for OK, WARN, CRIT thresholds you have to yield a status based on each condition
#HINT: try and give the check functions logical names so that when a check is registered it is easy to track what function is running
#inside what service. eg, there no point having check_test and function_test - if you are polling the RSSI from a radio, name the check
#something sensible like check_rssi and the function something like wlan_rssi_check. So that when you do multiple services in a single .py 
#you dont end up with an anuerism trying to debug it when it gets big.
def check_wlan_0(section):
    # Add custom check logic here
    noise_floor_thresh = -90
    wlan_0_freq = section.get("wlan_0_freq",None)
    wlan_0_noise = section.get("wlan_0_noise",None)
    easting = section.get("easting",None)
    northing = section.get("northing",None)
    altitude = section.get("altitude",None)
    if wlan_0_noise < noise_floor_thresh:
        yield Result(state=State.OK, summary=f"WLAN 0 FREQ: {wlan_0_freq}gHz - Noise Floor: {wlan_0_noise}dBm")
    if wlan_0_noise > noise_floor_thresh:
        yield Result(state=State.WARN, summary=f"FREQ: {wlan_0_freq}gHz - Noise Floor Threshold Exceeded: {wlan_0_noise}dBm - Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
    #yield Result(state=State.OK, summary=f"Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
def check_wlan_1(section):
    noise_floor_thresh = -90
    wlan_1_freq = section.get("wlan_1_freq",None)
    wlan_1_noise = section.get("wlan_1_noise",None)
    easting = section.get("easting",None)
    northing = section.get("northing",None)
    altitude = section.get("altitude",None)
    if wlan_1_noise < noise_floor_thresh:
        yield Result(state=State.OK, summary=f"WLAN 1 FREQ: {wlan_1_freq}gHz - Noise Floor: {wlan_1_noise}dBm")
    if wlan_1_noise > noise_floor_thresh:
        yield Result(state=State.WARN, summary=f"FREQ: {wlan_1_freq}gHz - Noise Floor Threshold Exceeded: {wlan_1_noise}dBm - Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
    #yield Result(state=State.OK, summary=f"Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
def check_wlan_2(section):
    noise_floor_thresh = -90
    wlan_2_freq = section.get("wlan_2_freq",None)
    wlan_2_noise = section.get("wlan_2_noise",None)
    easting = section.get("easting",None)
    northing = section.get("northing",None)
    altitude = section.get("altitude",None)
    if wlan_2_noise < noise_floor_thresh:
        yield Result(state=State.OK, summary=f"WLAN 2 FREQ: {wlan_2_freq}gHz - Noise Floor: {wlan_2_noise}dBm")
    if wlan_2_noise > noise_floor_thresh:
        yield Result(state=State.WARN, summary=f"FREQ: {wlan_2_freq}gHz - Noise Floor Threshold Exceeded: {wlan_2_noise}dBm - Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
    #yield Result(state=State.OK, summary=f"Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
def check_wlan_3(section):
    noise_floor_thresh = -90
    wlan_3_freq = section.get("wlan_3_freq",None)
    wlan_3_noise = section.get("wlan_3_noise",None)
    easting = section.get("easting",None)
    northing = section.get("northing",None)
    altitude = section.get("altitude",None)
    if wlan_3_noise < noise_floor_thresh:
        yield Result(state=State.OK, summary=f"WLAN 1 FREQ: {wlan_3_freq}gHz - Noise Floor: {wlan_3_noise}dBm")
    if wlan_3_noise > noise_floor_thresh:
        yield Result(state=State.WARN, summary=f"FREQ: {wlan_3_freq}gHz - Noise Floor Threshold Exceeded: {wlan_3_noise}dBm - Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
    #yield Result(state=State.OK, summary=f"Easting: {easting} - Northing: {northing} - Altitude: {altitude}m")
def all_model_checks(section):
    print("In all Model Checks")
    yield Result(state=State.OK, summary=f"Testing again")

snmp_section_all_models = SimpleSNMPSection(
    name="all_models",
    parse_function = parse_strings_all,
    detect = any_of(contains(".1.3.6.1.2.1.1.1.0", "FE1-2255B"),
                    contains(".1.3.6.1.2.1.1.1.0", "LX5-2255C"),
                    contains(".1.3.6.1.2.1.1.1.0", "FE1-2450A"),
                    contains(".1.3.6.1.2.1.1.1.0", "ME4-2450R"),
                    contains(".1.3.6.1.2.1.1.1.0", "ES1-2450R")
                   ),
    fetch = SNMPTree(base=".1.3.6.1.4.1.34861",
                     oids=["1.2",    #Temperature ( * 1000)
                           "1.3",    #Free Memory (Number of bytes)
                           "2.1",    #Arp Dropped
                           "2.2",    #ArpRequests
                           "2.3",    #Arps Requests Answered
                           "2.5",    #Arp Total
                           "2.6",    #Instamesh Floods Dropped
                           "2.7",    #Instamesh Packets Dropped
                           "2.8",    #Instamesh Packets Multicast
                           "2.9",    #Instamesh Packets Rec
                           "2.10",   #Instamesh Packets Sent
                           "2.11",   #Instamesh source Floods Dropped
                           "2.12"    #Instamesh Time Waited
                          ]),

)
snmp_section_4x_radios = SimpleSNMPSection(
    name="4xRadio_Noise",
    parse_function = parse_strings_4x,
    detect = any_of(contains(".1.3.6.1.2.1.1.1.0", "FE1-2255B"),
              contains(".1.3.6.1.2.1.1.1.0", "LX5-2255C"),
             ),
    fetch = SNMPTree(base=".1.3.6.1.4.1.34861",
		   oids=[
                        "3.1.2",          #Wlan0Freq
                        "3.1.3",          #Wlan0Noise
                        "3.2.2",          #Wlan1Freq
                        "3.2.3",          #Wlan1Noise
                        "3.3.2",          #Wlan2Freq
                        "3.3.3",          #Wlan2Noise
                        "3.4.2",          #Wlan3Freq
                        "3.4.3",          #Wlan3Noise
                        "4.3",            #Easting
                        "4.4",            #Northing
                        "4.5",            #Altitude
                        ]),
)
snmp_section_2x_radios = SimpleSNMPSection(
    name="2xRadio_Noise",
    parse_function = parse_strings_2x,
    detect = any_of(contains(".1.3.6.1.2.1.1.1.0", "FE1-2450A"),
              contains(".1.3.6.1.2.1.1.1.0", "ME4-2450R"),
              contains(".1.3.6.1.2.1.1.1.0", "ES1-2450R")
              ),
    fetch = SNMPTree(base=".1.3.6.1.4.1.34861",
                   oids=[
                        "3.1.2",          #Wlan0Freq
                        "3.1.3",          #Wlan0Noise
                        "3.2.2",          #Wlan1Freq
                        "3.2.3",          #Wlan1Noise
                        "4.3",            #Easting
                        "4.4",            #Northing
                        "4.5",            #Altitude
                        ]),
)
#This is the registration of the service. For multiple services in each function you need multiple service
#registrations.
#HINT: make sure you change your name and check_function so they are unique for each service that you want presented.
#to make the functionality for each service as easy to trouble shoot as possible.
check_plugin_4x_wlan0_noise = CheckPlugin(
    name="4xWLAN_0_Noise",
    sections=["4xRadio_Noise"],
    service_name="WLAN0 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_0,
)
check_plugin_4x_wlan1_noise = CheckPlugin(
    name="4xWLAN_1_Noise",
    sections=["4xRadio_Noise"],
    service_name="WLAN1 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_1,
)
check_plugin_4x_wlan2_noise = CheckPlugin(
    name="4xWLAN2_Noise",
    sections=["4xRadio_Noise"],
    service_name="WLAN2 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_2,
)
check_plugin_4x_wlan3_noise = CheckPlugin(
    name="4xWLAN3_Noise",
    sections=["4xRadio_Noise"],
    service_name="WLAN3 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_3,
)
check_plugin_2x_wlan0_noise = CheckPlugin(
    name="2xWLAN_0_Noise",
    sections=["2xRadio_Noise"],
    service_name="WLAN0 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_0,
)
check_plugin_2x_wlan1_noise = CheckPlugin(
    name="2xWLAN_1_Noise",
    sections=["2xRadio_Noise"],
    service_name="WLAN1 Noise Floor",
    discovery_function=discover_function,
    check_function=check_wlan_1,
)
check_plugin_all_breadcrumbs = CheckPlugin(
    name="all_breadcrumb_stats",
    sections=["all_models"],
    service_name="Testing",
    discovery_function=discover_multiple_function,
    check_function=all_model_checks,
)

