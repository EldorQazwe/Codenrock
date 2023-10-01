# /run.py
from app import app
from flask import jsonify
from flask import request

@app.route('/webhook', methods=['POST'])
def webhook():

    json_data = request.get_json()
    print("json_data", json_data)
    
    return jsonify({'status': 'ok'})
if __name__ == "__main__":
    app.run(debug=True)
