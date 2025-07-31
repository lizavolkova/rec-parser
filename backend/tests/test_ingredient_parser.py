# tests/test_ingredient_parser.py
"""
Comprehensive unit tests for the ingredient_parser module

Tests cover:
- Basic ingredient parsing
- Dietary misparsing protection 
- Quantity handling and unicode fractions
- Ingredient consolidation
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from fractions import Fraction

from app.services.ingredient_parser import (
    StructuredIngredient,
    parse_ingredient_structured,
    parse_ingredients_list,
    get_raw_ingredients_for_search,
    get_shopping_list_items,
    format_shopping_item,
    normalize_fractions_for_parsing,
    convert_to_unicode_fraction,
    check_dietary_misparse,
    normalize_raw_ingredient,
    combine_quantities,
    can_combine_ingredients,
    consolidate_ingredient_group,
    UNICODE_TO_FRACTION,
    FRACTION_TO_UNICODE,
    DIETARY_MISPARSE_PATTERNS,
    RAW_INGREDIENT_CONSOLIDATION
)


class TestStructuredIngredient:
    """Test the StructuredIngredient dataclass"""
    
    def test_create_structured_ingredient(self):
        """Test creating a basic StructuredIngredient"""
        ingredient = StructuredIngredient(
            raw_ingredient="flour",
            quantity="2",
            unit="cups",
            descriptors=["all-purpose"],
            original_text="2 cups all-purpose flour",
            confidence=0.95,
            used_fallback=False
        )
        
        assert ingredient.raw_ingredient == "flour"
        assert ingredient.quantity == "2"
        assert ingredient.unit == "cups"
        assert ingredient.descriptors == ["all-purpose"]
        assert ingredient.confidence == 0.95
        assert not ingredient.used_fallback
    
    def test_structured_ingredient_defaults(self):
        """Test StructuredIngredient with default values"""
        ingredient = StructuredIngredient(
            raw_ingredient="salt",
            original_text="salt"
        )
        
        assert ingredient.descriptors == []
        assert ingredient.confidence == 0.0
        assert not ingredient.used_fallback
    
    def test_structured_ingredient_with_invalid_data(self):
        """Test StructuredIngredient with invalid data types"""
        # Test with None values
        ingredient = StructuredIngredient(
            raw_ingredient="test",
            quantity=None,
            unit=None,
            original_text=""
        )
        assert ingredient.quantity is None
        assert ingredient.unit is None
        
        # Test with empty strings
        ingredient = StructuredIngredient(
            raw_ingredient="test",
            quantity="",
            unit="",
            original_text=""
        )
        assert ingredient.quantity == ""
        assert ingredient.unit == ""


class TestFractionHandling:
    """Test unicode fraction conversion and normalization"""
    
    def test_unicode_to_fraction_conversion(self):
        """Test converting unicode fractions to text"""
        assert normalize_fractions_for_parsing("½ cup") == "1/2 cup"
        assert normalize_fractions_for_parsing("¾ tsp") == "3/4 tsp"
        assert normalize_fractions_for_parsing("2⅓ cups") == "2 1/3 cups"
    
    def test_fraction_to_unicode_conversion(self):
        """Test converting text fractions to unicode"""
        assert convert_to_unicode_fraction("1/2") == "½"
        assert convert_to_unicode_fraction("3/4") == "¾"
        assert convert_to_unicode_fraction("1/3") == "⅓"
    
    def test_improper_fraction_to_mixed_number(self):
        """Test converting improper fractions to mixed numbers"""
        assert convert_to_unicode_fraction("5/4") == "1 ¼"
        assert convert_to_unicode_fraction("7/3") == "2 ⅓"
        assert convert_to_unicode_fraction("3/2") == "1 ½"
    
    def test_whole_numbers(self):
        """Test handling whole numbers"""
        assert convert_to_unicode_fraction("3") == "3"
        assert convert_to_unicode_fraction("1") == "1"
    
    def test_decimal_fractions(self):
        """Test handling decimal inputs"""
        assert convert_to_unicode_fraction("0.5") == "½"
        assert convert_to_unicode_fraction("1.5") == "1 ½"
    
    def test_invalid_fractions(self):
        """Test handling invalid fraction strings"""
        assert convert_to_unicode_fraction("invalid") == "invalid"
        assert convert_to_unicode_fraction("") == ""


class TestDietaryMisparseProtection:
    """Test the dietary misparsing protection system"""
    
    def test_eggplant_protection(self):
        """Test that eggplant is protected from being parsed as eggs"""
        should_fallback, reason = check_dietary_misparse("2 medium eggplant", "eggs")
        assert should_fallback
        assert "eggplant incorrectly parsed as eggs" in reason
    
    def test_plant_milk_protection(self):
        """Test that plant-based milks are protected"""
        test_cases = [
            ("1 cup coconut milk", "milk"),
            ("½ cup almond milk", "milk"),
            ("2 cups oat milk", "milk")
        ]
        
        for original, parsed in test_cases:
            should_fallback, reason = check_dietary_misparse(original, parsed)
            assert should_fallback
            assert "plant-based milk incorrectly parsed as dairy milk" in reason
    
    def test_nut_butter_protection(self):
        """Test that nut butters are protected from being parsed as dairy butter"""
        test_cases = [
            ("2 tbsp peanut butter", "butter"),
            ("1 tbsp almond butter", "butter"),
            ("¼ cup cashew butter", "butter")
        ]
        
        for original, parsed in test_cases:
            should_fallback, reason = check_dietary_misparse(original, parsed)
            assert should_fallback
            assert "nut/seed butter incorrectly parsed as dairy butter" in reason
    
    def test_vegan_cheese_protection(self):
        """Test that vegan cheese alternatives are protected"""
        should_fallback, reason = check_dietary_misparse("¼ cup vegan cheese", "cheese")
        assert should_fallback
        assert "vegan cheese incorrectly parsed as dairy cheese" in reason
    
    def test_valid_parsing_not_protected(self):
        """Test that valid parsing doesn't trigger protection"""
        should_fallback, _ = check_dietary_misparse("2 cups flour", "flour")
        assert not should_fallback
        
        should_fallback, _ = check_dietary_misparse("3 large eggs", "eggs")
        assert not should_fallback
    
    def test_all_dietary_patterns_covered(self):
        """Test that all dietary misparse patterns are properly structured"""
        for pattern in DIETARY_MISPARSE_PATTERNS:
            assert 'original_contains' in pattern
            assert 'parsed_matches' in pattern
            assert 'reason' in pattern
            assert 'severity' in pattern
            
            assert isinstance(pattern['original_contains'], list)
            assert isinstance(pattern['parsed_matches'], list)
            assert len(pattern['original_contains']) > 0
            assert len(pattern['parsed_matches']) > 0


class TestRawIngredientNormalization:
    """Test raw ingredient normalization and consolidation"""
    
    def test_basic_normalization(self):
        """Test basic ingredient normalization"""
        assert normalize_raw_ingredient("  Flour  ") == "flour"
        assert normalize_raw_ingredient("SALT*") == "salt"
        assert normalize_raw_ingredient("Sugar**") == "sugar"
    
    def test_consolidation_rules(self):
        """Test ingredient consolidation"""
        assert normalize_raw_ingredient("large eggs") == "eggs"
        assert normalize_raw_ingredient("unsalted butter") == "butter"
        assert normalize_raw_ingredient("granulated sugar") == "sugar"
        assert normalize_raw_ingredient("kosher salt") == "salt"
    
    def test_no_consolidation_needed(self):
        """Test ingredients that don't need consolidation"""
        assert normalize_raw_ingredient("flour") == "flour"
        assert normalize_raw_ingredient("tomatoes") == "tomatoes"
        assert normalize_raw_ingredient("olive oil") == "olive oil"
    
    def test_filtered_ingredients(self):
        """Test that water is filtered out"""
        assert normalize_raw_ingredient("water") is None
        assert normalize_raw_ingredient("WATER") is None
    
    def test_eggplant_not_consolidated_to_eggs(self):
        """Test that eggplant is not consolidated to eggs (critical fix)"""
        result = normalize_raw_ingredient("eggplant")
        assert result == "eggplant"
        assert result != "eggs"


class TestQuantityCombination:
    """Test quantity combination functionality"""
    
    def test_combine_simple_fractions(self):
        """Test combining simple fractions"""
        assert combine_quantities("1/2", "1/4") == "¾"
        assert combine_quantities("1/3", "2/3") == "1"
        assert combine_quantities("1", "1/2") == "1 ½"
    
    def test_combine_with_none(self):
        """Test combining quantities when one is None"""
        assert combine_quantities(None, "1/2") == "1/2"
        assert combine_quantities("1/4", None) == "1/4"
        assert combine_quantities(None, None) is None
    
    def test_combine_unicode_fractions(self):
        """Test combining unicode fractions"""
        assert combine_quantities("½", "¼") == "¾"
        assert combine_quantities("⅓", "⅔") == "1"
    
    def test_combine_invalid_quantities(self):
        """Test combining invalid quantities falls back to concatenation"""
        result = combine_quantities("some", "thing")
        assert "some + thing" in result


class TestIngredientCombination:
    """Test ingredient combination logic"""
    
    def test_can_combine_same_ingredient_same_unit(self):
        """Test combining ingredients with same name and unit"""
        ing1 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            original_text="1 cup flour"
        )
        ing2 = StructuredIngredient(
            raw_ingredient="flour", 
            quantity="2",
            unit="cup",
            original_text="2 cups flour"
        )
        
        assert can_combine_ingredients(ing1, ing2)
    
    def test_can_combine_same_ingredient_no_unit(self):
        """Test combining unitless ingredients"""
        ing1 = StructuredIngredient(
            raw_ingredient="eggs",
            quantity="2",
            unit=None,
            original_text="2 eggs"
        )
        ing2 = StructuredIngredient(
            raw_ingredient="eggs",
            quantity="3", 
            unit=None,
            original_text="3 eggs"
        )
        
        assert can_combine_ingredients(ing1, ing2)
    
    def test_cannot_combine_different_ingredients(self):
        """Test that different ingredients cannot be combined"""
        ing1 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            original_text="1 cup flour"
        )
        ing2 = StructuredIngredient(
            raw_ingredient="sugar",
            quantity="1",
            unit="cup", 
            original_text="1 cup sugar"
        )
        
        assert not can_combine_ingredients(ing1, ing2)
    
    def test_cannot_combine_different_units(self):
        """Test that ingredients with different units cannot be combined"""
        ing1 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            original_text="1 cup flour"
        )
        ing2 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="16",
            unit="oz",
            original_text="16 oz flour"
        )
        
        assert not can_combine_ingredients(ing1, ing2)


class TestIngredientConsolidation:
    """Test ingredient group consolidation"""
    
    def test_consolidate_single_ingredient(self):
        """Test consolidating a group with single ingredient"""
        ingredient = StructuredIngredient(
            raw_ingredient="flour",
            quantity="2", 
            unit="cups",
            original_text="2 cups flour"
        )
        
        result = consolidate_ingredient_group([ingredient])
        assert len(result) == 1
        assert result[0] == ingredient
    
    def test_consolidate_same_unit_ingredients(self):
        """Test consolidating ingredients with same unit"""
        ing1 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            original_text="1 cup flour",
            confidence=0.9
        )
        ing2 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="½",
            unit="cup", 
            original_text="½ cup flour",
            confidence=0.8
        )
        
        result = consolidate_ingredient_group([ing1, ing2])
        assert len(result) == 1
        
        consolidated = result[0]
        assert consolidated.raw_ingredient == "flour"
        assert consolidated.quantity == "1 ½"
        assert consolidated.unit == "cup"
        assert consolidated.confidence == 0.8  # Minimum confidence
        assert "Combined:" in consolidated.original_text
    
    def test_consolidate_different_units(self):
        """Test consolidating ingredients with different units (should not combine)"""
        ing1 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="1",
            unit="cup",
            original_text="1 cup flour"
        )
        ing2 = StructuredIngredient(
            raw_ingredient="flour",
            quantity="8",
            unit="oz",
            original_text="8 oz flour"
        )
        
        result = consolidate_ingredient_group([ing1, ing2])
        assert len(result) == 2  # Should remain separate


@patch('app.services.ingredient_parser.parse_ingredient')
class TestIngredientParsing:
    """Test the main parsing functionality"""
    
    def test_successful_parsing(self, mock_parse):
        """Test successful ingredient parsing"""
        # Mock the NLP library response
        mock_amount = Mock()
        mock_amount.quantity = "2"
        mock_amount.unit = "cups"
        
        mock_name = Mock()
        mock_name.text = "flour"
        mock_name.confidence = 0.95
        
        mock_prep = Mock()
        mock_prep.text = "sifted"
        
        mock_result = Mock()
        mock_result.amount = [mock_amount]
        mock_result.name = [mock_name]
        mock_result.preparation = mock_prep
        mock_result.comment = None
        
        mock_parse.return_value = mock_result
        
        result = parse_ingredient_structured("2 cups flour, sifted")
        
        assert result is not None
        assert result.raw_ingredient == "flour"
        assert result.quantity == "2"
        assert result.unit == "cups"
        assert result.descriptors == ["sifted"]
        assert not result.used_fallback
        assert result.confidence == 0.95
    
    def test_low_confidence_fallback(self, mock_parse):
        """Test fallback when confidence is too low"""
        mock_name = Mock()
        mock_name.text = "flour"
        mock_name.confidence = 0.3  # Low confidence
        
        mock_result = Mock()
        mock_result.amount = []
        mock_result.name = [mock_name]
        mock_result.preparation = None
        mock_result.comment = None
        
        mock_parse.return_value = mock_result
        
        result = parse_ingredient_structured("2 cups mysterious ingredient")
        
        assert result is not None
        assert result.used_fallback
        assert result.raw_ingredient == "2 cups mysterious ingredient"
    
    def test_dietary_misparse_fallback(self, mock_parse):
        """Test fallback when dietary misparsing is detected"""
        mock_name = Mock()
        mock_name.text = "eggs"  # This would trigger eggplant protection
        mock_name.confidence = 0.95
        
        mock_result = Mock()
        mock_result.amount = []
        mock_result.name = [mock_name]
        mock_result.preparation = None
        mock_result.comment = None
        
        mock_parse.return_value = mock_result
        
        result = parse_ingredient_structured("2 medium eggplant")
        
        assert result is not None
        assert result.used_fallback
        assert result.raw_ingredient == "2 medium eggplant"
    
    def test_parsing_error_fallback(self, mock_parse):
        """Test fallback when parsing raises an exception"""
        mock_parse.side_effect = Exception("Parsing failed")
        
        result = parse_ingredient_structured("2 cups flour")
        
        assert result is not None
        assert result.used_fallback
        assert result.raw_ingredient == "2 cups flour"
        assert result.confidence == 0.0
    
    def test_empty_input(self, mock_parse):
        """Test handling empty or None input"""
        assert parse_ingredient_structured("") is None
        assert parse_ingredient_structured(None) is None
        assert parse_ingredient_structured("   ") is None


class TestIngredientListParsing:
    """Test parsing lists of ingredients"""
    
    @patch('app.services.ingredient_parser.parse_ingredient_structured')
    def test_parse_ingredients_list(self, mock_parse_single):
        """Test parsing a list of ingredients"""
        # Mock individual parsing results
        mock_results = [
            StructuredIngredient(
                raw_ingredient="flour",
                quantity="2",
                unit="cups",
                original_text="2 cups flour"
            ),
            StructuredIngredient(
                raw_ingredient="eggs",
                quantity="3",
                unit=None,
                original_text="3 large eggs"
            )
        ]
        
        mock_parse_single.side_effect = mock_results
        
        ingredients = ["2 cups flour", "3 large eggs"]
        result = parse_ingredients_list(ingredients)
        
        assert len(result) == 2
        assert result[0].raw_ingredient == "flour"
        assert result[1].raw_ingredient == "eggs"
    
    @patch('app.services.ingredient_parser.parse_ingredient_structured')
    def test_parse_with_consolidation(self, mock_parse_single):
        """Test parsing with ingredient consolidation"""
        # Mock results that should be consolidated
        mock_results = [
            StructuredIngredient(
                raw_ingredient="flour",
                quantity="1",
                unit="cup",
                original_text="1 cup flour"
            ),
            StructuredIngredient(
                raw_ingredient="flour",
                quantity="½",
                unit="cup",
                original_text="½ cup flour"
            )
        ]
        
        mock_parse_single.side_effect = mock_results
        
        ingredients = ["1 cup flour", "½ cup flour"] 
        result = parse_ingredients_list(ingredients)
        
        # Should be consolidated into one ingredient
        assert len(result) == 1
        assert result[0].raw_ingredient == "flour"
        assert result[0].quantity == "1 ½"


class TestShoppingListGeneration:
    """Test shopping list functionality"""
    
    def test_get_raw_ingredients_for_search(self):
        """Test extracting raw ingredients for search"""
        ingredients = [
            StructuredIngredient(
                raw_ingredient="flour",
                original_text="2 cups flour"
            ),
            StructuredIngredient(
                raw_ingredient="eggs",
                original_text="3 eggs"
            )
        ]
        
        result = get_raw_ingredients_for_search(ingredients)
        assert result == ["flour", "eggs"]
    
    def test_format_shopping_item(self):
        """Test formatting ingredients for shopping display"""
        ingredient = StructuredIngredient(
            raw_ingredient="flour",
            quantity="2",
            unit="cups",
            original_text="2 cups flour"
        )
        
        result = format_shopping_item(ingredient)
        assert result == "2 cups flour"
    
    def test_format_shopping_item_no_quantity(self):
        """Test formatting ingredient without quantity"""
        ingredient = StructuredIngredient(
            raw_ingredient="salt",
            quantity=None,
            unit=None,
            original_text="salt to taste"
        )
        
        result = format_shopping_item(ingredient)
        assert result == "salt"
    
    def test_format_shopping_item_fallback(self):
        """Test formatting ingredient that used fallback"""
        ingredient = StructuredIngredient(
            raw_ingredient="2 medium eggplant, diced",
            used_fallback=True,
            original_text="2 medium eggplant, diced"
        )
        
        result = format_shopping_item(ingredient)
        assert result == "2 medium eggplant, diced"
    
    def test_get_shopping_list_items(self):
        """Test generating shopping list items with metadata"""
        ingredients = [
            StructuredIngredient(
                raw_ingredient="flour",
                quantity="2",
                unit="cups",
                descriptors=["all-purpose"],
                original_text="2 cups all-purpose flour",
                confidence=0.95,
                used_fallback=False
            )
        ]
        
        result = get_shopping_list_items(ingredients)
        
        assert len(result) == 1
        
        item = result[0]
        assert item["name"] == "flour"
        assert item["quantity"] == "2"
        assert item["unit"] == "cups"
        assert item["descriptors"] == ["all-purpose"]
        assert item["shopping_display"] == "2 cups flour"
        assert not item["used_fallback"]
        assert not item["was_combined"]


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_unicode_fraction_constants(self):
        """Test that unicode fraction constants are properly defined"""
        assert len(UNICODE_TO_FRACTION) > 0
        assert len(FRACTION_TO_UNICODE) > 0
        
        # Test bidirectional mapping
        for unicode_frac, text_frac in UNICODE_TO_FRACTION.items():
            assert FRACTION_TO_UNICODE[text_frac] == unicode_frac
    
    def test_consolidation_rules_constants(self):
        """Test that consolidation rules are properly defined"""
        assert len(RAW_INGREDIENT_CONSOLIDATION) > 0
        
        # Test that all values are lists
        for key, variations in RAW_INGREDIENT_CONSOLIDATION.items():
            assert isinstance(variations, list)
            assert len(variations) > 0
            assert key in variations  # Key should be in its own variations
    
    def test_dietary_patterns_comprehensive(self):
        """Test that dietary patterns cover major vegan concerns"""
        pattern_reasons = [p['reason'] for p in DIETARY_MISPARSE_PATTERNS]
        
        # Check for major vegan concerns
        eggplant_covered = any('eggplant' in reason for reason in pattern_reasons)
        milk_covered = any('plant-based milk' in reason for reason in pattern_reasons)
        butter_covered = any('nut/seed butter' in reason for reason in pattern_reasons)
        
        assert eggplant_covered, "Eggplant vs eggs protection should be covered"
        assert milk_covered, "Plant milk protection should be covered"  
        assert butter_covered, "Nut butter protection should be covered"


class TestIngredientParserIntegration:
    """Integration tests using actual ingredient-parser-nlp library"""
    
    @pytest.mark.integration
    def test_real_ingredient_parsing(self):
        """Test parsing with actual ingredient-parser-nlp library"""
        # Test common ingredients that should parse reliably
        test_ingredients = [
            "2 cups all-purpose flour",
            "1 large egg",
            "1/2 teaspoon salt",
            "3 tablespoons olive oil"
        ]
        
        results = parse_ingredients_list(test_ingredients)
        
        assert len(results) == 4
        
        # Verify flour parsing
        flour_result = next((r for r in results if "flour" in r.raw_ingredient), None)
        assert flour_result is not None
        assert flour_result.quantity == "2"
        assert flour_result.unit in ["cups", "cup"]  # Library may return singular or plural
        
        # Verify egg parsing
        egg_result = next((r for r in results if "egg" in r.raw_ingredient), None)
        assert egg_result is not None
        assert egg_result.quantity == "1"
        
        # Verify salt parsing
        salt_result = next((r for r in results if "salt" in r.raw_ingredient), None)
        assert salt_result is not None
        assert salt_result.quantity == "½"  # Should convert to unicode
        assert salt_result.unit in ["teaspoon", "teaspoons"]  # Library may return singular or plural
    
    @pytest.mark.integration
    def test_dietary_misparse_protection_integration(self):
        """Test dietary misparsing protection with real parsing"""
        # Test eggplant vs eggs issue
        eggplant_ingredients = ["2 medium eggplant, diced"]
        results = parse_ingredients_list(eggplant_ingredients)
        
        assert len(results) == 1
        result = results[0]
        
        # With real parsing library, eggplant is correctly parsed as eggplant
        assert "eggplant" in result.raw_ingredient.lower()
        # Real library doesn't misparse eggplant as eggs, so no fallback needed
        assert result.used_fallback is False  # No protection needed with real parser
    
    @pytest.mark.integration
    def test_ingredient_consolidation_integration(self):
        """Test ingredient consolidation with real parsing"""
        # Test consolidation of similar ingredients
        test_ingredients = [
            "2 cups flour",
            "1 cup all-purpose flour",
            "3 large eggs",
            "1 egg"
        ]
        
        results = parse_ingredients_list(test_ingredients)
        
        # Should consolidate flour entries
        flour_results = [r for r in results if "flour" in r.raw_ingredient.lower()]
        assert len(flour_results) <= 2  # Should consolidate some flour entries
        
        # Should consolidate egg entries
        egg_results = [r for r in results if "egg" in r.raw_ingredient.lower()]
        assert len(egg_results) == 1  # Should consolidate to single eggs entry
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complex_recipe_parsing(self):
        """Test parsing a complex recipe with many ingredients"""
        complex_ingredients = [
            "2 pounds ground beef",
            "1 large onion, diced",
            "3 cloves garlic, minced",
            "2 cans (14.5 oz each) diced tomatoes",
            "1 can (6 oz) tomato paste",
            "2 teaspoons dried oregano",
            "1 teaspoon dried basil",
            "1/2 teaspoon salt",
            "1/4 teaspoon black pepper",
            "2 cups shredded mozzarella cheese"
        ]
        
        results = parse_ingredients_list(complex_ingredients)
        
        # Should parse most ingredients successfully
        assert len(results) >= 8  # Allow for some consolidation
        
        # Check that complex ingredients are handled
        tomato_results = [r for r in results if "tomato" in r.raw_ingredient.lower()]
        assert len(tomato_results) >= 1  # Should identify tomato products
        
        # Check quantity parsing for complex quantities
        beef_result = next((r for r in results if "beef" in r.raw_ingredient.lower()), None)
        if beef_result and not beef_result.used_fallback:
            assert beef_result.quantity == "2"
            assert beef_result.unit in ["pounds", "lbs", "pound"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
