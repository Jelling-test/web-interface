import paho.mqtt.client as mqtt
import time
import logging
import sys

# Konfigurer logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# MQTT konfiguration
MQTT_BROKER = "192.168.9.61"
MQTT_PORT = 1890
MQTT_USER = "homeassistant"
MQTT_PASSWORD = "password123"
MQTT_KEEPALIVE = 60

# Callback når der forbindes til MQTT broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Forbundet til MQTT broker")
        # Subscribe til et test-emne
        client.subscribe("test/topic")
        logging.info("Subscribed til test/topic")
        
        # Send en test-besked
        client.publish("test/topic", "Hello from MQTT test")
        logging.info("Sendt test-besked")
    else:
        logging.error(f"Forbindelse fejlede med kode {rc}")
        error_messages = {
            1: "Forkert protokolversion",
            2: "Ugyldigt klient-ID",
            3: "Server utilgængelig",
            4: "Forkert brugernavn eller adgangskode",
            5: "Ikke autoriseret"
        }
        if rc in error_messages:
            logging.error(f"Fejldetaljer: {error_messages[rc]}")

# Callback når der modtages en MQTT besked
def on_message(client, userdata, msg):
    logging.info(f"Modtaget besked på emne: {msg.topic}, payload: {msg.payload.decode()}")

# Callback når forbindelsen afbrydes
def on_disconnect(client, userdata, rc):
    if rc == 0:
        logging.info("Normalt afbrudt fra MQTT broker")
    else:
        logging.error(f"Uventet afbrudt fra MQTT broker med kode {rc}")

def main():
    # Opret MQTT klient
    client = mqtt.Client()
    
    # Sæt callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Sæt brugeroplysninger
    logging.info(f"Sætter MQTT credentials: Bruger='{MQTT_USER}', Password='***'")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    try:
        # Forbind til broker
        logging.info(f"Forbinder til MQTT broker på {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        # Start MQTT loop
        client.loop_start()
        
        # Kør i 10 sekunder
        for i in range(10):
            logging.info(f"Test kører... {i+1}/10")
            time.sleep(1)
            
        # Afbryd forbindelsen
        client.disconnect()
        client.loop_stop()
        
    except Exception as e:
        logging.error(f"Fejl: {e}")

if __name__ == "__main__":
    main()
