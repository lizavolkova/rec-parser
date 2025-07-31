# tests/test_services/test_parsers.py
"""
Tests for parser modules
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from app.services.parsers.base import BaseParser
from app.services.parsers.recipe_scraper import RecipeScrapersParser
from app.services.parsers.extruct import ExtructParser
from app.models import Recipe


class TestBaseParser:
    """Test BaseParser abstract class"""
    
    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseParser()
    
    def test_base_parser_interface(self):
        """Test that BaseParser defines the correct interface"""
        # Create a concrete implementation for testing
        class ConcreteParser(BaseParser):
            def parse(self, url: str, **kwargs) -> Optional[Recipe]:
                return None
            
            def can_parse(self, url: str) -> bool:
                return True
            
            @property
            def name(self) -> str:
                return "test-parser"
        
        parser = ConcreteParser()
        assert parser.parse("https://example.com") is None
        assert parser.can_parse("https://example.com") is True
        assert parser.name == "test-parser"


class TestRecipeScrapersParser:
    """Test RecipeScrapersParser"""
    
    @pytest.fixture
    def parser(self):
        return RecipeScrapersParser()
    
    def test_parser_name(self, parser):
        """Test parser name property"""
        assert parser.name == "recipe-scrapers"
    
    def test_can_parse_any_url(self, parser):
        """Test that parser claims it can parse any URL"""
        assert parser.can_parse("https://example.com") is True
        assert parser.can_parse("https://allrecipes.com/recipe/123") is True
        assert parser.can_parse("not-a-url") is True  # It will try anything
    
    @patch('app.services.parsers.recipe_scraper.scrape_me')
    def test_parse_success(self, mock_scrape_me, parser):
        """Test successful recipe parsing"""
        # Mock the scraper object
        mock_scraper = Mock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.ingredients.return_value = ["1 cup flour", "2 eggs"]
        mock_scraper.instructions_list.return_value = ["Mix ingredients", "Cook"]
        mock_scraper.description.return_value = "A test recipe"
        mock_scraper.image.return_value = "https://example.com/image.jpg"
        mock_scraper.cuisine.return_value = "American"
        mock_scraper.category.return_value = "Main Course"
        mock_scraper.prep_time.return_value = 10
        mock_scraper.cook_time.return_value = 30
        mock_scraper.total_time.return_value = 40
        mock_scraper.yields.return_value = "4 servings"
        
        mock_scrape_me.return_value = mock_scraper
        
        result = parser.parse("https://example.com/recipe")
        
        assert result is not None
        assert result.title == "Test Recipe"
        assert result.ingredients == ["1 cup flour", "2 eggs"]
        assert result.instructions == ["Mix ingredients", "Cook"]
        assert result.description == "A test recipe"
        assert result.image == "https://example.com/image.jpg"
        assert result.cuisine == "American"
        assert result.category == "Main Course"
        assert result.prep_time == "10"
        assert result.cook_time == "30"
        assert result.servings == "4 servings"
        assert result.found_structured_data is True
        assert result.used_ai is False
        
        mock_scrape_me.assert_called_once_with("https://example.com/recipe")
    
    @patch('app.services.parsers.recipe_scraper.scrape_me')
    def test_parse_scrape_me_failure(self, mock_scrape_me, parser):
        """Test when scrape_me itself fails"""
        mock_scrape_me.side_effect = Exception("Scraping failed")
        
        result = parser.parse("https://example.com/recipe")
        
        assert result is None
    
    def test_safe_extract_method(self, parser):
        """Test the _safe_extract helper method"""
        # Create a mock function that works
        def working_func():
            return "success"
        
        assert parser._safe_extract(working_func) == "success"
        
        # Create a mock function that throws exception
        def failing_func():
            raise Exception("Error")
        
        assert parser._safe_extract(failing_func) is None
        
        # Test with None
        assert parser._safe_extract(None) is None


class TestExtructParser:
    """Test ExtructParser"""
    
    @pytest.fixture
    def parser(self):
        return ExtructParser()
    
    def test_parser_name(self, parser):
        """Test parser name property"""
        assert parser.name == "extruct"
    
    def test_can_parse_any_url(self, parser):
        """Test that parser claims it can parse any URL"""
        assert parser.can_parse("https://example.com") is True
        assert parser.can_parse("https://food.com/recipe") is True


class TestParserIntegration:
    """Integration tests for parsers"""
    
    def test_parser_inheritance(self):
        """Test that concrete parsers properly inherit from BaseParser"""
        recipe_scrapers_parser = RecipeScrapersParser()
        extruct_parser = ExtructParser()
        
        assert isinstance(recipe_scrapers_parser, BaseParser)
        assert isinstance(extruct_parser, BaseParser)
        
        # Test that they implement required methods
        assert hasattr(recipe_scrapers_parser, 'parse')
        assert hasattr(recipe_scrapers_parser, 'can_parse')
        assert hasattr(recipe_scrapers_parser, 'name')
        
        assert hasattr(extruct_parser, 'parse')
        assert hasattr(extruct_parser, 'can_parse')
        assert hasattr(extruct_parser, 'name')
    
    def test_parser_names_are_unique(self):
        """Test that different parsers have unique names"""
        recipe_scrapers_parser = RecipeScrapersParser()
        extruct_parser = ExtructParser()
        
        assert recipe_scrapers_parser.name != extruct_parser.name
        assert recipe_scrapers_parser.name == "recipe-scrapers"
        assert extruct_parser.name == "extruct"