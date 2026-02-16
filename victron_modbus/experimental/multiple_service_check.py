#!/usr/bin/env python3
import socket
import struct
import sys

def read_holding_registers(ip, port, unit_id, start_address, count):
    packet = struct.pack('>HHHBBHH', 1, 0, 6, unit_id, 3, start_address, count)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((ip, port))
            s.sendall(packet)
            res = s.recv(1024)
            if len(res) < 9: return None
            byte_count = res[8]
            data_bytes = res[9:9+byte_count]
            return [struct.unpack('>H', data_bytes[i:i+2])[0] for i in range(0, len(data_bytes), 2)]
    except:
        return None

def get_charge_label(state):
    # Victron specific state mapping for register 775
    mapping = {
        0: "Off", 2: "Fault", 3: "Bulk",
        4: "Absorption", 5: "Float", 6: "Storage",
        7: "Manual Equalize", 252: "External Control"
    }
    return mapping.get(state, f"Unknown ({state})")

def main():
    # --- HANDLING CLI ARGUMENTS ---
    if len(sys.argv) < 2:
        print("2 Victron_Solar - ERROR: No IP address provided. Usage: ./script.py <IP>")
        sys.exit(3)
    DEVICE_IP = sys.argv[1]
    DEVICE_PORT = 502
    SLAVE_ID = 247
    # Structure: Address: (ID, Name, Scale, Warn_Low, Crit_Low)
    points = {
        771: ("bat_volts", "Battery Voltage", 100, 47.5, 45),
#        772: ("bat_amps", "Battery Current", 10, None, None),
#        776: ("pv_volts", "Solar Voltage", 100, None, None),
#        777: ("pv_amps", "Solar Current", 10, None, None),
#        784: ("yield_today", "Yield Today", 10, None, None),
    }

    perf_data = []
    status_text = []
    item_status = 0

    # 1. Handle Numeric Points
    for addr, (id_name, display_name, scale, warn, crit) in points.items():
        raw = read_holding_registers(DEVICE_IP, DEVICE_PORT, SLAVE_ID, addr, 1)
        if isinstance(raw, list):
            val = raw[0] / scale

            # Threshold Check
            if crit and val <= crit: item_status = max(item_status, 2)
            elif warn and val <= warn: item_status = max(item_status, 1)

            w_s = str(warn) if warn else ""
            c_s = str(crit) if crit else ""
            perf = f"{id_name}={val};{w_s};{c_s}"

            print(f"{item_status} \"Victron Solar {display_name}\"{perf}{display_name} is {val}")
        else:
            item_status = max(item_status, 2) # Crit if communication fails

    # 2. Handle Charge State (Non-numeric mapping)
    state_raw = read_holding_registers(DEVICE_IP, DEVICE_PORT, SLAVE_ID, 775, 1)
    if isinstance(state_raw, list):
        label = get_charge_label(state_raw[0])
        status_text.append(f"State: {label}")
        perf_data.append(f"charge_state={state_raw[0]}")

    # Final Output
    perf_string = "|".join(perf_data)
    summary = " - ".join(status_text)
    #print(f"{overall_status} Victron_Solar {perf_string} {summary}")

if __name__ == "__main__":
    main()
