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
def handle_signed_number(val):
    if val < 32768:
        return val
    else:
        return val - 65536

def main():
    # --- HANDLING CLI ARGUMENTS ---
    if len(sys.argv) < 2:
        print("2 Victron_Solar - ERROR: No IP address provided. Usage: ./script.py <IP>")
        sys.exit(3)
    DEVICE_IP = sys.argv[1]
    DEVICE_PORT = 502
    SLAVE_ID = 100
    # Structure: addr, (id_name, display_name, scale, unit,  warn, crit, is_signed)
    points = {
        850: ("pv_power", "PV Power", 1, "W", None, None, False),
    }

    for addr, (id_name, display_name, scale, unit, warn, crit, is_signed) in points.items():
        item_status = 0
        raw = read_holding_registers(DEVICE_IP, DEVICE_PORT, SLAVE_ID, addr, 1)

        if isinstance(raw, list):
            raw_val = handle_signed_number(raw[0]) if is_signed else raw[0]
            val = raw_val / scale
            perf = f"{id_name}={val};;;;"
            summary = f"{val} {unit}"
            print(f"{summary} | {perf}")

        else:
            print(f"2 {display_name} - ERROR: Could not read register {addr}")


if __name__ == "__main__":
    main()

