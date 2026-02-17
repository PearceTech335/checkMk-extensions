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

def parse_string_table(string_table):
    #print(f"Your string table: {string_table}")
    results = {}
    try:
        results["target"] = float(string_table[0][0])

    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in parse function: {e}")
        #print(f"Just before return: {results}")
    return results

def discover_service(section):
    yield Service()

#Return the Target RSSI of the SM's
def target_rssi(section):
    target_rssi = section["target"]
    yield Result(state=State.OK, summary=f"{target_rssi} dBi")

#SNMP Section for Getting Data
snmp_section_Cambium_450i_ap = SimpleSNMPSection(
    name = "pmp450i_ap",
    parse_function = parse_string_table,
    detect = all_of(
                startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
                contains(".1.3.6.1.2.1.1.1.0", "AP")),
    fetch = SNMPTree(".1.3.6.1.4.1.161.19.3.1",
                    [
                     "1.90.0",   #Target RSSI Level - for SM
                    ]),
)

#Plugin Registration
check_plugin_target_sm_rssi = CheckPlugin(
    name = "pmp450i_target_sm_rssi",
    sections = ["pmp450i_ap"],
    service_name = "Subscriber Module Target RSSI",
    discovery_function = discover_service,
    check_function = target_rssi,
)
