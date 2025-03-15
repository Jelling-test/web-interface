import paho.mqtt.client as mqtt
import time
import sys
import json

# MQTT-konfiguration
MQTT_HOST = "192.168.9.61"
MQTT_PORT = 1890
MQTT_USER = "homeassistant"
MQTT_PASSWORD = "password123"

# Callback funktioner
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[OK] Forbundet til MQTT-broker på {MQTT_HOST}:{MQTT_PORT}")
        print(f"   Resultat kode: {rc}")
        
        # Abonnere på relevante emner
        client.subscribe("maaler/+/status")
        client.subscribe("maaler/+/data")
        client.subscribe("stat/+/Power")
        print("[OK] Abonneret på emner: maaler/+/status, maaler/+/data, stat/+/Power")
    else:
        print(f"[FEJL] Kunne ikke forbinde til MQTT-broker. Resultat kode: {rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[FEJL] Uventet afbrydelse af MQTT-forbindelse med kode {rc}")
    else:
        print("[INFO] MQTT-forbindelse afbrudt normalt")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"[BESKED] Modtog besked på emne '{topic}'")
        try:
            # Forsøg at tolke som JSON
            payload_json = json.loads(payload)
            print(f"   Payload (JSON): {json.dumps(payload_json, indent=2)}")
        except:
            # Hvis ikke JSON, vis som tekst
            print(f"   Payload (Rå): {payload}")
    except Exception as e:
        print(f"[FEJL] Fejl ved håndtering af besked: {e}")

def on_publish(client, userdata, mid):
    print(f"[OK] Besked publiceret med ID {mid}")

# Opret MQTT-klient
client_id = f"mqtt_test_client_{int(time.time())}"
client = mqtt.Client(client_id=client_id)

# Sæt callback funktioner
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_publish = on_publish

# Sæt brugeroplysninger
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# Forsøg at forbinde
print(f"[INFO] Forsøger at forbinde til MQTT-broker på {MQTT_HOST}:{MQTT_PORT}...")
try:
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    
    # Start forbindelsen i en baggrundstråd
    client.loop_start()
    
    # Vent på forbindelse
    time.sleep(2)
    
    # Test af kommando - prøv at sende en test-besked med korrekt format
    test_mac = "test_mac"
    print(f"[INFO] Forsøger at sende en test-besked til emnet 'cmnd/obk{test_mac}/Power'...")
    result = client.publish(f"cmnd/obk{test_mac}/Power", "ON", qos=1)
    time.sleep(1)
    
    # Lyt efter beskeder i 10 sekunder
    print("[INFO] Lytter efter MQTT-beskeder i 10 sekunder...")
    for i in range(10):
        print(f"[VENT] Venter... {10-i} sekunder tilbage")
        time.sleep(1)
    
    # Test af tænd/sluk-kommandoer med korrekt præfiks
    print("\n--- Test af tænd/sluk-kommandoer ---")
    test_meters = ["0884DD9F", "test_meter"]  # Tilføj rigtige MAC-adresser her
    
    for mac in test_meters:
        mac_no_colon = mac.replace(':', '')
        
        # Test tænd med OBK præfiks
        print(f"[INFO] Forsøger at tænde måler med MAC: {mac}")
        result = client.publish(f"cmnd/obk{mac_no_colon}/Power", "ON", qos=1)
        time.sleep(1)
        
        # Test sluk med OBK præfiks
        print(f"[INFO] Forsøger at slukke måler med MAC: {mac}")
        result = client.publish(f"cmnd/obk{mac_no_colon}/Power", "OFF", qos=1)
        time.sleep(1)
    
    # Stop MQTT-klienten
    client.loop_stop()
    client.disconnect()
    
except Exception as e:
    print(f"[FEJL] Fejl under MQTT-test: {e}")
    sys.exit(1)

print("[OK] MQTT-test afsluttet.")
