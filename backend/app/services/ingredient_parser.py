"""
COMPLETE Enhanced ingredient parser with robust dietary misparsing protection
Includes ALL original functionality + bug fixes for the consolidation issue
"""

from typing import List, Optional, Dict, Any
from fractions import Fraction
import re
from ingredient_parser import parse_ingredient

# Import StructuredIngredient from models
from app.models import StructuredIngredient

# Unicode fraction mappings (bidirectional)
UNICODE_TO_FRACTION = {
    '½': '1/2', '⅓': '1/3', '⅔': '2/3', '¼': '1/4', '¾': '3/4',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5', '⅙': '1/6', '⅚': '5/6',
    '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8'
}

FRACTION_TO_UNICODE = {v: k for k, v in UNICODE_TO_FRACTION.items()}

# Configuration
CONFIDENCE_THRESHOLD = 0.6  # Adjustable threshold


# Enhanced dietary misparsing protection patterns
DIETARY_MISPARSE_PATTERNS = [
    # Eggplant vs Eggs (the main issue)
    {
        'original_contains': ['eggplant'],
        'parsed_matches': ['eggs', 'egg'],
        'reason': 'eggplant incorrectly parsed as eggs (vegan vs non-vegan)',
        'severity': 'critical'  # Critical because it affects vegan classification
    },
    
    # Plant-based milks vs dairy milk
    {
        'original_contains': ['coconut milk', 'almond milk', 'oat milk', 'soy milk', 'rice milk', 'cashew milk'],
        'parsed_matches': ['milk'],
        'reason': 'plant-based milk incorrectly parsed as dairy milk (vegan vs non-vegan)',
        'severity': 'critical'
    },
    
    # Plant-based butters vs dairy butter  
    {
        'original_contains': ['almond butter', 'peanut butter', 'cashew butter', 'sunflower butter'],
        'parsed_matches': ['butter'],
        'reason': 'nut/seed butter incorrectly parsed as dairy butter (vegan vs non-vegan)',
        'severity': 'critical'
    },
    
    # Vegan cheese vs dairy cheese
    {
        'original_contains': ['vegan cheese', 'cashew cheese', 'nutritional yeast'],
        'parsed_matches': ['cheese'],
        'reason': 'vegan cheese incorrectly parsed as dairy cheese (vegan vs non-vegan)',
        'severity': 'critical'
    },
    
    # Plant-based cream vs dairy cream
    {
        'original_contains': ['coconut cream', 'cashew cream'],
        'parsed_matches': ['cream'],
        'reason': 'plant-based cream incorrectly parsed as dairy cream (vegan vs non-vegan)',
        'severity': 'critical'
    },
    
    # Egg replacers vs eggs
    {
        'original_contains': ['egg replacer', 'flax egg', 'chia egg'],
        'parsed_matches': ['eggs', 'egg'],
        'reason': 'egg substitute incorrectly parsed as eggs (vegan vs non-vegan)',
        'severity': 'critical'
    },
    
    # Additional common misparses that could affect classification
    {
        'original_contains': ['vanilla extract'],
        'parsed_matches': ['vanilla'],
        'reason': 'vanilla extract parsed as just vanilla (loses specificity)',
        'severity': 'medium'
    },
    
    # Sea vegetables vs meat (seaweed, etc.)
    {
        'original_contains': ['seaweed', 'kelp', 'nori'],
        'parsed_matches': ['meat', 'beef', 'pork', 'chicken'],
        'reason': 'sea vegetable incorrectly parsed as meat (vegan vs non-vegan)',
        'severity': 'critical'
    }
]


def normalize_fractions_for_parsing(text: str) -> str:
    """Convert unicode fractions to text fractions for ML parsing"""
    # Handle mixed numbers first (digit followed by fraction)
    for unicode_frac, text_frac in UNICODE_TO_FRACTION.items():
        # Add space for mixed numbers like "2⅓" -> "2 1/3"
        text = re.sub(f'(\\d){re.escape(unicode_frac)}', f'\\1 {text_frac}', text)
        # Handle standalone fractions
        text = text.replace(unicode_frac, text_frac)

    # Fix spacing issues like "1/2-inch" -> "1/2 inch"
    text = re.sub(r'(\d+/\d+)-', r'\1 ', text)

    return text

def convert_to_unicode_fraction(fraction_str: str) -> str:
    """Convert text fractions to unicode and improper fractions to mixed numbers"""
    if not fraction_str:
        return fraction_str
    
    try:
        # Handle decimal numbers
        if '.' in fraction_str:
            frac = Fraction(float(fraction_str)).limit_denominator()
        else:
            frac = Fraction(fraction_str)
        
        # Convert improper fractions to mixed numbers
        if frac.numerator >= frac.denominator and frac.denominator != 1:
            # Calculate whole part and remaining fraction
            whole_part = frac.numerator // frac.denominator
            remainder = frac.numerator % frac.denominator
            
            if remainder == 0:
                return str(whole_part)
            else:
                # Mixed number: whole + fraction
                fractional_part = Fraction(remainder, frac.denominator)
                fractional_str = str(fractional_part)
                unicode_frac = FRACTION_TO_UNICODE.get(fractional_str, fractional_str)
                return f"{whole_part} {unicode_frac}"
        else:
            # Proper fraction or whole number, just convert to unicode if possible
            frac_str = str(frac)
            return FRACTION_TO_UNICODE.get(frac_str, frac_str)
        
    except (ValueError, ZeroDivisionError):
        return fraction_str


def check_dietary_misparse(original_text: str, parsed_name: str) -> tuple[bool, str]:
    """
    Enhanced dietary misparsing detection using pattern matching
    Returns (should_fallback, reason)
    """
    original_lower = original_text.lower().strip()
    parsed_lower = parsed_name.lower().strip()
    
    print(f"🔍 PROTECTION CHECK: '{original_text}' -> '{parsed_name}'")
    
    for pattern in DIETARY_MISPARSE_PATTERNS:
        # Check if original text contains any of the trigger phrases
        original_match = any(phrase in original_lower for phrase in pattern['original_contains'])
        
        # Check if parsed name matches any of the problematic results
        parsed_match = any(parsed_lower == target or parsed_lower.endswith(target) 
                          for target in pattern['parsed_matches'])
        
        if original_match and parsed_match:
            print(f"🚨 DIETARY MISPARSE DETECTED: {pattern['reason']}")
            print(f"   Original contains: {[phrase for phrase in pattern['original_contains'] if phrase in original_lower]}")
            print(f"   Parsed as: '{parsed_name}' (matches: {[target for target in pattern['parsed_matches'] if parsed_lower == target or parsed_lower.endswith(target)]})")
            return True, pattern['reason']
    
    print(f"✅ No dietary misparsing detected")
    return False, ""


# FIXED: Better consolidation rules with exact word matching to prevent "eggplant" -> "eggs"
RAW_INGREDIENT_CONSOLIDATION = {
    "eggs": ["egg", "eggs", "whole egg", "whole eggs", "large egg", "large eggs"],
    "butter": ["butter", "unsalted butter", "salted butter"],
    "sugar": ["sugar", "granulated sugar", "white sugar", "cane sugar"],
    "brown sugar": ["brown sugar", "dark brown sugar", "light brown sugar"],
    "salt": ["salt", "kosher salt", "sea salt", "table salt", "fine salt"],
    "olive oil": ["olive oil", "extra virgin olive oil", "evoo"],
}

# Ingredients to ignore completely
IGNORED_INGREDIENTS = ["water"]


def normalize_raw_ingredient(ingredient_name: str) -> Optional[str]:
    """
    FIXED: Lightly normalize raw ingredient names for consolidation using EXACT WORD MATCHING
    This prevents "eggplant" from being consolidated to "eggs"
    """
    name = ingredient_name.lower().strip()
    
    # Remove asterisks (footnote markers)
    name = re.sub(r'\*+', '', name).strip()
    
    print(f"🔧 NORMALIZING: '{ingredient_name}' -> '{name}'")
    
    # Filter out water
    if any(ignored in name for ignored in IGNORED_INGREDIENTS):
        print(f"   🚫 Filtered out (ignored ingredient)")
        return None
    
    # FIXED: Check consolidation rules using EXACT MATCHING to prevent "eggplant" -> "eggs"
    for consolidated_name, variations in RAW_INGREDIENT_CONSOLIDATION.items():
        # Use exact match instead of substring match
        if name in [var.lower() for var in variations]:
            print(f"   🔄 Consolidated '{name}' -> '{consolidated_name}'")
            return consolidated_name
    
    # No consolidation rule matched, return as-is
    print(f"   ✅ No consolidation needed, keeping '{name}'")
    return name


def parse_ingredient_structured(ingredient_text: str, confidence_threshold: float = CONFIDENCE_THRESHOLD) -> Optional[StructuredIngredient]:
    """
    Parse a single ingredient into structured components using ingredient-parser-nlp
    Enhanced with comprehensive dietary misparsing protection
    """
    if not ingredient_text or not ingredient_text.strip():
        return None
    
    print(f"\n🔧 PARSING: '{ingredient_text}'")
    
    # Normalize fractions for ML parsing
    normalized_text = normalize_fractions_for_parsing(ingredient_text)
        
    try:
        parsed = parse_ingredient(normalized_text)
        
        # Extract quantity and unit
        quantity = None
        unit = None
        if hasattr(parsed, 'amount') and parsed.amount:
            if isinstance(parsed.amount, list) and len(parsed.amount) > 0:
                amount_obj = parsed.amount[0]
                raw_quantity = getattr(amount_obj, 'quantity', None)
                unit_obj = getattr(amount_obj, 'unit', None)
                unit = str(unit_obj) if unit_obj else None
                
                # Convert quantity back to unicode fraction for display
                if raw_quantity:
                    quantity = convert_to_unicode_fraction(str(raw_quantity))
        
        # Extract ingredient name and confidence
        ingredient_name = None
        name_confidence = 1.0
        if hasattr(parsed, 'name') and parsed.name:
            if isinstance(parsed.name, list) and len(parsed.name) > 0:
                ingredient_name = parsed.name[0].text
                name_confidence = getattr(parsed.name[0], 'confidence', 1.0)
            else:
                ingredient_name = str(parsed.name)
        
        if not ingredient_name:
            print("❌ No ingredient name extracted, using fallback")
            return StructuredIngredient(
                raw_ingredient=ingredient_text.strip(),
                quantity=None,
                unit=None,
                descriptors=[],
                original_text=ingredient_text,
                confidence=0.0,
                used_fallback=True
            )
        
        print(f"   NLP extracted: '{ingredient_name}' (confidence: {name_confidence:.6f})")
        
        # CRITICAL: Check for dietary misparsing BEFORE any normalization
        force_fallback, fallback_reason = check_dietary_misparse(ingredient_text, ingredient_name)
        
        # Check confidence threshold fallback
        confidence_fallback = name_confidence < confidence_threshold
        
        # Use fallback if forced or low confidence
        if force_fallback or confidence_fallback:
            if force_fallback:
                print(f"🛡️ DIETARY PROTECTION ACTIVATED: {fallback_reason}")
            elif confidence_fallback:
                print(f"🔄 Low confidence ({name_confidence:.3f}), using fallback")
            
            # Use original text as-is to preserve dietary accuracy
            raw_ingredient = ingredient_text.strip()
            
            return StructuredIngredient(
                raw_ingredient=raw_ingredient,
                quantity=quantity,  # Keep parsed quantity/unit if available
                unit=unit,
                descriptors=[],
                original_text=ingredient_text,
                confidence=name_confidence,
                used_fallback=True
            )
        
        # Normal case - parsing looks good, proceed with normalization
        raw_ingredient = normalize_raw_ingredient(ingredient_name)
        if not raw_ingredient:
            print(f"🚫 Ingredient filtered out: '{ingredient_name}'")
            return None  # Filtered out (like water)
        
        # Extract and clean descriptors
        descriptors = []
        if hasattr(parsed, 'preparation') and parsed.preparation:
            prep_text = getattr(parsed.preparation, 'text', str(parsed.preparation))
            if prep_text:
                # Clean up and split descriptors
                prep_text = prep_text.replace('(', '').replace(')', '').replace(',', '')
                descriptors = [part.strip() for part in prep_text.split() if len(part.strip()) > 1]
        
        # Add comment as descriptor if present
        if hasattr(parsed, 'comment') and parsed.comment:
            comment_text = getattr(parsed.comment, 'text', str(parsed.comment))
            if comment_text:
                comment_text = comment_text.replace('(', '').replace(')', '').replace(',', '')
                descriptors.extend([part.strip() for part in comment_text.split() if len(part.strip()) > 1])
        
        print(f"✅ Successfully parsed '{ingredient_text}' as '{raw_ingredient}' (confidence: {name_confidence:.3f})")
        
        return StructuredIngredient(
            raw_ingredient=raw_ingredient,
            quantity=quantity,
            unit=unit,
            descriptors=descriptors,
            original_text=ingredient_text,
            confidence=name_confidence,
            used_fallback=False
        )
        
    except Exception as e:
        print(f"❌ Parsing error for '{ingredient_text}': {e}")
        # Return fallback result for any parsing errors
        return StructuredIngredient(
            raw_ingredient=ingredient_text.strip(),
            quantity=None,
            unit=None,
            descriptors=[],
            original_text=ingredient_text,
            confidence=0.0,
            used_fallback=True
        )


def combine_quantities(qty1: Optional[str], qty2: Optional[str]) -> Optional[str]:
    """Combine two quantity strings, handling fractions and decimals"""
    if not qty1 and not qty2:
        return None
    if not qty1:
        return qty2
    if not qty2:
        return qty1
    
    try:
        # Parse both quantities as fractions to handle unicode fractions
        qty1_normalized = normalize_fractions_for_parsing(qty1)
        qty2_normalized = normalize_fractions_for_parsing(qty2)
        
        # Convert to fractions for accurate arithmetic
        frac1 = Fraction(qty1_normalized)
        frac2 = Fraction(qty2_normalized)
        
        # Add them together
        total = frac1 + frac2
        
        # Convert back to string and then to unicode fraction if possible
        total_str = str(total)
        return convert_to_unicode_fraction(total_str)
        
    except (ValueError, ZeroDivisionError):
        # If we can't parse as numbers, just concatenate with "+"
        return f"{qty1} + {qty2}"


def can_combine_ingredients(ing1: StructuredIngredient, ing2: StructuredIngredient) -> bool:
    """Check if two ingredients can be safely combined (same unit or both unitless)"""
    # Must be same raw ingredient
    if ing1.raw_ingredient != ing2.raw_ingredient:
        return False
    
    # Can combine if units are the same (including both None)
    if ing1.unit == ing2.unit:
        return True
    
    # Can combine if both are unitless (count items like "eggs")
    if ing1.unit is None and ing2.unit is None:
        return True
    
    return False


def consolidate_ingredient_group(ingredient_list: List[StructuredIngredient]) -> List[StructuredIngredient]:
    """Consolidate a group of ingredients with the same raw name"""
    if len(ingredient_list) <= 1:
        return ingredient_list
    
    # Group by unit (ingredients with same unit can be combined)
    unit_groups = {}
    for ing in ingredient_list:
        unit_key = ing.unit or "unitless"
        if unit_key not in unit_groups:
            unit_groups[unit_key] = []
        unit_groups[unit_key].append(ing)
    
    consolidated = []
    
    for unit_key, group in unit_groups.items():
        if len(group) == 1:
            # Only one ingredient with this unit, keep as-is
            consolidated.append(group[0])
        else:
            # Multiple ingredients with same unit, combine quantities
            base_ingredient = group[0]  # Use first as template
            combined_quantity = base_ingredient.quantity
            
            # Combine quantities from all ingredients in this unit group
            for ing in group[1:]:
                combined_quantity = combine_quantities(combined_quantity, ing.quantity)
            
            # Combine descriptors (remove duplicates)
            all_descriptors = []
            for ing in group:
                all_descriptors.extend(ing.descriptors)
            unique_descriptors = list(dict.fromkeys(all_descriptors))  # Preserve order, remove duplicates
            
            # Create consolidated ingredient
            consolidated_ingredient = StructuredIngredient(
                raw_ingredient=base_ingredient.raw_ingredient,
                quantity=combined_quantity,
                unit=base_ingredient.unit,
                descriptors=unique_descriptors,
                original_text=f"Combined: {', '.join([ing.original_text for ing in group])}",
                confidence=min([ing.confidence for ing in group]),  # Use lowest confidence
                used_fallback=any([ing.used_fallback for ing in group])  # True if any used fallback
            )
            
            consolidated.append(consolidated_ingredient)
    
    return consolidated


def parse_ingredients_list(ingredients: List[str], confidence_threshold: float = CONFIDENCE_THRESHOLD) -> List[StructuredIngredient]:
    """Parse a list of ingredient strings into structured format with quantity consolidation"""
    structured_ingredients = []
    ingredient_map = {}  # raw_ingredient -> list of StructuredIngredient
    
    print(f"\n📝 PARSING {len(ingredients)} INGREDIENTS:")
    print("=" * 60)
    
    # First pass: parse all ingredients
    for i, ingredient_text in enumerate(ingredients, 1):
        print(f"\n[{i}/{len(ingredients)}]")
        structured = parse_ingredient_structured(ingredient_text, confidence_threshold)
        
        if structured:
            raw_name = structured.raw_ingredient
            if raw_name not in ingredient_map:
                ingredient_map[raw_name] = []
            ingredient_map[raw_name].append(structured)
    
    print(f"\n🔄 CONSOLIDATING {len(ingredient_map)} UNIQUE INGREDIENTS:")
    print("-" * 40)
    
    # Second pass: consolidate ingredients with same name
    for raw_name, ingredient_list in ingredient_map.items():
        if len(ingredient_list) == 1:
            # Single occurrence, just add it
            structured_ingredients.append(ingredient_list[0])
            print(f"✅ {raw_name}: single occurrence")
        else:
            # Multiple occurrences, try to consolidate
            print(f"🔄 {raw_name}: {len(ingredient_list)} occurrences, consolidating...")
            consolidated = consolidate_ingredient_group(ingredient_list)
            structured_ingredients.extend(consolidated)
    
    print(f"\n✅ FINAL RESULT: {len(structured_ingredients)} ingredients")
    return structured_ingredients


def get_raw_ingredients_for_search(structured_ingredients: List[StructuredIngredient]) -> List[str]:
    """Extract just the raw ingredient names for recipe search/filtering"""
    return [ing.raw_ingredient for ing in structured_ingredients]


def get_shopping_list_items(structured_ingredients: List[StructuredIngredient]) -> List[Dict[str, Any]]:
    """Format ingredients for shopping list with quantities (using unicode fractions)"""
    shopping_items = []
    
    for ing in structured_ingredients:
        # Check if this was a consolidated ingredient
        was_combined = "Combined:" in ing.original_text
        
        item = {
            "name": ing.raw_ingredient,
            "quantity": ing.quantity,
            "unit": ing.unit,
            "descriptors": ing.descriptors,
            "original": ing.original_text,
            "confidence": ing.confidence,
            "shopping_display": format_shopping_item(ing),
            "used_fallback": ing.used_fallback,
            "was_combined": was_combined
        }
        shopping_items.append(item)
    
    return shopping_items


def format_shopping_item(ing: StructuredIngredient) -> str:
    """Format an ingredient for display on shopping list (with unicode fractions)"""
    if ing.used_fallback:
        # For fallback ingredients, use the raw ingredient which preserves original meaning
        return ing.raw_ingredient
    
    parts = []
    
    if ing.quantity:
        parts.append(ing.quantity)  # Will be "½" not "1/2"
    
    if ing.unit:
        parts.append(ing.unit)
    
    parts.append(ing.raw_ingredient)
    
    return " ".join(parts)


# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced protection system
    print("🧪 Testing COMPLETE Enhanced Dietary Protection:")
    print("=" * 60)
    
    test_ingredients = [
        "2 medium eggplant",  # Should NOT be consolidated to eggs anymore!
        "3 large eggs",       # Should be consolidated to eggs (correct)
        "1 cup coconut milk", # Should trigger protection
        "1 cup whole milk",   # Should parse normally
        "2 tbsp almond butter", # Should trigger protection
        "2 tbsp butter",      # Should parse normally
        "1 cup flour",        # Test normal ingredient
        "2 cups flour",       # Test consolidation
    ]
    
    structured = parse_ingredients_list(test_ingredients)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Input ingredients: {len(test_ingredients)}")
    print(f"   Parsed ingredients: {len(structured)}")
    print(f"   Used fallback: {sum(1 for ing in structured if ing.used_fallback)}")
    
    print(f"\n🛒 SHOPPING LIST:")
    for item in get_shopping_list_items(structured):
        fallback_indicator = " [FALLBACK]" if item["used_fallback"] else ""
        combined_indicator = " [COMBINED]" if item["was_combined"] else ""
        print(f"   • {item['shopping_display']}{fallback_indicator}{combined_indicator}")
