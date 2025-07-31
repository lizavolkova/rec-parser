# Testing Guide

This document explains how to run and write tests for the Recipe Parser API.

## Setup

The project uses pytest as the testing framework. All testing dependencies are managed through Poetry.

### Install Testing Dependencies

```bash
cd backend
poetry install  # Installs all dependencies including dev dependencies
```

## Running Tests

### Basic Commands

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_ingredient_parser.py

# Run specific test function
poetry run pytest tests/test_ingredient_parser.py::TestFractionHandling::test_unicode_to_fraction_conversion

# Run tests matching a pattern
poetry run pytest -k "fraction"
```

### Using the Test Runner Script

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests  
python run_tests.py --integration

# Skip slow tests
python run_tests.py --fast

# Run with coverage report
python run_tests.py --coverage

# Run specific file
python run_tests.py --file test_ingredient_parser.py

# Run specific test
python run_tests.py --test "test_eggplant_protection"
```

### Using Poetry Scripts

```bash
# Predefined scripts in pyproject.toml
poetry run test          # Run all tests
poetry run test-unit     # Run unit tests only
poetry run test-integration  # Run integration tests only
poetry run test-fast     # Skip slow tests
poetry run test-coverage # Run with coverage report
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may use external APIs)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.ai` - Tests requiring OpenAI API key

### Running Specific Markers

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"

# Skip AI tests (useful when no API key available)
poetry run pytest -m "not ai"
```

## Test Coverage

### Generate Coverage Report

```bash
# HTML report (opens in browser)
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
poetry run pytest --cov=app --cov-report=term

# XML report (for CI)
poetry run pytest --cov=app --cov-report=xml
```

### Coverage Thresholds

The project aims for:
- Overall coverage: >85%
- Unit test coverage: >90% 
- Critical modules (ingredient_parser, ai services): >95%

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_models.py           # Test Pydantic models
├── test_ingredient_parser.py # Test ingredient parsing (comprehensive)
├── test_ai/
│   ├── __init__.py
│   ├── test_recipe_categorizer.py
│   └── test_ai_integration.py
├── test_services/
│   ├── __init__.py
│   ├── test_recipe_service.py
│   └── test_parsers.py
└── test_routes/
    ├── __init__.py
    ├── test_health.py
    └── test_recipes.py
```

## Writing Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*` 
- Test functions: `test_*`

### Example Test Class

```python
import pytest
from unittest.mock import Mock, patch
from app.services.ingredient_parser import parse_ingredient_structured

class TestIngredientParsing:
    """Test ingredient parsing functionality"""
    
    def test_basic_parsing(self):
        """Test basic ingredient parsing"""
        result = parse_ingredient_structured("2 cups flour")
        
        assert result is not None
        assert result.raw_ingredient == "flour"
        assert result.quantity == "2"
        assert result.unit == "cups"
    
    @pytest.mark.parametrize("input_text,expected", [
        ("1/2 cup sugar", "½"),
        ("3/4 tsp salt", "¾"),
        ("1 1/3 cups milk", "1 ⅓"),
    ])
    def test_fraction_conversion(self, input_text, expected):
        """Test fraction conversion with parametrized inputs"""
        result = parse_ingredient_structured(input_text)
        assert result.quantity == expected
    
    @patch('app.services.ingredient_parser.parse_ingredient')
    def test_parsing_error_handling(self, mock_parse):
        """Test error handling with mocked dependencies"""
        mock_parse.side_effect = Exception("Parsing failed")
        
        result = parse_ingredient_structured("invalid input")
        
        assert result.used_fallback
        assert result.confidence == 0.0
```

### Using Fixtures

```python
def test_recipe_parsing(sample_recipe):
    """Test using a fixture from conftest.py"""
    assert sample_recipe.title == "Farro Salad with Parmesan"
    assert len(sample_recipe.ingredients) > 0

@pytest.fixture
def custom_ingredient():
    """Custom fixture for this test file"""
    return StructuredIngredient(
        raw_ingredient="test",
        original_text="test ingredient"
    )
```

### Mocking External Dependencies

```python
@patch('app.config.openai_client')
def test_ai_categorization(mock_client):
    """Test AI functionality with mocked OpenAI client"""
    # Setup mock response
    mock_response = Mock()
    mock_response.choices[0].message.content = '{"health_tags": ["vegan"]}'
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test the functionality
    result = categorize_recipe(sample_recipe)
    assert "vegan" in result.health_tags
```

## Testing Best Practices

### 1. Test Organization
- Group related tests in classes
- Use descriptive test names
- Keep tests focused and atomic

### 2. Test Data
- Use fixtures for common test data
- Parametrize tests for multiple inputs
- Test both happy path and edge cases

### 3. Mocking
- Mock external dependencies (APIs, databases)
- Mock at the appropriate level
- Verify mock calls when necessary

### 4. Assertions
- Use specific assertions
- Test both positive and negative cases
- Include error message context

### 5. Coverage
- Aim for high coverage but focus on quality
- Test error conditions and edge cases
- Don't test implementation details

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with Python debugger
poetry run pytest --pdb

# Stop on first failure  
poetry run pytest -x

# Show local variables in tracebacks
poetry run pytest -l

# Capture print statements
poetry run pytest -s
```

### Using pytest-mock

```python
def test_with_mocker(mocker):
    """Using pytest-mock for cleaner mocking"""
    mock_parse = mocker.patch('app.services.ingredient_parser.parse_ingredient')
    mock_parse.return_value = Mock()
    
    # Test code here
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Multiple Python versions (3.10, 3.11, 3.12)

### Local CI Simulation

```bash
# Run the same checks as CI
poetry run flake8 app tests
poetry run black --check app tests  
poetry run mypy app
poetry run pytest tests/ --cov=app
```

## Environment Variables for Testing

Create a `.env.test` file for test-specific configuration:

```bash
# .env.test
DEBUG=true
LOG_LEVEL=DEBUG

# Set to empty to skip AI tests in CI
OPENAI_API_KEY=""

# Test database settings
DATABASE_URL="sqlite:///test.db"
```

## Performance Testing

For performance-sensitive code:

```python
import pytest

@pytest.mark.slow
def test_performance():
    """Performance test - marked as slow"""
    import time
    start = time.time()
    
    # Run performance-sensitive code
    result = process_large_dataset()
    
    end = time.time()
    assert end - start < 5.0  # Should complete in under 5 seconds
```

## Integration Testing

Integration tests verify components work together:

```python
@pytest.mark.integration
async def test_full_recipe_parsing_pipeline():
    """Test the complete recipe parsing flow"""
    url = "https://example.com/recipe"
    
    # This would make actual HTTP requests
    recipe = await RecipeService.parse_recipe_hybrid(url)
    
    assert recipe is not None
    assert len(recipe.ingredients) > 0
    assert recipe.ai_enhanced  # Verify AI processing worked
```

Run integration tests separately as they may be slower and require network access.
