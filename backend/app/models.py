# backend/app/models.py (Enhanced version with adaptability tags)
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime

class RecipeURL(BaseModel):
    """Request model for recipe URL parsing"""
    url: HttpUrl = Field(..., description="The recipe URL to parse")

class RecipeAdaptability(BaseModel):
    """AI-generated recipe adaptability suggestions"""
    easily_veganizable: bool = Field(default=False, description="Can be easily made vegan")
    vegan_adaptations: Optional[str] = Field(None, description="How to make this recipe vegan")
    
    easily_vegetarianizable: bool = Field(default=False, description="Can be easily made vegetarian") 
    vegetarian_adaptations: Optional[str] = Field(None, description="How to make this recipe vegetarian")
    
    easily_healthified: bool = Field(default=False, description="Can be easily made healthier")
    healthy_adaptations: Optional[str] = Field(None, description="How to make this recipe healthier")

class RecipeCategorization(BaseModel):
    """AI-generated recipe categorization data"""
    health_tags: List[str] = Field(default_factory=list, description="Dietary and health-related tags")
    dish_type: List[str] = Field(default_factory=list, description="Type of dish (main course, dessert, etc.)")
    cuisine_type: List[str] = Field(default_factory=list, description="Cuisine style (italian, mexican, etc.)")
    meal_type: List[str] = Field(default_factory=list, description="Meal timing (breakfast, lunch, etc.)")
    season: List[str] = Field(default_factory=list, description="Seasonal associations")
    confidence_notes: Optional[str] = Field(None, description="AI confidence and reasoning notes")
    confidence_notes_user: Optional[str] = Field(None, description="Condensed user-friendly confidence explanation")  # ADD THIS LINE
    ai_model: Optional[str] = Field(None, description="AI model used for categorization")
    categorized_at: Optional[datetime] = Field(None, description="When categorization was performed")
    
    # NEW: Recipe adaptability suggestions
    adaptability: RecipeAdaptability = Field(default_factory=RecipeAdaptability, description="Recipe adaptation suggestions")

class Recipe(BaseModel):
    """Recipe data model with AI categorization and adaptability (now default)"""
    # Basic recipe data
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    source: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    servings: Optional[str] = None
    cuisine: Optional[str] = None  # Legacy field from scrapers
    category: Optional[str] = None  # Legacy field from scrapers
    keywords: List[str] = []
    found_structured_data: bool = False
    used_ai: bool = False
    
    # Fields that your existing RecipeService expects
    raw_ingredients: List[str] = Field(default_factory=list, description="Raw ingredient strings for search/processing")
    raw_ingredients_detailed: List[dict] = Field(default_factory=list, description="Detailed ingredient information with metadata")
    
    # AI-enhanced categorization fields (now standard)
    health_tags: List[str] = Field(default_factory=list, description="AI-identified health and dietary tags")
    dish_type: List[str] = Field(default_factory=list, description="AI-identified dish types")
    cuisine_type: List[str] = Field(default_factory=list, description="AI-identified cuisine styles")
    meal_type: List[str] = Field(default_factory=list, description="AI-identified meal types")
    season: List[str] = Field(default_factory=list, description="AI-identified seasonal associations")
    ai_confidence_notes: Optional[str] = Field(None, description="AI reasoning for categorization")
    ai_confidence_notes_user: Optional[str] = Field(None, description="User-friendly AI reasoning summary")
    
    # NEW: Recipe adaptability fields
    easily_veganizable: bool = Field(default=False, description="Recipe can be easily made vegan")
    vegan_adaptations: Optional[str] = Field(None, description="Instructions for making this recipe vegan")
    
    easily_vegetarianizable: bool = Field(default=False, description="Recipe can be easily made vegetarian")
    vegetarian_adaptations: Optional[str] = Field(None, description="Instructions for making this recipe vegetarian")
    
    easily_healthified: bool = Field(default=False, description="Recipe can be easily made healthier")
    healthy_adaptations: Optional[str] = Field(None, description="Instructions for making this recipe healthier")
    
    # Metadata
    ai_enhanced: bool = Field(default=False, description="Whether recipe has been AI-categorized")
    ai_model_used: Optional[str] = Field(None, description="AI model used for enhancement")

class RecipeSearchFilters(BaseModel):
    """Model for recipe search and filtering"""
    # Text search
    query: Optional[str] = Field(None, description="Text search in title, description, ingredients")
    
    # AI categorization filters
    health_tags: List[str] = Field(default_factory=list, description="Filter by health/dietary tags")
    dish_type: List[str] = Field(default_factory=list, description="Filter by dish type")
    cuisine_type: List[str] = Field(default_factory=list, description="Filter by cuisine")
    meal_type: List[str] = Field(default_factory=list, description="Filter by meal type")
    season: List[str] = Field(default_factory=list, description="Filter by season")
    
    # NEW: Adaptability filters
    show_veganizable: Optional[bool] = Field(None, description="Show recipes that can be made vegan")
    show_vegetarianizable: Optional[bool] = Field(None, description="Show recipes that can be made vegetarian")
    show_healthifiable: Optional[bool] = Field(None, description="Show recipes that can be made healthier")
    
    # Traditional filters
    max_prep_time: Optional[int] = Field(None, description="Maximum prep time in minutes")
    max_cook_time: Optional[int] = Field(None, description="Maximum cook time in minutes")
    has_image: Optional[bool] = Field(None, description="Filter recipes with/without images")
    
    # Pagination
    limit: int = Field(default=20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")

class RecipeStats(BaseModel):
    """Statistics about recipe categorization and adaptability"""
    total_recipes: int
    ai_enhanced_count: int
    ai_enhancement_percentage: float
    top_health_tags: List[dict]  # [{"tag": "vegetarian", "count": 15}, ...]
    top_cuisines: List[dict]
    top_dish_types: List[dict]
    seasonal_distribution: dict  # {"spring": 45, "summer": 67, ...}
    
    # NEW: Adaptability statistics
    veganizable_count: int = Field(default=0, description="Count of easily veganizable recipes")
    vegetarianizable_count: int = Field(default=0, description="Count of easily vegetarianizable recipes") 
    healthifiable_count: int = Field(default=0, description="Count of easily healthifiable recipes")
    
    adaptability_percentages: dict = Field(default_factory=dict, description="Percentages for each adaptability type")

class BatchCategorizationRequest(BaseModel):
    """Request model for batch categorizing existing recipes"""
    recipe_ids: Optional[List[int]] = Field(None, description="Specific recipe IDs to categorize")
    limit: Optional[int] = Field(None, description="Limit number of recipes to categorize")
    force_recategorize: bool = Field(default=False, description="Re-categorize already processed recipes")

class BatchCategorizationStatus(BaseModel):
    """Status response for batch categorization"""
    status: str  # "in_progress", "completed", "failed"
    total_recipes: int
    processed_count: int
    success_count: int
    error_count: int
    estimated_completion: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)

class DebugInfo(BaseModel):
    """Debug information about a webpage"""
    status: str
    html_length: Optional[int] = None
    json_scripts_found: Optional[int] = None
    json_scripts_content: Optional[List[dict]] = None
    ai_available: Optional[bool] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    ai_available: bool
    ai_model: Optional[str] = None
    ai_categorization_enabled: bool = Field(default=True, description="AI categorization is now standard")
    ai_adaptability_enabled: bool = Field(default=True, description="AI adaptability suggestions enabled")
    timestamp: Optional[str] = None
