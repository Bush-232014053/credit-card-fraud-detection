from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

# Load Trained Model
model = joblib.load('model.pkl')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract features from AJAX Form Data
        features = [
            float(request.form['Transaction_Amount']),
            float(request.form['Time_Since_Last_Tx']),
            float(request.form['Distance_From_Last_Tx']),
            float(request.form['Distance_From_Home']),
            float(request.form['Daily_Limit_Used']),
            float(request.form['Card_Age_Days'])
        ]
        
        final_features = [np.array(features)]
        prediction = model.predict(final_features)
        
        # Return JSON Response to JavaScript
        if prediction[0] == 1:
            return jsonify({
                'status': 'danger',
                'prediction_text': 'Warning: High Fraud Risk Detected!'
            })
        else:
            return jsonify({
                'status': 'success',
                'prediction_text': 'Success: Valid & Safe Transaction'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'danger',
            'prediction_text': f'Error: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True)