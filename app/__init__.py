from flask import Flask
import os

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Mengonfigurasi aplikasi Flask
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')


# Import models dan routes setelah app dan db diinisialisasi
from app import routes
