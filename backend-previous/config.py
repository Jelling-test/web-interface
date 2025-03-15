import os
from dotenv import load_dotenv

# Indlæs miljøvariabler fra .env filen
load_dotenv()

# Database konfiguration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '192.168.1.254'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'eldata'),
    'password': os.getenv('DB_PASSWORD', '7200Grindsted!'),
    'database': os.getenv('DB_NAME', 'el_data'),
}

# MQTT konfiguration
MQTT_CONFIG = {
    'host': os.getenv('MQTT_HOST', '192.168.9.61'),
    'port': int(os.getenv('MQTT_PORT', 1890)),
    'user': os.getenv('MQTT_USER', 'homeassistant'),
    'password': os.getenv('MQTT_PASSWORD', 'password123'),
    'client_id': 'maaler_web_interface',
    'keepalive': 60,
    'reconnect_delay_secs': 10,
    'max_reconnect_attempts': 5
}

# Web server konfiguration
PORT = int(os.getenv('BACKEND_PORT', 5000))
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
