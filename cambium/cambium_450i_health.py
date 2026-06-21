#!/usr/bin/env python3
"""
Cambium PMP 450i – Device Health Checks (CPU, Temperature, Packet Errors)

Sources:
  whispBoxStatus (.1.3.6.1.4.1.161.19.3.3.1)
    .35  – boxTemperatureC          (degrees Celsius)
    .288 – currentCpuUsage          (0-100 %)
    .94  – fecInDiscardsCount       (Ethernet in discards)
    .95  – fecInErrorsCount         (Ethernet in errors)
    .96  – fecOutDiscardsCount      (Ethernet out discards)
    .97  – fecOutErrorsCount        (Ethernet out errors)
    .278 – rfInDiscardsCountExt     (RF in discards, 64-bit)
    .279 – rfInErrorsCountExt       (RF in errors, 64-bit)
    .280 – rfOutDiscardsCountExt    (RF out discards, 64-bit)
    .281 – rfOutErrorsCountExt      (RF out errors, 64-bit)

  whispBoxConfig (.1.3.6.1.4.1.161.19.3.3.2)
    .83  – channelBandwidth         (display string, e.g. "20")

These metrics apply to both AP and SM hardware.  Two identically-structured
sections are registered – one with AP detect, one with SM detect – so that
CheckMK discovers health services on every Cambium 450i device it polls.
"""

from typing import Any, Dict, List
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
    SNMPTree,
    State,
    StringTable,
)

# ---------------------------------------------------------------------------
# Shared parse logic
# ---------------------------------------------------------------------------

def _parse_health(string_table: List[StringTable]) -> Dict[str, Any]:
    """
    string_table[0] – whispBoxStatus scalars
    string_table[1] – whispBoxConfig scalars (channel bandwidth)
    """
    results: Dict[str, Any] = {}
    try:
        row = string_table[0][0]
        results["temp_c"]             = int(row[0])
        results["cpu_pct"]            = int(row[1])
        results["eth_in_discards"]    = int(row[2])
        results["eth_in_errors"]      = int(row[3])
        results["eth_out_discards"]   = int(row[4])
        results["eth_out_errors"]     = int(row[5])
        results["rf_in_discards"]     = int(row[6])
        results["rf_in_errors"]       = int(row[7])
        results["rf_out_discards"]    = int(row[8])
        results["rf_out_errors"]      = int(row[9])
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in _parse_health (BoxStatus): {e}")

    try:
        results["channel_bw"] = string_table[1][0][0]
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in _parse_health (BoxConfig): {e}")

    return results

_BOX_FETCH = [
    SNMPTree(
        ".1.3.6.1.4.1.161.19.3.3.1",   # whispBoxStatus
        [
            "35.0",    # boxTemperatureC
            "288.0",   # currentCpuUsage
            "94.0",    # fecInDiscardsCount
            "95.0",    # fecInErrorsCount
            "96.0",    # fecOutDiscardsCount
            "97.0",    # fecOutErrorsCount
            "278.0",   # rfInDiscardsCountExt
            "279.0",   # rfInErrorsCountExt
            "280.0",   # rfOutDiscardsCountExt
            "281.0",   # rfOutErrorsCountExt
        ],
    ),
    SNMPTree(
        ".1.3.6.1.4.1.161.19.3.3.2",   # whispBoxConfig
        [
            "83.0",    # channelBandwidth
        ],
    ),
]

# ---------------------------------------------------------------------------
# SNMP Sections (AP + SM, same data)
# ---------------------------------------------------------------------------

snmp_section_pmp450i_ap_health = SNMPSection(
    name="pmp450i_ap_health",
    parse_function=_parse_health,
    detect=all_of(
        startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
        contains(".1.3.6.1.2.1.1.1.0", "AP"),
    ),
    fetch=_BOX_FETCH,
)

snmp_section_pmp450i_sm_health = SNMPSection(
    name="pmp450i_sm_health",
    parse_function=_parse_health,
    detect=all_of(
        startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
        contains(".1.3.6.1.2.1.1.1.0", "SM"),
    ),
    fetch=_BOX_FETCH,
)

# ---------------------------------------------------------------------------
# Discovery (shared)
# ---------------------------------------------------------------------------

def _discover_health(section: Dict[str, Any]) -> DiscoveryResult:
    if section:
        yield Service()

# ---------------------------------------------------------------------------
# CPU Utilization
# Thresholds: WARN ≥ 80 %, CRIT ≥ 95 %
# ---------------------------------------------------------------------------

def _check_cpu(section: Dict[str, Any]) -> CheckResult:
    cpu = section.get("cpu_pct")
    if cpu is None:
        yield Result(state=State.UNKNOWN, summary="CPU data unavailable")
        return
    if cpu >= 95:
        yield Result(state=State.CRIT, summary=f"CPU: {cpu}% (Critical ≥95%)")
    elif cpu >= 80:
        yield Result(state=State.WARN, summary=f"CPU: {cpu}% (Warning ≥80%)")
    else:
        yield Result(state=State.OK, summary=f"CPU: {cpu}%")

check_plugin_ap_cpu = CheckPlugin(
    name="pmp450i_ap_cpu",
    sections=["pmp450i_ap_health"],
    service_name="CPU Utilization",
    discovery_function=_discover_health,
    check_function=_check_cpu,
)

check_plugin_sm_cpu = CheckPlugin(
    name="pmp450i_sm_cpu",
    sections=["pmp450i_sm_health"],
    service_name="CPU Utilization",
    discovery_function=_discover_health,
    check_function=_check_cpu,
)

# ---------------------------------------------------------------------------
# Radio Temperature
# Thresholds: WARN ≥ 75 °C, CRIT ≥ 85 °C
# ---------------------------------------------------------------------------

def _check_temperature(section: Dict[str, Any]) -> CheckResult:
    temp = section.get("temp_c")
    if temp is None:
        yield Result(state=State.UNKNOWN, summary="Temperature data unavailable")
        return
    if temp >= 85:
        yield Result(state=State.CRIT, summary=f"Radio Temperature: {temp}°C (Critical ≥85°C)")
    elif temp >= 75:
        yield Result(state=State.WARN, summary=f"Radio Temperature: {temp}°C (Warning ≥75°C)")
    else:
        yield Result(state=State.OK, summary=f"Radio Temperature: {temp}°C")

check_plugin_ap_temperature = CheckPlugin(
    name="pmp450i_ap_temperature",
    sections=["pmp450i_ap_health"],
    service_name="Radio Temperature",
    discovery_function=_discover_health,
    check_function=_check_temperature,
)

check_plugin_sm_temperature = CheckPlugin(
    name="pmp450i_sm_temperature",
    sections=["pmp450i_sm_health"],
    service_name="Radio Temperature",
    discovery_function=_discover_health,
    check_function=_check_temperature,
)

# ---------------------------------------------------------------------------
# Packet Errors & Discards
# Reports cumulative counters; flags WARN when any error counter > 0.
# ---------------------------------------------------------------------------

def _check_packet_errors(section: Dict[str, Any]) -> CheckResult:
    eth_in_disc  = section.get("eth_in_discards",  0)
    eth_in_err   = section.get("eth_in_errors",    0)
    eth_out_disc = section.get("eth_out_discards", 0)
    eth_out_err  = section.get("eth_out_errors",   0)
    rf_in_disc   = section.get("rf_in_discards",   0)
    rf_in_err    = section.get("rf_in_errors",     0)
    rf_out_disc  = section.get("rf_out_discards",  0)
    rf_out_err   = section.get("rf_out_errors",    0)

    total_errors   = eth_in_err + eth_out_err + rf_in_err + rf_out_err
    total_discards = eth_in_disc + eth_out_disc + rf_in_disc + rf_out_disc

    summary = (
        f"Eth In: {eth_in_disc} disc / {eth_in_err} err  "
        f"Eth Out: {eth_out_disc} disc / {eth_out_err} err  "
        f"RF In: {rf_in_disc} disc / {rf_in_err} err  "
        f"RF Out: {rf_out_disc} disc / {rf_out_err} err"
    )

    if total_errors > 0:
        yield Result(state=State.WARN, summary=f"Packet errors detected – {summary}")
    elif total_discards > 0:
        yield Result(state=State.OK, summary=f"Discards present – {summary}")
    else:
        yield Result(state=State.OK, summary=f"No errors or discards – {summary}")

check_plugin_ap_packet_errors = CheckPlugin(
    name="pmp450i_ap_packet_errors",
    sections=["pmp450i_ap_health"],
    service_name="Packet Errors and Discards",
    discovery_function=_discover_health,
    check_function=_check_packet_errors,
)

check_plugin_sm_packet_errors = CheckPlugin(
    name="pmp450i_sm_packet_errors",
    sections=["pmp450i_sm_health"],
    service_name="Packet Errors and Discards",
    discovery_function=_discover_health,
    check_function=_check_packet_errors,
)

# ---------------------------------------------------------------------------
# Channel Bandwidth
# Informational – report the current channel width, alert on unexpected change.
# ---------------------------------------------------------------------------

def _check_channel_bw(section: Dict[str, Any]) -> CheckResult:
    bw = section.get("channel_bw")
    if bw is None:
        yield Result(state=State.UNKNOWN, summary="Channel bandwidth data unavailable")
        return
    yield Result(state=State.OK, summary=f"Channel Bandwidth: {bw} MHz")

check_plugin_ap_channel_bw = CheckPlugin(
    name="pmp450i_ap_channel_bw",
    sections=["pmp450i_ap_health"],
    service_name="Channel Bandwidth",
    discovery_function=_discover_health,
    check_function=_check_channel_bw,
)

check_plugin_sm_channel_bw = CheckPlugin(
    name="pmp450i_sm_channel_bw",
    sections=["pmp450i_sm_health"],
    service_name="Channel Bandwidth",
    discovery_function=_discover_health,
    check_function=_check_channel_bw,
)
