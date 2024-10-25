import os
import subprocess
import time
import glob

INTERFACE = "wlan1"
HANDSHAKE_DIR = "/home/pi/handshakes"
SCAN_TIME = 60  # Zeit für Netzwerkscan in Sekunden
HANDSHAKE_WAIT_TIME = 60  # Zeit für Handshake-Erfassung pro Netzwerk

def setup():
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)

def scan_networks():
    print("[*] Starte Netzwerkscan mit tcpdump...")
    scan_process = subprocess.Popen(
        ["sudo", "tcpdump", "-i", INTERFACE, "-w", HANDSHAKE_DIR + "/scan.pcap"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(SCAN_TIME)
    scan_process.terminate()
    return HANDSHAKE_DIR + "/scan.pcap"

def parse_networks(scan_file):
    # Alternative Methode, um Netzwerke in der pcap-Datei zu finden.
    print(f"[*] Netzwerkscan abgeschlossen, Ergebnisse in {scan_file}")
    # Hinweis: Die spezifische Netzwerk- und Handshake-Erkennung entfällt hier
    return [(None, None)]  # Eintrag für die Erfassung eines generellen Handshakes

def capture_handshake(bssid, channel):
    print(f"[*] Erfasse Handshake...")
    tcpdump_cmd = [
        "sudo", "tcpdump", "-i", INTERFACE, "-w",
        f"{HANDSHAKE_DIR}/handshake.pcap"
    ]
    tcpdump_process = subprocess.Popen(tcpdump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(HANDSHAKE_WAIT_TIME)
    tcpdump_process.terminate()

def convert_and_cleanup():
    print("[*] Konvertiere und bereinige Dateien...")
    pcap_files = glob.glob(f"{HANDSHAKE_DIR}/*.pcap")
    if not pcap_files:
        print("[!] Keine .pcap-Dateien gefunden.")
        return
    hccapx_file = os.path.join(HANDSHAKE_DIR, "handshake.hccapx")
    conversion_cmd = ["hcxpcapngtool", "-o", hccapx_file] + pcap_files
    subprocess.call(conversion_cmd)
    print(f"[*] Handshake-Datei erstellt: {hccapx_file}")
    # Lösche alle .pcap-Dateien nach der Konvertierung
    for pcap_file in pcap_files:
        os.remove(pcap_file)
    print("[*] Alle .pcap-Dateien wurden gelöscht.")

def main():
    setup()
    scan_file = scan_networks()
    networks = parse_networks(scan_file)
    for bssid, channel in networks:
        capture_handshake(bssid, channel)
    convert_and_cleanup()

if __name__ == "__main__":
    main()
