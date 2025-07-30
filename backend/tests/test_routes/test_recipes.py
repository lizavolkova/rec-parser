# tests/test_routes/test_recipes.py
"""
Comprehensive tests for recipe routes
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from app.models import Recipe, RecipeURL, DebugInfo, RecipeStats, BatchCategorizationRequest


# Use shared test_client and sample_recipe_url fixtures from conftest.py


@pytest.fixture
def mock_recipe_service():
    """Mock RecipeService for testing"""
    with patch('app.routes.recipes.RecipeService') as mock:
        yield mock


@pytest.fixture
def mock_ai_available():
    """Mock AI being available"""
    with patch('app.routes.recipes.AI_AVAILABLE', True):
        yield


@pytest.fixture
def mock_ai_unavailable():
    """Mock AI being unavailable"""
    with patch('app.routes.recipes.AI_AVAILABLE', False):
        yield


class TestDebugEndpoint:
    """Test debug recipe endpoint"""
    
    def test_debug_recipe_success(self, test_client, sample_recipe_url, mock_recipe_service):
        """Test successful recipe debugging"""
        # Mock the debug response
        mock_debug_info = DebugInfo(
            status="success",
            html_length=5000,
            json_scripts_found=2,
            json_scripts_content=[{"type": "application/ld+json"}],
            ai_available=True
        )
        mock_recipe_service.debug_recipe.return_value = mock_debug_info
        
        response = test_client.post("/debug-recipe", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["html_length"] == 5000
        assert data["json_scripts_found"] == 2
        mock_recipe_service.debug_recipe.assert_called_once_with(str(sample_recipe_url.url))
    
    def test_debug_recipe_invalid_url(self, test_client):
        """Test debug with invalid URL format"""
        response = test_client.post("/debug-recipe", json={"url": "not-a-valid-url"})
        
        assert response.status_code == 422  # Validation error


class TestParseRecipeEndpoint:
    """Test parse recipe endpoint"""
    
    @pytest.mark.asyncio
    async def test_parse_recipe_with_ai_success(self, test_client, sample_recipe_url, sample_recipe, mock_ai_available):
        """Test successful recipe parsing with AI enhancement"""
        
        # Mock the enhanced recipe service
        mock_enhanced_service = AsyncMock()
        mock_enhanced_service.parse_and_categorize_recipe.return_value = sample_recipe
        
        with patch('app.routes.recipes.enhanced_recipe_service', mock_enhanced_service):
            response = test_client.post("/parse-recipe", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_recipe.title
        assert data["ingredients"] == sample_recipe.ingredients
        mock_enhanced_service.parse_and_categorize_recipe.assert_called_once_with(str(sample_recipe_url.url))
    
    @pytest.mark.asyncio 
    async def test_parse_recipe_ai_fallback(self, test_client, sample_recipe_url, sample_recipe, mock_ai_available):
        """Test recipe parsing when AI fails and falls back to basic parsing"""
        
        # Mock enhanced service to fail
        mock_enhanced_service = AsyncMock()
        mock_enhanced_service.parse_and_categorize_recipe.side_effect = Exception("AI failed")
        
        # Mock basic service to succeed
        with patch('app.routes.recipes.enhanced_recipe_service', mock_enhanced_service):
            with patch('app.routes.recipes.RecipeService') as mock_basic_service:
                mock_basic_service.parse_recipe_hybrid = AsyncMock(return_value=sample_recipe)
                
                response = test_client.post("/parse-recipe", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_recipe.title
        mock_basic_service.parse_recipe_hybrid.assert_called_once_with(str(sample_recipe_url.url))
    
    @pytest.mark.asyncio
    async def test_parse_recipe_without_ai(self, test_client, sample_recipe_url, sample_recipe, mock_ai_unavailable):
        """Test recipe parsing when AI is not available"""
        
        with patch('app.routes.recipes.RecipeService') as mock_service:
            mock_service.parse_recipe_hybrid = AsyncMock(return_value=sample_recipe)
            
            response = test_client.post("/parse-recipe", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_recipe.title
        mock_service.parse_recipe_hybrid.assert_called_once_with(str(sample_recipe_url.url))


class TestCategorizeExistingRecipe:
    """Test categorize existing recipe endpoint"""
    
    @pytest.mark.asyncio
    async def test_categorize_recipe_success(self, test_client, sample_recipe, mock_ai_available):
        """Test successful recipe categorization"""
        
        # Mock categorization service and response
        mock_categorization = Mock()
        mock_categorization.health_tags = ["vegetarian"]
        mock_categorization.dish_type = ["salad"]
        mock_categorization.cuisine_type = ["mediterranean"]
        mock_categorization.meal_type = ["lunch"]
        mock_categorization.season = ["spring", "summer"]
        mock_categorization.confidence_notes = "High confidence categorization"
        mock_categorization.ai_model = "gpt-4o-mini"
        
        mock_service = AsyncMock()
        mock_service.categorize_recipe.return_value = mock_categorization
        
        with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_service):
            response = test_client.post("/categorize-recipe", json=sample_recipe.model_dump())
        
        assert response.status_code == 200
        data = response.json()
        assert data["health_tags"] == ["vegetarian"]
        assert data["dish_type"] == ["salad"]
        assert data["ai_enhanced"] is True
        assert data["used_ai"] is True
    
    def test_categorize_recipe_ai_unavailable(self, test_client, sample_recipe, mock_ai_unavailable):
        """Test categorization when AI is not available"""
        
        response = test_client.post("/categorize-recipe", json=sample_recipe.model_dump())
        
        assert response.status_code == 503
        assert "AI categorization service not available" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_categorize_recipe_ai_failure(self, test_client, sample_recipe, mock_ai_available):
        """Test categorization when AI service fails"""
        
        mock_service = AsyncMock()
        mock_service.categorize_recipe.return_value = None
        
        with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_service):
            response = test_client.post("/categorize-recipe", json=sample_recipe.model_dump())
        
        assert response.status_code == 500
        assert "AI categorization failed" in response.json()["detail"]


class TestSearchEndpoint:
    """Test recipe search endpoint"""
    
    def test_search_not_implemented(self, test_client):
        """Test that search returns not implemented error"""
        response = test_client.get("/search")
        
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"]
    
    def test_search_with_parameters(self, test_client):
        """Test search with various query parameters"""
        response = test_client.get("/search?q=pasta&health=vegetarian&limit=10&offset=20")
        
        assert response.status_code == 501  # Still not implemented


class TestCategoriesEndpoint:
    """Test get available categories endpoint"""
    
    def test_get_categories_with_ai(self, test_client, mock_ai_available):
        """Test getting categories when AI is available"""
        
        # Mock the categorization service
        mock_service = Mock()
        mock_service.HEALTH_TAGS = ["vegan", "vegetarian", "gluten-free"]
        mock_service.DISH_TYPES = ["main-course", "dessert", "appetizer"]
        mock_service.CUISINE_TYPES = ["italian", "mexican", "asian"]
        mock_service.MEAL_TYPES = ["breakfast", "lunch", "dinner"]
        mock_service.SEASONS = ["spring", "summer", "autumn", "winter"]
        
        with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_service):
            response = test_client.get("/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_available"] is True
        assert data["health_tags"] == ["vegan", "vegetarian", "gluten-free"]
        assert data["dish_types"] == ["main-course", "dessert", "appetizer"]
        assert data["cuisine_types"] == ["italian", "mexican", "asian"]
    
    def test_get_categories_without_ai(self, test_client, mock_ai_unavailable):
        """Test getting categories when AI is not available"""
        
        response = test_client.get("/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_available"] is False
        assert data["health_tags"] == []
        assert data["dish_types"] == []
        assert data["cuisine_types"] == []
    
    def test_get_categories_ai_error(self, test_client, mock_ai_available):
        """Test getting categories when AI service throws an error"""
        
        with patch('app.routes.recipes.RecipeCategorizationService', side_effect=Exception("Service error")):
            response = test_client.get("/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_available"] is False
        assert "error" in data
        assert data["error"] == "Service error"


class TestStatsEndpoint:
    """Test recipe stats endpoint"""
    
    def test_get_stats(self, test_client):
        """Test getting recipe statistics"""
        response = test_client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_recipes"] == 0
        assert data["ai_enhanced_count"] == 0
        assert data["ai_enhancement_percentage"] == 0.0
        assert data["top_health_tags"] == []
        assert "seasonal_distribution" in data


class TestDebugAICategorization:
    """Test debug AI categorization endpoint"""
    
    @pytest.mark.asyncio
    async def test_debug_ai_categorization_success(self, test_client, sample_recipe_url, sample_recipe, mock_ai_available):
        """Test successful AI categorization debugging"""
        
        # Mock enhanced service
        enhanced_recipe = sample_recipe.model_copy()
        enhanced_recipe.health_tags = ["vegetarian"]
        enhanced_recipe.dish_type = ["salad"]
        enhanced_recipe.ai_enhanced = True
        enhanced_recipe.ai_model_used = "gpt-4o-mini"
        
        mock_service = AsyncMock()
        mock_service.parse_and_categorize_recipe.return_value = enhanced_recipe
        
        with patch('app.routes.recipes.EnhancedRecipeService', return_value=mock_service):
            response = test_client.post("/debug-ai-categorization", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["recipe_title"] == sample_recipe.title
        assert data["ai_categorization"]["health_tags"] == ["vegetarian"]
        assert data["ai_categorization"]["ai_enhanced"] is True
        assert "debug_info" in data
    
    def test_debug_ai_categorization_unavailable(self, test_client, sample_recipe_url, mock_ai_unavailable):
        """Test debug AI categorization when AI is unavailable"""
        
        response = test_client.post("/debug-ai-categorization", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 503
        assert "AI categorization service not available" in response.json()["detail"]


class TestAIStatusEndpoint:
    """Test AI status endpoint"""
    
    def test_ai_status_available(self, test_client, mock_ai_available):
        """Test AI status when services are available"""
        
        with patch('app.routes.recipes.enhanced_recipe_service', Mock()):
            with patch('app.routes.recipes.batch_service', Mock()):
                response = test_client.get("/ai-status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_services_available"] is True
        assert data["enhanced_service_loaded"] is True
        assert data["batch_service_loaded"] is True
        assert "working correctly" in data["message"]
    
    def test_ai_status_unavailable(self, test_client, mock_ai_unavailable):
        """Test AI status when services are not available"""
        
        response = test_client.get("/ai-status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ai_services_available"] is False
        assert "not available" in data["message"]


class TestBatchCategorization:
    """Test batch categorization endpoints"""
    
    def test_start_batch_categorization_success(self, test_client, mock_ai_available):
        """Test starting batch categorization successfully"""
        
        request_data = {
            "recipe_ids": [1, 2, 3],
            "limit": 10,
            "force_recategorize": False
        }
        
        response = test_client.post("/batch-categorize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "started"
        assert "started in background" in data["message"]
    
    def test_start_batch_categorization_ai_unavailable(self, test_client, mock_ai_unavailable):
        """Test batch categorization when AI is unavailable"""
        
        request_data = {"recipe_ids": [1, 2, 3]}
        
        response = test_client.post("/batch-categorize", json=request_data)
        
        assert response.status_code == 503
        assert "AI categorization service not available" in response.json()["detail"]
    
    def test_get_batch_status_not_found(self, test_client):
        """Test getting status for non-existent batch task"""
        
        response = test_client.get("/batch-categorize/non-existent-id")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    def test_get_batch_status_success(self, test_client, mock_ai_available):
        """Test getting status for existing batch task"""
        
        # First start a batch task
        request_data = {"recipe_ids": [1]}
        start_response = test_client.post("/batch-categorize", json=request_data)
        task_id = start_response.json()["task_id"]
        
        # Then get its status
        response = test_client.get(f"/batch-categorize/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["total_recipes"] == 0
        assert data["processed_count"] == 0


class TestTestAICategorization:
    """Test the test AI categorization endpoint"""
    
    @pytest.mark.asyncio
    async def test_test_ai_categorization_success(self, test_client, mock_ai_available):
        """Test the AI categorization test endpoint"""
        
        # Mock categorization service
        mock_categorization = Mock()
        mock_categorization.health_tags = ["vegan"]
        mock_categorization.dish_type = ["curry"]
        mock_categorization.cuisine_type = ["indian"]
        mock_categorization.meal_type = ["dinner"]
        mock_categorization.season = ["winter"]
        mock_categorization.confidence_notes = "High confidence"
        
        mock_service = AsyncMock()
        mock_service.categorize_recipe.return_value = mock_categorization
        
        with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_service):
            response = test_client.post("/test-ai-categorization")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Creamy Coconut Curry"
        assert data["health_tags"] == ["vegan"]
        assert data["dish_type"] == ["curry"]
        assert data["ai_enhanced"] is True
    
    def test_test_ai_categorization_unavailable(self, test_client, mock_ai_unavailable):
        """Test AI categorization test when AI is unavailable"""
        
        response = test_client.post("/test-ai-categorization")
        
        assert response.status_code == 503
        assert "AI categorization service not available" in response.json()["detail"]


class TestDebugVeganDetection:
    """Test debug vegan detection endpoint"""
    
    @pytest.mark.asyncio
    async def test_debug_vegan_detection_success(self, test_client, sample_recipe_url, vegan_recipe, mock_ai_available):
        """Test successful vegan detection debugging"""
        
        # Mock categorization with vegan tag
        mock_categorization = Mock()
        mock_categorization.health_tags = ["vegan"]
        mock_categorization.dish_type = ["bowl"]
        mock_categorization.cuisine_type = ["healthy"]
        mock_categorization.meal_type = ["lunch"]
        mock_categorization.season = ["all-season"]
        mock_categorization.confidence_notes = "Clearly vegan ingredients"
        mock_categorization.ai_model = "gpt-4o-mini"
        
        mock_categorization_service = AsyncMock()
        mock_categorization_service.categorize_recipe.return_value = mock_categorization
        
        with patch('app.routes.recipes.RecipeService') as mock_recipe_service:
            mock_recipe_service.parse_recipe_hybrid.return_value = vegan_recipe
            
            with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_categorization_service):
                response = test_client.post("/debug-vegan-detection", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["recipe_title"] == vegan_recipe.title
        assert data["classification_analysis"]["should_be_vegan"] is True
        assert data["classification_analysis"]["actual_is_vegan"] is True
        assert data["classification_analysis"]["classification_correct"] is True
        assert " CORRECT" in data["recommendations"][0]
    
    @pytest.mark.asyncio
    async def test_debug_vegan_detection_with_animal_products(self, test_client, sample_recipe_url, sample_recipe, mock_ai_available):
        """Test vegan detection with recipe containing animal products"""
        
        # Mock categorization without vegan tag
        mock_categorization = Mock()
        mock_categorization.health_tags = ["vegetarian"]  # Not vegan
        mock_categorization.dish_type = ["salad"]
        mock_categorization.cuisine_type = ["mediterranean"]
        mock_categorization.meal_type = ["lunch"]
        mock_categorization.season = ["spring"]
        mock_categorization.confidence_notes = "Contains dairy"
        mock_categorization.ai_model = "gpt-4o-mini"
        
        mock_categorization_service = AsyncMock()
        mock_categorization_service.categorize_recipe.return_value = mock_categorization
        
        with patch('app.routes.recipes.RecipeService') as mock_recipe_service:
            mock_recipe_service.parse_recipe_hybrid.return_value = sample_recipe
            
            with patch('app.routes.recipes.RecipeCategorizationService', return_value=mock_categorization_service):
                response = test_client.post("/debug-vegan-detection", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 200
        data = response.json()
        assert data["classification_analysis"]["should_be_vegan"] is False
        assert data["classification_analysis"]["actual_is_vegan"] is False
        assert len(data["ingredient_analysis"]["animal_ingredients"]) > 0  # Should detect parmesan cheese
    
    def test_debug_vegan_detection_unavailable(self, test_client, sample_recipe_url, mock_ai_unavailable):
        """Test vegan detection debug when AI is unavailable"""
        
        response = test_client.post("/debug-vegan-detection", json={"url": str(sample_recipe_url.url)})
        
        assert response.status_code == 503
        assert "AI categorization service not available" in response.json()["detail"]