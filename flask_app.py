from flask import Flask, render_template, request, session, redirect, url_for
import os
from google.cloud import storage
from google.oauth2 import service_account
import json

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.secret_key = config['secret_key']  # Set the secret key from config.json


@app.route('/')
def index():
    return render_template('index.html', logged_in=session.get('logged_in'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Perform login validation using the data from config.json
    if username in config['users'] and password == config['users'][username]:
        session['logged_in'] = True
        session['username'] = username
        session['user_id'] = list(config['users'].keys()).index(username) + 1
        return redirect(url_for('index'))
    else:
        message = 'Nombre de usuario y contraseña inválido. Vuelva a intentar.'
        return render_template('index.html', message=message, logged_in=session.get('logged_in'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/upload_file', methods=['POST'])
def upload_file():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    # Save uploaded file to 'demo' folder
    file = request.files['file']
    username = session.get('username')
    user_id = session.get('user_id')
    filename = f"{user_id}_{file.filename}"
    file.save(os.path.join('demo', filename))

    # Load project id and service account file from config.json
    project_id = config['project_id']
    service_account_file = config['service_account_file']

    with open(service_account_file) as source:
        info = json.load(source)

    storage_credentials = service_account.Credentials.from_service_account_info(info)
    client = storage.Client(credentials=storage_credentials, project=project_id)
    bucket = client.get_bucket('lib-ia')
    blob = bucket.blob(f'libros/request_stage1/{filename}')
    blob.upload_from_filename(f'demo/{filename}')

    message = 'Archivo subido correctamente. Recibirá un e-mail con los resultados en las próximas 2 horas'
    return render_template('index.html', message=message, logged_in=session.get('logged_in'))


if __name__ == '__main__':
    app.run(debug=True)
