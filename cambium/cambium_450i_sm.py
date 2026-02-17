#!/usr/bin/env python3

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    startswith,
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

def parse_rssi(string_table):
    #print(f"Your string table: {string_table}")
    results = {}
    try:
        tx_power_string = string_table[0][2]
        tx_power_string = tx_power_string[0:2]

        results["radio_rssi"] = float(string_table[0][0])
        results["active_eirp"] = string_table[1][1]
        results["tx_power"] = float(tx_power_string)
        results["max_power"] = float(string_table[0][3])
        results["h_pol"] = float(string_table[0][4])
        results["v_pol"] = float(string_table[0][5])
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in parse function: {e}")
        #print(f"Just before return: {results}")
    return results

def discover_service(section):
    yield Service()

#Check the RSSI of the SM and return status
def check_rssi(section):
    rssi = section["radio_rssi"]
    if isinstance(rssi, float):
        #print(f"RSSI CHECK: {rssi}")
        if rssi < -80:
            #print("<-80")
            yield Result(state=State.CRIT, summary=f"Very Poor Link Quality: {rssi} dBm")
        elif rssi < -70:
            #print("<-70")
            yield Result(state=State.WARN, summary=f"Check Link Quality: {rssi} dBm")
        else:
            #print(f"FIRST ELSE {rssi}")
            yield Result(state=State.OK, summary=f"{rssi} dBm")
    else:
        #print("ELSE 2")
        yield Result(state=State.CRIT, summary=f"RSSI VALUE NOT VALID: {rssi}")

#Return the Acitve EIRP of the Radio
def check_active_eirp(section):
    active_eirp = section["active_eirp"]
    yield Result(state=State.OK, summary=f"{active_eirp}")

#Return the Link Status - Link Up Link Down
def check_tx_power(section):
    #print("In check power")
    tx_power = section["tx_power"]
    max_power = section["max_power"]
    if tx_power == max_power:
        yield Result(state=State.WARN, summary=f"Check Line of Sight/Link Distance-> TxPower:{tx_power}dBm MaxPower: {max_power}dBm")
    else:
        yield Result(state=State.OK, summary=f"{tx_power} dBm")
        #print(f"TX Power: {tx_power}")

#Return Polarization Stats
def check_polarization(section):

    v_pol = section["v_pol"]
    h_pol = section["h_pol"]
    disparity = v_pol - h_pol
    #print(f"Check Polarization: {v_pol}")
    if disparity < 0:
        disparity = disparity * -1
    #print(f"Disparity: {disparity}")
    if disparity > 10:
        yield Result(state=State.WARN, summary=f"Check Link Alignment - V <-> H Disparity greater than 10dBm: {disparity} dbm")
    else:
        yield Result(state=State.OK, summary=f"{disparity} dBm")


#SNMP Section for Getting Data
snmp_section_Cambium_450i_sm = SimpleSNMPSection(
    name = "pmp450i_sm",
    parse_function = parse_rssi,
    detect = all_of(
                startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
                contains(".1.3.6.1.2.1.1.1.0", "SM")),
    fetch = SNMPTree(".1.3.6.1.4.1.161.19.3",
                    [
                     "2.2.8.0",   #Radio dBm
                     "3.1.306",   #active EIRP
                     "2.2.23.0",  #TX Power Current
                     "2.1.161.0", #Max Transmit Power
                     "2.2.117.0", #Horizontal dBm
                     "2.2.118.0"  #Vertical dBm
                    ]),
)

#Plugin Registration
check_plugin_rssi = CheckPlugin(
    name = "pmp450i_rssi_check",
    sections = ["pmp450i_sm"],
    service_name = "RSSI - (from AP)",
    discovery_function = discover_service,
    check_function = check_rssi,
)
check_plugin_eirp = CheckPlugin(
    name = "pmp450i_active_eirp",
    sections = ["pmp450i_sm"],
    service_name = "Active EIRP",
    discovery_function = discover_service,
    check_function = check_active_eirp,
)
check_plugin_tx_power = CheckPlugin(
    name = "pmp450i_max_tx",
    sections = ["pmp450i_sm"],
    service_name = "Tx Power",
    discovery_function = discover_service,
    check_function = check_tx_power,
)
check_plugin_polarization = CheckPlugin(
    name = "pmp450i_check_polarization",
    sections = ["pmp450i_sm"],
    service_name = "V/H Polarization Disparity",
    discovery_function = discover_service,
    check_function = check_polarization,
)
