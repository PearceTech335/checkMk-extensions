#!/usr/bin/env python3

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
    SimpleSNMPSection,
    SNMPTree,
    State,
    StringTable,
)

# ---------------------------------------------------------------------------
# AP detect helper
# ---------------------------------------------------------------------------
_AP_DETECT = all_of(
    startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
    contains(".1.3.6.1.2.1.1.1.0", "AP"),
)

# ---------------------------------------------------------------------------
# Section: Target SM RSSI (existing)
# OID: whispApsConfig.90  (.1.3.6.1.4.1.161.19.3.1.1.90.0)
# ---------------------------------------------------------------------------

def _parse_ap_target_rssi(string_table: StringTable) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        results["target"] = float(string_table[0][0])
    except (IndexError, ValueError, TypeError):
        pass  # Return empty dict if parsing fails
    return results

snmp_section_pmp450i_ap = SimpleSNMPSection(
    name="pmp450i_ap",
    parse_function=_parse_ap_target_rssi,
    detect=_AP_DETECT,
    fetch=SNMPTree(
        ".1.3.6.1.4.1.161.19.3.1",
        [
            "1.90.0",   # targetRSSI – target receive power for SMs
        ],
    ),
)

def _discover_ap(section: Dict[str, Any]) -> DiscoveryResult:
    yield Service()

def _check_target_sm_rssi(section: Dict[str, Any]) -> CheckResult:
    target = section.get("target")
    if target is None:
        yield Result(state=State.UNKNOWN, summary="Target RSSI data unavailable")
        return
    yield Result(state=State.OK, summary=f"{target} dBm")

check_plugin_target_sm_rssi = CheckPlugin(
    name="pmp450i_target_sm_rssi",
    sections=["pmp450i_ap"],
    service_name="Subscriber Module Target RSSI",
    discovery_function=_discover_ap,
    check_function=_check_target_sm_rssi,
)

# ---------------------------------------------------------------------------
# Section: AP Extended – frame utilisation, SM count, GPS sync, frequency
#
# Fetches from four sub-trees of whispAps (.1.3.6.1.4.1.161.19.3.1):
#   [0] whispApsFrUtlStatsIntervalMedium (.12.2) – 5-min frame utilisation
#   [1] whispApsFrUtlStatsIntervalHigh   (.12.3) – 15-min frame utilisation
#   [2] whispApsStatus                   (.7)    – regCount, gpsStatus, opFreq
#   [3] whispApsGPS                      (.3)    – GPS sync integer
# ---------------------------------------------------------------------------

def _parse_ap_extended(string_table: List[StringTable]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        # 5-min frame utilisation
        t5 = string_table[0]
        if t5 and t5[0]:
            results["dl_util_5min"] = int(t5[0][0])
            results["ul_util_5min"] = int(t5[0][1])

        # 15-min frame utilisation
        t15 = string_table[1]
        if t15 and t15[0]:
            results["dl_util_15min"] = int(t15[0][0])
            results["ul_util_15min"] = int(t15[0][1])

        # AP status scalars
        tst = string_table[2]
        if tst and tst[0]:
            results["reg_count"]    = int(tst[0][0])
            results["gps_status"]   = tst[0][1]
            results["op_freq_khz"]  = int(tst[0][2])

        # GPS sync integer enum (1=synced, 2=lost, 3=generating)
        tgps = string_table[3]
        if tgps and tgps[0]:
            results["gps_sync_int"] = int(tgps[0][0])

    except (IndexError, ValueError, TypeError):
        pass  # Return partial results if parsing fails
    return results

snmp_section_pmp450i_ap_extended = SNMPSection(
    name="pmp450i_ap_extended",
    parse_function=_parse_ap_extended,
    detect=_AP_DETECT,
    fetch=[
        # whispApsFrUtlStatsIntervalMedium – 5-min percentages
        SNMPTree(
            ".1.3.6.1.4.1.161.19.3.1.12.2",
            [
                "1.0",   # frUtlMedTotalDownlinkUtilization
                "2.0",   # frUtlMedTotalUplinkUtilization
            ],
        ),
        # whispApsFrUtlStatsIntervalHigh – 15-min percentages
        SNMPTree(
            ".1.3.6.1.4.1.161.19.3.1.12.3",
            [
                "1.0",   # frUtlHighTotalDownlinkUtilization
                "2.0",   # frUtlHighTotalUplinkUtilization
            ],
        ),
        # whispApsStatus
        SNMPTree(
            ".1.3.6.1.4.1.161.19.3.1.7",
            [
                "1.0",   # regCount – number of registered SMs
                "2.0",   # gpsStatus – text description
                "37.0",  # operatingFrequency – current frequency in kHz
            ],
        ),
        # whispApsGPS
        SNMPTree(
            ".1.3.6.1.4.1.161.19.3.1.3",
            [
                "1.0",   # whispGPSStats – 1=synced, 2=lost, 3=generating
            ],
        ),
    ],
)

def _discover_ap_extended(section: Dict[str, Any]) -> DiscoveryResult:
    if section:
        yield Service()

# ---- Frame utilisation (5-min) ----
# Thresholds: WARN 70%, CRIT 85%, EMERG (also CRIT) 95%

def _check_frame_util(util: int, direction: str) -> CheckResult:
    if util >= 95:
        yield Result(state=State.CRIT, summary=f"{direction} Frame Utilization: {util}% (EMERGENCY ≥95%)")
    elif util >= 85:
        yield Result(state=State.CRIT, summary=f"{direction} Frame Utilization: {util}% (Critical ≥85%)")
    elif util >= 70:
        yield Result(state=State.WARN, summary=f"{direction} Frame Utilization: {util}% (Warning ≥70%)")
    else:
        yield Result(state=State.OK, summary=f"{direction} Frame Utilization: {util}%")

def _check_dl_frame_util(section: Dict[str, Any]) -> CheckResult:
    dl = section.get("dl_util_5min")
    dl15 = section.get("dl_util_15min")
    if dl is None:
        yield Result(state=State.UNKNOWN, summary="Downlink frame utilization data unavailable")
        return
    yield from _check_frame_util(dl, "Downlink")
    if dl15 is not None:
        yield Result(state=State.OK, summary=f"15-min avg: {dl15}%")

def _check_ul_frame_util(section: Dict[str, Any]) -> CheckResult:
    ul = section.get("ul_util_5min")
    ul15 = section.get("ul_util_15min")
    if ul is None:
        yield Result(state=State.UNKNOWN, summary="Uplink frame utilization data unavailable")
        return
    yield from _check_frame_util(ul, "Uplink")
    if ul15 is not None:
        yield Result(state=State.OK, summary=f"15-min avg: {ul15}%")

check_plugin_dl_frame_util = CheckPlugin(
    name="pmp450i_dl_frame_utilization",
    sections=["pmp450i_ap_extended"],
    service_name="Downlink Frame Utilization",
    discovery_function=_discover_ap_extended,
    check_function=_check_dl_frame_util,
)

check_plugin_ul_frame_util = CheckPlugin(
    name="pmp450i_ul_frame_utilization",
    sections=["pmp450i_ap_extended"],
    service_name="Uplink Frame Utilization",
    discovery_function=_discover_ap_extended,
    check_function=_check_ul_frame_util,
)

# ---- SM Registration Count ----

def _check_sm_count(section: Dict[str, Any]) -> CheckResult:
    count = section.get("reg_count")
    if count is None:
        yield Result(state=State.UNKNOWN, summary="SM count data unavailable")
        return
    yield Result(state=State.OK, summary=f"Registered SMs: {count}")

check_plugin_sm_count = CheckPlugin(
    name="pmp450i_sm_count",
    sections=["pmp450i_ap_extended"],
    service_name="Registered Subscriber Count",
    discovery_function=_discover_ap_extended,
    check_function=_check_sm_count,
)

# ---- GPS Sync Status ----

_GPS_SYNC_STATES = {
    1: (State.OK,   "GPS Synchronized"),
    2: (State.CRIT, "GPS Sync Lost"),
    3: (State.WARN, "Generating Sync (no GPS)"),
}

def _check_gps_sync(section: Dict[str, Any]) -> CheckResult:
    gps_int = section.get("gps_sync_int")
    gps_str = section.get("gps_status", "")
    if gps_int is None:
        yield Result(state=State.UNKNOWN, summary="GPS status data unavailable")
        return
    state, label = _GPS_SYNC_STATES.get(gps_int, (State.UNKNOWN, f"Unknown GPS state ({gps_int})"))
    detail = f" ({gps_str})" if gps_str else ""
    yield Result(state=state, summary=f"{label}{detail}")

check_plugin_gps_sync = CheckPlugin(
    name="pmp450i_gps_sync",
    sections=["pmp450i_ap_extended"],
    service_name="GPS Sync Status",
    discovery_function=_discover_ap_extended,
    check_function=_check_gps_sync,
)

# ---- Operating Frequency ----

def _check_operating_frequency(section: Dict[str, Any]) -> CheckResult:
    freq_khz = section.get("op_freq_khz")
    if freq_khz is None:
        yield Result(state=State.UNKNOWN, summary="Operating frequency data unavailable")
        return
    freq_mhz = freq_khz / 1000.0
    yield Result(state=State.OK, summary=f"Operating Frequency: {freq_mhz:.3f} MHz")

check_plugin_operating_frequency = CheckPlugin(
    name="pmp450i_operating_frequency",
    sections=["pmp450i_ap_extended"],
    service_name="Operating Frequency",
    discovery_function=_discover_ap_extended,
    check_function=_check_operating_frequency,
)
