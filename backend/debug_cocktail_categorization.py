# debug_cocktail_categorization.py
# Test and improve cocktail/drink categorization

import asyncio
import sys
import os

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

async def test_margarita_categorization():
    """Test the margarita recipe categorization"""
    print("🍹 DEBUGGING COCKTAIL CATEGORIZATION")
    print("=" * 60)
    
    # Test URL
    margarita_url = "https://cooking.nytimes.com/recipes/12855-dees-margarita"
    
    try:
        # Import recipe service
        from app.services.recipe_service import RecipeService
        
        print(f"📥 Testing recipe: {margarita_url}")
        
        # Parse the recipe
        recipe = await RecipeService.parse_recipe_hybrid(margarita_url)
        
        if recipe and recipe.title != "Unable to parse recipe":
            print(f"✅ Recipe parsed: {recipe.title}")
            print(f"📋 Ingredients: {len(recipe.ingredients)}")
            
            # Show ingredients
            print(f"\n🧪 INGREDIENTS:")
            for i, ingredient in enumerate(recipe.ingredients, 1):
                print(f"   {i:2d}. {ingredient}")
            
            # Check raw ingredients for alcohol keywords
            print(f"\n🔍 RAW INGREDIENTS ANALYSIS:")
            if hasattr(recipe, 'raw_ingredients') and recipe.raw_ingredients:
                alcohol_keywords = ['tequila', 'rum', 'vodka', 'gin', 'whiskey', 'wine', 'beer', 'liqueur', 'triple sec', 'cointreau']
                cocktail_keywords = ['lime juice', 'lemon juice', 'simple syrup', 'bitters', 'vermouth']
                
                found_alcohol = []
                found_cocktail = []
                
                for raw_ingredient in recipe.raw_ingredients:
                    ingredient_lower = raw_ingredient.lower()
                    
                    for keyword in alcohol_keywords:
                        if keyword in ingredient_lower:
                            found_alcohol.append(f"{raw_ingredient} (contains '{keyword}')")
                    
                    for keyword in cocktail_keywords:
                        if keyword in ingredient_lower:
                            found_cocktail.append(f"{raw_ingredient} (contains '{keyword}')")
                
                print(f"   🍸 Alcohol ingredients found: {len(found_alcohol)}")
                for item in found_alcohol:
                    print(f"     • {item}")
                
                print(f"   🍋 Cocktail ingredients found: {len(found_cocktail)}")
                for item in found_cocktail:
                    print(f"     • {item}")
                
                # Determine if this should be categorized as a cocktail
                should_be_cocktail = len(found_alcohol) > 0
                print(f"\n🎯 CATEGORIZATION RECOMMENDATION:")
                if should_be_cocktail:
                    print(f"   ✅ This SHOULD be categorized as: [cocktail, drink, alcoholic beverage]")
                else:
                    print(f"   ❌ No alcohol detected - not a cocktail")
            
            # Check if there's existing categorization
            print(f"\n📊 CURRENT CATEGORIZATION:")
            categorization_fields = ['dishType', 'cuisine', 'meal', 'season', 'tags']
            
            for field in categorization_fields:
                if hasattr(recipe, field):
                    value = getattr(recipe, field)
                    print(f"   {field}: {value}")
                else:
                    print(f"   {field}: NOT FOUND")
            
            # Check if AI categorization was used
            if hasattr(recipe, 'used_ai'):
                print(f"\n🤖 AI USAGE:")
                print(f"   Used AI: {recipe.used_ai}")
            
        else:
            print("❌ Recipe parsing failed")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def create_enhanced_categorization_rules():
    """Create enhanced categorization rules for cocktails and drinks"""
    print(f"\n💡 ENHANCED CATEGORIZATION RULES:")
    print("-" * 40)
    
    categorization_rules = {
        'cocktail_indicators': {
            'alcohol_spirits': [
                'tequila', 'rum', 'vodka', 'gin', 'whiskey', 'whisky', 'bourbon', 'scotch',
                'brandy', 'cognac', 'mezcal', 'sake', 'wine', 'champagne', 'prosecco',
                'beer', 'ale', 'lager', 'stout'
            ],
            'liqueurs': [
                'triple sec', 'cointreau', 'grand marnier', 'kahlua', 'baileys',
                'amaretto', 'chambord', 'limoncello', 'sambuca', 'schnapps',
                'crème de', 'liqueur'
            ],
            'cocktail_mixers': [
                'simple syrup', 'lime juice', 'lemon juice', 'bitters', 'vermouth',
                'tonic water', 'soda water', 'ginger beer', 'grenadine',
                'margarita mix', 'bloody mary mix'
            ],
            'cocktail_terms': [
                'cocktail shaker', 'muddled', 'rimmed with salt', 'garnish',
                'on the rocks', 'straight up', 'shaken', 'stirred'
            ]
        },
        
        'non_alcoholic_drinks': {
            'beverages': [
                'coffee', 'tea', 'hot chocolate', 'smoothie', 'juice',
                'lemonade', 'iced tea', 'milkshake', 'frappe', 'lassi'
            ],
            'mocktails': [
                'virgin', 'non-alcoholic', 'alcohol-free', 'mocktail'
            ]
        },
        
        'dish_types': {
            'alcoholic': ['cocktail', 'drink', 'alcoholic beverage', 'mixed drink'],
            'non_alcoholic': ['beverage', 'drink', 'non-alcoholic drink'],
            'hot_drinks': ['hot beverage', 'warm drink'],
            'cold_drinks': ['cold beverage', 'iced drink', 'frozen drink']
        }
    }
    
    return categorization_rules


def suggest_ai_prompt_improvements():
    """Suggest improvements to the AI categorization prompt"""
    print(f"\n🔧 AI PROMPT IMPROVEMENTS:")
    print("-" * 40)
    
    improved_prompt = """
ENHANCED CATEGORIZATION PROMPT:

When categorizing recipes, pay special attention to beverages and cocktails:

COCKTAIL/ALCOHOLIC DRINK INDICATORS:
- Contains spirits: tequila, rum, vodka, gin, whiskey, etc.
- Contains liqueurs: triple sec, cointreau, grand marnier, etc.
- Contains cocktail mixers: lime juice, simple syrup, bitters, etc.
- Instructions mention: shaking, stirring, rimming glass, garnishing
- Serving suggestions: on the rocks, straight up, in cocktail glass

CATEGORIZATION RULES:
1. If recipe contains ANY alcoholic spirit or liqueur:
   dishType: ["cocktail", "drink", "alcoholic beverage"]

2. If recipe is clearly a margarita (tequila + lime + orange liqueur):
   dishType: ["cocktail", "margarita", "drink", "alcoholic beverage"]
   cuisine: ["mexican", "tex-mex"] (optional)
   meal: ["happy hour", "party"] (optional)

3. If recipe is a non-alcoholic drink:
   dishType: ["beverage", "drink", "non-alcoholic drink"]

4. Consider serving context:
   - Party drinks, happy hour → meal: ["party", "happy hour"]
   - Summer drinks → season: ["summer"]
   - Holiday drinks → tags: ["holiday", "celebration"]

EXAMPLES:
- Margarita → dishType: ["cocktail", "margarita", "drink"]
- Moscow Mule → dishType: ["cocktail", "drink", "alcoholic beverage"]
- Virgin Mojito → dishType: ["beverage", "mocktail", "non-alcoholic drink"]
- Iced Coffee → dishType: ["beverage", "drink", "coffee"]
"""
    
    print(improved_prompt)


async def test_categorization_with_sample_ingredients():
    """Test categorization logic with sample margarita ingredients"""
    print(f"\n🧪 TESTING WITH SAMPLE MARGARITA INGREDIENTS:")
    print("-" * 50)
    
    sample_margarita_ingredients = [
        "2 ounces blanco tequila",
        "1 ounce triple sec",
        "1 ounce fresh lime juice", 
        "Salt for rim",
        "Lime wedge for garnish",
        "Ice"
    ]
    
    print("Sample Margarita Ingredients:")
    for ingredient in sample_margarita_ingredients:
        print(f"  • {ingredient}")
    
    # Test the enhanced parser on these ingredients
    try:
        from app.services.ingredient_parser import parse_ingredients_list
        
        structured = parse_ingredients_list(sample_margarita_ingredients)
        
        print(f"\n📋 PARSED INGREDIENTS:")
        alcohol_found = False
        cocktail_mixers_found = False
        
        for ing in structured:
            print(f"  • {ing.raw_ingredient}")
            
            # Check for alcohol
            if any(spirit in ing.raw_ingredient.lower() for spirit in ['tequila', 'rum', 'vodka', 'gin', 'whiskey']):
                alcohol_found = True
                print(f"    🍸 ALCOHOL DETECTED!")
            
            # Check for liqueurs
            if any(liqueur in ing.raw_ingredient.lower() for liqueur in ['triple sec', 'cointreau', 'grand marnier']):
                alcohol_found = True
                print(f"    🍸 LIQUEUR DETECTED!")
            
            # Check for cocktail mixers
            if any(mixer in ing.raw_ingredient.lower() for mixer in ['lime juice', 'lemon juice', 'simple syrup']):
                cocktail_mixers_found = True
                print(f"    🍋 COCKTAIL MIXER DETECTED!")
        
        print(f"\n🎯 CATEGORIZATION RESULT:")
        if alcohol_found:
            print(f"   ✅ SHOULD BE CATEGORIZED AS:")
            print(f"      dishType: ['cocktail', 'drink', 'alcoholic beverage']")
            if cocktail_mixers_found:
                print(f"      Additional: ['margarita'] (if tequila + lime + orange liqueur)")
        else:
            print(f"   ❌ No alcohol detected - not a cocktail")
            
    except Exception as e:
        print(f"   ❌ Error testing with enhanced parser: {e}")


if __name__ == "__main__":
    print("🚀 COCKTAIL CATEGORIZATION DEBUGGING")
    
    # Test the actual margarita recipe
    asyncio.run(test_margarita_categorization())
    
    # Show enhanced categorization rules
    create_enhanced_categorization_rules()
    
    # Suggest AI prompt improvements
    suggest_ai_prompt_improvements()
    
    # Test with sample ingredients
    asyncio.run(test_categorization_with_sample_ingredients())
    
    print(f"\n🎯 ACTION ITEMS:")
    print("1. Check if AI categorization prompt includes cocktail detection")
    print("2. Add alcohol/cocktail keywords to categorization logic")
    print("3. Test the enhanced prompt with the margarita recipe")
    print("4. Consider adding manual categorization rules for common cocktails")
