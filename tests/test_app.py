"""
Unit tests for the main Flask application
"""

import pytest
import json
from src.app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test that the index page loads correctly"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Realty AI Scout' in response.data

def test_analyze_endpoint_no_address(client):
    """Test analyze endpoint with missing address"""
    response = client.post('/analyze', 
                          json={},
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Address is required' in data['error']

def test_analyze_endpoint_with_address(client):
    """Test analyze endpoint with valid address"""
    response = client.post('/analyze',
                          json={'address': '123 Main St, Anytown, CA'},
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'address' in data
    assert data['address'] == '123 Main St, Anytown, CA'

def test_analyze_endpoint_invalid_json(client):
    """Test analyze endpoint with invalid JSON"""
    response = client.post('/analyze',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400