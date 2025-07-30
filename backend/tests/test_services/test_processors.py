# tests/test_services/test_processors.py
"""
Tests for processor modules
"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from app.services.processors.image_extractor import ImageExtractor
from app.services.processors.instruction_processor import InstructionProcessor  
from app.services.processors.recipe_converter import RecipeConverter
from app.models import Recipe


class TestImageExtractor:
    """Test ImageExtractor functionality"""
    
    def test_extract_og_image_success(self):
        """Test successful og:image extraction"""
        html = '''
        <html>
            <head>
                <meta property="og:image" content="https://example.com/recipe-image.jpg">
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ImageExtractor.extract_og_image(soup)
        assert result == "https://example.com/recipe-image.jpg"
    
    def test_extract_og_image_fallback_to_twitter(self):
        """Test fallback to twitter:image when og:image not available"""
        html = '''
        <html>
            <head>
                <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ImageExtractor.extract_og_image(soup)
        assert result == "https://example.com/twitter-image.jpg"
    
    def test_extract_og_image_prefer_og_over_twitter(self):
        """Test that og:image is preferred over twitter:image when both exist"""
        html = '''
        <html>
            <head>
                <meta property="og:image" content="https://example.com/og-image.jpg">
                <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ImageExtractor.extract_og_image(soup)
        assert result == "https://example.com/og-image.jpg"
    
    def test_extract_og_image_no_image(self):
        """Test when no image meta tags are present"""
        html = '''
        <html>
            <head>
                <title>No Images Here</title>
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ImageExtractor.extract_og_image(soup)
        assert result is None
    
    def test_extract_og_image_empty_content(self):
        """Test when image meta tags have empty content"""
        html = '''
        <html>
            <head>
                <meta property="og:image" content="">
                <meta name="twitter:image" content="">
            </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ImageExtractor.extract_og_image(soup)
        assert result is None
    
    def test_extract_from_structured_data_string_url(self):
        """Test extraction from simple string URL"""
        result = ImageExtractor.extract_from_structured_data("https://example.com/image.jpg")
        assert result == "https://example.com/image.jpg"
    
    def test_extract_from_structured_data_invalid_string(self):
        """Test extraction from invalid string (not HTTP URL)"""
        result = ImageExtractor.extract_from_structured_data("not-a-url")
        assert result is None
    
    def test_extract_from_structured_data_object_with_url(self):
        """Test extraction from object with url property"""
        image_data = {"url": "https://example.com/structured-image.jpg"}
        result = ImageExtractor.extract_from_structured_data(image_data)
        assert result == "https://example.com/structured-image.jpg"
    
    def test_extract_from_structured_data_array_of_strings(self):
        """Test extraction from array of strings (takes first valid one)"""
        image_data = [
            "not-a-url",
            "https://example.com/first-valid.jpg",
            "https://example.com/second-valid.jpg"
        ]
        result = ImageExtractor.extract_from_structured_data(image_data)
        assert result == "https://example.com/first-valid.jpg"
    
    def test_extract_from_structured_data_array_of_objects(self):
        """Test extraction from array of objects"""
        image_data = [
            {"url": "https://example.com/object-image.jpg"},
            {"url": "https://example.com/second-image.jpg"}
        ]
        result = ImageExtractor.extract_from_structured_data(image_data)
        assert result == "https://example.com/object-image.jpg"
    
    def test_extract_from_structured_data_none(self):
        """Test extraction when data is None"""
        result = ImageExtractor.extract_from_structured_data(None)
        assert result is None
    
    def test_extract_from_structured_data_empty_array(self):
        """Test extraction from empty array"""
        result = ImageExtractor.extract_from_structured_data([])
        assert result is None


class TestInstructionProcessor:
    """Test InstructionProcessor functionality"""
    
    def test_process_instructions_list_of_strings(self):
        """Test processing simple list of instruction strings"""
        instructions = [
            "Preheat oven to 350°F",
            "Mix flour and sugar",
            "Bake for 30 minutes"
        ]
        
        result = InstructionProcessor.process_instructions(instructions)
        
        assert result == instructions
        assert len(result) == 3
    
    def test_process_instructions_list_of_objects(self):
        """Test processing list of instruction objects with text property"""
        instructions = [
            {"@type": "HowToStep", "text": "Preheat oven to 350°F"},
            {"@type": "HowToStep", "text": "Mix ingredients"},
            {"@type": "HowToStep", "text": "Bake until golden"}
        ]
        
        result = InstructionProcessor.process_instructions(instructions)
        
        expected = [
            "Preheat oven to 350°F",
            "Mix ingredients", 
            "Bake until golden"
        ]
        assert result == expected
    
    def test_process_instructions_mixed_format(self):
        """Test processing mixed format (strings and objects)"""
        instructions = [
            "First step as string",
            {"@type": "HowToStep", "text": "Second step as object"},
            "Third step as string"
        ]
        
        result = InstructionProcessor.process_instructions(instructions)
        
        expected = [
            "First step as string",
            "Second step as object",
            "Third step as string"
        ]
        assert result == expected
    
    def test_process_instructions_objects_without_text(self):
        """Test processing objects that don't have text property"""
        instructions = [
            {"@type": "HowToStep", "name": "Step without text"},
            {"@type": "HowToStep", "text": "Step with text"},
            {"@type": "HowToStep"}  # Object with no text at all
        ]
        
        result = InstructionProcessor.process_instructions(instructions)
        
        # Should skip objects without text and only return valid ones
        expected = ["Step with text"]
        assert result == expected
    
    def test_process_instructions_empty_list(self):
        """Test processing empty instruction list"""
        result = InstructionProcessor.process_instructions([])
        assert result == []
    
    def test_process_instructions_none(self):
        """Test processing None instructions"""
        result = InstructionProcessor.process_instructions(None)
        assert result == []
    
    def test_process_instructions_single_string(self):
        """Test processing single string instruction"""
        result = InstructionProcessor.process_instructions("Single instruction")
        assert result == ["Single instruction"]
    
    def test_process_instructions_nested_arrays(self):
        """Test processing nested instruction arrays (flattens them)"""
        instructions = [
            ["Step 1", "Step 2"],
            "Step 3",
            [{"@type": "HowToStep", "text": "Step 4"}]
        ]
        
        result = InstructionProcessor.process_instructions(instructions)
        
        expected = ["Step 1", "Step 2", "Step 3", "Step 4"]
        assert result == expected


class TestRecipeConverter:
    """Test RecipeConverter functionality"""
    
    def test_convert_json_ld_to_recipe(self):
        """Test converting JSON-LD structured data to Recipe"""
        recipe_data = {
            "@type": "Recipe",
            "name": "Test Recipe",
            "description": "A delicious test recipe",
            "recipeIngredient": ["1 cup flour", "2 eggs", "1 tsp salt"],
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "Mix ingredients"},
                {"@type": "HowToStep", "text": "Cook until done"}
            ],
            "image": "https://example.com/recipe-image.jpg",
            "prepTime": "PT10M",
            "cookTime": "PT30M",
            "recipeYield": "4 servings",
            "recipeCategory": "Main Course",
            "recipeCuisine": "American"
        }
        
        with patch('app.services.processors.recipe_converter.ImageExtractor.extract_from_structured_data') as mock_image:
            mock_image.return_value = "https://example.com/recipe-image.jpg"
            
            with patch('app.services.processors.recipe_converter.InstructionProcessor.process_instructions') as mock_instructions:
                mock_instructions.return_value = ["Mix ingredients", "Cook until done"]
                
                result = RecipeConverter.convert_structured_data_to_recipe(recipe_data)
        
        assert isinstance(result, Recipe)
        assert result.title == "Test Recipe"
        assert result.description == "A delicious test recipe"
        assert result.ingredients == ["1 cup flour", "2 eggs", "1 tsp salt"]
        assert result.instructions == ["Mix ingredients", "Cook until done"]
        assert result.image == "https://example.com/recipe-image.jpg"
        assert result.prep_time == "10 minutes"
        assert result.cook_time == "30 minutes"
        assert result.servings == "4 servings"
        assert result.category == "Main Course"
        assert result.cuisine == "American"
        assert result.found_structured_data is True
        assert result.used_ai is False
    
    def test_convert_microdata_to_recipe(self):
        """Test converting microdata structured data to Recipe"""
        recipe_data = {
            "type": "http://schema.org/Recipe",
            "properties": {
                "name": ["Microdata Test Recipe"],
                "description": ["Recipe from microdata"],
                "recipeIngredient": ["ingredient 1", "ingredient 2"],
                "recipeInstructions": ["step 1", "step 2"]
            }
        }
        
        with patch('app.services.processors.recipe_converter.ImageExtractor.extract_from_structured_data'):
            with patch('app.services.processors.recipe_converter.InstructionProcessor.process_instructions') as mock_instructions:
                mock_instructions.return_value = ["step 1", "step 2"]
                
                result = RecipeConverter.convert_structured_data_to_recipe(recipe_data)
        
        assert result.title == "Microdata Test Recipe"
        assert result.description == "Recipe from microdata"
        assert result.ingredients == ["ingredient 1", "ingredient 2"]
        assert result.instructions == ["step 1", "step 2"]
    
    def test_convert_minimal_data(self):
        """Test converting with minimal required data"""
        recipe_data = {
            "@type": "Recipe"
            # Missing name, ingredients, instructions
        }
        
        with patch('app.services.processors.recipe_converter.ImageExtractor.extract_from_structured_data'):
            with patch('app.services.processors.recipe_converter.InstructionProcessor.process_instructions') as mock_instructions:
                mock_instructions.return_value = []
                
                result = RecipeConverter.convert_structured_data_to_recipe(recipe_data)
        
        assert result.title == "Untitled Recipe"  # Fallback title
        assert result.ingredients == []
        assert result.instructions == []
    
    def test_is_complete_recipe_true(self):
        """Test recipe completeness check for complete recipe"""
        complete_recipe = Recipe(
            title="Complete Recipe",
            ingredients=["flour", "eggs", "sugar"],
            instructions=["mix", "bake", "cool"],
            prep_time="10 minutes",
            cook_time="30 minutes",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        assert RecipeConverter.is_complete_recipe(complete_recipe) is True
    
    def test_is_complete_recipe_false(self):
        """Test recipe completeness check for incomplete recipe"""
        incomplete_recipe = Recipe(
            title="Incomplete Recipe", 
            ingredients=["flour"],  # Only one ingredient
            instructions=[],  # No instructions
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        assert RecipeConverter.is_complete_recipe(incomplete_recipe) is False
    
    def test_is_good_enough_recipe_true(self):
        """Test good enough recipe check"""
        good_enough_recipe = Recipe(
            title="Good Enough Recipe",
            ingredients=["flour", "eggs"],  # At least 2 ingredients
            instructions=["mix and bake"],  # At least 1 instruction
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        assert RecipeConverter.is_good_enough_recipe(good_enough_recipe) is True
    
    def test_is_good_enough_recipe_false(self):
        """Test good enough recipe check for poor recipe"""
        poor_recipe = Recipe(
            title="Poor Recipe",
            ingredients=[],  # No ingredients
            instructions=[],  # No instructions
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        assert RecipeConverter.is_good_enough_recipe(poor_recipe) is False
    
    def test_get_value_helper_simple_string(self):
        """Test _get_value helper with simple string"""
        data = {"name": "Simple Recipe"}
        result = RecipeConverter._get_value(data, "name")
        assert result == "Simple Recipe"
    
    def test_get_value_helper_array(self):
        """Test _get_value helper with array (microdata format)"""
        data = {"name": ["Array Recipe"]}
        result = RecipeConverter._get_value(data, "name")
        assert result == "Array Recipe"
    
    def test_get_value_helper_missing_key(self):
        """Test _get_value helper with missing key"""
        data = {"title": "Recipe"}
        result = RecipeConverter._get_value(data, "name")
        assert result is None
    
    def test_clean_ingredients_removes_empty(self):
        """Test ingredient cleaning removes empty strings"""
        ingredients = ["1 cup flour", "", "2 eggs", "   ", "1 tsp salt"]
        result = RecipeConverter._clean_ingredients(ingredients)
        assert result == ["1 cup flour", "2 eggs", "1 tsp salt"]
    
    def test_extract_source_from_publisher(self):
        """Test source extraction from publisher field"""
        data = {"publisher": {"name": "Food Network"}}
        result = RecipeConverter._extract_source(data)
        assert result == "Food Network"
    
    def test_extract_source_from_author(self):
        """Test source extraction from author when no publisher"""
        data = {"author": {"name": "Chef John"}}
        result = RecipeConverter._extract_source(data)
        assert result == "Chef John"
    
    def test_extract_source_none(self):
        """Test source extraction when no publisher or author"""
        data = {"name": "Recipe"}
        result = RecipeConverter._extract_source(data)
        assert result is None


class TestProcessorIntegration:
    """Integration tests for processors working together"""
    
    def test_full_conversion_workflow(self):
        """Test complete conversion workflow from structured data to Recipe"""
        structured_data = {
            "@type": "Recipe",
            "name": "Integration Test Recipe",
            "description": "Testing full conversion",
            "recipeIngredient": ["flour", "sugar", "eggs"],
            "recipeInstructions": [
                {"@type": "HowToStep", "text": "Mix dry ingredients"},
                "Add eggs and mix",
                {"@type": "HowToStep", "text": "Bake until golden"}
            ],
            "image": [
                {"url": "https://example.com/recipe-image.jpg"},
                "https://example.com/backup-image.jpg"
            ],
            "prepTime": "PT15M",
            "cookTime": "PT45M",
            "publisher": {"name": "Test Kitchen"}
        }
        
        # This should use all processors together
        result = RecipeConverter.convert_structured_data_to_recipe(structured_data)
        
        assert result.title == "Integration Test Recipe"
        assert result.description == "Testing full conversion"
        assert len(result.ingredients) == 3
        assert len(result.instructions) == 3
        assert result.instructions[0] == "Mix dry ingredients"
        assert result.instructions[1] == "Add eggs and mix"
        assert result.instructions[2] == "Bake until golden"
        assert result.image == "https://example.com/recipe-image.jpg"
        assert result.prep_time == "15 minutes"
        assert result.cook_time == "45 minutes"
        assert result.source == "Test Kitchen"
        assert result.found_structured_data is True