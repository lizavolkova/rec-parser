# debug_ingredient_parser.py - Test the eggplant parsing issue
from app.services.ingredient_parser import parse_ingredient_structured

def test_eggplant_parsing():
    print("🧪 Testing Eggplant vs Eggs Parsing")
    print("=" * 50)
    
    test_cases = [
        "2 medium eggplant",
        "3 large eggs",
        "1 small eggplant, diced",
        "6 egg whites"
    ]
    
    for ingredient_text in test_cases:
        print(f"\nTesting: '{ingredient_text}'")
        result = parse_ingredient_structured(ingredient_text)
        
        if result:
            print(f"  ✅ Parsed name: '{result.raw_ingredient}'")
            print(f"  📊 Confidence: {result.confidence:.6f}")
            print(f"  🔄 Used fallback: {result.used_fallback}")
            print(f"  🛒 Shopping display: '{result.shopping_display}'")
            
            # Check if this is the problematic case
            if "eggplant" in ingredient_text.lower() and result.raw_ingredient.lower() in ["eggs", "egg"]:
                print(f"  ❌ PROBLEM: Eggplant parsed as eggs!")
                print(f"  💡 This should have been caught by validation")
            elif "eggplant" in ingredient_text.lower() and result.used_fallback:
                print(f"  ✅ FIXED: Used fallback for eggplant")
            elif "egg" in ingredient_text.lower() and not "eggplant" in ingredient_text.lower():
                print(f"  ✅ CORRECT: Actual eggs parsed correctly")
        else:
            print(f"  ❌ Failed to parse")
        
        print("-" * 30)

if __name__ == "__main__":
    test_eggplant_parsing()
