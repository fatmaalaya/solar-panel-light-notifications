from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)


@app.route('/')
def index():
    return "Bienvenue à l'application de notification Flask!"


# Whatabot configuration
WHATABOT_API_KEY = os.getenv('9ab75662-c0e3-4426-bb6e')
WHATABOT_API_URL = 'https://app.whatabot.io/api/sendMessage'

# Adafruit IO configuration
AIO_USERNAME = os.getenv('fatma72001')
AIO_KEY = os.getenv('ADAFRUIT_IO_KEY')
AIO_FEED_URL = f'https://io.adafruit.com/api/v2/fatma72001/feeds/lightlumen/data'

def get_maintenance_state():
    headers = {'X-AIO-Key': AIO_KEY}
    response = requests.get(AIO_FEED_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['value'] == '1'
    return False

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        lumen_value = data.get('value')
        if float(lumen_value) < 10:
            maintenance_state = get_maintenance_state()
            cause = "ombrage ou accumulation de poussière" if maintenance_state else "problème de maintenance"
            send_whatsapp_notification(lumen_value, cause)
        return jsonify({'status': 'success', 'data': data}), 200
    return jsonify({'status': 'failure'}), 400

def send_whatsapp_notification(lumen_value, cause):
    message = f"La luminosité a chuté à {lumen_value} lumen. Cause probable : {cause}. Veuillez vérifier les panneaux solaires."
    payload = {
        'api_key': WHATABOT_API_KEY,
        'phone': '28375219',
        'message': message
    }
    response = requests.post(WHATABOT_API_URL, json=payload)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)
