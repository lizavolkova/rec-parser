# fixed_debug_script.py
import sys
import os

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

def test_eggplant_parsing():
    print("🧪 ENHANCED DEBUG: Testing Eggplant vs Eggs Parsing")
    print("=" * 60)
    
    try:
        from app.services.ingredient_parser import (
            parse_ingredient_structured, 
            check_dietary_misparse,
            DIETARY_MISPARSE_PATTERNS
        )
        
        print(f"✅ Successfully imported enhanced functions")
        print(f"📋 Found {len(DIETARY_MISPARSE_PATTERNS)} dietary protection patterns")
        
        # Show the eggplant pattern specifically
        eggplant_pattern = None
        for pattern in DIETARY_MISPARSE_PATTERNS:
            if 'eggplant' in pattern.get('original_contains', []):
                eggplant_pattern = pattern
                break
        
        if eggplant_pattern:
            print(f"🍆 Eggplant protection pattern found:")
            print(f"   Original contains: {eggplant_pattern['original_contains']}")
            print(f"   Parsed matches: {eggplant_pattern['parsed_matches']}")
            print(f"   Reason: {eggplant_pattern['reason']}")
        else:
            print("❌ Eggplant protection pattern NOT found!")
            return
        
        # Test the protection function directly
        print(f"\n🔍 TESTING PROTECTION FUNCTION DIRECTLY:")
        original_text = "2 medium eggplant"
        parsed_name = "eggs"  # This is what the NLP library returns
        
        should_fallback, reason = check_dietary_misparse(original_text, parsed_name)
        print(f"   Input: '{original_text}' -> '{parsed_name}'")
        print(f"   Should fallback: {should_fallback}")
        print(f"   Reason: {reason}")
        
        if not should_fallback:
            print("❌ PROBLEM: Protection function not triggering!")
            
            # Test each condition manually
            print(f"\n🔬 MANUAL CONDITION TESTING:")
            original_lower = original_text.lower().strip()
            parsed_lower = parsed_name.lower().strip()
            
            for pattern in DIETARY_MISPARSE_PATTERNS:
                print(f"\n   Pattern: {pattern.get('reason', 'No reason')}")
                original_match = any(phrase in original_lower for phrase in pattern['original_contains'])
                parsed_match = any(parsed_lower == target or parsed_lower.endswith(target) 
                                  for target in pattern['parsed_matches'])
                
                print(f"     Original '{original_lower}' contains {pattern['original_contains']}: {original_match}")
                print(f"     Parsed '{parsed_lower}' matches {pattern['parsed_matches']}: {parsed_match}")
                print(f"     Both conditions met: {original_match and parsed_match}")
        
        # Test with the actual NLP library
        print(f"\n🤖 TESTING WITH ACTUAL NLP LIBRARY:")
        
        # Import the original NLP library to see what it actually returns
        try:
            from ingredient_parser import parse_ingredient
            
            test_text = "2 medium eggplant"
            nlp_result = parse_ingredient(test_text)
            
            print(f"   Input: '{test_text}'")
            print(f"   NLP Library Result: {nlp_result}")
            
            # Extract what the NLP library actually parsed
            if hasattr(nlp_result, 'name') and nlp_result.name:
                if isinstance(nlp_result.name, list) and len(nlp_result.name) > 0:
                    actual_parsed_name = nlp_result.name[0].text
                else:
                    actual_parsed_name = str(nlp_result.name)
                
                print(f"   Actual parsed name: '{actual_parsed_name}'")
                
                # Test protection with actual result
                should_fallback_actual, reason_actual = check_dietary_misparse(test_text, actual_parsed_name)
                print(f"   Protection should trigger: {should_fallback_actual}")
                print(f"   Reason: {reason_actual}")
            
        except Exception as e:
            print(f"   ❌ Error testing NLP library: {e}")
        
        # Now test the full structured parsing
        print(f"\n🔧 TESTING FULL STRUCTURED PARSING:")
        result = parse_ingredient_structured("2 medium eggplant")
        
        if result:
            print(f"   Raw ingredient: '{result.raw_ingredient}'")
            print(f"   Quantity: {result.quantity}")
            print(f"   Unit: {result.unit}")
            print(f"   Used fallback: {result.used_fallback}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Original text: '{result.original_text}'")
            
            # Check if it worked
            if result.used_fallback:
                print(f"   ✅ SUCCESS: Fallback protection activated!")
            elif 'eggplant' in result.raw_ingredient.lower():
                print(f"   ✅ SUCCESS: Correctly parsed as eggplant!")
            elif 'egg' in result.raw_ingredient.lower() and 'eggplant' not in result.raw_ingredient.lower():
                print(f"   ❌ FAILURE: Still parsed as eggs!")
            else:
                print(f"   ⚠️ UNEXPECTED: Parsed as something else")
                
        else:
            print(f"   ❌ No result returned")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This means the enhanced parser code is not properly installed.")
        
        # Check what's actually in the file
        parser_file = "backend/app/services/ingredient_parser.py"
        if os.path.exists(parser_file):
            with open(parser_file, 'r') as f:
                content = f.read()
                if 'DIETARY_MISPARSE_PATTERNS' in content:
                    print("✅ Enhanced code appears to be in the file")
                else:
                    print("❌ Enhanced code NOT found in the file")
        else:
            print(f"❌ File {parser_file} not found")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def test_integration():
    """Test if the integration is using the new functions"""
    print(f"\n🔌 TESTING INTEGRATION:")
    print("-" * 40)
    
    try:
        from app.services.ingredient_parser import parse_ingredients_list, get_shopping_list_items
        
        test_ingredients = ["2 medium eggplant", "3 large eggs"]
        
        print(f"   Testing with: {test_ingredients}")
        
        # Test the new functions
        structured = parse_ingredients_list(test_ingredients)
        shopping_items = get_shopping_list_items(structured)
        
        print(f"   Structured ingredients: {len(structured)}")
        print(f"   Shopping items: {len(shopping_items)}")
        
        for item in shopping_items:
            original = item.get('original', '')
            name = item.get('name', '')
            used_fallback = item.get('used_fallback', False)
            
            print(f"     '{original}' -> '{name}' (fallback: {used_fallback})")
            
            if 'eggplant' in original.lower() and 'egg' in name.lower() and 'eggplant' not in name.lower():
                print(f"       ❌ ISSUE: Eggplant still parsed as eggs!")
            elif 'eggplant' in original.lower():
                print(f"       ✅ GOOD: Eggplant handled correctly!")
                
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")


if __name__ == "__main__":
    test_eggplant_parsing()
    test_integration()
    
    print(f"\n💡 DIAGNOSIS:")
    print("If protection function isn't triggering, there's a bug in the pattern matching.")
    print("If it is triggering but result is still wrong, there's a bug in the fallback logic.")
    print("If everything looks good here but API still fails, it's an integration issue.")
