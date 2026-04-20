"""
ATLAS AI Chatbot API - Segurança Máxima
"""

import time
import secrets
import os
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach
from chatbot import AtlasChatbot

app = Flask(__name__)
CORS(app)

API_KEY = "atlas-secure-key-2024"

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"]
)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Server'] = 'ATLAS-SECURE'
    response.headers['Cache-Control'] = 'no-store'
    return response

def sanitize_input(text, max_length=500):
    if not isinstance(text, str):
        return ""
    text = text.strip()[:max_length]
    cleaned = bleach.clean(text, tags=[], attributes={}, protocols=[], strip=True)
    return cleaned[:max_length]

@app.before_request
def log_request():
    g.start_time = time.time()

chatbot = AtlasChatbot()

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_key
def chat():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        message = data.get('message', '')
        context = data.get('context', '')
        
        if not isinstance(message, str):
            return jsonify({'error': 'Message must be a string'}), 400
        
        clean_message = sanitize_input(message, 500)
        clean_context = sanitize_input(context, 1000)
        
        if not clean_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        result = chatbot.chat(clean_message, clean_context)
        
        if result.get('success'):
            return jsonify({
                'response': result.get('response'),
                'request_id': secrets.token_hex(8),
                'timestamp': int(time.time())
            })
        else:
            return jsonify({
                'error': result.get('error', 'Error processing request')
            }), 500
            
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    is_online = chatbot.is_online()
    return jsonify({
        'status': 'healthy' if is_online else 'degraded',
    }), 200 if is_online else 503

@app.route('/api/status', methods=['GET'])
@require_api_key
def status():
    is_online = chatbot.is_online()
    return jsonify({
        'status': 'online' if is_online else 'offline',
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

if __name__ == '__main__':
    print("ATLAS AI API - Seguranca Total")
    print("=" * 40)
    print("Endpoints (requer X-API-Key: atlas-secure-key-2024):")
    print("  POST /api/chat")
    print("  GET  /api/status")
    print("  GET  /api/health (publico)")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)