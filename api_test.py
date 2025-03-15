import requests
import time
import sys

# Backend-URL (ændre denne, hvis din backend kører på en anden adresse/port)
BASE_URL = "http://localhost:5000/api"  # Standard-URL for Flask-appen

# Test system-status
def test_system_status():
    url = f"{BASE_URL}/health"
    print("Tester system-status...")
    try:
        response = requests.get(url)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            status = response.json()
            print(f"System status: {status}")
            print(f"MQTT forbundet: {status.get('mqtt_connected', 'Ukendt')}")
            print(f"Database forbundet: {status.get('db_connected', 'Ukendt')}")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Fejl: {e}")
        return False

# Hent alle målere
def test_get_all_meters():
    url = f"{BASE_URL}/meters"
    print("\nHenter alle målere...")
    try:
        response = requests.get(url)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            meters = response.json()
            print(f"Antal målere: {len(meters)}")
            for i, meter in enumerate(meters[:5]):  # Vis kun de første 5 af pladshensyn
                print(f"Måler {i+1}: MAC={meter.get('mac')}, Navn={meter.get('name')}, Status={meter.get('status')}")
            if len(meters) > 5:
                print(f"...og {len(meters)-5} flere målere")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Fejl: {e}")
        return False, None

# Test måler-informationer
def test_get_meter(mac):
    url = f"{BASE_URL}/meters/{mac}"
    print(f"\nHenter information om måler {mac}...")
    try:
        response = requests.get(url)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            meter = response.json()
            print(f"Måler data:")
            print(f"  MAC: {meter.get('mac')}")
            print(f"  Navn: {meter.get('name')}")
            print(f"  Status: {meter.get('status')}")
            print(f"  Power: {meter.get('power')}")
            print(f"  Sidst set: {meter.get('lastSeen')}")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Fejl: {e}")
        return False

# Test tænd-funktion
def test_turn_on(mac):
    url = f"{BASE_URL}/meters/{mac}/on"
    print(f"\nTester tænd-funktion for måler {mac}...")
    try:
        response = requests.post(url)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            print(f"Svar: {response.json()}")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Fejl: {e}")
        return False

# Test sluk-funktion
def test_turn_off(mac):
    url = f"{BASE_URL}/meters/{mac}/off"
    print(f"\nTester sluk-funktion for måler {mac}...")
    try:
        response = requests.post(url)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            print(f"Svar: {response.json()}")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Fejl: {e}")
        return False

# Test beskedhistorik
def test_check_history(mac):
    url = f"{BASE_URL}/meters/{mac}/readings"
    params = {"limit": 5}  # Begrænser til 5 læsninger
    print(f"\nHenter historik for måler {mac}...")
    try:
        response = requests.get(url, params=params)
        print(f"Status kode: {response.status_code}")
        if response.status_code == 200:
            readings = response.json()
            print(f"Antal aflæsninger: {len(readings)}")
            for i, reading in enumerate(readings):
                print(f"Aflæsning {i+1}: Tidspunkt={reading.get('timestamp')}, Værdi={reading.get('value')}")
        else:
            print(f"Fejl: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Fejl: {e}")
        return False

if __name__ == "__main__":
    # Brug standardværdien for URL (ikke interaktiv input)
    print(f"Bruger backend URL: {BASE_URL}")
    
    # Test system-status
    if not test_system_status():
        print("ADVARSEL: Kunne ikke få kontakt med backend-systemet. Kontroller URL'en og at backend kører.")
        sys.exit(1)
    
    # Hent alle målere
    success, meters = test_get_all_meters()
    
    # Vælg en standard MAC-adresse for test eller brug den første måler fra listen
    test_mac = "0884DD9F"  # Standard testmåler
    
    if success and meters and len(meters) > 0:
        test_mac = meters[0].get('mac')  # Brug den første måler fra listen
        print(f"\nBruger måler med MAC={test_mac} til test")
    
    # Test valgt måler
    test_get_meter(test_mac)
    
    # Test tænd
    if test_turn_on(test_mac):
        print("Venter 5 sekunder for at se effekten...")
        time.sleep(5)
        test_get_meter(test_mac)  # Tjek status efter tænd
    
    # Test sluk
    if test_turn_off(test_mac):
        print("Venter 5 sekunder for at se effekten...")
        time.sleep(5)
        test_get_meter(test_mac)  # Tjek status efter sluk
    
    # Test historik
    test_check_history(test_mac)
    
    print("\nTest afsluttet.")
