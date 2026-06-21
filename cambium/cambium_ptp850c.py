#!/usr/bin/env python3

from typing import Any, Dict, List, Optional
from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    contains,
    any_of,
    DiscoveryResult,
    Result,
    Service,
    SNMPSection,
    SNMPTree,
    State,
    StringTable,
)

_SYS_DESCR_OID = ".1.3.6.1.2.1.1.1.0"
_PTP850_DETECT = any_of(
    contains(_SYS_DESCR_OID, "PTP 850"),
    contains(_SYS_DESCR_OID, "IP-50C"),
    contains(_SYS_DESCR_OID, "IP-50E"),
)


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _first_row(table: StringTable) -> List[str]:
    return table[0] if table and table[0] else []


def _parse_ptp850c(string_table: List[StringTable]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    # [0] RFU status table - local RSL and RF temperature
    local_row = _first_row(string_table[0])
    if local_row:
        results["local_rsl"] = _safe_int(local_row[0])
        results["rf_temp"] = _safe_int(local_row[1])

    # [1] RFU config table - local ATPC reference RSL
    local_cfg_row = _first_row(string_table[1])
    if local_cfg_row:
        results["local_rsl_ref"] = _safe_int(local_cfg_row[0])

    # [2] Remote radio table - communication + remote RSL + remote reference RSL
    remote_row = _first_row(string_table[2])
    if remote_row:
        results["remote_comm"] = _safe_int(remote_row[0])
        results["remote_rsl"] = _safe_int(remote_row[1])
        results["remote_rsl_ref"] = _safe_int(remote_row[2])

    # [3] PM traffic signal level table - interval min/max RSL
    pm_rsl_row = _first_row(string_table[3])
    if pm_rsl_row:
        results["interval_min_rsl"] = _safe_int(pm_rsl_row[0])
        results["interval_max_rsl"] = _safe_int(pm_rsl_row[1])

    # [4] MRMC current table - current TX/RX QAM
    qam_curr_row = _first_row(string_table[4])
    if qam_curr_row:
        results["qam_tx_current"] = _safe_int(qam_curr_row[0])
        results["qam_rx_current"] = _safe_int(qam_curr_row[1])

    # [5] MRMC profile table - max TX/RX QAM across profiles
    max_tx_qam: Optional[int] = None
    max_rx_qam: Optional[int] = None
    for row in string_table[5] if len(string_table) > 5 else []:
        tx_qam = _safe_int(row[0]) if len(row) > 0 else None
        rx_qam = _safe_int(row[1]) if len(row) > 1 else None
        if tx_qam is not None:
            max_tx_qam = tx_qam if max_tx_qam is None else max(max_tx_qam, tx_qam)
        if rx_qam is not None:
            max_rx_qam = rx_qam if max_rx_qam is None else max(max_rx_qam, rx_qam)
    results["qam_tx_max"] = max_tx_qam
    results["qam_rx_max"] = max_rx_qam

    # [6] Traffic aggregate PM table - ES / SES / UAS (sample latest row available)
    pm_agg_row = _first_row(string_table[6])
    if pm_agg_row:
        results["es"] = _safe_int(pm_agg_row[0])
        results["ses"] = _safe_int(pm_agg_row[1])
        results["uas"] = _safe_int(pm_agg_row[2])

    # [7] IF-MIB counters - sum across all interfaces
    if_rows = string_table[7]
    in_discards = in_errors = out_discards = out_errors = 0
    for row in if_rows:
        if len(row) < 4:
            continue
        in_discards += _safe_int(row[0]) or 0
        in_errors += _safe_int(row[1]) or 0
        out_discards += _safe_int(row[2]) or 0
        out_errors += _safe_int(row[3]) or 0
    results["if_in_discards"] = in_discards
    results["if_in_errors"] = in_errors
    results["if_out_discards"] = out_discards
    results["if_out_errors"] = out_errors

    # [8] Unit scalars - IDU temp + input voltage
    unit_row = _first_row(string_table[8])
    if unit_row:
        results["idu_temp"] = _safe_int(unit_row[0])
        results["idu_voltage"] = _safe_int(unit_row[1])

    # [9] System alarm scalar
    alarm_row = _first_row(string_table[9])
    if alarm_row:
        results["most_severe_alarm"] = _safe_int(alarm_row[0])

    # [10] XPIC scalar
    xpic_row = _first_row(string_table[10])
    if xpic_row:
        results["xpic_interfaces"] = _safe_int(xpic_row[0])

    return results


snmp_section_ptp850c = SNMPSection(
    name="ptp850c",
    parse_function=_parse_ptp850c,
    detect=_PTP850_DETECT,
    fetch=[
        SNMPTree(".1.3.6.1.4.1.2281.10.5.1.1", ["2", "4"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.5.2.1", ["6"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.7.3.1.1", ["2", "4", "8"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.6.3.2.1.1", ["4", "5"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.7.4.1.1", ["6", "10"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.7.4.4.1", ["4", "6"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.6.3.3.1.1", ["3", "4", "5"]),
        SNMPTree(".1.3.6.1.2.1.2.2.1", ["13", "14", "19", "20"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.1.1", ["9.0", "10.0"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.3.1", ["3.0"]),
        SNMPTree(".1.3.6.1.4.1.2281.10.7.8.2", ["10.0"]),
    ],
)


def _discover(section: Dict[str, Any]) -> DiscoveryResult:
    if section:
        yield Service()


def _check_rsl(section: Dict[str, Any]) -> CheckResult:
    local_rsl = section.get("local_rsl")
    remote_rsl = section.get("remote_rsl")
    local_ref = section.get("local_rsl_ref")
    interval_min = section.get("interval_min_rsl")
    interval_max = section.get("interval_max_rsl")

    if local_rsl is None:
        yield Result(state=State.UNKNOWN, summary="Local RSL unavailable")
        return

    degradation = max(0, local_ref - local_rsl) if local_ref is not None else None
    if degradation is None:
        state = State.OK
        deviation_txt = "n/a"
    elif degradation > 6:
        state = State.CRIT
        deviation_txt = f"{degradation} dB (Critical >6 dB)"
    elif degradation > 3:
        state = State.WARN
        deviation_txt = f"{degradation} dB (Warning >3 dB)"
    else:
        state = State.OK
        deviation_txt = f"{degradation} dB"

    parts = [f"Local RSL {local_rsl} dBm", f"Degradation vs baseline {deviation_txt}"]
    if local_ref is not None:
        parts.append(f"Local baseline {local_ref} dBm")
    if remote_rsl is not None:
        parts.append(f"Remote RSL {remote_rsl} dBm")
    if interval_min is not None and interval_max is not None:
        parts.append(f"Interval Min/Max {interval_min}/{interval_max} dBm")

    yield Result(state=state, summary="; ".join(parts))


def _check_modulation(section: Dict[str, Any]) -> CheckResult:
    tx_curr = section.get("qam_tx_current")
    rx_curr = section.get("qam_rx_current")
    tx_max = section.get("qam_tx_max")
    rx_max = section.get("qam_rx_max")

    if tx_curr is None and rx_curr is None:
        yield Result(state=State.UNKNOWN, summary="Modulation data unavailable")
        return

    state = State.OK
    if (tx_curr is not None and tx_max is not None and tx_curr < tx_max) or (
        rx_curr is not None and rx_max is not None and rx_curr < rx_max
    ):
        state = State.WARN

    yield Result(
        state=state,
        summary=(
            f"Current TX/RX QAM: {tx_curr}/{rx_curr}; "
            f"Max TX/RX QAM: {tx_max}/{rx_max}"
        ),
    )


def _check_link_availability(section: Dict[str, Any]) -> CheckResult:
    remote_comm = section.get("remote_comm")
    es = section.get("es")
    ses = section.get("ses")
    uas = section.get("uas")

    if remote_comm is None:
        yield Result(state=State.UNKNOWN, summary="Link state unavailable")
        return

    # remote communication enum commonly: 1=up, 2=down
    if remote_comm == 1:
        state = State.OK
        status = "Link state: up"
    elif remote_comm == 2:
        state = State.CRIT
        status = "Link state: down"
    else:
        state = State.WARN
        status = f"Link state: {remote_comm}"

    kpi = []
    if es is not None:
        kpi.append(f"ES {es}")
    if ses is not None:
        kpi.append(f"SES {ses}")
    if uas is not None:
        kpi.append(f"UAS {uas}")

    if kpi:
        status = f"{status}; {'; '.join(kpi)}"

    yield Result(state=state, summary=status)


def _check_ethernet_errors(section: Dict[str, Any]) -> CheckResult:
    in_discards = section.get("if_in_discards", 0)
    in_errors = section.get("if_in_errors", 0)
    out_discards = section.get("if_out_discards", 0)
    out_errors = section.get("if_out_errors", 0)

    total_errors = in_errors + out_errors
    summary = (
        f"In: {in_errors} err / {in_discards} disc; "
        f"Out: {out_errors} err / {out_discards} disc"
    )

    if total_errors > 0:
        yield Result(state=State.WARN, summary=f"Ethernet errors present - {summary}")
    elif in_discards > 0 or out_discards > 0:
        yield Result(state=State.OK, summary=f"Discards present - {summary}")
    else:
        yield Result(state=State.OK, summary=f"No Ethernet errors/discards - {summary}")


def _check_temperature(section: Dict[str, Any]) -> CheckResult:
    rf_temp = section.get("rf_temp")
    idu_temp = section.get("idu_temp")

    if rf_temp is None and idu_temp is None:
        yield Result(state=State.UNKNOWN, summary="Temperature data unavailable")
        return

    peak = max(v for v in [rf_temp, idu_temp] if v is not None)
    if peak >= 80:
        state = State.CRIT
    elif peak >= 70:
        state = State.WARN
    else:
        state = State.OK

    yield Result(state=state, summary=f"RFU {rf_temp}°C; IDU {idu_temp}°C")


def _check_power(section: Dict[str, Any]) -> CheckResult:
    voltage = section.get("idu_voltage")
    if voltage is None:
        yield Result(state=State.UNKNOWN, summary="Input voltage unavailable")
        return

    # Typical telecom DC feeds are around 48V; apply broad guard rails.
    if voltage < 40 or voltage > 60:
        state = State.WARN
    else:
        state = State.OK

    yield Result(state=state, summary=f"Input voltage: {voltage} V")


def _check_xpic(section: Dict[str, Any]) -> CheckResult:
    xpic_interfaces = section.get("xpic_interfaces")
    if xpic_interfaces is None:
        yield Result(state=State.UNKNOWN, summary="XPIC data unavailable")
        return

    if xpic_interfaces > 0:
        yield Result(state=State.OK, summary=f"XPIC enabled ({xpic_interfaces} interfaces)")
    else:
        yield Result(state=State.OK, summary="XPIC not enabled")


def _check_alarm(section: Dict[str, Any]) -> CheckResult:
    severity = section.get("most_severe_alarm")
    if severity is None:
        yield Result(state=State.UNKNOWN, summary="Alarm severity unavailable")
        return

    # Vendor severity is integer-coded and model-dependent; map conservatively.
    if severity >= 5:
        state = State.CRIT
    elif severity >= 3:
        state = State.WARN
    else:
        state = State.OK

    yield Result(state=state, summary=f"Most severe alarm level: {severity}")


check_plugin_ptp850c_rsl = CheckPlugin(
    name="ptp850c_rsl",
    sections=["ptp850c"],
    service_name="PTP850C RSL",
    discovery_function=_discover,
    check_function=_check_rsl,
)

check_plugin_ptp850c_modulation = CheckPlugin(
    name="ptp850c_modulation",
    sections=["ptp850c"],
    service_name="PTP850C Adaptive Modulation",
    discovery_function=_discover,
    check_function=_check_modulation,
)

check_plugin_ptp850c_link = CheckPlugin(
    name="ptp850c_link_availability",
    sections=["ptp850c"],
    service_name="PTP850C Link Availability",
    discovery_function=_discover,
    check_function=_check_link_availability,
)

check_plugin_ptp850c_ethernet = CheckPlugin(
    name="ptp850c_ethernet_errors",
    sections=["ptp850c"],
    service_name="PTP850C Ethernet Errors",
    discovery_function=_discover,
    check_function=_check_ethernet_errors,
)

check_plugin_ptp850c_temperature = CheckPlugin(
    name="ptp850c_temperature",
    sections=["ptp850c"],
    service_name="PTP850C Temperature",
    discovery_function=_discover,
    check_function=_check_temperature,
)

check_plugin_ptp850c_power = CheckPlugin(
    name="ptp850c_power",
    sections=["ptp850c"],
    service_name="PTP850C Power Input",
    discovery_function=_discover,
    check_function=_check_power,
)

check_plugin_ptp850c_xpic = CheckPlugin(
    name="ptp850c_xpic",
    sections=["ptp850c"],
    service_name="PTP850C XPIC",
    discovery_function=_discover,
    check_function=_check_xpic,
)

check_plugin_ptp850c_alarm = CheckPlugin(
    name="ptp850c_alarm",
    sections=["ptp850c"],
    service_name="PTP850C Alarm Summary",
    discovery_function=_discover,
    check_function=_check_alarm,
)
