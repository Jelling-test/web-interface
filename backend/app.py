from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import time
import threading
import re
from decimal import Decimal
from datetime import datetime
from config import MQTT_CONFIG, PORT, DEBUG
from db import test_connection, get_all_meters, get_meter_info, get_meter_readings, get_daily_readings, update_meter_name, delete_meter, get_unnamed_meters, check_meter_number_exists, update_meter_info

# Tilpasset JSON encoder der kan håndtere Decimal og datetime typer
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Opret Flask app
app = Flask(__name__)
CORS(app)
# Brug vores tilpassede JSON encoder
app.json_encoder = CustomJSONEncoder
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

# MQTT klient
mqtt_client = None
connected_to_mqtt = False

# Callback når forbindelsen til MQTT er etableret
def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    global connected_to_mqtt
    # I MQTTv311 er rc en integer
    if rc == 0:
        connected_to_mqtt = True
        print("Forbundet til MQTT broker")
        # Abonner på relevante emner
        client.subscribe("maaler/+/status")
        client.subscribe("maaler/+/data")
        # Abonner på Power-relaterede emner
        client.subscribe("stat/+/Power")
        print("Abonneret på MQTT-emner: maaler/+/status, maaler/+/data, stat/+/Power")
    else:
        connected_to_mqtt = False
        print(f"Fejl ved forbindelse til MQTT broker. Returkode: {rc}")
        error_messages = {
            1: "Forkert protokolversion",
            2: "Ugyldigt klient-ID",
            3: "Server utilgængelig",
            4: "Forkert brugernavn eller adgangskode",
            5: "Ikke autoriseret"
        }
        if rc in error_messages:
            print(f"Fejldetaljer: {error_messages[rc]}")
        print(f"Forbindelsesparametre: Host={MQTT_CONFIG['host']}, Port={MQTT_CONFIG['port']}, User={MQTT_CONFIG['user']}")

# Callback når en besked modtages fra MQTT
def on_mqtt_message(client, userdata, message, properties=None):
    print(f"Modtaget besked på emne: {message.topic}, payload: {message.payload.decode()}")
    try:
        topic = message.topic
        payload_str = message.payload.decode()
        
        # Håndter Power-kommandoer særskilt
        if 'Power' in topic:
            print(f"Power-kommando modtaget: {topic} - {payload_str}")
            
            # Emnet kan være i formatet: stat/obkXXXXXXXXXXXX/Power
            parts = topic.split('/')
            if len(parts) >= 2:
                mac_part = parts[1]
                if mac_part.startswith('obk'):
                    mac_no_colon = mac_part.replace('obk', '')
                    
                    # Indsæt kolon i MAC-adressen for at matche formatet i vores app
                    mac = ':'.join([mac_no_colon[i:i+2] for i in range(0, len(mac_no_colon), 2)])
                    
                    # Bestem status baseret på payload
                    status = "Tændt" if payload_str == "ON" else "Slukket"
                    
                    # Send status-opdatering til frontend
                    print(f"Sender power_status_update til frontend: {mac} - {status}")
                    socketio.emit('power_status_update', {
                        'mac': mac,
                        'status': status,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"Status for {mac} opdateret til {status}")
                    return  # Afslut funktionen her, da vi har håndteret Power-kommandoen
        
        # Forsøg at parse payload som JSON
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            # Hvis payload ikke er JSON, brug raw string
            payload = payload_str
        
        # Videreformidl besked til forbundne webklienter via SocketIO
        socketio.emit('mqtt_message', {
            'topic': topic,
            'payload': payload
        })
        
        print(f"Modtaget MQTT besked: {topic} - {payload}")
    except Exception as e:
        print(f"Fejl ved håndtering af MQTT-besked: {e}")

# Callback når forbindelsen til MQTT afbrydes
def on_mqtt_disconnect(client, userdata, rc, properties=None):
    global connected_to_mqtt
    connected_to_mqtt = False
    
    # I MQTTv311 er rc en integer
    if rc == 0:
        print("Normalt afbrudt fra MQTT broker")
    else:
        print(f"Afbrudt fra MQTT broker med kode {rc}")
        error_messages = {
            1: "Forkert protokolversion",
            2: "Ugyldigt klient-ID",
            3: "Server utilgængelig",
            4: "Forkert brugernavn eller adgangskode",
            5: "Ikke autoriseret"
        }
        if rc in error_messages:
            print(f"Fejldetaljer: {error_messages[rc]}")
        print("Uventet afbrydelse, forsøger at genforbinde...")
        try:
            client.reconnect()
        except Exception as e:
            print(f"Genopkoblingsfejl: {e}")

# Konfigurer og start MQTT-klienten
def setup_mqtt():
    global mqtt_client, connected_to_mqtt
    
    client_id = f"{MQTT_CONFIG['client_id']}_{int(time.time())}"
    
    # Opret MQTT klient med MQTTv311 protokol (mest kompatibel)
    mqtt_client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    
    # Sæt callbacks
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.on_disconnect = on_mqtt_disconnect
    
    # Tilføj detaljeret logging
    mqtt_client.enable_logger()
    
    # Sæt brugeroplysninger - brug direkte værdier for at sikre korrekt autentificering
    user = "homeassistant"
    password = "password123"
    print(f"Sætter MQTT credentials: Bruger='{user}', Password='{password[:2]}***'")
    mqtt_client.username_pw_set(user, password)
    
    # Forbind til broker med timeout og genopkoblingsforsøg
    try:
        print(f"Forsøger at forbinde til MQTT broker på {MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}")
        
        # Sæt automatisk genopkobling
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=MQTT_CONFIG.get('reconnect_delay_secs', 10))
        
        # Forbind med keepalive
        connect_result = mqtt_client.connect(
            MQTT_CONFIG['host'], 
            MQTT_CONFIG['port'], 
            keepalive=MQTT_CONFIG.get('keepalive', 60)
        )
        print(f"MQTT connect resultat: {connect_result}")
        
        # Start MQTT loop i baggrunden
        mqtt_client.loop_start()
        
        # Vent op til 5 sekunder på forbindelse
        retry_count = 0
        max_retries = MQTT_CONFIG.get('max_reconnect_attempts', 5)
        while not connected_to_mqtt and retry_count < max_retries:
            time.sleep(1)
            retry_count += 1
            print(f"Venter på MQTT forbindelse... forsøg {retry_count}/{max_retries}")
        
        if not connected_to_mqtt:
            print(f"Kunne ikke forbinde til MQTT broker efter {max_retries} forsøg")
            print("Fortsætter alligevel - vil forsøge at genforbinde senere")
        else:
            print("MQTT forbindelse etableret!")
            
    except Exception as e:
        print(f"Fejl ved MQTT-forbindelse: {e}")
        print("Fortsætter alligevel - vil forsøge at genforbinde senere")

# Start MQTT-klienten i en separat tråd
def start_mqtt_thread():
    print("Starter MQTT-forbindelse i separat tråd...")
    mqtt_thread = threading.Thread(target=setup_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    print("MQTT-tråd startet")

# Funktion til at genforbinde MQTT hvis nødvendigt
def ensure_mqtt_connection():
    global mqtt_client, connected_to_mqtt
    
    if not mqtt_client:
        print("MQTT-klient er ikke initialiseret. Starter ny...")
        setup_mqtt()
        time.sleep(2)  # Vent på forbindelse
        
    if not connected_to_mqtt and mqtt_client:
        print("MQTT-klient er ikke forbundet. Forsøger at genforbinde...")
        try:
            mqtt_client.reconnect()
            time.sleep(2)  # Vent på forbindelse
            
            if connected_to_mqtt:
                print("MQTT-genforbindelse lykkedes!")
                return True
            else:
                print("MQTT-genforbindelse fejlede!")
                return False
        except Exception as e:
            print(f"Fejl ved MQTT-genforbindelse: {e}")
            return False
    
    return connected_to_mqtt

# API-endpoint: Sundhedstjek
@app.route('/api/health', methods=['GET'])
def health_check():
    db_connected = test_connection()
    return jsonify({
        'status': 'ok',
        'db_connected': db_connected,
        'mqtt_connected': connected_to_mqtt
    })

# API-endpoint: Hent alle målere
@app.route('/api/meters', methods=['GET'])
def get_meters():
    meters = get_all_meters()
    return jsonify(meters)

# API-endpoint: Hent målerinfo
@app.route('/api/meters/<mac>')
def get_meter(mac):
    try:
        meter = get_meter_info(mac)
        if meter and 'error' not in meter:
            return jsonify(meter)
        elif meter and 'error' in meter:
            return jsonify(meter), 500
        return jsonify({'error': 'Måler ikke fundet', 'mac': mac}), 404
    except Exception as e:
        print(f"Fejl i get_meter: {str(e)}")
        return jsonify({'error': str(e), 'mac': mac}), 500

# API-endpoint: Hent måleraflæsninger
@app.route('/api/meters/<mac>/readings', methods=['GET'])
def get_readings(mac):
    limit = request.args.get('limit', default=200, type=int)
    readings = get_meter_readings(mac, limit)
    return jsonify(readings)

# API-endpoint: Hent daglige måleraflæsninger
@app.route('/api/meters/<mac>/daily', methods=['GET'])
def get_daily(mac):
    days = request.args.get('days', default=30, type=int)
    readings = get_daily_readings(mac, days)
    return jsonify(readings)

# API-endpoint: Opdater måler-navn
@app.route('/api/meter/update', methods=['POST'])
def update_meter_name():
    try:
        # Hent data fra request
        data = request.json
        if not data or 'mac' not in data or 'name' not in data or 'number' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Manglende påkrævede felter: mac, name, number'
            }), 400
        
        # Valider nummer-formatet (3 cifre)
        if not re.match(r'^\d{3}$', data['number']):
            return jsonify({
                'status': 'error',
                'message': 'Nummer skal være 3 cifre (000-999)'
            }), 400
            
        # Konverter nummer til integer for at sikre korrekt format
        number_int = int(data['number'])
        
        # Tjek om nummeret allerede er i brug af en anden måler
        existing_meter = check_meter_number_exists(number_int)
        if existing_meter and existing_meter['mac'] != data['mac']:
            return jsonify({
                'status': 'error',
                'message': f'Måler-nummer {data["number"]} er allerede i brug af {existing_meter["name"]}'
            }), 409
        
        # Opdater eller opret måler i databasen
        success = update_meter_info(data['mac'], data['name'], number_int)
        
        if success:
            # Log til konsollen
            print(f"Måler opdateret: MAC={data['mac']}, Navn={data['name']}, Nummer={data['number']}")
            
            # Send besked via SocketIO om at måler er opdateret
            socketio.emit('meter_updated', {
                'mac': data['mac'],
                'name': data['name'],
                'number': data['number']
            })
            
            return jsonify({
                'status': 'success',
                'message': 'Måler opdateret',
                'meter': {
                    'mac': data['mac'],
                    'name': data['name'],
                    'number': data['number']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Kunne ikke opdatere måler i databasen'
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        print(f"Fejl ved opdatering af måler: {error_msg}")
        return jsonify({
            'status': 'error',
            'message': 'Der opstod en fejl ved opdatering af måler',
            'error': error_msg
        }), 500

# API-endpoint: Opdater målernavn
@app.route('/api/meters/<mac>/name', methods=['POST'])
def update_name(mac):
    data = request.json
    if not data or 'name' not in data or 'number' not in data:
        return jsonify({'error': 'Manglende navn eller nummer'}), 400
    
    success = update_meter_name(mac, data['name'], data['number'])
    if success:
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Kunne ikke opdatere målerinfo'}), 500

# API-endpoint: Slet måler
@app.route('/api/meters/<mac>', methods=['DELETE'])
def delete_meter_endpoint(mac):
    data = request.json
    if not data or 'code' not in data or data['code'] != '2012':
        return jsonify({'error': 'Ugyldig sikkerhedskode'}), 403
    
    success = delete_meter(mac)
    if success:
        return jsonify({'status': 'ok'})
    return jsonify({'error': 'Kunne ikke slette måler'}), 500

# API-endpoint: Tænd måler
@app.route('/api/meters/<mac>/on', methods=['POST'])
def turn_on_meter(mac):
    # Sikrer MQTT-forbindelse
    if not ensure_mqtt_connection():
        return jsonify({'error': 'Ikke forbundet til MQTT efter genforbindelsesforsøg'}), 503
    
    # Fjern kolon fra MAC-adressen for at matche MQTT-emneformatet
    mac_no_colon = mac.replace(':', '')
    
    # Send MQTT-besked for at tænde måleren med korrekt format
    topic = f"cmnd/obk{mac_no_colon}/Power"
    payload = "ON"
    
    print(f"Sender MQTT-kommando: {topic} med payload: {payload}")
    
    try:
        result = mqtt_client.publish(topic, payload)
        
        # Tjek om beskeden blev sendt korrekt
        if result.rc == 0:
            print(f"MQTT-kommando sendt: {topic} = {payload}")
            return jsonify({'status': 'ok', 'message': 'Kommando sendt til måleren', 'topic': topic, 'payload': payload})
        else:
            print(f"Fejl ved afsendelse af MQTT-kommando. Fejlkode: {result.rc}")
            return jsonify({'error': f'Kunne ikke sende kommando. Fejlkode: {result.rc}'}), 500
    except Exception as e:
        print(f"Exception ved afsendelse af MQTT-kommando: {e}")
        return jsonify({'error': f'Fejl ved afsendelse af kommando: {str(e)}'}), 500

# API-endpoint: Sluk måler
@app.route('/api/meters/<mac>/off', methods=['POST'])
def turn_off_meter(mac):
    # Sikrer MQTT-forbindelse
    if not ensure_mqtt_connection():
        return jsonify({'error': 'Ikke forbundet til MQTT efter genforbindelsesforsøg'}), 503
    
    # Fjern kolon fra MAC-adressen for at matche MQTT-emneformatet
    mac_no_colon = mac.replace(':', '')
    
    # Send MQTT-besked for at slukke måleren med korrekt format
    topic = f"cmnd/obk{mac_no_colon}/Power"
    payload = "OFF"
    
    print(f"Sender MQTT-kommando: {topic} med payload: {payload}")
    
    try:
        result = mqtt_client.publish(topic, payload)
        
        # Tjek om beskeden blev sendt korrekt
        if result.rc == 0:
            print(f"MQTT-kommando sendt: {topic} = {payload}")
            return jsonify({'status': 'ok', 'message': 'Kommando sendt til måleren', 'topic': topic, 'payload': payload})
        else:
            print(f"Fejl ved afsendelse af MQTT-kommando. Fejlkode: {result.rc}")
            return jsonify({'error': f'Kunne ikke sende kommando. Fejlkode: {result.rc}'}), 500
    except Exception as e:
        print(f"Exception ved afsendelse af MQTT-kommando: {e}")
        return jsonify({'error': f'Fejl ved afsendelse af kommando: {str(e)}'}), 500

# API-endpoint: Søg efter nye målere
@app.route('/api/scan', methods=['POST'])
def scan_for_meters():
    try:
        # Hent ubenævnte målere fra databasen
        unnamed_meters = get_unnamed_meters()
        
        # Log til debugging
        print(f"Fandt {len(unnamed_meters)} ubenævnte målere i databasen")
        
        # Konverter tidspunkter til strenge for JSON-serialisering
        for meter in unnamed_meters:
            if 'sidst_set' in meter and meter['sidst_set']:
                meter['sidst_set'] = meter['sidst_set'].isoformat() if hasattr(meter['sidst_set'], 'isoformat') else str(meter['sidst_set'])
        
        # Hent også alle målere markeret som "Unavngivet" fra get_all_meters
        all_meters = get_all_meters()
        for meter in all_meters:
            if meter.get('name') == 'Unavngivet':
                # Tjek om denne måler allerede er i unnamed_meters
                if not any(m['mac'] == meter['mac'] for m in unnamed_meters):
                    # Tilføj manglende felter hvis nødvendigt
                    if 'antal_dage_med_data' not in meter:
                        meter['antal_dage_med_data'] = 0
                    if 'number' not in meter:
                        meter['number'] = None
                    # Sæt name til None for at følge formatet i unnamed_meters
                    meter['name'] = None
                    unnamed_meters.append(meter)
        
        # Send opdatering til alle tilkoblede klienter via SocketIO
        if len(unnamed_meters) > 0:
            socketio.emit('new_unnamed_meters', {
                'count': len(unnamed_meters),
                'meters': unnamed_meters
            })
        
        return jsonify({
            'status': 'success', 
            'message': 'Database-scanning gennemført', 
            'count': len(unnamed_meters),
            'meters': unnamed_meters
        })
    except Exception as e:
        error_msg = str(e)
        print(f"Fejl ved scanning af database: {error_msg}")
        return jsonify({
            'status': 'error',
            'message': 'Kunne ikke gennemføre søgning efter ubenævnte målere',
            'error': error_msg
        }), 500

# API-endpoint: Test MQTT-forbindelse
@app.route('/api/mqtt/test', methods=['GET'])
def test_mqtt_connection():
    global mqtt_client, connected_to_mqtt
    
    # Hvis MQTT-klienten ikke er oprettet eller ikke er forbundet, forsøg at genforbinde
    if not mqtt_client or not connected_to_mqtt:
        try:
            # Hvis klienten allerede eksisterer, stop den først
            if mqtt_client:
                mqtt_client.loop_stop()
            
            # Forsøg at oprette ny forbindelse
            print("Forsøger at genforbinde til MQTT broker...")
            setup_mqtt()
            
            # Hvis stadig ikke forbundet, returner fejl
            if not connected_to_mqtt:
                return jsonify({
                    'status': 'error',
                    'connected': False,
                    'broker': f"{MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}",
                    'message': 'Ikke forbundet til MQTT broker efter genforbindelsesforsøg',
                    'debug_info': {
                        'host': MQTT_CONFIG['host'],
                        'port': MQTT_CONFIG['port'],
                        'user': bool(MQTT_CONFIG.get('user')),  # Viser kun om bruger er angivet, ikke selve brugeren
                        'password': bool(MQTT_CONFIG.get('password'))  # Viser kun om password er angivet, ikke selve passwordet
                    }
                }), 503
        except Exception as e:
            return jsonify({
                'status': 'error',
                'connected': False,
                'broker': f"{MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}",
                'message': f'Fejl ved genforbindelse til MQTT broker: {str(e)}',
                'error_type': type(e).__name__
            }), 503
    
    try:
        # Send en test-besked til et test-topic
        test_topic = "maaler/test/connection"
        test_payload = f"Test forbindelse fra web interface: {datetime.now().isoformat()}"
        result = mqtt_client.publish(test_topic, test_payload)
        
        # Tjek om beskeden blev sendt korrekt
        if result.rc == 0:
            return jsonify({
                'status': 'success',
                'connected': True,
                'broker': f"{MQTT_CONFIG['host']}:{MQTT_CONFIG['port']}",
                'message': 'MQTT-forbindelse OK, test-besked sendt',
                'test_topic': test_topic,
                'test_payload': test_payload
            })
        else:
            return jsonify({
                'status': 'error',
                'connected': True,
                'message': f'Kunne ikke sende test-besked. Fejlkode: {result.rc}',
                'result_code': result.rc
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': connected_to_mqtt,
            'message': f'Fejl ved test af MQTT-forbindelse: {str(e)}',
            'error_type': type(e).__name__
        }), 500

# API-endpoint: Test MQTT-forbindelse og send en besked
@app.route('/api/test_mqtt', methods=['GET'])
def test_mqtt():
    if not mqtt_client or not connected_to_mqtt:
        return jsonify({
            'status': 'error',
            'message': 'MQTT-klient er ikke forbundet',
            'connected': connected_to_mqtt
        }), 500
    
    try:
        # Send en test-besked
        test_topic = "test/topic"
        test_message = f"Test besked fra web interface: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        result = mqtt_client.publish(test_topic, test_message)
        result.wait_for_publish()
        
        return jsonify({
            'status': 'success',
            'message': 'MQTT-besked sendt',
            'topic': test_topic,
            'payload': test_message,
            'connected': connected_to_mqtt,
            'publish_result': result.rc
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fejl ved sending af MQTT-besked: {str(e)}',
            'connected': connected_to_mqtt
        }), 500

# API-endpoint: Test tænd/sluk af en måler via MQTT
@app.route('/api/test_meter_control/<mac>/<action>', methods=['GET'])
def test_meter_control(mac, action):
    if not mqtt_client or not connected_to_mqtt:
        return jsonify({
            'status': 'error',
            'message': 'MQTT-klient er ikke forbundet',
            'connected': connected_to_mqtt
        }), 500
    
    try:
        # Validér action
        if action not in ['on', 'off']:
            return jsonify({
                'status': 'error',
                'message': 'Ugyldig handling. Brug "on" eller "off"'
            }), 400
        
        # Formatér MAC-adresse
        mac = mac.lower()
        if not re.match(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac):
            return jsonify({
                'status': 'error',
                'message': 'Ugyldig MAC-adresse format. Brug format: xx:xx:xx:xx:xx:xx'
            }), 400
        
        # Fjern kolon fra MAC-adressen for at matche MQTT-emneformatet
        mac_no_colon = mac.replace(':', '')
        
        # Opret MQTT-emne og payload
        topic = f"cmnd/obk{mac_no_colon}/Power"
        payload = "ON" if action == 'on' else "OFF"
        
        # Send kommando
        result = mqtt_client.publish(topic, payload)
        result.wait_for_publish()
        
        return jsonify({
            'status': 'success',
            'message': f'MQTT-kommando sendt: {action}',
            'topic': topic,
            'payload': payload,
            'mac': mac,
            'connected': connected_to_mqtt,
            'publish_result': result.rc
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fejl ved sending af MQTT-kommando: {str(e)}',
            'connected': connected_to_mqtt
        }), 500

# SocketIO event: Klient forbundet
@socketio.on('connect')
def handle_connect():
    print(f"Ny webclient forbundet: {request.sid}")

# SocketIO event: Klient afbrudt
@socketio.on('disconnect')
def handle_disconnect():
    print(f"Webclient afbrudt: {request.sid}")

if __name__ == '__main__':
    # Test database forbindelse
    if test_connection():
        print("Forbindelse til database oprettet")
    else:
        print("ADVARSEL: Kunne ikke forbinde til database")
    
    # Start MQTT-klienten
    start_mqtt_thread()
    
    # Start Flask-SocketIO serveren
    socketio.run(app, host='0.0.0.0', port=PORT, debug=DEBUG)
