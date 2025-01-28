from flask import Flask, request, jsonify
import pdfplumber
import os
from dotenv import load_dotenv
from comdirect.ynab_comdirect_config import YNABComdirectConfig
from paypal.ynab_paypal_config import YNABPayPalConfig
from hanseatic.hanseatic_ynab_config import YNABHanseaticConfig
from csv_adapter.ynab_csv_config import YNABCSVConfig
import tempfile
import re
from datetime import datetime
# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger to attach...")
# debugpy.wait_for_client()


app = Flask(__name__)
if os.name == "nt":  # 'nt' is used for Windows
    env_path = "C:/Users/sebas/Desktop/free/.env"
else:
    env_path = "/config/.env"

load_dotenv(env_path)

API_SECRET = os.getenv('API_SECRET')

def validate_secret(request):
    secret = request.headers.get('X-API-Secret')
    return secret and secret == API_SECRET

@app.route('/import', methods=['POST'])
def import_data():
    if not validate_secret(request):
        return jsonify({'error': 'Unauthorized'}), 401

    import_type = request.args.get('type')
    what = request.args.get('what', '')
    config_path = '/config/ynab_comdirect_conf.json'

    try:
        if import_type == 'comdirect':
            if what == 'start':
                YNABComdirectConfig(config_path, start_only=True)
                return jsonify({'message': 'Comdirect login started'})
            elif what == 'validate_tan':
                YNABComdirectConfig(config_path, validate_only=True)
                return jsonify({'message': 'TAN validated and import completed'})
            else:
                return jsonify({'error': 'Invalid what parameter'}), 400
            
        elif import_type == 'paypal':
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)
                YNABPayPalConfig(config_path, csv=temp_file.name)
            os.unlink(temp_file.name)
            return jsonify({'message': 'PayPal import successful'})
        
        elif import_type == 'csv':
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)
                YNABCSVConfig(config_path, csv=temp_file.name)
            os.unlink(temp_file.name)
            return jsonify({'message': 'CSV import successful'})
        
        elif import_type == 'hanseatic':
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)
                YNABHanseaticConfig(config_path, temp_file.name)
            os.unlink(temp_file.name)
            return jsonify({'message': 'Hanseatic import successful'})
            
        else:
            return jsonify({'error': 'Invalid import type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)