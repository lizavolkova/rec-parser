# tests/test_routes/test_health.py
"""
Tests for health check endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

from app.models import HealthResponse


# Use shared test_client fixture from conftest.py


class TestHealthRoutes:
    """Test health check endpoints"""
    
    def test_read_root(self, test_client):
        """Test basic hello world endpoint returns correct message"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, AI-Enhanced Recipe Parser!"}
    
    @patch('app.routes.health.openai_client')
    @patch('app.routes.health.settings')
    def test_health_check_with_ai_available(self, mock_settings, mock_openai_client, test_client):
        """Test health check when AI is available"""
        # Mock AI being available
        mock_openai_client = Mock()
        mock_settings.AI_MODEL = "gpt-4o-mini"
        
        with patch('app.routes.health.openai_client', mock_openai_client):
            with patch('app.routes.health.settings', mock_settings):
                response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["ai_available"] is True
        assert data["ai_model"] == "gpt-4o-mini"
        assert data["ai_categorization_enabled"] is True
        assert "timestamp" in data
        
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"])
    
    @patch('app.routes.health.openai_client', None)
    @patch('app.routes.health.settings')
    def test_health_check_without_ai(self, mock_settings, test_client):
        """Test health check when AI is not available"""
        mock_settings.AI_MODEL = "gpt-4o-mini"
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["ai_available"] is False
        assert data["ai_model"] is None
        assert data["ai_categorization_enabled"] is True  # Still enabled, just not available
        assert "timestamp" in data
    
    def test_health_response_model_validation(self):
        """Test HealthResponse model validates correctly"""
        # Test with all fields
        response = HealthResponse(
            status="healthy",
            ai_available=True,
            ai_model="gpt-4o-mini",
            ai_categorization_enabled=True,
            timestamp="2024-01-01T12:00:00"
        )
        
        assert response.status == "healthy"
        assert response.ai_available is True
        assert response.ai_model == "gpt-4o-mini"
        assert response.ai_categorization_enabled is True
        assert response.timestamp == "2024-01-01T12:00:00"
        
    def test_health_response_optional_fields(self):
        """Test HealthResponse works with optional fields"""
        response = HealthResponse(
            status="healthy",
            ai_available=False
        )
        
        assert response.status == "healthy"
        assert response.ai_available is False
        assert response.ai_model is None
        assert response.ai_categorization_enabled is True  # Default value
        assert response.ai_adaptability_enabled is True   # Default value
        assert response.timestamp is None