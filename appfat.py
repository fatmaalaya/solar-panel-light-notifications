from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return "Bienvenue à l'application de notification Flask!"

# Configuration Whatabot
WHATABOT_API_KEY = os.getenv('WHATABOT_API_KEY')
WHATABOT_API_URL = 'https://api.whatabot.io/Whatsapp/RequestSendMessage'

# Configuration Adafruit IO
AIO_USERNAME = os.getenv('AIO_USERNAME')
AIO_KEY = os.getenv('ADAFRUIT_IO_KEY')

# URL du flux pour la lumière en lumens
AIO_LUMEN_FEED_URL = f'https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/lightlumen/data'

# URL du flux pour l'état de maintenance
AIO_MAINTENANCE_FEED_URL = f'https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/maintenance/data'

def get_maintenance_state():
    """
    Récupère l'état de maintenance à partir du flux Adafruit IO.

    Returns:
        bool: True si l'état de maintenance est activé ('1'), False sinon.
    """
    headers = {'X-AIO-Key': AIO_KEY}
    try:
        response = requests.get(AIO_MAINTENANCE_FEED_URL, headers=headers)
        response.raise_for_status()  # Gérer les erreurs HTTP
        data = response.json()
        if data:
            latest_value = data[0].get('value')
            return latest_value == '1'
    except requests.RequestException as e:
        app.logger.error(f"Erreur lors de la récupération de l'état de maintenance : {e}")
    return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Gère les requêtes POST du webhook, vérifie la diminution de la lumière et envoie des notifications WhatsApp.

    Returns:
        Response: JSON response indiquant le succès ou l'échec.
    """
    data = request.json

    if not data or 'value' not in data:
        return jsonify({'status': 'failure', 'message': 'Invalid data'}), 400

    try:
        lumen_value = float(data['value'])
    except ValueError:
        return jsonify({'status': 'failure', 'message': 'Invalid lumen value'}), 400

    if lumen_value < 10:
        maintenance_state = get_maintenance_state()
        cause = determine_cause(maintenance_state)
        send_whatsapp_notification(lumen_value, cause)

    return jsonify({'status': 'success', 'data': data}), 200

def determine_cause(maintenance_state):
    """
    Détermine la cause de la diminution de la lumière en fonction de l'état de maintenance.

    Args:
        maintenance_state (bool): L'état de maintenance.

    Returns:
        str: La cause probable de la diminution de la lumière.
    """
    if maintenance_state:
        return "ombrage ou accumulation de poussière"
    return "problème de maintenance"

def send_whatsapp_notification(lumen_value, cause):
    """
    Envoie une notification WhatsApp avec la valeur de la lumière et la cause probable.

    Args:
        lumen_value (float): La valeur de la lumière en lumens.
        cause (str): La cause probable de la diminution de la lumière.
    """
    message = f"La luminosité a chuté à {lumen_value} lumen. Cause probable : {cause}. Veuillez vérifier les panneaux solaires."
    payload = {
        'api_key': WHATABOT_API_KEY,
        'phone': '28375219',  # Remplacez par le numéro de téléphone réel
        'message': message
    }
    try:
        response = requests.post(WHATABOT_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        app.logger.error(f"Erreur lors de l'envoi de la notification WhatsApp : {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)