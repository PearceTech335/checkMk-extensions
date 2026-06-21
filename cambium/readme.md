# Cambium PMP 450i CheckMK Plugins

## Installation

Copy the plugin files into:

```
/omd/sites/<your-site>/local/lib/python3/cmk_addons/plugins/<folder-name>/agent_based/
```

Services are discovered automatically during an SNMP discovery scan based on the `sysDescr` OID
(must start with `CANOPY` and contain `AP` or `SM`).

---

## Services per Device Type

### Access Point (`cambium_450i_ap.py`)

| Service Name                    | Description                                      | Alert Thresholds                     |
|---------------------------------|--------------------------------------------------|--------------------------------------|
| Subscriber Module Target RSSI   | Configured target RSSI for associated SMs        | Informational                        |
| Downlink Frame Utilization      | DL frame utilization % (5-min avg + 15-min avg)  | WARN ≥ 70 %, CRIT ≥ 85 %            |
| Uplink Frame Utilization        | UL frame utilization % (5-min avg + 15-min avg)  | WARN ≥ 70 %, CRIT ≥ 85 %            |
| Registered Subscriber Count     | Number of SMs currently registered               | Informational                        |
| GPS Sync Status                 | GPS synchronisation state                        | WARN: generating, CRIT: sync lost    |
| Operating Frequency             | Current operating frequency (MHz)                | Informational                        |

### Subscriber Module (`cambium_450i_sm.py`)

| Service Name              | Description                                         | Alert Thresholds                     |
|---------------------------|-----------------------------------------------------|--------------------------------------|
| RSSI - (from AP)          | Receive signal strength (dBm, display string)       | WARN < −70 dBm, CRIT < −80 dBm      |
| Active EIRP               | Effective isotropic radiated power                  | Informational                        |
| Tx Power                  | Current transmit power vs. maximum                  | WARN if at max power                 |
| V/H Polarization Disparity| Difference between V and H antenna signal (dBm)     | WARN if disparity > 10 dBm           |
| SM Registration Status    | Whether the SM is registered to its AP              | CRIT if not registered               |
| CINR / SNR                | Signal-to-noise ratio (V path; H path if MIMO)      | WARN < 15 dB, CRIT < 10 dB          |

### Both AP and SM (`cambium_450i_health.py`)

| Service Name                  | Description                                      | Alert Thresholds                       |
|-------------------------------|--------------------------------------------------|----------------------------------------|
| CPU Utilization               | Current CPU usage %                              | WARN ≥ 80 %, CRIT ≥ 95 %              |
| Radio Temperature             | Internal radio temperature (°C)                  | WARN ≥ 75 °C, CRIT ≥ 85 °C            |
| Packet Errors and Discards    | Ethernet + RF error and discard counters         | WARN if any error counter > 0          |
| Channel Bandwidth             | Configured channel width (MHz)                   | Informational                          |

---

## MIBs Required

The plugins use the following Cambium MIB files (included in `PM450 25.0.1 MIBS.zip`):

- `WHISP-APS-MIB.txt` – AP frame utilisation, GPS, SM count, frequency
- `WHISP-SM-MIB.txt`  – SM RSSI, CINR/SNR, registration status
- `WHISP-BOX-MIBV2-MIB.txt` – CPU, temperature, error counters, channel bandwidth

### PTP 850C (`cambium_ptp850c.py`)

| Service Name                 | Description                                                           | Alert Thresholds                                      |
|-----------------------------|-----------------------------------------------------------------------|-------------------------------------------------------|
| PTP850C RSL                | Local/remote RSL, baseline deviation, interval min/max RSL            | WARN drop > 3 dB from baseline, CRIT drop > 6 dB     |
| PTP850C Adaptive Modulation| Current TX/RX QAM vs max profile QAM                                  | WARN when current QAM is below max design profile     |
| PTP850C Link Availability  | Remote link state plus ES/SES/UAS counters                            | CRIT when link state reports down                     |
| PTP850C Ethernet Errors    | Summed IF-MIB `ifInErrors/ifOutErrors/ifInDiscards/ifOutDiscards`     | WARN if any Ethernet errors are present               |
| PTP850C Temperature        | RFU and IDU temperatures                                               | WARN ≥ 70 °C, CRIT ≥ 80 °C                            |
| PTP850C Power Input        | IDU input voltage                                                      | WARN outside 40–60 V                                  |
| PTP850C XPIC               | XPIC enablement indicator                                              | Informational (enabled/disabled)                      |
| PTP850C Alarm Summary      | Most severe system alarm integer level                                | WARN/CRIT on elevated severity                        |

PTP 850C OIDs are sourced from `PTP 850 MIB_Reference_13.0_Rev_S.zip` (notably `MWRM-RADIO-MIB`, `MWRM-PM-MIB`, `MWRM-UNIT-MIB`, and IF-MIB objects).
