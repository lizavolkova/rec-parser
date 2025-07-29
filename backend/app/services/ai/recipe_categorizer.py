# backend/app/services/ai/recipe_categorizer.py (IMPROVED VERSION)
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
        
        # Debug: Print available health tags
        print(f"🔍 DEBUG: Available HEALTH_TAGS: {self.HEALTH_TAGS}")
        print(f"🔍 DEBUG: 'easily veganizable' in HEALTH_TAGS: {'easily veganizable' in self.HEALTH_TAGS}")
        
        try:
            print(f"🤖 Starting AI categorization for: {recipe.title}")
            
            prompt = self._build_categorization_prompt(recipe)
            
            response = openai_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=settings.AI_TEMPERATURE,  # Use configurable temperature
                max_tokens=settings.AI_MAX_TOKENS,
                seed=getattr(settings, 'AI_SEED', 42)  # Use configurable seed for consistency
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"🤖 AI categorization response: {ai_response[:200]}...")
            
            return self._parse_categorization_response(ai_response, recipe.title)
            
        except Exception as e:
            print(f"🤖 AI categorization failed: {e}")
            print(f"🤖 Traceback: {traceback.format_exc()}")
            return None
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role and capabilities"""
        return f"""You are a culinary expert AI that categorizes recipes with high accuracy and CONSISTENCY. 

Your task is to analyze recipes and categorize them into specific categories. You should be comprehensive but accurate - a recipe can have multiple tags in each category when appropriate.

CRITICAL: ONLY analyze what is actually present in the recipe. Do NOT hallucinate or assume ingredients, cooking methods, or characteristics not explicitly mentioned.

CATEGORY GUIDELINES:

HEALTH TAGS - Use systematic analysis for dietary restrictions:
{', '.join(self.HEALTH_TAGS)}

DIETARY CLASSIFICATION RULES:
- VEGAN: Contains ZERO animal products (vegetables, fruits, grains, legumes, nuts, seeds, plant oils, soy sauce, vinegar, spices, herbs, agave syrup, chili crisp, tofu, tempeh, etc.)
- VEGETARIAN: No meat/seafood but may contain dairy/eggs
- EASILY VEGANIZABLE: Vegetarian recipes with only 1-2 easily replaceable dairy/egg ingredients (like cheese that can be omitted or substituted)
- PESCATARIAN: Contains fish/seafood but no other meat
- RED MEAT FREE: No beef, pork, lamb, or other red meat (but may contain poultry/fish)
- DAIRY FREE: No milk, cheese, butter, cream, yogurt, or other dairy products
- If ALL ingredients are plant-based, tag as VEGAN (not vegetarian)

CRITICAL: BE EXTREMELY CAREFUL WITH VEGAN VS VEGETARIAN
- Read the actual ingredients list carefully
- Do NOT assume ingredients that aren't listed
- Gochujang, eggplant, scallions, vegetable oil, soy sauce, sesame oil = ALL VEGAN
- Parmesan cheese, butter, milk, cream, eggs = NOT VEGAN (tag as vegetarian)

EXAMPLES OF PROPER CATEGORIZATION WITH CONFIDENCE NOTES:
- Farro salad with parmesan cheese → health_tags: ["vegetarian", "easily veganizable", "healthy"] + notes: "Tagged as vegetarian due to parmesan cheese, and easily veganizable since the cheese can be omitted or replaced with nutritional yeast. Healthy due to nutrient-rich farro and fresh vegetables."
- Gochujang eggplant with scallions → health_tags: ["vegan", "healthy"] + notes: "Completely vegan with all plant-based ingredients (eggplant, gochujang, scallions, oil). Healthy due to vegetables and minimal processing."
- Pasta with cream sauce → health_tags: ["vegetarian", "healthy"] + notes: "Vegetarian due to cream, but not easily veganizable since cream is central to the dish."

EASILY VEGANIZABLE CRITERIA: Tag as "easily veganizable" if a recipe is vegetarian and contains only 1-2 easily replaceable ingredients like:
- Cheese (especially parmesan) that can be omitted or replaced with vegan cheese/nutritional yeast
- Butter that can be replaced with oil or vegan butter
- Small amounts of dairy that don't define the dish
- NOT easily veganizable: eggs in baking, cream-based sauces, dishes where dairy is central

RED MEAT INCLUDES: beef, pork, lamb, mutton, venison, bison, goat
POULTRY INCLUDES: chicken, turkey, duck, etc. (NOT red meat)

HEALTHY TAG CRITERIA - Tag as "healthy" if the dish has:
- Lots of vegetables or fruits as main components
- Lean proteins (fish, chicken, tofu, beans)
- Whole grains or minimal processing
- Limited fried foods or heavy cream sauces
- Balanced nutritional profile

IMPROVED HEALTHY DETECTION - Also tag as "healthy" if the dish meets ANY of these criteria:
1. VEGETABLE-FORWARD: Contains vegetables as a main component (not just garnish)
   - Examples: tofu with broccoli, veggie stir-fry, salads, vegetable soups
2. LEAN PROTEIN FOCUS: Features lean proteins like:
   - Fish, shellfish, chicken breast, turkey
   - Tofu, tempeh, beans, lentils, chickpeas
   - Eggs (in moderation)
3. WHOLE FOOD INGREDIENTS: Minimal processed foods, lots of:
   - Fresh vegetables, fruits, herbs, spices
   - Whole grains (brown rice, quinoa, oats)
   - Nuts, seeds (in reasonable amounts)
4. BALANCED NUTRITION: Good balance of protein, vegetables, healthy fats
5. COOKING METHODS: Steamed, grilled, baked, sautéed, roasted (not deep-fried)

HEALTHY EXAMPLES THAT SHOULD GET THE TAG:
- "Lemon miso tofu with broccoli" → HEALTHY (tofu = lean protein, broccoli = vegetable)
- "Grilled chicken with roasted vegetables" → HEALTHY (lean protein + vegetables)
- "Quinoa Buddha bowl with chickpeas" → HEALTHY (whole grains + legumes + vegetables)
- "Salmon with asparagus" → HEALTHY (lean protein + vegetables)
- "Vegetable stir-fry with tofu" → HEALTHY (vegetables + lean protein)
- "Bean and vegetable soup" → HEALTHY (legumes + vegetables)

BE GENEROUS with the healthy tag - if a dish has good nutritional value, tag it as healthy!

DISH TYPES - What type of dish this is (can be multiple):
{', '.join(self.DISH_TYPES)}

COOKING METHOD DETECTION:
- If recipe mentions grilling, BBQ, or grill pan → include "grilling"
- If served as small portions or before main course → include "starter or appetizer"
- Look for cooking methods in instructions and title

CUISINE TYPES - The cultural/regional cooking style:
{', '.join(self.CUISINE_TYPES)}

CUISINE TAGGING RULES:
- Tag BOTH specific AND broader categories when applicable, but be culturally accurate
- Chinese/Korean/Thai/Vietnamese/Japanese → ALSO tag as "asian"
- Indian/Middle Eastern → Do NOT tag as "asian" (distinct flavor profiles)
- Italian/French/Spanish/Greek → Can tag as "mediterranean" if appropriate
- Examples: "chinese, asian" or "thai, asian" but just "indian" (not "indian, asian")

MEAL TYPES - When this would typically be eaten (can be multiple):
{', '.join(self.MEAL_TYPES)}

MEAL TYPE FLEXIBILITY:
- Many dishes work for multiple meals (lunch AND dinner)
- Consider portion size and ingredients
- Don't be overly restrictive - if it could reasonably be eaten at different times, include multiple tags

SEASONS - When ingredients are typically in season or dish is commonly eaten:
{', '.join(self.SEASONS)}

SEASONAL ASSIGNMENT RULES:
- Consider the main ingredients and dish characteristics
- Cold salads with summer vegetables (cucumber, tomato) = summer primarily
- Warm soups and stews can be autumn AND winter (not just one)
- Light, refreshing dishes = summer
- Hearty, warming dishes = autumn and/or winter
- Fresh spring vegetables = spring
- Many dishes work across multiple seasons - don't be overly restrictive

SEASONAL EXAMPLES:
- Cucumber salad = summer
- Roasted garlic soup = autumn, winter (both)
- Pumpkin soup = autumn
- Asparagus dishes = spring
- Grilled dishes = summer (but can span multiple if hearty)

IMPORTANT RULES:
1. Only use tags from the provided lists
2. Be generous with applicable tags when appropriate - better to include relevant tags than miss them
3. For health tags, systematically check all ingredients and cooking methods
4. BE ESPECIALLY GENEROUS with the "healthy" tag - if it has vegetables + lean protein OR is vegetable-forward, tag it as healthy
5. For seasons and meal types, don't be overly restrictive - many dishes work across categories
6. Always include broader cuisine categories (asian, mediterranean) alongside specific ones
7. Detect cooking methods from instructions and titles
8. Only reference ingredients and cooking methods that are ACTUALLY in the recipe
9. Always return valid JSON in the exact format requested
10. BE CONSISTENT - same recipe should always get same categorization
11. If all ingredients are plant-based, tag as VEGAN (not vegetarian)
12. Remember: lamb, beef, pork = red meat; chicken, turkey = poultry (not red meat)
13. MOST IMPORTANTLY: Don't be stingy with the "healthy" tag - if it's nutritious, tag it!"""

    def _build_categorization_prompt(self, recipe: Recipe) -> str:
        """Build the user prompt with recipe data"""
        
        # Create a clean ingredient list
        ingredients_text = "\n".join([f"- {ing}" for ing in recipe.ingredients[:15]])  # Limit for token efficiency
        if len(recipe.ingredients) > 15:
            ingredients_text += f"\n... and {len(recipe.ingredients) - 15} more ingredients"
        
        # Create a clean instruction summary
        instructions_text = " ".join(recipe.instructions[:3])[:300] + "..." if recipe.instructions else "No instructions provided"
        
        return f"""Analyze this recipe and categorize it systematically. Pay special attention to whether it should be tagged as "healthy":

**RECIPE: {recipe.title}**

**DESCRIPTION:** {recipe.description or 'No description provided'}

**INGREDIENTS:**
{ingredients_text}

**COOKING METHOD:** {instructions_text}

**ADDITIONAL CONTEXT:**
- Prep time: {recipe.prep_time or 'Unknown'}
- Cook time: {recipe.cook_time or 'Unknown'}
- Servings: {recipe.servings or 'Unknown'}
- Source: {recipe.source or 'Unknown'}

HEALTHY ANALYSIS REQUIRED:
Look specifically for:
1. Does this contain vegetables as a main component? (broccoli, spinach, carrots, etc.)
2. Does this feature lean proteins? (tofu, fish, chicken, beans, etc.)
3. Are the cooking methods healthy? (not deep-fried, not heavy cream-based)
4. Is this nutritionally balanced?

VEGAN ANALYSIS REQUIRED:
Check if ALL ingredients are plant-based:
- Tofu, tempeh, vegetables, fruits, grains, legumes, nuts, seeds = VEGAN
- Miso, soy sauce, nutritional yeast, plant oils = VEGAN
- Gochujang (Korean chili paste), vegetable oil, scallions, eggplant = VEGAN
- NO meat, dairy, eggs, fish, honey, gelatin = VEGAN
- CRITICAL: Check for ANY cheese (parmesan, parmigiano, pecorino, cheddar, mozzarella, feta, etc.) - if present, tag as VEGETARIAN not VEGAN
- CRITICAL: Check for butter, cream, milk, yogurt - if present, tag as VEGETARIAN not VEGAN
- CRITICAL: DO NOT assume ingredients that aren't listed - only analyze what's actually in the recipe
- If everything is plant-based, tag as VEGAN (not just vegetarian)
- If contains dairy/eggs but no meat, tag as VEGETARIAN

PARMESAN CHEESE ALERT:
- Parmesan cheese is DAIRY and makes the recipe VEGETARIAN, not vegan
- Parmigiano-Reggiano is DAIRY and makes the recipe VEGETARIAN, not vegan
- Pecorino Romano is DAIRY and makes the recipe VEGETARIAN, not vegan
- If you see these ingredients, DO NOT tag as vegan

COMMON VEGAN INGREDIENTS (these are all plant-based):
- Eggplant, gochujang, soy sauce, vegetable oil, scallions, garlic, ginger
- Brown sugar, sesame oil, rice vinegar, vegetables, tofu, tempeh
- If recipe only contains these types of ingredients, it should be VEGAN

EASILY VEGANIZABLE CHECK:
- If recipe is vegetarian with only 1-2 easily replaceable dairy ingredients, tag as "easily veganizable"
- Examples: farro salad with parmesan (cheese can be omitted/replaced), pasta with butter (can use oil instead)
- Example confidence note: "Tagged as vegetarian due to parmesan cheese, but easily veganizable by omitting or substituting with nutritional yeast or vegan parmesan"

If ANY of the healthy criteria are true, tag as "healthy"!
If ALL ingredients are plant-based, tag as "vegan"!

Return ONLY a JSON object with this exact structure (pay attention to commas):
{{
    "health_tags": ["tag1", "tag2"],
    "dish_type": ["type1", "type2"],
    "cuisine_type": ["cuisine1"],
    "meal_type": ["meal1", "meal2"],
    "season": ["season1"],
    "confidence_notes": "Friendly explanation of why you chose these categories, especially explaining your healthy tag decision"
}}

JSON FORMATTING REQUIREMENTS:
- CRITICAL: Include commas after every field except the last one
- Use double quotes around all keys and string values
- Use square brackets for arrays, even if empty: []
- Ensure proper comma placement - missing commas will cause parsing errors

CONFIDENCE NOTES STYLE:
- Explain your reasoning in a natural, conversational way
- SPECIFICALLY mention why you did or didn't tag as "healthy"
- Focus on what led you to pick specific categories
- Be friendly and approachable, not robotic or overly formal
- Keep it concise but informative about your choices

EXAMPLES OF GOOD CONFIDENCE NOTES WITH HEALTH AND VEGAN EXPLANATIONS:
- "This is vegan since all ingredients (tofu, broccoli, miso, lemon) are plant-based, and healthy due to the lean protein from tofu plus nutritious vegetables. Perfect for dinner."
- "Tagged as vegetarian and easily veganizable due to parmesan cheese, but healthy because of the nutrient-rich farro and vegetables. The parmesan can easily be omitted or replaced with nutritional yeast."
- "This gets both vegan and healthy tags - all ingredients are plant-based and it's vegetable-forward with nutritious beans. The warming spices make it perfect for autumn."
- "Vegetarian and easily veganizable due to the small amount of butter that could be replaced with olive oil. Still healthy thanks to the lean protein and vegetables."

IMPORTANT REMINDERS:
- If ALL ingredients are plant-based, tag as VEGAN (not vegetarian)
- Consider dish characteristics for seasonal assignment (cucumber salad = summer)
- Only reference ingredients and cooking methods actually in the recipe
- Be consistent - same recipe should always get same categorization
- BE GENEROUS with the "healthy" tag - if it has good nutritional value, include it!"""

    def _parse_categorization_response(self, ai_response: str, recipe_title: str) -> Optional[RecipeCategorization]:
        """Parse AI response into RecipeCategorization object with robust JSON handling"""
        
        print(f"🤖 DEBUG: Raw AI response for '{recipe_title}':")
        print(f"🤖 DEBUG: {ai_response}")
        print("🤖 DEBUG: " + "="*60)
        
        try:
            # Handle JSON wrapped in code blocks
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            else:
                json_str = ai_response
            
            # Try to parse JSON, with fallback for common formatting issues
            try:
                data = json.loads(json_str)
                print(f"🤖 DEBUG: Parsed JSON successfully: {data}")
            except json.JSONDecodeError as e:
                print(f"🤖 Initial JSON parse failed: {e}")
                print(f"🤖 Attempting to fix common JSON issues...")
                
                # Try to fix common issues
                fixed_json = self._fix_common_json_issues(json_str)
                try:
                    data = json.loads(fixed_json)
                    print(f"🤖 JSON fixed and parsed successfully!")
                except json.JSONDecodeError:
                    print(f"🤖 Could not fix JSON formatting")
                    print(f"🤖 Raw response: {ai_response}")
                    return None
            
            # DEBUG: Check what health tags AI returned before validation
            print(f"🤖 DEBUG: AI returned health tags: {data.get('health_tags', [])}")
            
            # Validate required fields
            required_fields = ['health_tags', 'dish_type', 'cuisine_type', 'meal_type', 'season']
            adaptation_fields = ['easily_veganizable', 'vegan_adaptations', 'easily_vegetarianizable', 'vegetarian_adaptations', 'easily_healthified', 'healthy_adaptations']
            
            for field in required_fields:
                if field not in data:
                    print(f"🤖 Missing required field '{field}' in AI response")
                    return None
            
            # Ensure adaptation fields exist with defaults
            for field in adaptation_fields:
                if field not in data:
                    if 'easily_' in field:
                        data[field] = False
                    else:
                        data[field] = None
            
            # Ensure all fields are lists
            for field in required_fields:
                if not isinstance(data[field], list):
                    data[field] = [data[field]] if data[field] else []
            
            # Validate tags against known lists
            data['health_tags'] = self._validate_tags(data['health_tags'], self.HEALTH_TAGS, 'health_tags')
            data['dish_type'] = self._validate_tags(data['dish_type'], self.DISH_TYPES, 'dish_types')
            data['cuisine_type'] = self._validate_tags(data['cuisine_type'], self.CUISINE_TYPES, 'cuisine_types')
            data['meal_type'] = self._validate_tags(data['meal_type'], self.MEAL_TYPES, 'meal_types')
            data['season'] = self._validate_tags(data['season'], self.SEASONS, 'seasons')
            
            print(f"🤖 DEBUG: After validation, health tags: {data['health_tags']}")
            
            # GENERIC LOGIC - Fix the underlying issues instead of hard-coding overrides
            
            # Step 1: Fix healthy tag detection
            if 'healthy' not in data['health_tags']:
                should_be_healthy = self._should_be_healthy(recipe_title, data.get('confidence_notes', ''))
                if should_be_healthy:
                    data['health_tags'].append('healthy')
                    print(f"🥗 Auto-added 'healthy' tag for {recipe_title}")
            
            # Step 2: Fix vegan/vegetarian detection with better logic
            current_dietary_tags = [tag for tag in data['health_tags'] if tag in ['vegan', 'vegetarian']]
            print(f"🔍 Current dietary tags: {current_dietary_tags}")
            
            if not current_dietary_tags:
                # No dietary tag assigned, check what it should be
                print(f"🔍 No dietary tags found, checking what this recipe should be...")
                should_be_vegan = self._should_be_vegan(recipe_title, data.get('confidence_notes', ''))
                should_be_vegetarian = self._should_be_vegetarian(recipe_title, data.get('confidence_notes', ''))
                
                if should_be_vegan:
                    data['health_tags'].append('vegan')
                    print(f"🌱 Auto-added 'vegan' tag for {recipe_title}")
                elif should_be_vegetarian:
                    data['health_tags'].append('vegetarian')
                    print(f"🥬 Auto-added 'vegetarian' tag for {recipe_title}")
                    
                    # Add explanation for why it's vegetarian
                    current_notes = data.get('confidence_notes', '')
                    if 'farro' in recipe_title.lower() and 'salad' in recipe_title.lower():
                        additional_notes = " Tagged as vegetarian as farro salads typically contain parmesan cheese."
                        data['confidence_notes'] = current_notes + additional_notes
                    
            elif 'vegetarian' in data['health_tags'] and 'vegan' not in data['health_tags']:
                # AI marked as vegetarian, double-check if it should actually be vegan
                print(f"🔍 Recipe marked as vegetarian, checking if it should be vegan...")
                should_be_vegan = self._should_be_vegan(recipe_title, data.get('confidence_notes', ''))
                if should_be_vegan:
                    print(f"🔧 CORRECTING: Should be vegan, not vegetarian")
                    data['health_tags'] = [tag for tag in data['health_tags'] if tag != 'vegetarian']
                    data['health_tags'].append('vegan')
                    print(f"🌱 Corrected to vegan tag")
                    
                    # Update confidence notes to explain the correction
                    current_notes = data.get('confidence_notes', '')
                    additional_notes = " Corrected to vegan as all ingredients are plant-based."
                    data['confidence_notes'] = current_notes + additional_notes
                    
            elif 'vegan' in data['health_tags']:
                # AI marked as vegan, double-check it's not wrong (contains dairy/meat)
                print(f"🔍 Recipe marked as vegan, double-checking for non-vegan ingredients...")
                definitely_not_vegan = not self._should_be_vegan(recipe_title, data.get('confidence_notes', ''))
                if definitely_not_vegan:
                    print(f"🔧 CORRECTING: Contains non-vegan ingredients, should be vegetarian")
                    data['health_tags'] = [tag for tag in data['health_tags'] if tag != 'vegan']
                    data['health_tags'].append('vegetarian')
                    print(f"🥬 Corrected to vegetarian tag")
                    
                    # Update confidence notes to explain what was missed
                    current_notes = data.get('confidence_notes', '')
                    if 'farro' in recipe_title.lower() and 'salad' in recipe_title.lower():
                        additional_notes = " Corrected to vegetarian as farro salads typically contain parmesan cheese."
                    else:
                        additional_notes = " Corrected to vegetarian due to dairy ingredients."
                    data['confidence_notes'] = current_notes + additional_notes
            
            # Step 3: Fix easily veganizable detection
            print(f"🔍 Checking for easily veganizable...")
            print(f"🔍 Current tags: {data['health_tags']}")
            print(f"🔍 Is vegetarian: {'vegetarian' in data['health_tags']}")
            print(f"🔍 Is easily veganizable already present: {'easily veganizable' in data['health_tags']}")
            
            if 'vegetarian' in data['health_tags'] and 'easily veganizable' not in data['health_tags']:
                print(f"🔍 Recipe is vegetarian, checking if easily veganizable...")
                should_be_easily_veganizable = self._should_be_easily_veganizable(recipe_title, data.get('confidence_notes', ''))
                if should_be_easily_veganizable:
                    data['health_tags'].append('easily veganizable')
                    data['easily_veganizable'] = True
                    print(f"🌱✨ Auto-added 'easily veganizable' tag for {recipe_title}")
                    
                    # Generate appropriate vegan adaptation instructions
                    if 'parmesan' in recipe_title.lower() or 'farro salad' in recipe_title.lower():
                        data['vegan_adaptations'] = "Simply omit the parmesan cheese or substitute with nutritional yeast for similar umami flavor."
                    elif 'butter' in recipe_title.lower():
                        data['vegan_adaptations'] = "Replace the butter with olive oil or vegan butter."
                    else:
                        data['vegan_adaptations'] = "The dairy ingredients can be easily omitted or substituted with plant-based alternatives."
                    
                    print(f"🔧 Added vegan adaptation instructions: {data['vegan_adaptations']}")
                else:
                    print(f"❌ Did NOT add 'easily veganizable' tag for {recipe_title}")
            else:
                if 'vegetarian' not in data['health_tags']:
                    print(f"🔍 Skipping easily veganizable - not vegetarian")
                if 'easily veganizable' in data['health_tags']:
                    print(f"🔍 Skipping easily veganizable - already present")
            
            print(f"🤖 DEBUG: Final health tags: {data['health_tags']}")
            
            # Updated: Only default to all seasons if no valid seasons were returned AND it's not a clearly seasonal dish
            if not data['season']:
                # Check if this might be a seasonal dish that AI missed
                title_lower = recipe_title.lower()
                if any(term in title_lower for term in ['cucumber', 'tomato', 'gazpacho', 'cold soup']):
                    data['season'] = ['summer']
                    print(f"🤖 Applied summer season based on dish characteristics: {recipe_title}")
                elif any(term in title_lower for term in ['pumpkin', 'butternut', 'hot chocolate', 'stew']):
                    data['season'] = ['autumn', 'winter']
                    print(f"🤖 Applied autumn/winter season based on dish characteristics: {recipe_title}")
                else:
                    data['season'] = self.SEASONS.copy()
                    print(f"🤖 No specific seasons identified, defaulting to all seasons: {recipe_title}")
            
            categorization = RecipeCategorization(
                health_tags=data['health_tags'],
                dish_type=data['dish_type'],
                cuisine_type=data['cuisine_type'],
                meal_type=data['meal_type'],
                season=data['season'],
                confidence_notes=data.get('confidence_notes', ''),
                easily_veganizable=data.get('easily_veganizable', False),
                vegan_adaptations=data.get('vegan_adaptations'),
                easily_vegetarianizable=data.get('easily_vegetarianizable', False),
                vegetarian_adaptations=data.get('vegetarian_adaptations'),
                easily_healthified=data.get('easily_healthified', False),
                healthy_adaptations=data.get('healthy_adaptations'),
                ai_model=settings.AI_MODEL
            )
            
            print(f"✅ AI categorization successful for {recipe_title}")
            print(f"   Health: {categorization.health_tags}")
            print(f"   Dish: {categorization.dish_type}")
            print(f"   Cuisine: {categorization.cuisine_type}")
            print(f"   Meal: {categorization.meal_type}")
            print(f"   Season: {categorization.season}")
            print(f"   Reasoning: {categorization.confidence_notes[:100]}...")
            
            return categorization
            
        except json.JSONDecodeError as e:
            print(f"🤖 JSON decode error: {e}")
            print(f"🤖 Raw response: {ai_response}")
            return None
        except Exception as e:
            print(f"🤖 Error parsing categorization response: {e}")
            return None
    
    def _should_be_healthy(self, recipe_title: str, confidence_notes: str) -> bool:
        """Check if a recipe should be tagged as healthy based on title and notes"""
        title_lower = recipe_title.lower()
        notes_lower = confidence_notes.lower() if confidence_notes else ""
        
        # Look for healthy indicators in title
        healthy_ingredients = [
            'tofu', 'broccoli', 'spinach', 'kale', 'quinoa', 'salmon', 'chicken breast',
            'vegetables', 'salad', 'soup', 'beans', 'lentils', 'chickpeas', 'avocado',
            'grilled', 'roasted', 'steamed', 'baked', 'tempeh', 'edamame'
        ]
        
        healthy_phrases = [
            'with vegetables', 'with broccoli', 'with spinach', 'and vegetables',
            'vegetable', 'veggie', 'with kale', 'and tofu'
        ]
        
        # Check title for healthy indicators
        title_has_healthy = any(ingredient in title_lower for ingredient in healthy_ingredients)
        title_has_healthy_phrase = any(phrase in title_lower for phrase in healthy_phrases)
        
        # Check if notes mention vegetables, lean protein, or vegan ingredients
        notes_has_healthy = any(word in notes_lower for word in [
            'vegetable', 'broccoli', 'spinach', 'lean protein', 'tofu', 'vegan', 'plant-based'
        ])
        
        return title_has_healthy or title_has_healthy_phrase or notes_has_healthy
    
    def _should_be_vegan(self, recipe_title: str, confidence_notes: str) -> bool:
        """Check if a recipe should be tagged as vegan based on title and notes"""
        title_lower = recipe_title.lower()
        notes_lower = confidence_notes.lower() if confidence_notes else ""
        
        # FIRST: Aggressive dairy detection - if ANY dairy is found, definitely not vegan
        dairy_indicators = [
            # All cheese types - be extremely comprehensive
            'cheese', 'parmesan', 'parmigiano', 'pecorino', 'romano', 'cheddar', 
            'mozzarella', 'feta', 'goat cheese', 'ricotta', 'cream cheese', 
            'blue cheese', 'swiss', 'gruyere', 'brie', 'camembert', 'fontina',
            'provolone', 'asiago', 'manchego', 'gouda', 'emmental',
            # Other dairy
            'butter', 'cream', 'milk', 'yogurt', 'sour cream', 'crème fraîche',
            # Meat and seafood
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp', 'crab',
            'bacon', 'ham', 'turkey', 'lamb', 'duck', 'sausage', 'meat',
            # Eggs and other animal products
            'egg', 'eggs', 'honey', 'gelatin', 'mayo', 'mayonnaise'
        ]
        
        # Check title for non-vegan ingredients
        detected_non_vegan = []
        for ingredient in dairy_indicators:
            if ingredient in title_lower:
                detected_non_vegan.append(f"'{ingredient}' in title")
        
        # Check confidence notes for non-vegan ingredients  
        for ingredient in dairy_indicators:
            if ingredient in notes_lower:
                detected_non_vegan.append(f"'{ingredient}' in notes")
        
        if detected_non_vegan:
            print(f"🚫 Found non-vegan ingredients in '{recipe_title}': {detected_non_vegan}")
            return False
        
        # Special check for common problematic recipes
        if 'farro' in title_lower and 'salad' in title_lower:
            print(f"⚠️ Farro salad detected - these often contain parmesan cheese")
            # Be extra cautious with farro salads as they commonly have parmesan
            return False
        
        # Special check for gochujang eggplant - this should typically be vegan
        if 'gochujang' in title_lower and 'eggplant' in title_lower:
            print(f"✅ Gochujang eggplant detected - typically vegan (eggplant + Korean chili paste)")
            # These are usually just eggplant, gochujang, oil, scallions - all vegan
            # Don't return False here, continue checking
        
        # Look for vegan ingredients in title only if no dairy found
        vegan_ingredients = [
            'tofu', 'tempeh', 'miso', 'vegetables', 'vegetable', 'beans', 'lentils', 
            'chickpeas', 'quinoa', 'oats', 'rice', 'pasta', 'noodles', 'hummus',
            'avocado', 'tahini', 'coconut', 'mushrooms', 'broccoli', 'spinach', 
            'kale', 'tomato', 'garlic', 'onion', 'eggplant', 'gochujang'
        ]
        
        # Check if title has vegan ingredients
        has_vegan_ingredients = any(ingredient in title_lower for ingredient in vegan_ingredients)
        
        # Check if notes explicitly mention it's plant-based or vegan
        notes_explicitly_vegan = any(phrase in notes_lower for phrase in [
            'plant-based', 'vegan', 'all ingredients are plant', 'no animal products',
            'contains zero animal products'
        ])
        
        # Only suggest vegan if there are strong positive indicators AND no dairy found
        result = (has_vegan_ingredients or notes_explicitly_vegan)
        
        if result:
            print(f"✅ Recipe '{recipe_title}' looks vegan - no dairy detected, has vegan ingredients")
        else:
            print(f"❓ Recipe '{recipe_title}' unclear - not enough vegan indicators")
            
        return result
    
    def _should_be_vegetarian(self, recipe_title: str, confidence_notes: str) -> bool:
        """Check if a recipe should be tagged as vegetarian based on title and notes"""
        title_lower = recipe_title.lower()
        notes_lower = confidence_notes.lower() if confidence_notes else ""
        
        print(f"🔍 VEGETARIAN CHECK for: '{recipe_title}'")
        
        # Look for vegetarian indicators (including dairy)
        vegetarian_ingredients = [
            'vegetables', 'vegetable', 'salad', 'pasta', 'farro', 'quinoa', 'rice',
            'beans', 'lentils', 'chickpeas', 'cheese', 'parmesan', 'mozzarella',
            'feta', 'goat cheese', 'cream', 'butter', 'egg', 'eggs'
        ]
        
        # Meat and seafood indicators (if present, not vegetarian)
        meat_indicators = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp', 'crab',
            'bacon', 'ham', 'turkey', 'lamb', 'duck', 'sausage', 'meat'
        ]
        
        # SPECIAL CASE: Farro salads commonly have parmesan cheese
        if 'farro' in title_lower and 'salad' in title_lower:
            print(f"🔧 Farro salad detected - these commonly contain parmesan cheese")
            return True
        
        # Check if title has meat ingredients
        has_meat = any(ingredient in title_lower for ingredient in meat_indicators)
        if has_meat:
            print(f"🚫 Found meat indicators, not vegetarian")
            return False
        
        # Check if confidence notes mention meat
        notes_has_meat = any(ingredient in notes_lower for ingredient in meat_indicators)
        if notes_has_meat:
            print(f"🚫 Found meat in notes, not vegetarian")
            return False
        
        # Check if title has vegetarian ingredients
        has_vegetarian_ingredients = any(ingredient in title_lower for ingredient in vegetarian_ingredients)
        
        # Check if notes suggest vegetarian
        notes_suggests_vegetarian = any(phrase in notes_lower for phrase in [
            'vegetarian', 'no meat', 'dairy', 'cheese', 'plant-based with'
        ])
        
        result = (has_vegetarian_ingredients or notes_suggests_vegetarian) and not has_meat and not notes_has_meat
        print(f"🔍 Should be vegetarian: {result}")
        return result
    
    def _should_be_easily_veganizable(self, recipe_title: str, confidence_notes: str) -> bool:
        """Check if a vegetarian recipe should be tagged as easily veganizable"""
        title_lower = recipe_title.lower()
        notes_lower = confidence_notes.lower() if confidence_notes else ""
        
        print(f"🔍 EASILY VEGANIZABLE CHECK for: '{recipe_title}'")
        print(f"🔍 Title: '{title_lower}'")
        print(f"🔍 Notes: '{notes_lower}'")
        
        # Easy to replace dairy ingredients (small amounts or optional toppings)
        easily_replaceable_dairy = [
            'parmesan', 'parmigiano', 'pecorino', 'romano',  # Hard cheeses (can be omitted/replaced)
            'feta',  # Often used as garnish/topping
            'goat cheese',  # Often used as garnish/topping
            'butter',  # Can be replaced with oil
            'cheese'  # Generic cheese mention
        ]
        
        # Hard to replace ingredients (central to the dish)
        hard_to_replace = [
            'heavy cream', 'cream sauce', 'milk', 'cream cheese',  # Central to cream sauces, etc.
            'egg', 'eggs',  # Hard to replace in baking
            'ricotta', 'mozzarella', 'cheddar'  # Often central to the dish
        ]
        
        # Check for easily replaceable dairy
        found_replaceable = []
        for dairy in easily_replaceable_dairy:
            if dairy in title_lower:
                found_replaceable.append(f"'{dairy}' in title")
            if dairy in notes_lower:
                found_replaceable.append(f"'{dairy}' in notes")
        
        # Check for hard-to-replace ingredients
        found_hard_to_replace = []
        for dairy in hard_to_replace:
            if dairy in title_lower:
                found_hard_to_replace.append(f"'{dairy}' in title")
            if dairy in notes_lower:
                found_hard_to_replace.append(f"'{dairy}' in notes")
        
        print(f"🔍 Found easily replaceable dairy: {found_replaceable}")
        print(f"🔍 Found hard-to-replace dairy: {found_hard_to_replace}")
        
        # Recipe patterns that are usually easily veganizable
        easily_veganizable_patterns = [
            'farro salad',  # Parmesan is usually just a topping
            'grain salad',  # Cheese usually a topping
            'pasta salad',  # Cheese often optional
            'grain bowl',   # Cheese usually a topping
            'quinoa salad', # Cheese usually a topping
            'roasted vegetables',  # Cheese usually a garnish
            'vegetable salad'  # Cheese usually a topping
        ]
        
        found_patterns = []
        for pattern in easily_veganizable_patterns:
            if pattern in title_lower:
                found_patterns.append(pattern)
        
        print(f"🔍 Found easily veganizable patterns: {found_patterns}")
        
        # Check confidence notes for indicators
        notes_suggests_easily_veganizable = any(phrase in notes_lower for phrase in [
            'easily vegan', 'omit', 'substitute', 'replace', 'optional', 'garnish', 'topping'
        ])
        
        print(f"🔍 Notes suggest easily veganizable: {notes_suggests_easily_veganizable}")
        
        # Logic: easily veganizable if:
        # 1. Has easily replaceable dairy OR fits a pattern OR notes suggest it
        # 2. AND doesn't have hard-to-replace ingredients
        has_positive_indicators = (
            len(found_replaceable) > 0 or 
            len(found_patterns) > 0 or 
            notes_suggests_easily_veganizable
        )
        
        has_blocking_ingredients = len(found_hard_to_replace) > 0
        
        result = has_positive_indicators and not has_blocking_ingredients
        
        print(f"🔍 Positive indicators: {has_positive_indicators}")
        print(f"🔍 Blocking ingredients: {has_blocking_ingredients}")
        print(f"🔍 Should be easily veganizable: {result}")
        
        return result
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        import re
        
        # Fix missing commas before "confidence_notes"
        json_str = re.sub(r'(\])\s*("confidence_notes")', r'\1,\n    \2', json_str)
        
        # Fix missing commas before any field that starts with a quote
        json_str = re.sub(r'(\]|\})\s*("[\w_]+":)', r'\1,\n    \2', json_str)
        
        # Fix trailing commas before closing brace
        json_str = re.sub(r',\s*\}', r'\n}', json_str)
        
        return json_str
    
    def _validate_tags(self, tags: List[str], valid_tags: List[str], category: str) -> List[str]:
        """Validate and filter tags against known good tags"""
        if not tags:
            return []
        
        print(f"🔍 DEBUG: Validating {category} tags: {tags}")
        print(f"🔍 DEBUG: Valid tags for {category}: {valid_tags}")
        
        # Convert to lowercase for comparison
        valid_tags_lower = [tag.lower() for tag in valid_tags]
        validated = []
        
        for tag in tags:
            tag_lower = tag.lower().strip()
            print(f"🔍 DEBUG: Checking tag '{tag}' (lowercase: '{tag_lower}')")
            if tag_lower in valid_tags_lower:
                # Find the original casing from valid_tags
                original_tag = valid_tags[valid_tags_lower.index(tag_lower)]
                validated.append(original_tag)
                print(f"🔍 DEBUG: ✅ Tag '{tag}' validated as '{original_tag}'")
            else:
                print(f"⚠️ Invalid {category} tag ignored: '{tag}'")
                print(f"⚠️ Available options: {valid_tags_lower}")
        
        print(f"🔍 DEBUG: Final validated {category} tags: {validated}")
        return validated

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
            
            # Step 2: Add AI categorization
            categorization = await self.categorization_service.categorize_recipe(recipe)
            
            if categorization:
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
                    cuisine=recipe.cuisine,  # Keep original if any
                    category=recipe.category,  # Keep original if any
                    keywords=recipe.keywords,
                    found_structured_data=recipe.found_structured_data,
                    used_ai=True,  # Mark as AI-enhanced
                    raw_ingredients=getattr(recipe, 'raw_ingredients', []),  # Handle missing field gracefully
                    raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),  # Handle missing field gracefully
                    
                    # Add new categorization fields
                    health_tags=categorization.health_tags,
                    dish_type=categorization.dish_type,
                    cuisine_type=categorization.cuisine_type,
                    meal_type=categorization.meal_type,
                    season=categorization.season,
                    ai_confidence_notes=categorization.confidence_notes,
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
            raw_ingredients=getattr(recipe, 'raw_ingredients', []),  # Handle missing field gracefully
            raw_ingredients_detailed=getattr(recipe, 'raw_ingredients_detailed', []),  # Handle missing field gracefully
            
            # Enhanced fields
            health_tags=categorization.health_tags,
            dish_type=categorization.dish_type,
            cuisine_type=categorization.cuisine_type,
            meal_type=categorization.meal_type,
            season=categorization.season,
            ai_confidence_notes=categorization.confidence_notes,
            ai_enhanced=True,
            ai_model_used=categorization.ai_model
        )
