# simple_test.py - Quick test for AI categorization
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_simple():
    try:
        from app.models import Recipe
        from app.services.ai.recipe_categorizer import RecipeCategorizationService
        
        # Simple test recipe
        recipe = Recipe(
            title="Farro Salad with Parmesan",
            ingredients=[
                "1 cup farro",
                "1/4 cup parmesan cheese, grated",
                "2 tbsp olive oil",
                "1 tbsp lemon juice",
                "Salt and pepper"
            ],
            instructions=["Cook farro", "Mix with other ingredients"],
            raw_ingredients=[],
            raw_ingredients_detailed=[]
        )
        
        service = RecipeCategorizationService()
        result = await service.categorize_recipe(recipe)
        
        if result:
            print("✅ SUCCESS!")
            print(f"Health tags: {result.health_tags}")
            print(f"Easily veganizable: {result.adaptability.easily_veganizable}")
            print(f"Vegan adaptations: {result.adaptability.vegan_adaptations}")
        else:
            print("❌ FAILED")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())
