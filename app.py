from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Firebase app
cred = credentials.Certificate({
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
})

firebase_admin.initialize_app(cred)
db = firestore.client()

# Custom decorator for verifying Firebase ID token
def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            decoded_token = firebase_admin.auth.verify_id_token(token)
            kwargs['user_id'] = decoded_token['uid']
            return f(*args, **kwargs)
        except firebase_admin.auth.InvalidIdTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

    return decorated_function

# Routes will be defined here
# Authentication route

@app.route('/register', methods=['POST'])
def register():
    email = request.json['email']
    password = request.json['password']

    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        return jsonify({'message': 'User created successfully', 'uid': user.uid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']

    try:
        user = auth.get_user_by_email(email)
        auth.get_user(user.uid)
        custom_token = auth.create_custom_token(user.uid)
        return jsonify({'token': custom_token.decode()}), 200
    except auth.UserNotFoundError:
        return jsonify({'message': 'Invalid credentials!'}), 401
    except auth.InvalidIdTokenError:
        return jsonify({'message': 'Invalid credentials!'}), 401


# # Articles routes
# @app.route('/articles', methods=['GET'])
# @authenticate
# def get_articles(user_id):
#     articles = db.collection('articles').where('user_id', '==', user_id).get()
#     return jsonify([article.to_dict() for article in articles]), 200

# @app.route('/articles', methods=['POST'])
# @authenticate
# def create_article(user_id):
#     data = request.get_json()
#     data['user_id'] = user_id

#     doc_ref = db.collection('articles').document()
#     doc_ref.set(data)

#     return jsonify({'id': doc_ref.id}), 201

# @app.route('/articles/<article_id>', methods=['GET'])
# @authenticate
# def get_article(user_id, article_id):
#     article = db.collection('articles').document(article_id).get()
#     if article.exists and article.to_dict().get('user_id') == user_id:
#         return jsonify(article.to_dict()), 200
#     return jsonify({'message': 'Article not found!'}), 404

# @app.route('/articles/<article_id>', methods=['PUT'])
# @authenticate
# def update_article(user_id, article_id):
#     data = request.get_json()
#     article_ref = db.collection('articles').document(article_id)
#     article = article_ref.get()

#     if article.exists and article.to_dict().get('user_id') == user_id:
#         article_ref.update(data)
#         return jsonify({'message': 'Article updated successfully!'}), 200

#     return jsonify({'message': 'Article not found or access denied!'}), 404

# @app.route('/articles/<article_id>', methods=['DELETE'])
# @authenticate
# def delete_article(user_id, article_id):
#     article_ref = db.collection('articles').document(article_id)
#     article = article_ref.get()

#     if article.exists and article.to_dict().get('user_id') == user_id:
#         article_ref.delete()
#         return jsonify({'message': 'Article deleted successfully!'}), 200

#     return jsonify({'message': 'Article not found or access denied!'}), 404

# # Galleries routes
# @app.route('/galleries', methods=['GET'])
# @authenticate
# def get_galleries(user_id):
#     galleries = db.collection('galleries').where('user_id', '==', user_id).get()
#     return jsonify([gallery.to_dict() for gallery in galleries]), 200

# @app.route('/galleries', methods=['POST'])
# @authenticate
# def create_gallery(user_id):
#     data = request.get_json()
#     data['user_id'] = user_id

#     doc_ref = db.collection('galleries').document()
#     doc_ref.set(data)

#     return jsonify({'id': doc_ref.id}), 201

# Add routes for updating, getting, and deleting galleries (similar to articles routes)

# Define the main entry point of the application
if __name__ == '__main__':
    app.run()
