# tests/test_models.py
"""
Unit tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import (
    Recipe, RecipeURL, RecipeCategorization, RecipeAdaptability,
    RecipeSearchFilters, RecipeStats, DebugInfo, HealthResponse
)


class TestRecipeModel:
    """Test the Recipe model"""
    
    def test_create_basic_recipe(self):
        """Test creating a basic recipe"""
        recipe = Recipe(
            title="Test Recipe",
            ingredients=["flour", "eggs"],
            instructions=["Mix ingredients", "Bake"]
        )
        
        assert recipe.title == "Test Recipe"
        assert len(recipe.ingredients) == 2
        assert len(recipe.instructions) == 2
        assert recipe.raw_ingredients == []  # Default
        assert not recipe.found_structured_data  # Default
        assert not recipe.used_ai  # Default
    
    def test_recipe_with_all_fields(self):
        """Test creating a recipe with all fields"""
        recipe = Recipe(
            title="Complete Recipe",
            description="A complete test recipe",
            image="https://example.com/image.jpg",
            source="Test Kitchen",
            ingredients=["1 cup flour", "2 eggs"],
            instructions=["Mix", "Bake"],
            prep_time="10 minutes",
            cook_time="20 minutes",
            servings="4",
            cuisine="American",
            category="dessert",
            keywords=["easy", "quick"],
            found_structured_data=True,
            used_ai=True,
            raw_ingredients=["flour", "eggs"],
            health_tags=["vegetarian"],
            dish_type=["dessert"],
            cuisine_type=["american"],
            meal_type=["dessert"],
            season=["all"],
            ai_enhanced=True
        )
        
        assert recipe.description == "A complete test recipe"
        assert recipe.source == "Test Kitchen"
        assert recipe.health_tags == ["vegetarian"]
        assert recipe.ai_enhanced
    
    def test_recipe_adaptability_defaults(self):
        """Test that adaptability fields default properly"""
        recipe = Recipe(
            title="Test Recipe",
            ingredients=["flour"],
            instructions=["Mix"]
        )
        
        assert not recipe.easily_veganizable
        assert recipe.vegan_adaptations is None
        assert not recipe.easily_vegetarianizable
        assert recipe.vegetarian_adaptations is None
        assert not recipe.easily_healthified
        assert recipe.healthy_adaptations is None


class TestRecipeURL:
    """Test the RecipeURL model"""
    
    def test_valid_url(self):
        """Test valid URL creation"""
        recipe_url = RecipeURL(url="https://example.com/recipe")
        assert str(recipe_url.url) == "https://example.com/recipe"
    
    def test_invalid_url(self):
        """Test invalid URL raises validation error"""
        with pytest.raises(ValidationError):
            RecipeURL(url="not-a-url")
    
    def test_url_without_scheme(self):
        """Test URL without scheme raises validation error"""
        with pytest.raises(ValidationError):
            RecipeURL(url="example.com/recipe")


class TestRecipeAdaptability:
    """Test the RecipeAdaptability model"""
    
    def test_default_adaptability(self):
        """Test default adaptability values"""
        adaptability = RecipeAdaptability()
        
        assert not adaptability.easily_veganizable
        assert adaptability.vegan_adaptations is None
        assert not adaptability.easily_vegetarianizable
        assert adaptability.vegetarian_adaptations is None
        assert not adaptability.easily_healthified
        assert adaptability.healthy_adaptations is None
    
    def test_adaptability_with_values(self):
        """Test adaptability with values"""
        adaptability = RecipeAdaptability(
            easily_veganizable=True,
            vegan_adaptations="Replace cheese with nutritional yeast",
            easily_healthified=True,
            healthy_adaptations="Use whole wheat flour"
        )
        
        assert adaptability.easily_veganizable
        assert "nutritional yeast" in adaptability.vegan_adaptations
        assert adaptability.easily_healthified
        assert "whole wheat" in adaptability.healthy_adaptations


class TestRecipeCategorization:
    """Test the RecipeCategorization model"""
    
    def test_basic_categorization(self):
        """Test basic categorization creation"""
        categorization = RecipeCategorization(
            health_tags=["vegetarian"],
            dish_type=["salad"],
            cuisine_type=["mediterranean"],
            meal_type=["lunch"],
            season=["summer"]
        )
        
        assert categorization.health_tags == ["vegetarian"]
        assert categorization.dish_type == ["salad"]
        assert categorization.cuisine_type == ["mediterranean"]
        assert categorization.adaptability is not None  # Default factory
    
    def test_categorization_with_adaptability(self):
        """Test categorization with custom adaptability"""
        adaptability = RecipeAdaptability(
            easily_veganizable=True,
            vegan_adaptations="Remove cheese"
        )
        
        categorization = RecipeCategorization(
            health_tags=["vegetarian"],
            adaptability=adaptability
        )
        
        assert categorization.adaptability.easily_veganizable
        assert "Remove cheese" in categorization.adaptability.vegan_adaptations


class TestRecipeSearchFilters:
    """Test the RecipeSearchFilters model"""
    
    def test_default_filters(self):
        """Test default filter values"""
        filters = RecipeSearchFilters()
        
        assert filters.query is None
        assert filters.health_tags == []
        assert filters.limit == 20
        assert filters.offset == 0
        assert filters.show_veganizable is None
    
    def test_filters_with_values(self):
        """Test filters with custom values"""
        filters = RecipeSearchFilters(
            query="pasta",
            health_tags=["vegetarian", "healthy"],
            dish_type=["main course"],
            limit=50,
            offset=10,
            show_veganizable=True
        )
        
        assert filters.query == "pasta"
        assert "vegetarian" in filters.health_tags
        assert filters.limit == 50
        assert filters.show_veganizable
    
    def test_limit_validation(self):
        """Test that limit is validated"""
        # Valid limits
        RecipeSearchFilters(limit=1)
        RecipeSearchFilters(limit=100)
        
        # Invalid limits should raise validation error
        with pytest.raises(ValidationError):
            RecipeSearchFilters(limit=0)
        
        with pytest.raises(ValidationError):
            RecipeSearchFilters(limit=101)
    
    def test_offset_validation(self):
        """Test that offset is validated"""
        # Valid offset
        RecipeSearchFilters(offset=0)
        RecipeSearchFilters(offset=100)
        
        # Invalid offset
        with pytest.raises(ValidationError):
            RecipeSearchFilters(offset=-1)


class TestRecipeStats:
    """Test the RecipeStats model"""
    
    def test_basic_stats(self):
        """Test basic stats creation"""
        stats = RecipeStats(
            total_recipes=100,
            ai_enhanced_count=75,
            ai_enhancement_percentage=75.0,
            top_health_tags=[{"tag": "vegetarian", "count": 30}],
            top_cuisines=[{"cuisine": "italian", "count": 25}],
            top_dish_types=[{"type": "main course", "count": 40}],
            seasonal_distribution={"spring": 25, "summer": 30, "autumn": 25, "winter": 20}
        )
        
        assert stats.total_recipes == 100
        assert stats.ai_enhancement_percentage == 75.0
        assert len(stats.top_health_tags) == 1
        assert stats.seasonal_distribution["summer"] == 30
    
    def test_stats_with_adaptability(self):
        """Test stats with adaptability counts"""
        stats = RecipeStats(
            total_recipes=100,
            ai_enhanced_count=75,
            ai_enhancement_percentage=75.0,
            top_health_tags=[],
            top_cuisines=[],
            top_dish_types=[],
            seasonal_distribution={},
            veganizable_count=20,
            vegetarianizable_count=15,
            healthifiable_count=30,
            adaptability_percentages={
                "veganizable": 20.0,
                "vegetarianizable": 15.0,
                "healthifiable": 30.0
            }
        )
        
        assert stats.veganizable_count == 20
        assert stats.adaptability_percentages["healthifiable"] == 30.0


class TestDebugInfo:
    """Test the DebugInfo model"""
    
    def test_successful_debug_info(self):
        """Test successful debug info"""
        debug = DebugInfo(
            status="success",
            html_length=5000,
            json_scripts_found=2,
            json_scripts_content=[{"script": 1, "content": "test"}],
            ai_available=True
        )
        
        assert debug.status == "success"
        assert debug.html_length == 5000
        assert debug.ai_available
    
    def test_error_debug_info(self):
        """Test error debug info"""
        debug = DebugInfo(
            status="error",
            error="Failed to fetch URL",
            error_type="RequestException"
        )
        
        assert debug.status == "error"
        assert debug.error == "Failed to fetch URL"
        assert debug.html_length is None


class TestHealthResponse:
    """Test the HealthResponse model"""
    
    def test_healthy_response(self):
        """Test healthy response"""
        health = HealthResponse(
            status="healthy",
            ai_available=True,
            ai_model="gpt-3.5-turbo",
            timestamp="2025-01-20T12:00:00Z"
        )
        
        assert health.status == "healthy"
        assert health.ai_available
        assert health.ai_categorization_enabled  # Default True
        assert health.ai_adaptability_enabled  # Default True
    
    def test_unhealthy_response(self):
        """Test response when AI is not available"""
        health = HealthResponse(
            status="unhealthy",
            ai_available=False,
            ai_model=None
        )
        
        assert health.status == "unhealthy"
        assert not health.ai_available
        assert health.ai_model is None
