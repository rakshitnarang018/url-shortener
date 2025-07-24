"""
URL Shortener API - Main Flask Application
"""
from flask import Flask, request, jsonify, redirect
from datetime import datetime, timezone  # <-- IMPORTED: For timestamp conversion
from app.models import url_store
from app.utils import URLValidator, generate_short_code, normalize_url


app = Flask(__name__)


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500


# Health check endpoints
@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })


@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })


# Core API endpoints
@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """
    Shorten URL endpoint
    POST /api/shorten
    Body: {"url": "https://example.com"}
    Returns: {"short_code": "abc123", "original_url": "https://example.com"}
    """
    try:
        # Check content type first
        if not request.is_json:
            return jsonify({'error': 'Request body must be JSON'}), 400
            
        # Parse request data - handle JSON parsing errors
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({'error': 'Request body must be valid JSON'}), 400
            
        # Check if data is None or empty
        if data is None:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        # Check if URL field exists and is not empty
        original_url = data.get('url')
        if not original_url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL
        is_valid, error_message = URLValidator.is_valid_url(original_url)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Normalize URL
        normalized_url = normalize_url(original_url)
        
        # Check if URL already exists (duplicate detection)
        existing_short_code = url_store.get_by_original_url(normalized_url)
        if existing_short_code:
            url_data = url_store.get_by_short_code(existing_short_code)
            # --- MODIFIED: Format timestamp for existing URL ---
            created_at_iso = datetime.fromtimestamp(url_data.created_at, tz=timezone.utc).isoformat()
            return jsonify({
                'short_code': existing_short_code,
                'original_url': url_data.original_url,
                'created_at': created_at_iso,
                'message': 'URL already exists'
            }), 200
        
        # Generate unique short code
        short_code = generate_short_code()
        while url_store.get_by_short_code(short_code):
             short_code = generate_short_code() # Regenerate if collision occurs
        
        # Store URL mapping
        url_data = url_store.store_url(normalized_url, short_code)
        
        # --- MODIFIED: Format timestamp for new URL ---
        created_at_iso = datetime.fromtimestamp(url_data.created_at, tz=timezone.utc).isoformat()
        
        return jsonify({
            'short_code': short_code,
            'original_url': normalized_url,
            'created_at': created_at_iso
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.route('/<short_code>')
def redirect_url(short_code):
    """
    Redirect endpoint
    GET /<short_code>
    Redirects to original URL and increments click count
    Returns 404 if short code doesn't exist
    """
    try:
        # Validate short code format
        if not short_code or not isinstance(short_code, str):
            return jsonify({'error': 'Invalid short code'}), 404
        
        # Get URL data
        url_data = url_store.get_by_short_code(short_code)
        if not url_data:
            return jsonify({'error': 'Short code not found'}), 404
        
        # Increment click count
        url_store.increment_clicks(short_code)
        
        # Redirect to original URL
        return redirect(url_data.original_url, code=302)
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    """
    Analytics endpoint
    GET /api/stats/<short_code>
    Returns: {
        "short_code": "abc123",
        "original_url": "https://example.com",
        "click_count": 5,
        "created_at": "2025-07-24T02:12:34.567890+00:00"
    }
    """
    try:
        # Validate short code format
        if not short_code or not isinstance(short_code, str):
            return jsonify({'error': 'Invalid short code'}), 400
        
        # Get URL data
        url_data = url_store.get_by_short_code(short_code)
        if not url_data:
            return jsonify({'error': 'Short code not found'}), 404
        
        # --- MODIFIED: Format timestamp for stats response ---
        created_at_iso = datetime.fromtimestamp(url_data.created_at, tz=timezone.utc).isoformat()
        
        # Return analytics data
        return jsonify({
            'short_code': url_data.short_code,
            'original_url': url_data.original_url,
            'click_count': url_data.click_count,
            'created_at': created_at_iso
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


# Additional utility endpoints
@app.route('/api/stats')
def get_global_stats():
    """Get global statistics"""
    try:
        stats = url_store.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
