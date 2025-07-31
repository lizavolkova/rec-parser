# tests/test_services/test_recipe_service.py
"""
Comprehensive tests for RecipeService
"""

import pytest
import requests
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.services.recipe_service import RecipeService
from app.models import Recipe, DebugInfo, StructuredIngredient

# Test constants
MOCK_HTML_CONTENT = "<html>test content</html>"
MOCK_HTML_SIMPLE = "<html>test</html>"


@pytest.fixture
def recipe_service():
    """Create RecipeService instance for testing"""
    return RecipeService()


@pytest.fixture
def mock_response():
    """Mock HTTP response"""
    response = Mock()
    response.text = """
    <html>
        <head>
            <meta property="og:image" content="https://example.com/image.jpg">
            <script type="application/ld+json">
                {"@type": "Recipe", "name": "Test Recipe"}
            </script>
        </head>
        <body>
            <h1>Test Recipe</h1>
        </body>
    </html>
    """
    response.content = response.text.encode()
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_soup():
    """Mock BeautifulSoup object"""
    html = """
    <html>
        <head>
            <meta property="og:image" content="https://example.com/image.jpg">
            <script type="application/ld+json">
                {"@type": "Recipe", "name": "Test Recipe"}
            </script>
        </head>
        <body>
            <h1>Test Recipe</h1>
        </body>
    </html>
    """
    return BeautifulSoup(html, 'html.parser')


@pytest.fixture
def sample_complete_recipe():
    """Sample complete recipe for testing"""
    return Recipe(
        title="Complete Test Recipe",
        description="A complete recipe for testing",
        ingredients=["1 cup flour", "2 eggs", "1 tsp salt"],
        instructions=["Mix ingredients", "Cook for 30 minutes"],
        prep_time="10 minutes",
        cook_time="30 minutes",
        servings="4",
        image="https://example.com/image.jpg",
        source="Test Source",
        raw_ingredients=[],
        raw_ingredients_detailed=[]
    )


@pytest.fixture
def sample_incomplete_recipe():
    """Sample incomplete recipe for testing"""
    return Recipe(
        title="Incomplete Recipe",
        ingredients=["some ingredient"],
        instructions=[],  # Missing instructions
        raw_ingredients=[],
        raw_ingredients_detailed=[]
    )


class TestRecipeServiceInit:
    """Test RecipeService initialization"""
    
    def test_recipe_service_init(self, recipe_service):
        """Test RecipeService initializes correctly"""
        assert recipe_service.recipe_scrapers_parser is not None
        assert recipe_service.extruct_parser is not None


class TestAddRawIngredients:
    """Test _add_raw_ingredients method"""
    
    @patch('app.services.recipe_service.parse_ingredients_list')
    @patch('app.services.recipe_service.get_raw_ingredients_for_search')
    def test_add_raw_ingredients_success(self, mock_get_raw, mock_parse, recipe_service, sample_complete_recipe):
        """Test successful raw ingredients addition"""
        # Mock structured ingredients
        mock_structured_ingredient = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            descriptors=[],
            original_text="1 cup flour",
            confidence=0.95,
            used_fallback=False
        )
        
        mock_parse.return_value = [mock_structured_ingredient]
        mock_get_raw.return_value = ["flour"]
        
        result = recipe_service._add_raw_ingredients(sample_complete_recipe)
        
        assert result.raw_ingredients == ["flour"]
        assert len(result.raw_ingredients_detailed) == 1
        assert result.raw_ingredients_detailed[0]["name"] == "flour"
        assert result.raw_ingredients_detailed[0]["quantity"] == "1"
        assert result.raw_ingredients_detailed[0]["unit"] == "cup"
        
        mock_parse.assert_called_once_with(sample_complete_recipe.ingredients)
        mock_get_raw.assert_called_once()
    
    def test_add_raw_ingredients_no_ingredients(self, recipe_service):
        """Test with recipe that has no ingredients"""
        recipe = Recipe(
            title="No Ingredients Recipe",
            ingredients=[],
            instructions=["Just instructions"],
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        result = recipe_service._add_raw_ingredients(recipe)
        
        assert result.raw_ingredients == []
        assert result.raw_ingredients_detailed == []
    
    @patch('app.services.recipe_service.parse_ingredients_list')
    def test_add_raw_ingredients_parse_error(self, mock_parse, recipe_service, sample_complete_recipe):
        """Test handling of parsing errors"""
        mock_parse.side_effect = Exception("Parsing failed")
        
        result = recipe_service._add_raw_ingredients(sample_complete_recipe)
        
        assert result.raw_ingredients == []
        assert result.raw_ingredients_detailed == []


class TestFetchPage:
    """Test _fetch_page method"""
    
    @patch('app.services.recipe_service.requests.get')
    def test_fetch_page_success(self, mock_get, recipe_service, mock_response):
        """Test successful page fetching"""
        mock_get.return_value = mock_response
        
        response, soup = recipe_service._fetch_page("https://example.com/recipe")
        
        assert response == mock_response
        assert isinstance(soup, BeautifulSoup)
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    
    @patch('app.services.recipe_service.requests.get')
    def test_fetch_page_http_error(self, mock_get, recipe_service):
        """Test HTTP error during page fetching"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            recipe_service._fetch_page("https://example.com/nonexistent")


class TestEnsureImageAndSource:
    """Test _ensure_image_and_source method"""
    
    def test_ensure_image_and_source_complete(self, recipe_service):
        """Test with recipe that already has image and source"""
        recipe = Recipe(
            title="Complete Recipe",
            image="https://example.com/existing.jpg",
            source="Existing Source",
            ingredients=["flour"],
            instructions=["cook"],
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        result = recipe_service._ensure_image_and_source(
            recipe, 
            "https://example.com/fallback.jpg", 
            "https://example.com/recipe"
        )
        
        assert result.image == "https://example.com/existing.jpg"  # Should keep existing
        assert result.source == "Existing Source"  # Should keep existing
    
    def test_ensure_image_and_source_missing(self, recipe_service):
        """Test with recipe missing image and source"""
        recipe = Recipe(
            title="Incomplete Recipe",
            image=None,
            source=None,
            ingredients=["flour"],
            instructions=["cook"],
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        result = recipe_service._ensure_image_and_source(
            recipe, 
            "https://example.com/fallback.jpg", 
            "https://loveandlemons.com/recipe"
        )
        
        assert result.image == "https://example.com/fallback.jpg"  # Should use fallback
        assert result.source == "Love and Lemons"  # Should extract from URL
    
    def test_ensure_image_and_source_no_fallbacks(self, recipe_service):
        """Test with no fallback image or recognizable URL"""
        recipe = Recipe(
            title="Recipe",
            image=None,
            source=None,
            ingredients=["flour"],
            instructions=["cook"],
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        result = recipe_service._ensure_image_and_source(
            recipe, 
            None, 
            "https://unknown-site.com/recipe"
        )
        
        assert result.image is None
        assert result.source == "Unknown Site"  # Should create generic source


class TestExtractSourceFromUrl:
    """Test _extract_source_from_url method"""
    
    def test_extract_source_known_domains(self, recipe_service):
        """Test extraction from known recipe domains"""
        test_cases = [
            ("https://www.loveandlemons.com/recipe", "Love and Lemons"),
            ("https://allrecipes.com/recipe/123", "Allrecipes"),
            ("https://www.foodnetwork.com/recipes", "Food Network"),
            ("https://seriouseats.com/recipe", "Serious Eats"),
        ]
        
        for url, expected_source in test_cases:
            result = recipe_service._extract_source_from_url(url)
            assert result == expected_source
    
    def test_extract_source_unknown_domain(self, recipe_service):
        """Test extraction from unknown domains"""
        test_cases = [
            ("https://my-food-blog.com/recipe", "My Food Blog"),
            ("https://www.awesome-recipes.net/recipe", "Awesome Recipes"),
            ("https://chef-john.org/recipe", "Chef John"),
        ]
        
        for url, expected_source in test_cases:
            result = recipe_service._extract_source_from_url(url)
            assert result == expected_source
    
    def test_extract_source_invalid_url(self, recipe_service):
        """Test extraction from invalid URL"""
        result = recipe_service._extract_source_from_url("not-a-url")
        assert result is None


class TestDebugRecipe:
    """Test debug_recipe static method"""
    
    @patch.object(RecipeService, '_fetch_page')
    @patch('app.services.recipe_service.ImageExtractor.extract_og_image')
    def test_debug_recipe_success(self, mock_extract_image, mock_fetch_page, mock_soup):
        """Test successful recipe debugging"""
        mock_response = Mock()
        mock_response.content = MOCK_HTML_CONTENT.encode()
        mock_fetch_page.return_value = (mock_response, mock_soup)
        mock_extract_image.return_value = "https://example.com/image.jpg"
        
        result = RecipeService.debug_recipe("https://example.com/recipe")
        
        assert isinstance(result, DebugInfo)
        assert result.status == "success"
        assert result.html_length == len(mock_response.content)
        assert result.json_scripts_found == 1  # One script in mock_soup
        assert len(result.json_scripts_content) == 1
        assert result.json_scripts_content[0]["og_image_found"] == "https://example.com/image.jpg"
    
    @patch.object(RecipeService, '_fetch_page')
    def test_debug_recipe_error(self, mock_fetch_page):
        """Test debug recipe with error"""
        mock_fetch_page.side_effect = Exception("Network error")
        
        result = RecipeService.debug_recipe("https://example.com/recipe")
        
        assert isinstance(result, DebugInfo)
        assert result.status == "error"
        assert result.error == "Network error"
        assert result.error_type == "Exception"


class TestParseRecipeHybrid:
    """Test parse_recipe_hybrid method"""
    
    @pytest.mark.asyncio
    @patch.object(RecipeService, '_fetch_page')
    @patch('app.services.recipe_service.ImageExtractor.extract_og_image')
    async def test_parse_recipe_hybrid_recipe_scrapers_success(self, mock_extract_image, mock_fetch_page, mock_response, mock_soup, sample_complete_recipe):
        """Test successful parsing with recipe-scrapers"""
        mock_fetch_page.return_value = (mock_response, mock_soup)
        mock_extract_image.return_value = "https://example.com/image.jpg"
        
        with patch.object(RecipeService, '_add_raw_ingredients') as mock_add_raw:
            mock_add_raw.return_value = sample_complete_recipe
            
            with patch('app.services.recipe_service.RecipeScrapersParser') as mock_parser_class:
                mock_parser = Mock()
                mock_parser.parse.return_value = sample_complete_recipe
                mock_parser_class.return_value = mock_parser
                
                with patch('app.services.recipe_service.RecipeConverter.is_complete_recipe', return_value=True):
                    result = await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert result.title == sample_complete_recipe.title
        mock_add_raw.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(RecipeService, '_fetch_page')
    @patch('app.services.recipe_service.ImageExtractor.extract_og_image')
    async def test_parse_recipe_hybrid_extruct_fallback(self, mock_extract_image, mock_fetch_page, mock_response, mock_soup, sample_complete_recipe):
        """Test fallback to extruct when recipe-scrapers fails"""
        mock_fetch_page.return_value = (mock_response, mock_soup)
        mock_extract_image.return_value = "https://example.com/image.jpg"
        
        with patch.object(RecipeService, '_add_raw_ingredients') as mock_add_raw:
            mock_add_raw.return_value = sample_complete_recipe
            
            with patch('app.services.recipe_service.RecipeScrapersParser') as mock_scrapers_class:
                mock_scrapers = Mock()
                mock_scrapers.parse.return_value = None  # Fail recipe-scrapers
                mock_scrapers_class.return_value = mock_scrapers
                
                with patch('app.services.recipe_service.ExtructParser') as mock_extruct_class:
                    mock_extruct = Mock()
                    mock_extruct.parse.return_value = sample_complete_recipe
                    mock_extruct_class.return_value = mock_extruct
                    
                    with patch('app.services.recipe_service.RecipeConverter.is_complete_recipe', return_value=True):
                        result = await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert result.title == sample_complete_recipe.title
        mock_add_raw.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(RecipeService, '_fetch_page')
    @patch('app.services.recipe_service.ImageExtractor.extract_og_image')
    @patch('app.services.recipe_service.parse_with_ai')
    async def test_parse_recipe_hybrid_ai_fallback(self, mock_parse_ai, mock_extract_image, mock_fetch_page, mock_response, mock_soup, sample_complete_recipe):
        """Test fallback to AI when structured parsing fails"""
        mock_fetch_page.return_value = (mock_response, mock_soup)
        mock_extract_image.return_value = "https://example.com/image.jpg"
        mock_parse_ai.return_value = sample_complete_recipe
        
        with patch.object(RecipeService, '_add_raw_ingredients') as mock_add_raw:
            mock_add_raw.return_value = sample_complete_recipe
            
            with patch('app.services.recipe_service.RecipeScrapersParser') as mock_scrapers_class:
                mock_scrapers = Mock()
                mock_scrapers.parse.return_value = None
                mock_scrapers_class.return_value = mock_scrapers
                
                with patch('app.services.recipe_service.ExtructParser') as mock_extruct_class:
                    mock_extruct = Mock()
                    mock_extruct.parse.return_value = None
                    mock_extruct_class.return_value = mock_extruct
                    
                    with patch('app.services.recipe_service.RecipeConverter.is_complete_recipe', return_value=True):
                        result = await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert result.title == sample_complete_recipe.title
        mock_parse_ai.assert_called_once()
        mock_add_raw.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(RecipeService, '_fetch_page')
    @patch('app.services.recipe_service.ImageExtractor.extract_og_image')
    @patch('app.services.recipe_service.parse_with_ai')
    async def test_parse_recipe_hybrid_all_fail(self, mock_parse_ai, mock_extract_image, mock_fetch_page, mock_response, mock_soup):
        """Test when all parsing methods fail"""
        mock_fetch_page.return_value = (mock_response, mock_soup)
        mock_extract_image.return_value = "https://example.com/image.jpg"
        mock_parse_ai.return_value = None
        
        with patch('app.services.recipe_service.RecipeScrapersParser') as mock_scrapers_class:
            mock_scrapers = Mock()
            mock_scrapers.parse.return_value = None
            mock_scrapers_class.return_value = mock_scrapers
            
            with patch('app.services.recipe_service.ExtructParser') as mock_extruct_class:
                mock_extruct = Mock()
                mock_extruct.parse.return_value = None
                mock_extruct_class.return_value = mock_extruct
                
                result = await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert result.title == "Unable to parse recipe"
        assert result.image == "https://example.com/image.jpg"  # Should still have og:image
        assert "Could not extract" in result.ingredients[0]
    
    @pytest.mark.asyncio
    @patch.object(RecipeService, '_fetch_page')
    async def test_parse_recipe_hybrid_http_error(self, mock_fetch_page):
        """Test handling of HTTP errors"""
        mock_fetch_page.side_effect = Exception("Network error")
        
        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert exc_info.value.status_code == 500
        assert "Network error" in str(exc_info.value.detail)


class TestIntegration:
    """Integration tests for RecipeService"""
    
    @pytest.mark.asyncio
    async def test_full_recipe_parsing_workflow(self, sample_complete_recipe):
        """Test the complete recipe parsing workflow with mocked dependencies"""
        
        # Mock all external dependencies
        with patch.object(RecipeService, '_fetch_page') as mock_fetch:
            mock_response = Mock()
            mock_response.text = MOCK_HTML_SIMPLE
            mock_soup = BeautifulSoup(MOCK_HTML_SIMPLE, 'html.parser')
            mock_fetch.return_value = (mock_response, mock_soup)
            
            with patch('app.services.recipe_service.ImageExtractor.extract_og_image', return_value="https://example.com/image.jpg"):
                with patch('app.services.recipe_service.RecipeScrapersParser') as mock_scrapers_class:
                    mock_scrapers = Mock()
                    mock_scrapers.parse.return_value = sample_complete_recipe
                    mock_scrapers_class.return_value = mock_scrapers
                    
                    with patch('app.services.recipe_service.RecipeConverter.is_complete_recipe', return_value=True):
                        with patch('app.services.recipe_service.parse_ingredients_list', return_value=[]):
                            with patch('app.services.recipe_service.get_raw_ingredients_for_search', return_value=[]):
                                
                                result = await RecipeService.parse_recipe_hybrid("https://example.com/recipe")
        
        assert result is not None
        assert result.title == sample_complete_recipe.title
        assert isinstance(result.raw_ingredients, list)
        assert isinstance(result.raw_ingredients_detailed, list)