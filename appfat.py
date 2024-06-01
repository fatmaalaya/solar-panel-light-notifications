from flask import Flask, request
import requests
import paho.mqtt.client as mqtt
import os

app = Flask(__name__)

# MQTT configuration
MQTT_BROKER = 'io.adafruit.com'
MQTT_PORT = 1883
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_KEY = os.getenv('MQTT_KEY')

# WhatsApp API configuration
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL')
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN')
USER_PHONE_NUMBER = os.getenv('USER_PHONE_NUMBER')

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_KEY)

def send_whatsapp_message(message):
    payload = {
        'token': WHATSAPP_API_TOKEN,
        'to': USER_PHONE_NUMBER,
        'message': message
    }
    response = requests.post(WHATSAPP_API_URL, json=payload)
    if response.status_code == 200:
        print("Message WhatsApp envoyé avec succès.")
    else:
        print(f"Erreur lors de l'envoi du message WhatsApp: {response.status_code} - {response.text}")

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(f"{MQTT_USERNAME}/feeds/maintenance")

def on_message(client, userdata, msg):
    maintenance_state = msg.payload.decode()
    print(f"Received message '{maintenance_state}' on topic '{msg.topic}'")
    if msg.topic == f"{MQTT_USERNAME}/feeds/maintenance":
        if maintenance_state == 'on':
            send_whatsapp_message('Maintenance status updated: Maintenance has been performed recently.')
        else:
            send_whatsapp_message('Maintenance status updated: Maintenance has not been performed recently.')

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
except ValueError as e:
    print(f"Error connecting to MQTT Broker: {e}")

mqtt_client.loop_start()

@app.route('/webhook/luminosité', methods=['POST'])
def handle_luminosity():
    data = request.json
    luminosity = float(data['value'])
    if luminosity < 100:
        maintenance_state = get_last_maintenance_state()
        if maintenance_state == 'on':
            send_whatsapp_message('Luminosity is below 100 lumens. Cause: Shading or dust accumulation.')
        else:
            send_whatsapp_message('Luminosity is below 100 lumens. Cause: Maintenance problem.')
    return '', 200

def get_last_maintenance_state():
    # Simulating the retrieval of the latest maintenance state
    # In a real scenario, you would implement a proper way to retrieve the latest state
    mqtt_client.subscribe(f"{MQTT_USERNAME}/feeds/maintenance")
    return "on"  # Default value for testing purposes

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Utilisez le port défini par Render, ou 5000 par défaut
    app.run(host='0.0.0.0', port=port, debug=True)
