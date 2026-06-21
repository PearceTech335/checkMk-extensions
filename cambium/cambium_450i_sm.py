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
# SM detect helper
# ---------------------------------------------------------------------------
_SM_DETECT = all_of(
    startswith(".1.3.6.1.2.1.1.1.0", "CANOPY"),
    contains(".1.3.6.1.2.1.1.1.0", "SM"),
)

# ---------------------------------------------------------------------------
# Section: SM RSSI (existing)
# Fetches from whispProducts base (.1.3.6.1.4.1.161.19.3) spanning both
# whispSm (.2) and whispBox (.3) sub-trees.
# ---------------------------------------------------------------------------

def _parse_rssi(string_table: StringTable) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        tx_power_string = string_table[0][2]
        tx_power_string = tx_power_string[0:2]

        results["radio_rssi"] = float(string_table[0][0])
        results["active_eirp"] = string_table[1][1]
        results["tx_power"]    = float(tx_power_string)
        results["max_power"]   = float(string_table[0][3])
        results["h_pol"]       = float(string_table[0][4])
        results["v_pol"]       = float(string_table[0][5])
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in _parse_rssi: {e}")
    return results

snmp_section_pmp450i_sm = SimpleSNMPSection(
    name="pmp450i_sm",
    parse_function=_parse_rssi,
    detect=_SM_DETECT,
    fetch=SNMPTree(
        ".1.3.6.1.4.1.161.19.3",
        [
            "2.2.8.0",    # radioDbm – Rx power level (display string)
            "3.1.306",    # activeEirpStr – currently active EIRP per carrier
            "2.2.23.0",   # txPowerCurrent – current TX power
            "2.1.161.0",  # maxTransmitPower – max TX power
            "2.2.117.0",  # radioDbmHorizontal – horizontal Rx power (dBm)
            "2.2.118.0",  # radioDbmVertical   – vertical Rx power (dBm)
        ],
    ),
)

def _discover_sm(section: Dict[str, Any]) -> DiscoveryResult:
    yield Service()

# ---- RSSI ----

def _check_rssi(section: Dict[str, Any]) -> CheckResult:
    rssi = section.get("radio_rssi")
    if rssi is None:
        yield Result(state=State.UNKNOWN, summary="RSSI data unavailable")
        return
    if rssi < -80:
        yield Result(state=State.CRIT, summary=f"Very Poor Link Quality: {rssi} dBm")
    elif rssi < -70:
        yield Result(state=State.WARN, summary=f"Check Link Quality: {rssi} dBm")
    else:
        yield Result(state=State.OK, summary=f"{rssi} dBm")

# ---- Active EIRP ----

def _check_active_eirp(section: Dict[str, Any]) -> CheckResult:
    active_eirp = section.get("active_eirp", "")
    yield Result(state=State.OK, summary=f"{active_eirp}")

# ---- TX Power ----

def _check_tx_power(section: Dict[str, Any]) -> CheckResult:
    tx_power  = section.get("tx_power")
    max_power = section.get("max_power")
    if tx_power is None:
        yield Result(state=State.UNKNOWN, summary="TX Power data unavailable")
        return
    if tx_power == max_power:
        yield Result(
            state=State.WARN,
            summary=(
                f"Check Line of Sight/Link Distance -> "
                f"TxPower:{tx_power}dBm MaxPower: {max_power}dBm"
            ),
        )
    else:
        yield Result(state=State.OK, summary=f"{tx_power} dBm")

# ---- V/H Polarization Disparity ----

def _check_polarization(section: Dict[str, Any]) -> CheckResult:
    v_pol = section.get("v_pol")
    h_pol = section.get("h_pol")
    if v_pol is None or h_pol is None:
        yield Result(state=State.UNKNOWN, summary="Polarization data unavailable")
        return
    disparity = abs(v_pol - h_pol)
    if disparity > 10:
        yield Result(
            state=State.WARN,
            summary=(
                f"Check Link Alignment - V <-> H Disparity greater than 10 dBm: "
                f"{disparity} dBm"
            ),
        )
    else:
        yield Result(state=State.OK, summary=f"{disparity} dBm")

check_plugin_rssi = CheckPlugin(
    name="pmp450i_rssi_check",
    sections=["pmp450i_sm"],
    service_name="RSSI - (from AP)",
    discovery_function=_discover_sm,
    check_function=_check_rssi,
)
check_plugin_eirp = CheckPlugin(
    name="pmp450i_active_eirp",
    sections=["pmp450i_sm"],
    service_name="Active EIRP",
    discovery_function=_discover_sm,
    check_function=_check_active_eirp,
)
check_plugin_tx_power = CheckPlugin(
    name="pmp450i_max_tx",
    sections=["pmp450i_sm"],
    service_name="Tx Power",
    discovery_function=_discover_sm,
    check_function=_check_tx_power,
)
check_plugin_polarization = CheckPlugin(
    name="pmp450i_check_polarization",
    sections=["pmp450i_sm"],
    service_name="V/H Polarization Disparity",
    discovery_function=_discover_sm,
    check_function=_check_polarization,
)

# ---------------------------------------------------------------------------
# Section: SM Extended – registration status, integer RSSI, CINR/SNR
#
# Fetches from whispSmStatus (.1.3.6.1.4.1.161.19.3.2.2):
#   sessionStatus             (.1)  – "Registered" or other string
#   radioDbmInt               (.21) – combined Rx power as integer (dBm)
#   signalToNoiseRatioSMVertical   (.95)  – SNR vertical path (dB)
#   signalToNoiseRatioSMHorizontal (.106) – SNR horizontal path (dB, MIMO only)
# ---------------------------------------------------------------------------

def _parse_sm_extended(string_table: StringTable) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        row = string_table[0]
        results["session_status"] = row[0]
        results["rssi_int"]       = int(row[1])
        results["snr_vertical"]   = int(row[2])
        results["snr_horizontal"] = int(row[3])
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error in _parse_sm_extended: {e}")
    return results

snmp_section_pmp450i_sm_extended = SimpleSNMPSection(
    name="pmp450i_sm_extended",
    parse_function=_parse_sm_extended,
    detect=_SM_DETECT,
    fetch=SNMPTree(
        ".1.3.6.1.4.1.161.19.3.2.2",
        [
            "1.0",    # sessionStatus – "Registered" / "Not Registered"
            "21.0",   # radioDbmInt – combined Rx power (integer dBm)
            "95.0",   # signalToNoiseRatioSMVertical
            "106.0",  # signalToNoiseRatioSMHorizontal (MIMO only; 0 if N/A)
        ],
    ),
)

def _discover_sm_extended(section: Dict[str, Any]) -> DiscoveryResult:
    if section:
        yield Service()

# ---- Registration Status ----

def _check_registration_status(section: Dict[str, Any]) -> CheckResult:
    status = section.get("session_status", "")
    if not status:
        yield Result(state=State.UNKNOWN, summary="Registration status data unavailable")
        return
    if "registered" in status.lower():
        yield Result(state=State.OK, summary=f"SM Registered: {status}")
    else:
        yield Result(state=State.CRIT, summary=f"SM Not Registered: {status}")

check_plugin_registration_status = CheckPlugin(
    name="pmp450i_registration_status",
    sections=["pmp450i_sm_extended"],
    service_name="SM Registration Status",
    discovery_function=_discover_sm_extended,
    check_function=_check_registration_status,
)

# ---- CINR / SNR ----
# Thresholds:  WARN < 15 dB,  CRIT < 10 dB

def _snr_result(snr: int, label: str) -> Result:
    if snr < 10:
        return Result(state=State.CRIT,  summary=f"{label}: {snr} dB (Critical <10 dB)")
    if snr < 15:
        return Result(state=State.WARN,  summary=f"{label}: {snr} dB (Warning <15 dB)")
    return     Result(state=State.OK,   summary=f"{label}: {snr} dB")

def _check_cinr(section: Dict[str, Any]) -> CheckResult:
    snr_v = section.get("snr_vertical")
    snr_h = section.get("snr_horizontal")
    if snr_v is None:
        yield Result(state=State.UNKNOWN, summary="CINR/SNR data unavailable")
        return
    yield _snr_result(snr_v, "SNR Vertical")
    # snr_horizontal returns 0 on non-MIMO radios; skip if zero
    if snr_h is not None and snr_h != 0:
        yield _snr_result(snr_h, "SNR Horizontal")

check_plugin_cinr = CheckPlugin(
    name="pmp450i_cinr",
    sections=["pmp450i_sm_extended"],
    service_name="CINR / SNR",
    discovery_function=_discover_sm_extended,
    check_function=_check_cinr,
)
