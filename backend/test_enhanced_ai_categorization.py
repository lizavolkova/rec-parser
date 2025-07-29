# backend/test_enhanced_ai_categorization.py
"""
Enhanced test script to verify AI recipe categorization with adaptability detection
Run this to test your enhanced AI integration including vegan/vegetarian/healthy adaptations
"""

import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your enhanced services
from app.models import Recipe
from app.services.ai.recipe_categorizer import RecipeCategorizationService, EnhancedRecipeService

async def test_adaptability_detection():
    """Test the new adaptability detection features"""
    print("🌱 Testing AI Adaptability Detection")
    print("=" * 60)
    
    # Create test recipes that should trigger different adaptability suggestions
    test_recipes = [
        # Recipe that should be easily veganizable
        Recipe(
            title="Creamy Chicken Alfredo Pasta",
            description="Rich pasta with chicken, cream, and parmesan cheese",
            ingredients=[
                "1 lb fettuccine pasta",
                "2 chicken breasts, sliced",
                "1 cup heavy cream", 
                "1/2 cup butter",
                "1 cup parmesan cheese, grated",
                "3 cloves garlic, minced",
                "Salt and black pepper",
                "Fresh parsley for garnish"
            ],
            instructions=[
                "Cook pasta according to package directions",
                "Season and cook chicken until golden brown",
                "Melt butter, add garlic and cook briefly", 
                "Add heavy cream and bring to simmer",
                "Add parmesan cheese and stir until melted",
                "Toss pasta with sauce and top with chicken",
                "Garnish with parsley and serve"
            ],
            prep_time="15 minutes",
            cook_time="20 minutes", 
            servings="4",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # BUG TEST: Recipe that's already vegetarian but might get vegetarian adaptations
        Recipe(
            title="Classic Pumpkin Pie (Vegetarian Bug Test)",
            description="Traditional pumpkin pie with eggs and dairy - already vegetarian",
            ingredients=[
                "1 pre-made pie crust",
                "15 oz pumpkin puree",
                "3 large eggs",
                "1 cup heavy cream",
                "1/2 cup brown sugar",
                "1/4 cup granulated sugar",
                "1 tsp vanilla extract",
                "1 tsp ground cinnamon",
                "1/2 tsp ground nutmeg",
                "1/2 tsp salt"
            ],
            instructions=[
                "Preheat oven to 425°F",
                "Mix pumpkin puree, eggs, and cream",
                "Add sugars, vanilla, and spices",
                "Pour into pie crust",
                "Bake for 15 minutes, then reduce to 350°F",
                "Bake additional 40-50 minutes until set"
            ],
            prep_time="15 minutes",
            cook_time="60 minutes",
            servings="8",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # Recipe that should be easily vegetarianizable
        Recipe(
            title="Beef and Vegetable Stir Fry",
            description="Quick stir fry with beef strips and fresh vegetables",
            ingredients=[
                "1 lb beef sirloin, sliced thin",
                "2 cups broccoli florets",
                "1 red bell pepper, sliced",
                "1 cup snap peas",
                "3 cloves garlic, minced",
                "2 tbsp vegetable oil",
                "3 tbsp soy sauce",
                "1 tbsp cornstarch",
                "1 tsp sesame oil",
                "Green onions for garnish"
            ],
            instructions=[
                "Heat oil in wok over high heat",
                "Add beef and stir-fry until browned",
                "Remove beef and set aside",
                "Add vegetables and stir-fry until crisp-tender",
                "Return beef to wok",
                "Add sauce mixture and toss to coat",
                "Serve immediately over rice"
            ],
            prep_time="20 minutes",
            cook_time="10 minutes",
            servings="4",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # Recipe that should be easily healthified
        Recipe(
            title="Classic Chocolate Chip Cookies",
            description="Soft and chewy cookies loaded with chocolate chips",
            ingredients=[
                "2 1/4 cups all-purpose flour",
                "1 cup butter, softened",
                "3/4 cup granulated sugar",
                "3/4 cup brown sugar, packed",
                "2 large eggs",
                "2 tsp vanilla extract",
                "1 tsp baking soda",
                "1 tsp salt",
                "2 cups chocolate chips"
            ],
            instructions=[
                "Preheat oven to 375°F",
                "Cream butter and sugars until fluffy",
                "Beat in eggs and vanilla",
                "Mix in flour, baking soda, and salt",
                "Stir in chocolate chips",
                "Drop dough onto baking sheets",
                "Bake 9-11 minutes until golden brown"
            ],
            prep_time="15 minutes",
            cook_time="11 minutes",
            servings="36 cookies",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # Recipe that's already vegan (should not suggest veganizing)
        Recipe(
            title="Mediterranean Quinoa Salad",
            description="Fresh quinoa salad with vegetables and herbs",
            ingredients=[
                "1 cup quinoa, rinsed",
                "2 cups vegetable broth",
                "1 cucumber, diced",
                "2 tomatoes, diced",
                "1/4 cup red onion, diced",
                "1/4 cup fresh parsley, chopped",
                "2 tbsp olive oil",
                "2 tbsp lemon juice",
                "1 tsp dried oregano",
                "Salt and pepper to taste"
            ],
            instructions=[
                "Cook quinoa in vegetable broth until tender",
                "Let quinoa cool completely",
                "Mix in all vegetables and herbs",
                "Whisk together oil, lemon juice, and oregano",
                "Toss salad with dressing",
                "Season with salt and pepper",
                "Chill before serving"
            ],
            prep_time="15 minutes",
            cook_time="15 minutes",
            servings="6",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        ),
        
        # BUG TEST: Recipe that's clearly vegan but AI might hallucinate non-vegan ingredients
        Recipe(
            title="Peanut Chili Oil Cucumber Salad",
            description="Fresh and spicy cucumber salad with peanut chili oil dressing",
            ingredients=[
                "3 large cucumbers, julienned",
                "2 tbsp peanut oil",
                "1 tbsp chili oil", 
                "2 tbsp rice vinegar",
                "1 tbsp soy sauce",
                "1 tsp sesame oil",
                "2 cloves garlic, minced",
                "1 tsp sugar",
                "1/4 cup roasted peanuts, crushed",
                "2 green onions, sliced",
                "Fresh cilantro for garnish",
                "Salt to taste"
            ],
            instructions=[
                "Julienne cucumbers and salt them lightly",
                "Let cucumbers drain for 10 minutes",
                "Mix oils, vinegar, soy sauce, garlic, and sugar",
                "Toss cucumbers with dressing",
                "Top with peanuts, green onions, and cilantro",
                "Serve immediately"
            ],
            prep_time="20 minutes",
            cook_time="0 minutes",
            servings="4",
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
    ]
    
    categorization_service = RecipeCategorizationService()
    
    for i, recipe in enumerate(test_recipes, 1):
        print(f"\n🍽️ Test Recipe {i}: {recipe.title}")
        print(f"Description: {recipe.description}")
        
        try:
            categorization = await categorization_service.categorize_recipe(recipe)
            
            if categorization and categorization.adaptability:
                print(f"✅ Categorization and adaptability analysis successful!")
                
                # Show basic categorization
                print(f"   📋 Basic Categories:")
                print(f"      Health Tags: {categorization.health_tags}")
                print(f"      Dish Type: {categorization.dish_type}")
                print(f"      Cuisine: {categorization.cuisine_type}")
                print(f"      Meal Type: {categorization.meal_type}")
                
                # Show adaptability analysis
                print(f"   🌱 Adaptability Analysis:")
                adaptability = categorization.adaptability
                
                if adaptability.easily_veganizable:
                    print(f"      ✅ Easily Veganizable: YES")
                    print(f"         How: {adaptability.vegan_adaptations[:100]}...")
                else:
                    print(f"      ❌ Easily Veganizable: NO")
                
                if adaptability.easily_vegetarianizable:
                    print(f"      ✅ Easily Vegetarianizable: YES") 
                    print(f"         How: {adaptability.vegetarian_adaptations[:100]}...")
                else:
                    print(f"      ❌ Easily Vegetarianizable: NO")
                
                if adaptability.easily_healthified:
                    print(f"      ✅ Easily Healthified: YES")
                    print(f"         How: {adaptability.healthy_adaptations[:100]}...")
                else:
                    print(f"      ❌ Easily Healthified: NO")
                
                print(f"   💭 AI Reasoning: {categorization.confidence_notes[:150]}...")
                
            else:
                print(f"❌ Categorization failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

async def test_enhanced_recipe_service_with_adaptability():
    """Test the enhanced recipe service with real URLs to see adaptability in action"""
    print("\n🌐 Testing Enhanced Recipe Service with Adaptability")
    print("=" * 60)
    
    # Test URLs - using recipes that should have good adaptability potential
    test_urls = [
        "https://www.loveandlemons.com/spaghetti-carbonara-recipe/",  # Should be veganizable
        # Add more test URLs as needed - look for recipes with dairy/meat that could be adapted
    ]
    
    enhanced_service = EnhancedRecipeService()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔗 Test URL {i}: {url}")
        
        try:
            recipe = await enhanced_service.parse_and_categorize_recipe(url)
            
            if recipe and recipe.title != "Unable to parse recipe":
                print(f"✅ Recipe parsing successful!")
                print(f"   📝 Title: {recipe.title}")
                print(f"   🥘 Ingredients: {len(recipe.ingredients)} items")
                print(f"   📋 Instructions: {len(recipe.instructions)} steps")
                print(f"   🏷️ Source: {recipe.source}")
                print(f"   🖼️ Image: {'Yes' if recipe.image else 'No'}")
                
                if recipe.ai_enhanced:
                    print(f"   🤖 AI Enhanced: Yes")
                    print(f"      Health Tags: {recipe.health_tags}")
                    print(f"      Cuisine: {recipe.cuisine_type}")
                    
                    # Show adaptability results
                    print(f"   🌱 Adaptability Options:")
                    
                    if recipe.easily_veganizable:
                        print(f"      ✅ Can be made VEGAN:")
                        print(f"         {recipe.vegan_adaptations}")
                    
                    if recipe.easily_vegetarianizable:
                        print(f"      ✅ Can be made VEGETARIAN:")
                        print(f"         {recipe.vegetarian_adaptations}")
                    
                    if recipe.easily_healthified:
                        print(f"      ✅ Can be made HEALTHIER:")
                        print(f"         {recipe.healthy_adaptations}")
                    
                    if not any([recipe.easily_veganizable, recipe.easily_vegetarianizable, recipe.easily_healthified]):
                        print(f"      ℹ️ No easy adaptations suggested by AI")
                        
                else:
                    print(f"   🤖 AI Enhanced: No")
            else:
                print(f"❌ Recipe parsing failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

async def test_bug_validation():
    """Test specific bug scenarios to ensure they're fixed"""
    print("\n🐛 Testing Bug Validation & Fixes")
    print("=" * 60)
    
    # Test the specific bug: vegan recipe incorrectly getting vegan adaptations
    bug_test_recipe = Recipe(
        title="Peanut Chili Oil Cucumber Salad (Bug Test)",
        description="Already vegan recipe that should NOT get vegan adaptations",
        ingredients=[
            "3 large cucumbers, julienned",
            "2 tbsp peanut oil",
            "1 tbsp chili oil", 
            "2 tbsp rice vinegar",
            "1 tbsp soy sauce",
            "1 tsp sesame oil",
            "2 cloves garlic, minced",
            "1 tsp sugar",
            "1/4 cup roasted peanuts, crushed",
            "2 green onions, sliced",
            "Fresh cilantro for garnish",
            "Salt to taste"
        ],
        instructions=[
            "Julienne cucumbers and salt them lightly",
            "Let cucumbers drain for 10 minutes", 
            "Mix oils, vinegar, soy sauce, garlic, and sugar",
            "Toss cucumbers with dressing",
            "Top with peanuts, green onions, and cilantro"
        ],
        prep_time="20 minutes",
        cook_time="0 minutes",
        servings="4",
        raw_ingredients=[],
        raw_ingredients_detailed=[]
    )
    
    categorization_service = RecipeCategorizationService()
    
    print(f"🧪 Testing: {bug_test_recipe.title}")
    print("Expected behavior:")
    print("  - Should be tagged as 'vegan' (all ingredients are plant-based)")
    print("  - Should NOT suggest vegan adaptations (already vegan)")
    print("  - Should NOT mention honey or other non-existent ingredients")
    
    try:
        categorization = await categorization_service.categorize_recipe(bug_test_recipe)
        
        if categorization and categorization.adaptability:
            adaptability = categorization.adaptability
            health_tags = categorization.health_tags
            
            print(f"\nResults:")
            print(f"  Health tags: {health_tags}")
            print(f"  Easily veganizable: {adaptability.easily_veganizable}")
            print(f"  Vegan adaptations: {adaptability.vegan_adaptations}")
            
            # Check for the specific bug
            is_tagged_vegan = 'vegan' in [tag.lower() for tag in health_tags]
            suggests_vegan_adaptations = adaptability.easily_veganizable and adaptability.vegan_adaptations
            
            if is_tagged_vegan and suggests_vegan_adaptations:
                print(f"  ❌ BUG DETECTED: Recipe tagged as vegan but still suggests vegan adaptations!")
                print(f"  Problematic suggestion: {adaptability.vegan_adaptations}")
        async def test_adaptability_accuracy():
    """Test the accuracy of adaptability suggestions with known cases"""
    print("\n🎯 Testing Adaptability Accuracy")
    print("=" * 60)
    
    # Test cases where we know what the AI should suggest
    accuracy_tests = [
        {
            "recipe": Recipe(
                title="Butter Cookies",
                ingredients=["flour", "butter", "sugar", "eggs", "vanilla"],
                instructions=["Mix ingredients", "Bake at 350F"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": True,
            "expected_vegetarianizable": False,  # Already vegetarian
            "expected_healthifiable": True,
            "reasoning": "Simple butter/egg substitutions should make this easily vegan"
        },
        {
            "recipe": Recipe(
                title="Grilled Chicken Salad",
                ingredients=["chicken breast", "mixed greens", "tomatoes", "cucumber", "olive oil", "lemon juice"],
                instructions=["Grill chicken", "Toss with vegetables"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": True,
            "expected_vegetarianizable": True,
            "expected_healthifiable": False,  # Already healthy
            "reasoning": "Chicken can be replaced with plant protein easily"
        },
        {
            "recipe": Recipe(
                title="Quinoa Buddha Bowl", 
                ingredients=["quinoa", "sweet potato", "kale", "avocado", "chickpeas", "tahini", "lemon"],
                instructions=["Cook quinoa", "Roast vegetables", "Assemble bowl"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": False,  # Already vegan
            "expected_vegetarianizable": False,  # Already vegetarian
            "expected_healthifiable": False,  # Already healthy
            "reasoning": "Already meets all criteria"
        }
    ]
    
    categorization_service = RecipeCategorizationService()
    correct_predictions = 0
    total_predictions = 0
    
    for test_case in accuracy_tests:
        recipe = test_case["recipe"]
        print(f"\n🧪 Testing: {recipe.title}")
        print(f"Expected: Vegan={test_case['expected_veganizable']}, Veg={test_case['expected_vegetarianizable']}, Healthy={test_case['expected_healthifiable']}")
        print(f"Reasoning: {test_case['reasoning']}")
        
        try:
            categorization = await categorization_service.categorize_recipe(recipe)
            
            if categorization and categorization.adaptability:
                adaptability = categorization.adaptability
                print(f"Actual: Vegan={adaptability.easily_veganizable}, Veg={adaptability.easily_vegetarianizable}, Healthy={adaptability.easily_healthified}")
                
                # Check accuracy
                vegan_correct = adaptability.easily_veganizable == test_case['expected_veganizable']
                veg_correct = adaptability.easily_vegetarianizable == test_case['expected_vegetarianizable']
                healthy_correct = adaptability.easily_healthified == test_case['expected_healthifiable']
                
                correct_predictions += sum([vegan_correct, veg_correct, healthy_correct])
                total_predictions += 3
                
                print(f"Accuracy: Vegan={'✅' if vegan_correct else '❌'}, Veg={'✅' if veg_correct else '❌'}, Healthy={'✅' if healthy_correct else '❌'}")
                
                if adaptability.vegan_adaptations:
                    print(f"Vegan suggestion: {adaptability.vegan_adaptations[:100]}...")
                if adaptability.vegetarian_adaptations:
                    print(f"Vegetarian suggestion: {adaptability.vegetarian_adaptations[:100]}...")
                if adaptability.healthy_adaptations:
                    print(f"Healthy suggestion: {adaptability.healthy_adaptations[:100]}...")
                    
            else:
                print("❌ Categorization failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    if total_predictions > 0:
        accuracy_percentage = (correct_predictions / total_predictions) * 100
        print(f"\n📊 Overall Accuracy: {correct_predictions}/{total_predictions} ({accuracy_percentage:.1f}%)")
        
        if accuracy_percentage >= 70:
            print("✅ Good accuracy! Adaptability detection is working well.")
        else:
            print("⚠️ Lower accuracy - may need prompt tuning or more testing.")
            elif is_tagged_vegan and not suggests_vegan_adaptations:
                print(f"  ✅ BUG FIXED: Recipe correctly tagged as vegan with no vegan adaptations")
                return True
            elif not is_tagged_vegan:
                print(f"  ⚠️ ISSUE: Recipe should be tagged as vegan but isn't")
                print(f"  Ingredients are all plant-based: {bug_test_recipe.ingredients}")
                return False
            else:
                print(f"  ✅ WORKING: Correct logic applied")
                return True
                
        else:
            print(f"❌ Categorization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    print("\n🎯 Testing Adaptability Accuracy")
    print("=" * 60)
    
    # Test cases where we know what the AI should suggest
    accuracy_tests = [
        {
            "recipe": Recipe(
                title="Butter Cookies",
                ingredients=["flour", "butter", "sugar", "eggs", "vanilla"],
                instructions=["Mix ingredients", "Bake at 350F"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": True,
            "expected_vegetarianizable": False,  # Already vegetarian
            "expected_healthifiable": True,
            "reasoning": "Simple butter/egg substitutions should make this easily vegan"
        },
        {
            "recipe": Recipe(
                title="Grilled Chicken Salad",
                ingredients=["chicken breast", "mixed greens", "tomatoes", "cucumber", "olive oil", "lemon juice"],
                instructions=["Grill chicken", "Toss with vegetables"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": True,
            "expected_vegetarianizable": True,
            "expected_healthifiable": False,  # Already healthy
            "reasoning": "Chicken can be replaced with plant protein easily"
        },
        {
            "recipe": Recipe(
                title="Quinoa Buddha Bowl", 
                ingredients=["quinoa", "sweet potato", "kale", "avocado", "chickpeas", "tahini", "lemon"],
                instructions=["Cook quinoa", "Roast vegetables", "Assemble bowl"],
                raw_ingredients=[],
                raw_ingredients_detailed=[]
            ),
            "expected_veganizable": False,  # Already vegan
            "expected_vegetarianizable": False,  # Already vegetarian
            "expected_healthifiable": False,  # Already healthy
            "reasoning": "Already meets all criteria"
        }
    ]
    
    categorization_service = RecipeCategorizationService()
    correct_predictions = 0
    total_predictions = 0
    
    for test_case in accuracy_tests:
        recipe = test_case["recipe"]
        print(f"\n🧪 Testing: {recipe.title}")
        print(f"Expected: Vegan={test_case['expected_veganizable']}, Veg={test_case['expected_vegetarianizable']}, Healthy={test_case['expected_healthifiable']}")
        print(f"Reasoning: {test_case['reasoning']}")
        
        try:
            categorization = await categorization_service.categorize_recipe(recipe)
            
            if categorization and categorization.adaptability:
                adaptability = categorization.adaptability
                print(f"Actual: Vegan={adaptability.easily_veganizable}, Veg={adaptability.easily_vegetarianizable}, Healthy={adaptability.easily_healthified}")
                
                # Check accuracy
                vegan_correct = adaptability.easily_veganizable == test_case['expected_veganizable']
                veg_correct = adaptability.easily_vegetarianizable == test_case['expected_vegetarianizable']
                healthy_correct = adaptability.easily_healthified == test_case['expected_healthifiable']
                
                correct_predictions += sum([vegan_correct, veg_correct, healthy_correct])
                total_predictions += 3
                
                print(f"Accuracy: Vegan={'✅' if vegan_correct else '❌'}, Veg={'✅' if veg_correct else '❌'}, Healthy={'✅' if healthy_correct else '❌'}")
                
                if adaptability.vegan_adaptations:
                    print(f"Vegan suggestion: {adaptability.vegan_adaptations[:100]}...")
                if adaptability.vegetarian_adaptations:
                    print(f"Vegetarian suggestion: {adaptability.vegetarian_adaptations[:100]}...")
                if adaptability.healthy_adaptations:
                    print(f"Healthy suggestion: {adaptability.healthy_adaptations[:100]}...")
                    
            else:
                print("❌ Categorization failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    if total_predictions > 0:
        accuracy_percentage = (correct_predictions / total_predictions) * 100
        print(f"\n📊 Overall Accuracy: {correct_predictions}/{total_predictions} ({accuracy_percentage:.1f}%)")
        
        if accuracy_percentage >= 70:
            print("✅ Good accuracy! Adaptability detection is working well.")
        else:
            print("⚠️ Lower accuracy - may need prompt tuning or more testing.")

def print_enhanced_test_summary():
    """Print information about running the enhanced tests"""
    print("🚀 Enhanced AI Recipe Categorization Test Suite")
    print("=" * 60)
    print("This script tests your enhanced AI categorization with adaptability features:")
    print("1. 🌱 Test adaptability detection (vegan, vegetarian, healthy)")
    print("2. 🌐 Test real recipe URLs with adaptability analysis")
    print("3. 🎯 Test accuracy of adaptability suggestions")
    print("")
    print("NEW FEATURES BEING TESTED:")
    print("✨ Easily Veganizable Detection & Instructions")
    print("✨ Easily Vegetarianizable Detection & Instructions") 
    print("✨ Easily Healthifiable Detection & Instructions")
    print("✨ User-friendly adaptation explanations")
    print("")
    print("Prerequisites:")
    print("- OPENAI_API_KEY set in your .env file")
    print("- Enhanced AI categorization service files installed")
    print("- Internet connection for URL parsing tests")
    print("")

async def main():
    """Run all enhanced tests"""
    print_enhanced_test_summary()
    
    try:
        await test_adaptability_detection()
        await test_enhanced_recipe_service_with_adaptability()
        bug_test_passed = await test_bug_validation()  # NEW: Bug validation test
        await test_adaptability_accuracy()
        
        print("\n🎉 All enhanced tests completed!")
        
        if bug_test_passed:
            print("✅ Bug validation passed - no incorrect adaptations for already-compliant recipes!")
        else:
            print("❌ Bug validation failed - check the logic for suggesting adaptations")
        
        print("\nWhat to look for in results:")
        print("✅ Recipes with dairy/meat should be marked as 'easily veganizable/vegetarianizable'")
        print("✅ Recipes with processed ingredients should be marked as 'easily healthifiable'")
        print("✅ Already vegan/healthy recipes should NOT be marked for those adaptations")
        print("✅ Adaptation instructions should be specific and actionable")
        print("✅ No suggestions for ingredients that don't exist in the recipe")
        print("\nNext steps:")
        print("1. Try the /test-ai-categorization endpoint in your API")
        print("2. Test the new /analyze-adaptability endpoint")
        print("3. Check the enhanced /debug-ai-categorization endpoint")
        print("4. Add database persistence for the adaptability data")
        print("5. Build UI components to display adaptation suggestions")
        
    except Exception as e:
        print(f"\n❌ Enhanced test suite failed with error: {e}")
        print("Check your environment setup and try again")

if __name__ == "__main__":
    asyncio.run(main())
