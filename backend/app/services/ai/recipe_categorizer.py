# backend/app/services/ai/recipe_categorizer.py (ROBUST VERSION)
import json
import traceback
from typing import Optional, List, Dict, Any
from app.config import openai_client, settings
from app.models import Recipe, RecipeCategorization
import asyncio

class RecipeCategorizationService:
    """AI-powered recipe categorization service"""
    
    # Reference data for AI prompts
    HEALTH_TAGS = [
        "vegan", "vegetarian", "dairy free", "red meat free", "nut free", 
        "gluten free", "paleo", "keto", "FODMAP free", "pescatarian", 
        "healthy", "whole30", "easily veganizable"
    ]
    
    DISH_TYPES = [
        "bread", "dessert", "pies and tarts", "salad", "sandwich", "seafood",
        "side dish", "main course", "soup or stew", "curry", "special occasion",
        "starter or appetizer", "sweet", "pasta", "egg", "drink",
        "condiment or sauce", "grilling", "alcohol cocktail", "biscuits and cookies",
        "drinks", "ice cream and custard", "pizza", "preserve", "sheet pan meal",
        "grain bowl", "freezer-friendly"
    ]
    
    CUISINE_TYPES = [
        "american", "asian", "british", "caribbean", "central europe", "chinese",
        "eastern europe", "french", "greek", "indian", "italian", "japanese",
        "korean", "mediterranean", "mexican", "middle eastern", "nordic",
        "south american", "south east asian", "african"
    ]
    
    MEAL_TYPES = [
        "breakfast", "brunch", "lunch", "dinner", "snack", "dessert"
    ]
    
    SEASONS = [
        "spring", "summer", "winter", "autumn"
    ]
    
    async def categorize_recipe(self, recipe: Recipe) -> Optional[RecipeCategorization]:
        """
        Analyze a recipe and return AI-generated categorization
        """
        if not openai_client:
            print("❌ AI categorization requested but OpenAI client not available")
            return None
        
        try:
            print(f"🤖 Starting AI categorization for: {recipe.title}")
            
            # Step 1: Basic categorization
            basic_prompt = self._build_basic_categorization_prompt(recipe)
            basic_response = await self._call_openai(basic_prompt, "basic categorization")
            
            if not basic_response:
                print("❌ Basic categorization failed")
                return None
            
            basic_data = self._parse_basic_response(basic_response)
            if not basic_data:
                print("❌ Could not parse basic categorization")
                return None
            
            # Step 2: Adaptability analysis
            adaptability_prompt = self._build_adaptability_prompt(recipe, basic_data)
            adaptability_response = await self._call_openai(adaptability_prompt, "adaptability analysis")
            
            adaptability_data = {}
            if adaptability_response:
                adaptability_data = self._parse_adaptability_response(adaptability_response)
            
            # Step 3: Combine results
            return self._create_categorization(basic_data, adaptability_data, recipe.title, recipe.ingredients)
            
        except Exception as e:
            print(f"🤖 AI categorization failed: {e}")
            print(f"🤖 Traceback: {traceback.format_exc()}")
            return None
    
    async def _call_openai(self, prompt: str, operation: str) -> Optional[str]:
        """Make OpenAI API call with error handling"""
        try:
            response = openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a culinary expert AI. Always respond with valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS,
                seed=getattr(settings, 'AI_SEED', 42)
            )
            
            result = response.choices[0].message.content.strip()
            print(f"🤖 {operation} response received (length: {len(result)})")
            return result
            
        except Exception as e:
            print(f"❌ OpenAI API call failed for {operation}: {e}")
            return None
    
    def _build_basic_categorization_prompt(self, recipe: Recipe) -> str:
        """Build prompt for basic categorization with detailed analysis"""
        
        ingredients_text = "\n".join([f"- {ing}" for ing in recipe.ingredients[:15]])
        if len(recipe.ingredients) > 15:
            ingredients_text += f"\n... and {len(recipe.ingredients) - 15} more"
        
        instructions_text = " ".join(recipe.instructions[:2])[:200] + "..." if recipe.instructions else "No instructions"
        
        return f"""Analyze this recipe comprehensively and categorize it. Return ONLY valid JSON.

RECIPE: {recipe.title}
DESCRIPTION: {recipe.description or 'No description'}
INGREDIENTS:
{ingredients_text}
COOKING METHOD: {instructions_text}

Return this exact JSON structure:
{{
    "health_tags": [],
    "dish_type": [],
    "cuisine_type": [],
    "meal_type": [],
    "season": [],
    "confidence_notes": "",
    "confidence_notes_user": ""
}}

DETAILED ANALYSIS REQUIRED:

HEALTH TAGS - Systematic dietary analysis (be very precise):
- "vegan": ALL ingredients are plant-based (vegetables, grains, oils, herbs, spices, nuts, seeds)
- "vegetarian": No meat/seafood but may contain dairy (cheese, butter, milk) or eggs
- "healthy": Nutrient-dense ingredients (vegetables, whole grains, lean proteins, healthy fats)
- "dairy free": No milk, cheese, butter, cream, yogurt products

CRITICAL VEGAN VS VEGETARIAN RULES:
- ONLY mark as "vegetarian" if you can identify SPECIFIC dairy or egg ingredients
- Do NOT assume hidden dairy/eggs - only categorize based on listed ingredients

VEGAN INGREDIENTS (100% plant-based):
- ALL vegetables: eggplant, zucchini, tomatoes, onions, garlic, peppers, etc.
- ALL plant oils: olive oil, vegetable oil, sunflower oil, coconut oil, avocado oil, etc.
- ALL herbs and spices: basil, oregano, thyme, salt, pepper, etc.
- ALL grains: rice, quinoa, farro, wheat, oats, etc.
- ALL legumes: beans, lentils, chickpeas, etc.
- ALL nuts and seeds: almonds, walnuts, sesame seeds, etc.
- Vinegar, lemon juice, lime juice, wine (for cooking)

ACTUAL DAIRY/EGG INGREDIENTS (NOT vegan):
- Cheese: "parmesan", "mozzarella", "feta", "cheddar", "goat cheese", etc.
- Dairy: "butter", "milk", "cream", "heavy cream", "yogurt", "sour cream"
- Eggs: "egg", "eggs", "egg whites", "mayonnaise" 
- Other animal: "honey", "gelatin"

CRITICAL ERRORS TO AVOID:
- Olive oil is NOT dairy - it's from olives (plant-based)
- Vegetable oil is NOT dairy - it's from plants
- All plant oils are VEGAN, not vegetarian

If ALL ingredients are clearly plant-based = "vegan" (not vegetarian)

MANDATORY: If you mark a recipe as "vegetarian" (not vegan), you MUST explain in confidence_notes EXACTLY which dairy/egg ingredients you found that prevent it from being vegan. Do NOT mention plant oils as dairy.

DISH TYPES - What kind of dish is this:
- "salad": Mixed ingredients, often raw or lightly cooked, served cold/room temp
- "main course": Substantial dish that could be a meal centerpiece
- "side dish": Accompanies main dishes
- "soup", "pasta", "dessert", etc.

CUISINE TYPES - Cultural/regional style based on ingredients, techniques, and dish names:
- "american": Classic American dishes (cobbler, pie, BBQ, mac and cheese, meatloaf, pancakes, cornbread, biscuits, fried chicken, apple pie, etc.)
- "italian": pasta, olive oil, parmesan, herbs like basil, oregano, tomato-based sauces
- "mediterranean": olive oil, lemon, herbs, fresh vegetables, feta cheese
- "asian": soy sauce, sesame oil, ginger, rice, noodles (be specific if possible: chinese, japanese, korean, thai)
- "mexican": cumin, cilantro, lime, peppers, tortillas, beans
- "french": butter, cream sauces, wine, refined techniques
- "indian": curry spices, garam masala, turmeric, coriander, basmati rice

CUISINE DETECTION RULES:
- Look at dish TYPE first: cobbler, pie, cornbread, biscuits, barbecue = american
- Consider cooking techniques: deep-frying, grilling, baking fruit desserts = often american
- Regional ingredients: blueberries in baked goods, pecans, maple syrup = american
- Traditional dish names: if it's a well-known dish from a specific culture, tag accordingly
- If no clear cultural markers, use "american" as default for simple, home-style cooking

MEAL TYPES - When would this typically be eaten:
- "lunch": Light-moderate dishes, salads, sandwiches
- "dinner": More substantial dishes, main courses
- "breakfast": Morning foods
- "snack": Small portions
- Salads can be both lunch AND dinner - include both if appropriate

SEASONS - When are main ingredients in season or when is dish typically enjoyed:
- "spring": Fresh greens, asparagus, peas, light dishes
- "summer": Tomatoes, cucumbers, berries, cold/fresh dishes  
- "autumn": Squash, apples, hearty warming dishes
- "winter": Root vegetables, stews, warming comfort foods
- Fresh salads with vegetables = typically spring/summer
- Look at the main ingredients to determine seasonality

CONFIDENCE NOTES - REQUIRED:
Provide TWO types of explanations:

confidence_notes: Detailed explanation (2-3 sentences) for developers/detailed analysis:
- Why you chose the health tags (what made it vegetarian vs vegan, why healthy/not)
- CRITICAL: If marked as "vegetarian", explicitly state which dairy/egg ingredients you found
- What made you pick the dish type and cuisine
- Why you assigned those meal types and seasons
- Keep tone conversational and informative

confidence_notes_user: Condensed version (1-2 sentences) for end users:
- Give an interesting, digestible overview of your reasoning
- Focus on the most notable aspects (cuisine style, health benefits, seasonality)
- Make it engaging and informative without technical details
- Think "what would a food enthusiast find interesting about this categorization?"

EXAMPLE CONFIDENCE NOTES:
confidence_notes: "This is a vegetarian grain salad featuring nutrient-rich farro and fresh vegetables, making it healthy. The parmesan cheese prevents it from being vegan. With Italian ingredients like parmesan and olive oil, it has Mediterranean/Italian influences. Fresh ingredients make it perfect for spring and summer meals, and it works well for both lunch and dinner."

confidence_notes_user: "A healthy Mediterranean-style grain salad that's perfect for fresh spring and summer dining, featuring nutrient-rich farro and Italian flavors."

EXAMPLE FOR VEGAN DISH (all plant ingredients):
confidence_notes: "This is a vegan Mediterranean vegetable dish with all plant-based ingredients: eggplant, zucchini, tomatoes, onions, garlic, olive oil, and herbs. It's healthy due to the abundance of fresh vegetables and minimal processing. The combination of Mediterranean vegetables and French cooking technique gives it a clear French cuisine identity, perfect for summer when these vegetables are in season."

EXAMPLE FOR VEGETARIAN DISH (must specify actual dairy/egg found):
confidence_notes: "This is vegetarian due to the butter and heavy cream used in the sauce, preventing it from being vegan. The cream-based sauce and pasta make it a comforting Italian dish perfect for dinner."

WRONG EXAMPLE (DO NOT DO THIS):
confidence_notes: "This recipe is vegetarian due to potential dairy ingredients like olive oil." ← WRONG! Olive oil is plant-based and vegan!

Be thorough but accurate. Return valid JSON only."""

    def _build_adaptability_prompt(self, recipe: Recipe, basic_data: Dict) -> str:
        """Build comprehensive prompt for adaptability analysis"""
        
        health_tags = [tag.lower() for tag in basic_data.get('health_tags', [])]
        is_vegetarian = 'vegetarian' in health_tags
        is_vegan = 'vegan' in health_tags
        is_healthy = 'healthy' in health_tags
        
        ingredients_text = "\n".join([f"- {ing}" for ing in recipe.ingredients[:15]])
        
        return f"""Analyze if this recipe can be easily adapted. Return ONLY valid JSON.

RECIPE: {recipe.title}
CURRENT CLASSIFICATION: Health tags = {basic_data.get('health_tags', [])}
INGREDIENTS:
{ingredients_text}

Return this exact JSON structure:
{{
    "easily_veganizable": false,
    "vegan_adaptations": null,
    "easily_vegetarianizable": false,
    "vegetarian_adaptations": null,
    "easily_healthified": false,
    "healthy_adaptations": null
}}

DETAILED ADAPTABILITY ANALYSIS:

VEGAN ADAPTABILITY:
Current status: vegetarian={is_vegetarian}, vegan={is_vegan}
Mark "easily_veganizable" as TRUE if:
- Recipe is currently vegetarian (has dairy/eggs but no meat)
- Contains only 1-3 easily replaceable/omittable dairy ingredients
- Examples: parmesan cheese (can omit), butter (use oil), small amounts of cream
- NOT easily veganizable: eggs in baking, cream-based sauces, cheese as main component

If easily veganizable, provide specific instructions like:
"Simply omit the parmesan cheese or substitute with nutritional yeast for similar umami flavor."
"Replace the butter with olive oil or vegan butter."

VEGETARIAN ADAPTABILITY:
Mark "easily_vegetarianizable" as TRUE if:
- Recipe contains meat/seafood that can be easily replaced
- Examples: chicken in stir-fry (use tofu), beef in tacos (use beans)
- NOT if already vegetarian/vegan

If easily vegetarianizable, provide specific instructions like:
"Replace the chicken with firm tofu, tempeh, or chickpeas for protein."

HEALTHY ADAPTABILITY:
Current status: healthy={is_healthy}
Mark "easily_healthified" as TRUE if:
- Recipe has processed/refined ingredients that can be easily swapped
- Examples: white flour → whole wheat, sugar → natural sweeteners, fried → baked
- NOT if already healthy

If easily healthifiable, provide specific instructions like:
"Use whole wheat flour instead of white flour and reduce sugar by half."

CRITICAL RULES:
1. If already vegan, set "easily_veganizable": false and "vegan_adaptations": null
2. If already vegetarian/vegan, set "easily_vegetarianizable": false  
3. If already healthy, set "easily_healthified": false
4. Provide SPECIFIC, actionable instructions when adaptation is possible
5. Use null (not "null" string) when no adaptations apply

FOCUS ON COMMON ADAPTATIONS:
- Cheese omission/substitution (very common and easy)
- Butter → oil substitution
- Meat → plant protein substitution  
- Refined → whole grain substitution

Return valid JSON only."""

    def _parse_basic_response(self, response: str) -> Optional[Dict]:
        """Parse basic categorization response"""
        try:
            # Handle JSON wrapped in code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            # Ensure required fields exist
            required_fields = ['health_tags', 'dish_type', 'cuisine_type', 'meal_type', 'season']
            for field in required_fields:
                if field not in data:
                    data[field] = []
                elif not isinstance(data[field], list):
                    data[field] = [data[field]] if data[field] else []
            
            # Ensure confidence notes exist
            if 'confidence_notes' not in data:
                data['confidence_notes'] = ''
            if 'confidence_notes_user' not in data:
                data['confidence_notes_user'] = ''
            
            # Validate tags
            data['health_tags'] = self._validate_tags(data['health_tags'], self.HEALTH_TAGS)
            data['dish_type'] = self._validate_tags(data['dish_type'], self.DISH_TYPES)
            data['cuisine_type'] = self._validate_tags(data['cuisine_type'], self.CUISINE_TYPES)
            data['meal_type'] = self._validate_tags(data['meal_type'], self.MEAL_TYPES)
            data['season'] = self._validate_tags(data['season'], self.SEASONS)
            
            print(f"✅ Basic categorization parsed: {data}")
            return data
            
        except Exception as e:
            print(f"❌ Error parsing basic response: {e}")
            print(f"Raw response: {response}")
            return None
    
    def _parse_adaptability_response(self, response: str) -> Dict:
        """Parse adaptability response with fallback to empty dict"""
        try:
            # Handle JSON wrapped in code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            
            # Ensure all adaptability fields exist
            adaptability_fields = [
                'easily_veganizable', 'vegan_adaptations',
                'easily_vegetarianizable', 'vegetarian_adaptations', 
                'easily_healthified', 'healthy_adaptations'
            ]
            
            for field in adaptability_fields:
                if field not in data:
                    if 'easily_' in field:
                        data[field] = False
                    else:
                        data[field] = None
            
            print(f"✅ Adaptability parsed: veganizable={data.get('easily_veganizable')}")
            return data
            
        except Exception as e:
            print(f"⚠️ Error parsing adaptability response: {e}")
            print(f"Raw response: {response}")
            # Return empty adaptability data
            return {
                'easily_veganizable': False,
                'vegan_adaptations': None,
                'easily_vegetarianizable': False,
                'vegetarian_adaptations': None,
                'easily_healthified': False,
                'healthy_adaptations': None
            }
    
    def _validate_tags(self, tags: List[str], valid_tags: List[str]) -> List[str]:
        """Validate tags against known lists"""
        if not tags:
            return []
        
        valid_tags_lower = [tag.lower() for tag in valid_tags]
        validated = []
        
        for tag in tags:
            tag_lower = tag.lower().strip()
            if tag_lower in valid_tags_lower:
                original_tag = valid_tags[valid_tags_lower.index(tag_lower)]
                validated.append(original_tag)
        
        return validated
    
    def _validate_adaptability_logic(self, data: Dict[str, Any], recipe_title: str, recipe_ingredients: List[str]):
        """Enhanced validation with ingredient analysis for better accuracy"""
        
        health_tags = [tag.lower() for tag in data.get('health_tags', [])]
        ingredients_text = ' '.join(recipe_ingredients).lower()
        
        # Rule 1: If recipe is already vegan, it shouldn't be "easily veganizable"
        if 'vegan' in health_tags and data.get('easily_veganizable'):
            print(f"⚠️ Logic correction: Recipe is already vegan, removing veganizable flag")
            data['easily_veganizable'] = False
            data['vegan_adaptations'] = None
        
        # Rule 2: If recipe is already vegetarian or vegan, it shouldn't be "easily vegetarianizable"  
        if ('vegetarian' in health_tags or 'vegan' in health_tags) and data.get('easily_vegetarianizable'):
            print(f"⚠️ Logic correction: Recipe is already vegetarian/vegan, removing vegetarianizable flag")
            data['easily_vegetarianizable'] = False
            data['vegetarian_adaptations'] = None
        
        # Rule 3: If recipe is already healthy, it shouldn't be "easily healthified"
        if 'healthy' in health_tags and data.get('easily_healthified'):
            print(f"⚠️ Logic correction: Recipe is already healthy, removing healthifiable flag")
            data['easily_healthified'] = False
            data['healthy_adaptations'] = None
        
        # Enhanced Rule 4: Check for incorrect vegetarian classification (should be vegan)
        if 'vegetarian' in health_tags and 'vegan' not in health_tags:
            print(f"🔍 DEBUGGING: Recipe marked as vegetarian, checking ingredients for dairy/eggs...")
            print(f"🔍 DEBUGGING: Ingredients text: {ingredients_text}")
            
            # Check if recipe actually contains any dairy/egg ingredients
            dairy_egg_ingredients = [
                'cheese', 'parmesan', 'parmigiano', 'pecorino', 'romano', 'feta', 'mozzarella',
                'cheddar', 'goat cheese', 'ricotta', 'cream cheese', 'blue cheese',
                'butter', 'milk', 'cream', 'heavy cream', 'sour cream', 'yogurt',
                'egg', 'eggs', 'egg white', 'egg yolk', 'mayo', 'mayonnaise', 'honey'
            ]
            
            # Plant-based ingredients that AI might incorrectly think are dairy
            plant_based_ingredients = [
                'olive oil', 'vegetable oil', 'sunflower oil', 'coconut oil', 'avocado oil',
                'oil', 'vinegar', 'lemon juice', 'lime juice'
            ]
            
            found_dairy_eggs = []
            found_incorrect_dairy = []
            
            for dairy_egg in dairy_egg_ingredients:
                if dairy_egg in ingredients_text:
                    found_dairy_eggs.append(dairy_egg)
                    print(f"🔍 DEBUGGING: Found dairy/egg ingredient: '{dairy_egg}'")
            
            # Check if AI mentioned plant-based ingredients as dairy in confidence notes
            confidence_notes_lower = data.get('confidence_notes', '').lower()
            for plant_ingredient in plant_based_ingredients:
                if plant_ingredient in confidence_notes_lower and ('dairy' in confidence_notes_lower or 'potential dairy' in confidence_notes_lower):
                    found_incorrect_dairy.append(plant_ingredient)
                    print(f"🔍 DEBUGGING: AI incorrectly mentioned '{plant_ingredient}' as dairy in confidence notes")
            
            print(f"🔍 DEBUGGING: Total actual dairy/eggs found: {found_dairy_eggs}")
            print(f"🔍 DEBUGGING: Plant ingredients incorrectly labeled as dairy: {found_incorrect_dairy}")
            
            # If no actual dairy/eggs found, it should be vegan
            if not found_dairy_eggs:
                print(f"🔧 Auto-correction: Recipe marked as vegetarian but no dairy/eggs found in ingredients, changing to vegan")
                if found_incorrect_dairy:
                    print(f"🔧 AI incorrectly classified these plant ingredients as dairy: {found_incorrect_dairy}")
                
                # Remove vegetarian and add vegan
                data['health_tags'] = [tag for tag in data.get('health_tags', []) if tag.lower() != 'vegetarian']
                data['health_tags'].append('vegan')
                # Update health_tags reference for subsequent logic
                health_tags = [tag.lower() for tag in data.get('health_tags', [])]
                
                # Update confidence notes to reflect the correction
                current_notes = data.get('confidence_notes', '')
                if found_incorrect_dairy:
                    correction_note = f" [Auto-corrected from vegetarian to vegan - {', '.join(found_incorrect_dairy)} are plant-based, not dairy.]"
                else:
                    correction_note = " [Auto-corrected from vegetarian to vegan as no dairy/egg ingredients were found in the actual ingredient list.]"
                data['confidence_notes'] = current_notes + correction_note
            else:
                print(f"🔍 Vegetarian classification confirmed: found dairy/eggs: {found_dairy_eggs}")
                
                # Check if AI explained these ingredients in confidence notes
                current_notes = data.get('confidence_notes', '').lower()
                explained_ingredients = []
                for ingredient in found_dairy_eggs:
                    if ingredient in current_notes:
                        explained_ingredients.append(ingredient)
                
                missing_explanations = [ing for ing in found_dairy_eggs if ing not in explained_ingredients]
                if missing_explanations:
                    print(f"⚠️ AI didn't explain these dairy/egg ingredients in confidence notes: {missing_explanations}")
                    # Add explanation to confidence notes
                    additional_note = f" Contains {', '.join(found_dairy_eggs)} which prevents it from being vegan."
                    data['confidence_notes'] = data.get('confidence_notes', '') + additional_note
        
        # Enhanced Rule 5: Check for obvious veganizable cases AI might miss
        if ('vegetarian' in health_tags and not data.get('easily_veganizable')):
            # Look for easily omittable/replaceable dairy
            easily_replaceable_dairy = [
                'parmesan', 'parmigiano', 'pecorino', 'romano', 'feta',
                'goat cheese', 'butter', 'grated cheese'
            ]
            
            found_replaceable = []
            for dairy in easily_replaceable_dairy:
                if dairy in ingredients_text:
                    found_replaceable.append(dairy)
            
            # Check for hard-to-replace ingredients that would prevent easy veganizing
            hard_to_replace = [
                'heavy cream', 'cream sauce', 'milk', 'cream cheese',
                'egg', 'eggs', 'ricotta', 'mozzarella', 'cheddar'
            ]
            
            found_hard_to_replace = []
            for hard_dairy in hard_to_replace:
                if hard_dairy in ingredients_text:
                    found_hard_to_replace.append(hard_dairy)
            
            # If we found easily replaceable dairy and no hard-to-replace ingredients
            if found_replaceable and not found_hard_to_replace:
                print(f"🔧 Auto-correction: Found easily replaceable dairy ({found_replaceable}), marking as veganizable")
                data['easily_veganizable'] = True
                
                # Generate appropriate adaptation instruction
                if 'parmesan' in found_replaceable or 'pecorino' in found_replaceable:
                    data['vegan_adaptations'] = "Simply omit the parmesan cheese or substitute with nutritional yeast for similar umami flavor."
                elif 'butter' in found_replaceable:
                    data['vegan_adaptations'] = "Replace the butter with olive oil or vegan butter."
                elif 'feta' in found_replaceable or 'goat cheese' in found_replaceable:
                    data['vegan_adaptations'] = "Omit the cheese or substitute with vegan feta or cashew-based cheese."
                else:
                    data['vegan_adaptations'] = f"The {found_replaceable[0]} can be easily omitted or substituted with a plant-based alternative."
        
        # Enhanced Rule 5: Ensure meal types include obvious cases
        meal_types = [meal.lower() for meal in data.get('meal_type', [])]
        dish_types = [dish.lower() for dish in data.get('dish_type', [])]
        
        if 'salad' in dish_types and not meal_types:
            print(f"🔧 Auto-correction: Salad with no meal types, adding lunch and dinner")
            data['meal_type'] = ['lunch', 'dinner']
        elif 'salad' in dish_types and len(meal_types) == 1:
            # If only one meal type, likely should include both lunch and dinner for salads
            if 'lunch' in meal_types and 'dinner' not in meal_types:
                data['meal_type'].append('dinner')
            elif 'dinner' in meal_types and 'lunch' not in meal_types:
                data['meal_type'].append('lunch')
        
        # Enhanced Rule 6: Check seasonal indicators in ingredients
        seasons = [season.lower() for season in data.get('season', [])]
        
        # Spring/Summer indicators
        fresh_summer_ingredients = [
            'cucumber', 'tomato', 'tomatoes', 'fresh herbs', 'basil', 'arugula',
            'spinach', 'lettuce', 'fresh', 'lemon', 'lime'
        ]
        
        # Look for fresh, light ingredients that suggest spring/summer
        found_fresh = []
        for ingredient in fresh_summer_ingredients:
            if ingredient in ingredients_text:
                found_fresh.append(ingredient)
        
        # If we have fresh ingredients and salad, likely spring/summer
        if found_fresh and 'salad' in dish_types and not seasons:
            print(f"🔧 Auto-correction: Fresh salad with {found_fresh}, adding spring and summer seasons")
            data['season'] = ['spring', 'summer']
        elif found_fresh and 'salad' in dish_types and len(seasons) > 2:
            # If too many seasons, narrow it down for fresh salads
            print(f"🔧 Auto-correction: Fresh salad should be spring/summer focused")
            data['season'] = ['spring', 'summer']
        
        # Enhanced Rule 8: Check for obvious American cuisine dishes that AI might miss
        cuisine_types = [cuisine.lower() for cuisine in data.get('cuisine_type', [])]
        title_lower = recipe_title.lower()
        
        # Classic American dishes/desserts
        american_dishes = [
            'cobbler', 'pie', 'cornbread', 'biscuits', 'pancakes', 'waffles',
            'mac and cheese', 'meatloaf', 'fried chicken', 'barbecue', 'bbq',
            'apple crisp', 'banana bread', 'chocolate chip', 'brownies',
            'casserole', 'pot roast', 'chili', 'coleslaw', 'potato salad'
        ]
        
        # American ingredients that suggest American cuisine
        american_ingredients = [
            'blueberries', 'cranberries', 'pecans', 'maple syrup', 'cornmeal',
            'buttermilk', 'peanut butter', 'marshmallow'
        ]
        
        found_american_dishes = []
        found_american_ingredients = []
        
        for dish in american_dishes:
            if dish in title_lower:
                found_american_dishes.append(dish)
        
        for ingredient in american_ingredients:
            if ingredient in ingredients_text:
                found_american_ingredients.append(ingredient)
        
        # If we found American indicators but no cuisine assigned
        if (found_american_dishes or found_american_ingredients) and not cuisine_types:
            print(f"🔧 Auto-correction: Found American dish/ingredients ({found_american_dishes + found_american_ingredients}), adding american cuisine")
            data['cuisine_type'] = ['american']
        
        # Rule 10: If adaptation flag is True but no instructions provided, add generic instruction
        if data.get('easily_veganizable') and not data.get('vegan_adaptations'):
            data['vegan_adaptations'] = "This recipe can be made vegan with simple ingredient substitutions."
            print(f"🔧 Added generic vegan adaptation instruction")
        
        if data.get('easily_vegetarianizable') and not data.get('vegetarian_adaptations'):
            data['vegetarian_adaptations'] = "This recipe can be made vegetarian by replacing the meat/seafood with plant-based protein."
            print(f"🔧 Added generic vegetarian adaptation instruction")
        
        if data.get('easily_healthified') and not data.get('healthy_adaptations'):
            data['healthy_adaptations'] = "This recipe can be made healthier with ingredient substitutions or cooking method changes."
            print(f"🔧 Added generic healthy adaptation instruction")

    
    def _create_categorization(self, basic_data: Dict, adaptability_data: Dict, recipe_title: str, recipe_ingredients: List[str]) -> RecipeCategorization:
        """Create final categorization object with enhanced validation"""
        
        # Import here to avoid circular imports
        from app.models import RecipeAdaptability
        
        # Combine data for validation
        combined_data = {**basic_data, **adaptability_data}
        
        # Apply enhanced validation logic
        self._validate_adaptability_logic(combined_data, recipe_title, recipe_ingredients)
        
        # Split back out after validation
        validated_basic = {k: v for k, v in combined_data.items() if k in ['health_tags', 'dish_type', 'cuisine_type', 'meal_type', 'season', 'confidence_notes', 'confidence_notes_user']}
        validated_adaptability = {k: v for k, v in combined_data.items() if k in ['easily_veganizable', 'vegan_adaptations', 'easily_vegetarianizable', 'vegetarian_adaptations', 'easily_healthified', 'healthy_adaptations']}
        
        # Default to all seasons if none specified and no seasonal indicators found
        if not validated_basic.get('season'):
            validated_basic['season'] = self.SEASONS.copy()
        
        # Create adaptability object
        adaptability = RecipeAdaptability(
            easily_veganizable=validated_adaptability.get('easily_veganizable', False),
            vegan_adaptations=validated_adaptability.get('vegan_adaptations'),
            easily_vegetarianizable=validated_adaptability.get('easily_vegetarianizable', False),
            vegetarian_adaptations=validated_adaptability.get('vegetarian_adaptations'),
            easily_healthified=validated_adaptability.get('easily_healthified', False),
            healthy_adaptations=validated_adaptability.get('healthy_adaptations')
        )
        
        categorization = RecipeCategorization(
            health_tags=validated_basic.get('health_tags', []),
            dish_type=validated_basic.get('dish_type', []),
            cuisine_type=validated_basic.get('cuisine_type', []),
            meal_type=validated_basic.get('meal_type', []),
            season=validated_basic.get('season', []),
            confidence_notes=validated_basic.get('confidence_notes', ''),
            confidence_notes_user=validated_basic.get('confidence_notes_user', ''),
            adaptability=adaptability,
            ai_model=settings.AI_MODEL
        )
        
        print(f"✅ Final categorization for {recipe_title}:")
        print(f"   Health: {categorization.health_tags}")
        print(f"   Dish: {categorization.dish_type}")
        print(f"   Meal: {categorization.meal_type}")
        print(f"   Season: {categorization.season}")
        print(f"   Adaptability: vegan={adaptability.easily_veganizable}, veg={adaptability.easily_vegetarianizable}, healthy={adaptability.easily_healthified}")
        print(f"   Confidence: {categorization.confidence_notes[:100]}...")
        
        return categorization

# Enhanced recipe service integration (no changes needed)
class EnhancedRecipeService:
    """Enhanced recipe service that includes AI categorization"""
    
    def __init__(self):
        from app.services.parsers import RecipeScrapersParser, ExtructParser
        from app.services.processors import ImageExtractor
        
        self.recipe_scrapers_parser = RecipeScrapersParser()
        self.extruct_parser = ExtructParser()
        self.categorization_service = RecipeCategorizationService()
    
    async def parse_and_categorize_recipe(self, url: str) -> Recipe:
        """
        Parse recipe from URL and add AI categorization
        Integrates with existing parsing pipeline
        """
        # Import here to avoid circular imports
        from app.services.recipe_service import RecipeService
        
        try:
            print(f"🔍 Starting enhanced recipe parsing for: {url}")
            
            # Step 1: Use existing parsing pipeline
            recipe = await RecipeService.parse_recipe_hybrid(url)
            
            if not recipe or recipe.title == "Unable to parse recipe":
                print("❌ Base recipe parsing failed, skipping categorization")
                return recipe
            
            print(f"✅ Base recipe parsed: {recipe.title}")
            print(f"   Ingredients: {len(recipe.ingredients)}")
            
            # Step 2: Add AI categorization
            print("🤖 Starting AI categorization...")
            categorization = await self.categorization_service.categorize_recipe(recipe)
            
            if categorization:
                print("✅ AI categorization successful!")
                
                # Enhance the recipe with categorization data
                enhanced_recipe = Recipe(
                    title=recipe.title,
                    description=recipe.description,
                    image=recipe.image,
                    source=recipe.source,
                    ingredients=recipe.ingredients,
                    instructions=recipe.instructions,
                    prep_time=recipe.prep_time,
                    cook_time=recipe.cook_time,
                    servings=recipe.servings,
                    cuisine=recipe.cuisine,
                    category=recipe.category,
                    keywords=recipe.keywords,
                    found_structured_data=recipe.found_structured_data,
                    used_ai=True,
                    raw_ingredients=getattr(recipe, 'raw_ingredients', []),
                    raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),
                    
                    # Add new categorization fields
                    health_tags=categorization.health_tags,
                    dish_type=categorization.dish_type,
                    cuisine_type=categorization.cuisine_type,
                    meal_type=categorization.meal_type,
                    season=categorization.season,
                    ai_confidence_notes=categorization.confidence_notes,
                    ai_confidence_notes_user=categorization.confidence_notes_user,
                    
                    # Add adaptability fields (extract from nested object)
                    easily_veganizable=categorization.adaptability.easily_veganizable,
                    vegan_adaptations=categorization.adaptability.vegan_adaptations,
                    easily_vegetarianizable=categorization.adaptability.easily_vegetarianizable,
                    vegetarian_adaptations=categorization.adaptability.vegetarian_adaptations,
                    easily_healthified=categorization.adaptability.easily_healthified,
                    healthy_adaptations=categorization.adaptability.healthy_adaptations,
                    
                    ai_enhanced=True,
                    ai_model_used=categorization.ai_model
                )
                
                print(f"✅ Recipe successfully enhanced with AI categorization")
                return enhanced_recipe
            else:
                print("⚠️ AI categorization failed, returning base recipe")
                return recipe
                
        except Exception as e:
            print(f"❌ Enhanced recipe parsing failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            # Return the base recipe if enhancement fails
            try:
                from app.services.recipe_service import RecipeService
                return await RecipeService.parse_recipe_hybrid(url)
            except:
                raise

# Batch categorization for existing recipes (no changes needed)
class BatchCategorizationService:
    """Service for categorizing existing recipes in bulk"""
    
    def __init__(self):
        self.categorization_service = RecipeCategorizationService()
    
    async def categorize_recipes_batch(self, recipes: List[Recipe], batch_size: int = 5) -> List[Recipe]:
        """
        Categorize multiple recipes with rate limiting
        """
        enhanced_recipes = []
        
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            print(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} recipes)")
            
            # Process batch
            batch_tasks = [
                self.categorization_service.categorize_recipe(recipe) 
                for recipe in batch
            ]
            
            categorizations = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Apply categorizations
            for recipe, categorization in zip(batch, categorizations):
                if isinstance(categorization, RecipeCategorization):
                    enhanced_recipe = self._apply_categorization(recipe, categorization)
                    enhanced_recipes.append(enhanced_recipe)
                else:
                    print(f"⚠️ Categorization failed for {recipe.title}")
                    enhanced_recipes.append(recipe)
            
            # Rate limiting - be nice to the API
            if i + batch_size < len(recipes):
                print("⏳ Rate limiting pause...")
                await asyncio.sleep(2)
        
        return enhanced_recipes
    
    def _apply_categorization(self, recipe: Recipe, categorization: RecipeCategorization) -> Recipe:
        """Apply categorization to a recipe"""
        return Recipe(
            title=recipe.title,
            description=recipe.description,
            image=recipe.image,
            source=recipe.source,
            ingredients=recipe.ingredients,
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            servings=recipe.servings,
            cuisine=recipe.cuisine,
            category=recipe.category,
            keywords=recipe.keywords,
            found_structured_data=recipe.found_structured_data,
            used_ai=True,
            raw_ingredients=getattr(recipe, 'raw_ingredients', []),
            raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),
            
            # Enhanced fields
            health_tags=categorization.health_tags,
            dish_type=categorization.dish_type,
            cuisine_type=categorization.cuisine_type,
            meal_type=categorization.meal_type,
            season=categorization.season,
            ai_confidence_notes=categorization.confidence_notes,
            ai_confidence_notes_user=categorization.confidence_notes_user,
            
            # Adaptability fields (extract from nested object)
            easily_veganizable=categorization.adaptability.easily_veganizable,
            vegan_adaptations=categorization.adaptability.vegan_adaptations,
            easily_vegetarianizable=categorization.adaptability.easily_vegetarianizable,
            vegetarian_adaptations=categorization.adaptability.vegetarian_adaptations,
            easily_healthified=categorization.adaptability.easily_healthified,
            healthy_adaptations=categorization.adaptability.healthy_adaptations,
            
            ai_enhanced=True,
            ai_model_used=categorization.ai_model
        )
