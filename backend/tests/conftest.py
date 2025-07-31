# tests/conftest.py
"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from typing import Generator

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), "..")
backend_path = os.path.abspath(backend_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now import after path is set
try:
    from app.models import Recipe, StructuredIngredient
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Backend path: {backend_path}")
    print(f"Current directory: {os.getcwd()}")
    raise


@pytest.fixture
def sample_recipe() -> Recipe:
    """Fixture providing a sample recipe for testing"""
    return Recipe(
        title="Farro Salad with Parmesan",
        description="A healthy grain salad with cheese",
        ingredients=[
            "1 cup farro",
            "1/4 cup parmesan cheese, grated", 
            "2 tbsp olive oil",
            "1 tbsp lemon juice",
            "Salt and pepper to taste"
        ],
        instructions=[
            "Cook farro according to package directions",
            "Mix with parmesan, olive oil, and lemon juice",
            "Season with salt and pepper"
        ],
        prep_time="10 minutes",
        cook_time="20 minutes",
        servings="4",
        raw_ingredients=[],
        raw_ingredients_detailed=[],
        found_structured_data=False,
        used_ai=False
    )


@pytest.fixture
def vegan_recipe() -> Recipe:
    """Fixture providing a vegan recipe for testing"""
    return Recipe(
        title="Quinoa Vegetable Bowl",
        description="A nutritious vegan bowl",
        ingredients=[
            "1 cup quinoa",
            "2 cups vegetable broth",
            "1 cup chickpeas",
            "2 tbsp olive oil",
            "1 tbsp lemon juice",
            "Fresh herbs"
        ],
        instructions=[
            "Cook quinoa in vegetable broth",
            "Mix with chickpeas and herbs",
            "Dress with olive oil and lemon"
        ],
        raw_ingredients=[],
        raw_ingredients_detailed=[],
        found_structured_data=False,
        used_ai=False
    )


@pytest.fixture
def eggplant_recipe() -> Recipe:
    """Fixture providing a recipe with eggplant (to test parsing issues)"""
    return Recipe(
        title="Mediterranean Eggplant",
        ingredients=[
            "2 medium eggplant, diced",
            "3 tbsp olive oil",
            "1 onion, chopped",
            "2 cloves garlic, minced"
        ],
        instructions=["Cook eggplant with oil and aromatics"],
        raw_ingredients=[],
        raw_ingredients_detailed=[],
        found_structured_data=False,
        used_ai=False
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing AI functionality"""
    with patch('app.config.openai_client') as mock_client:
        # Create a mock response structure
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        
        mock_message.content = """
        {
            "health_tags": ["vegetarian"],
            "dish_type": ["salad"],
            "cuisine_type": ["mediterranean"],
            "meal_type": ["lunch"],
            "season": ["spring", "summer"],
            "confidence_notes": "This is vegetarian due to parmesan cheese",
            "confidence_notes_user": "A healthy Mediterranean grain salad"
        }
        """
        
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def sample_structured_ingredients() -> list[StructuredIngredient]:
    """Fixture providing sample structured ingredients"""
    return [
        StructuredIngredient(
            raw_ingredient="farro",
            quantity="1",
            unit="cup",
            descriptors=[],
            original_text="1 cup farro",
            confidence=0.95,
            used_fallback=False
        ),
        StructuredIngredient(
            raw_ingredient="parmesan cheese",
            quantity="1/4",
            unit="cup",
            descriptors=["grated"],
            original_text="1/4 cup parmesan cheese, grated",
            confidence=0.90,
            used_fallback=False
        )
    ]


@pytest.fixture
def mock_requests():
    """Mock requests for web scraping tests"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Mock HTML content</body></html>'
        mock_response.content = mock_response.text.encode()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def test_client():
    """Shared test client fixture for FastAPI application"""
    try:
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    except ImportError as e:
        pytest.skip(f"Cannot import main module: {e}")


@pytest.fixture
def sample_recipe_url():
    """Shared sample recipe URL for testing"""
    from app.models import RecipeURL
    return RecipeURL(url="https://example.com/recipe")
