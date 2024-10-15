from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import json

app = Flask(__name__)

# Define the fields that should be extracted
FIELDS_TO_EXTRACT = [
    "Country Name", "Country Code", "State", 
    "District", "City", "Postal Code", 
    "Latitude", "Longitude"
]

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        return request.remote_addr

@app.route('/myip', methods=['GET'])
def get_ip_info():
    ip_address = request.args.get('address') or get_client_ip()
    url = f"https://scamalytics.com/ip/{ip_address}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the IP address
        ip_div = soup.find('h1')
        if ip_div and 'Fraud Risk' in ip_div.text:
            ip_info = ip_div.text.split()[0]
        else:
            ip_info = "Unknown IP"

        # Extract the Fraud Score
        score_div = soup.find('div', class_='score')
        if score_div:
            fraud_score = score_div.text.replace('Fraud Score: ', '').strip()
        else:
            fraud_score = "No score available"

        # Extract additional data from panel_body
        data_div = soup.find('div', class_='panel_body')
        if data_div:
            data_text = data_div.get_text(separator=' ', strip=True)
        else:
            data_text = "No additional data available"

        # Extract the geographical and other details (filtered by FIELDS_TO_EXTRACT)
        details = {}
        table_rows = soup.find_all('tr')
        for row in table_rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                field_name = th.get_text(strip=True)
                if field_name in FIELDS_TO_EXTRACT:  # Only extract specified fields
                    details[field_name] = td.get_text(strip=True)

        # Create the response data
        response_data = {
            "ip address": ip_info,
            "Fraud Score": fraud_score,
            "Geographical Details": details,
            "data": data_text
        }

        # Use json.dumps to pretty-print the response
        return app.response_class(
            response=json.dumps(response_data, indent=4),  # Pretty-print with indent
            mimetype='application/json'
        )

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
