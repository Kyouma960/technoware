from flask import Flask, request, jsonify
import json
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
@app.route('/config.json')
def get_config():
    with open('data/config.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/send', methods=['POST'])
def reserve_table():
    data = request.json
    print("Received:", data)
    with open('data/main.json', 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({'message': f"Table {data['id']} received!"})

if __name__ == '__main__':
    app.run(debug=True)