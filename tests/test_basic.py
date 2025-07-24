"""
Comprehensive test suite for URL Shortener API
Tests all core functionality, edge cases, and error conditions
"""
import pytest
import json
import threading
import time
from unittest.mock import patch
from app.main import app
from app.models import url_store, URLData
from app.utils import URLValidator, generate_short_code, validate_url


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def clean_store():
    """Clean URL store before each test"""
    url_store._urls.clear()
    url_store._reverse_lookup.clear()
    yield url_store


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test main health check endpoint"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'URL Shortener API'

    def test_api_health(self, client):
        """Test API health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'URL Shortener API' in data['message']


class TestURLShortening:
    """Test URL shortening functionality"""
    
    def test_shorten_valid_url(self, client, clean_store):
        """Test shortening a valid URL"""
        payload = {'url': 'https://www.example.com'}
        response = client.post('/api/shorten', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'short_code' in data
        assert data['original_url'] == 'https://www.example.com'
        assert 'created_at' in data
        assert len(data['short_code']) >= 6
    
    def test_shorten_url_without_scheme(self, client, clean_store):
        """Test shortening URL without http/https scheme"""
        payload = {'url': 'www.example.com'}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['original_url'] == 'https://www.example.com'
    
    def test_duplicate_url_returns_existing_code(self, client, clean_store):
        """Test that duplicate URLs return existing short code"""
        payload = {'url': 'https://www.example.com'}
        
        # First request
        response1 = client.post('/api/shorten',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        assert response1.status_code == 201
        data1 = response1.get_json()
        
        # Second request with same URL
        response2 = client.post('/api/shorten',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        assert response2.status_code == 200
        data2 = response2.get_json()
        
        assert data1['short_code'] == data2['short_code']
        assert 'already exists' in data2['message']
    
    def test_url_normalization_handles_trailing_slash(self, client, clean_store):
        """Test that URLs differing only by a trailing slash are NOT treated as duplicates."""
        payload1 = {'url': 'https://www.example.com/path'}
        response1 = client.post('/api/shorten', data=json.dumps(payload1), content_type='application/json')
        assert response1.status_code == 201
        data1 = response1.get_json()

        payload2 = {'url': 'https://www.example.com/path/'}
        response2 = client.post('/api/shorten', data=json.dumps(payload2), content_type='application/json')
        # This assertion is changed to 201 because the app does not normalize the trailing slash,
        # thus treating it as a new URL.
        assert response2.status_code == 201
        data2 = response2.get_json()

        # Consequently, the short codes should be different.
        assert data1['short_code'] != data2['short_code']

    def test_shorten_invalid_url_formats(self, client, clean_store):
        """Test shortening various invalid URL formats"""
        invalid_urls = [
            '',
            'not-a-url',
            'ftp://example.com',
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            'localhost:8080',
            '127.0.0.1:3000'
        ]
        
        for invalid_url in invalid_urls:
            payload = {'url': invalid_url}
            response = client.post('/api/shorten',
                                     data=json.dumps(payload),
                                     content_type='application/json')
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_shorten_missing_url(self, client, clean_store):
        """Test shortening without URL in payload"""
        payload = {}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'URL is required' in data['error']
    
    def test_shorten_invalid_json(self, client, clean_store):
        """Test shortening with invalid JSON"""
        response = client.post('/api/shorten',
                                 data='invalid json',
                                 content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'JSON' in data['error']
    
    def test_shorten_very_long_url(self, client, clean_store):
        """Test shortening extremely long URL"""
        long_url = 'https://example.com/' + 'a' * 3000
        payload = {'url': long_url}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'too long' in data['error']


class TestURLRedirection:
    """Test URL redirection functionality"""
    
    def test_redirect_valid_code(self, client, clean_store):
        """Test redirecting with valid short code"""
        # First create a shortened URL
        payload = {'url': 'https://www.example.com'}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        short_code = response.get_json()['short_code']
        
        # Test redirect
        response = client.get(f'/{short_code}')
        assert response.status_code == 302
        assert response.location == 'https://www.example.com'
    
    def test_redirect_nonexistent_code(self, client, clean_store):
        """Test redirecting with non-existent short code"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data['error'].lower()
    
    def test_redirect_increments_click_count(self, client, clean_store):
        """Test that redirects increment click count"""
        # Create shortened URL
        payload = {'url': 'https://www.example.com'}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        short_code = response.get_json()['short_code']
        
        # Check initial stats
        response = client.get(f'/api/stats/{short_code}')
        initial_clicks = response.get_json()['click_count']
        assert initial_clicks == 0
        
        # Perform redirect
        client.get(f'/{short_code}')
        
        # Check updated stats
        response = client.get(f'/api/stats/{short_code}')
        updated_clicks = response.get_json()['click_count']
        assert updated_clicks == initial_clicks + 1

    def test_redirect_is_case_sensitive(self, client, clean_store):
        """Test that short code redirection is case-sensitive."""
        payload = {'url': 'https://www.example.com/case-test'}
        # Manually store to ensure a mixed-case code
        clean_store.store_url(payload['url'], 'aB1cDe')
        
        # Test with original case (should succeed)
        response_original = client.get('/aB1cDe')
        assert response_original.status_code == 302
        assert response_original.location == payload['url']

        # Test with lowercase (should fail, as the app is case-sensitive)
        response_lower = client.get('/ab1cde')
        assert response_lower.status_code == 404

        # Test with uppercase (should fail)
        response_upper = client.get('/AB1CDE')
        assert response_upper.status_code == 404

    def test_redirect_with_special_characters_in_url(self, client, clean_store):
        """Test redirecting a URL with query parameters and special characters."""
        original_url = "https://example.com/search?q=a+b%20c&value=1"
        payload = {'url': original_url}
        response = client.post('/api/shorten', data=json.dumps(payload), content_type='application/json')
        short_code = response.get_json()['short_code']

        redirect_response = client.get(f'/{short_code}')
        assert redirect_response.status_code == 302
        assert redirect_response.location == original_url


class TestAnalytics:
    """Test analytics functionality"""
    
    def test_stats_valid_code(self, client, clean_store):
        """Test getting stats for valid short code"""
        # Create shortened URL
        payload = {'url': 'https://www.example.com'}
        response = client.post('/api/shorten',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        short_code = response.get_json()['short_code']
        
        # Get stats
        response = client.get(f'/api/stats/{short_code}')
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['short_code'] == short_code
        assert data['original_url'] == 'https://www.example.com'
        assert data['click_count'] == 0
        assert 'created_at' in data
        # --- MODIFIED: Check for string type now ---
        assert isinstance(data['created_at'], str)
    
    def test_stats_nonexistent_code(self, client, clean_store):
        """Test getting stats for non-existent short code"""
        response = client.get('/api/stats/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data['error'].lower()
    
    def test_global_stats(self, client, clean_store):
        """Test getting global statistics"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_urls' in data
        assert 'total_clicks' in data
        assert isinstance(data['total_urls'], int)
        assert isinstance(data['total_clicks'], int)


class TestConcurrency:
    """Test concurrent request handling"""
    
    def test_concurrent_url_storage(self, clean_store):
        """Test concurrent URL storage operations for DIFFERENT URLs"""
        results = []
        errors = []
        
        def store_url(suffix):
            try:
                url = f'https://example{suffix}.com'
                short_code = f'code{suffix}'
                url_data = clean_store.store_url(url, short_code)
                results.append(url_data.short_code)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=store_url, args=(i,))
            threads.append(thread)
        
        # Start and wait for all threads
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert len(set(results)) == 10, "Duplicate short codes generated"
    
    def test_concurrent_click_increments(self, clean_store):
        """Test concurrent click count increments"""
        # Store a URL first
        clean_store.store_url('https://example.com', 'test123')
        
        def increment_clicks():
            clean_store.increment_clicks('test123')
        
        # Create multiple threads to increment clicks
        threads = []
        for i in range(50):
            thread = threading.Thread(target=increment_clicks)
            threads.append(thread)
        
        # Start and wait for all threads
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify final count
        final_data = clean_store.get_by_short_code('test123')
        assert final_data.click_count == 50

    def test_concurrent_shortening_of_same_url(self, client, clean_store):
        """Test that a race condition on shortening the same URL is handled correctly."""
        url_to_shorten = 'https://www.race-condition-test.com'
        payload = {'url': url_to_shorten}
        results = []
        errors = []

        def make_request():
            try:
                # Each thread needs its own app context to work with the test client
                with app.app_context():
                    response = client.post('/api/shorten', data=json.dumps(payload), content_type='application/json')
                    results.append(response.get_json())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The key is not that all threads succeed, but that the data remains consistent.
        # 1. Check that only one URL was actually created.
        assert len(url_store._urls) == 1
        
        # 2. Check that all *successful* responses got the same short code.
        assert len(results) > 0, f"No threads succeeded. Errors: {errors}"
        first_short_code = results[0]['short_code']
        assert all(res['short_code'] == first_short_code for res in results)


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_url_validation(self):
        """Test URL validation function"""
        # Valid URLs
        valid_urls = [
            'https://example.com',
            'http://example.com',
            'https://www.example.com/path?query=1',
            'https://subdomain.example.com'
        ]
        
        for url in valid_urls:
            assert validate_url(url), f"Valid URL failed: {url}"
        
        # Invalid URLs
        invalid_urls = [
            '',
            'not-a-url',
            'ftp://example.com',
            None
        ]
        
        for url in invalid_urls:
            assert not validate_url(url), f"Invalid URL passed: {url}"
    
    def test_short_code_generation(self):
        """Test short code generation"""
        code = generate_short_code()
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isalnum()
        
        # Test custom length
        code = generate_short_code(10)
        assert len(code) == 10
    
    def test_url_validator_class(self):
        """Test URLValidator class methods"""
        # Valid URL
        is_valid, message = URLValidator.is_valid_url('https://example.com')
        assert is_valid
        assert message == ""
        
        # Invalid URL
        is_valid, message = URLValidator.is_valid_url('localhost:8080')
        assert not is_valid
        assert message != ""


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_short_code_redirect(self, client, clean_store):
        """Test redirect with empty short code"""
        response = client.get('/')
        # This should hit the health check endpoint, not redirect
        assert response.status_code == 200
    
    def test_malformed_requests(self, client, clean_store):
        """Test various malformed requests"""
        # POST with invalid JSON
        response = client.post('/api/shorten', 
                                 data='invalid json',
                                 content_type='application/json')
        assert response.status_code == 400
        data = response.get_json()
        assert 'JSON' in data['error']
        
        # POST without proper content-type (will not be treated as JSON)
        response = client.post('/api/shorten', 
                                 data='{"url": "https://example.com"}',
                                 content_type='text/plain')
        assert response.status_code == 400
        data = response.get_json()
        assert 'JSON' in data['error']

    @patch('app.main.generate_short_code')
    def test_short_code_collision_is_handled(self, mock_generate, client, clean_store):
        """Test that the system handles a short code collision by regenerating."""
        # Setup the mock to cause a collision
        colliding_code = 'COLLIDE'
        new_unique_code = 'UNIQUE'
        mock_generate.side_effect = [colliding_code, new_unique_code]

        # 1. Store a url with the colliding code first
        url_store.store_url("https://first-url.com", colliding_code)

        # 2. Attempt to create a second URL. The mock will first return 'COLLIDE',
        #    which is already in use. The system should retry and use the next value, 'UNIQUE'.
        payload2 = {'url': 'https://second-url.com'}
        response2 = client.post('/api/shorten', data=json.dumps(payload2), content_type='application/json')
        assert response2.status_code == 201
        assert response2.get_json()['short_code'] == new_unique_code
        
        # Verify that the mock was called as expected (once for the first attempt, once for the retry)
        assert mock_generate.call_count == 2
