from typing import Optional
from recipe_scrapers import scrape_me
from app.models import Recipe
from .base import BaseParser

class RecipeScrapersParser(BaseParser):
    """Parser using the recipe-scrapers library"""
    
    @property
    def name(self) -> str:
        return "recipe-scrapers"
    
    def can_parse(self, url: str) -> bool:
        """recipe-scrapers can attempt to parse any URL"""
        return True
    
    def parse(self, url: str, **kwargs) -> Optional[Recipe]:
        """Parse recipe using recipe-scrapers library"""
        try:
            scraper = scrape_me(url)
            
            # Extract with error handling for each field
            title = scraper.title() or "Untitled Recipe"
            ingredients = scraper.ingredients() or []
            instructions = scraper.instructions_list() or []
            
            # Optional fields with error handling
            description = self._safe_extract(scraper.description)
            image = self._safe_extract(scraper.image)
            cuisine = self._safe_extract(scraper.cuisine)
            category = self._safe_extract(scraper.category)
            
            # Handle prep/cook time safely
            prep_time = self._safe_extract(scraper.prep_time)
            cook_time = self._safe_extract(scraper.cook_time)
            servings = self._safe_extract(scraper.yields)
            
            # Extract source (author or site name)
            source = self._extract_source(scraper, url)

            # Handle keywords
            keywords = self._extract_keywords(scraper)
            
            print(f"recipe-scrapers extracted: {title}")
            print(f"  - {len(ingredients)} ingredients, {len(instructions)} instructions")
            print(f"  - image: {image}")
            
            return Recipe(
                title=title,
                description=description,
                image=image,
                ingredients=ingredients,
                source=source,
                instructions=instructions,
                prep_time=str(prep_time) if prep_time else None,
                cook_time=str(cook_time) if cook_time else None,
                servings=str(servings) if servings else None,
                cuisine=cuisine,
                category=category,
                keywords=keywords,
                found_structured_data=True,
                used_ai=False
            )
            
        except Exception as e:
            print(f"recipe-scrapers failed: {e}")
            return None
    
    def _extract_source(self, scraper, url: str) -> Optional[str]:
        """Extract source organization/blog name"""
        # Try to get author from scraper (might be organization name)
        try:
            author = scraper.author()
            if author and isinstance(author, str):
                # Clean up author - often contains org name or blog name
                author = author.strip()
                if author and not self._looks_like_person_name(author):
                    return author
        except:
            pass
        
        # Fallback: Extract site name from URL
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Convert domain to readable site name
            site_name = self._domain_to_site_name(domain)
            return site_name
            
        except:
            return None
        
    def _safe_extract(self, extractor_func):
        """Safely extract data with error handling"""
        try:
            return extractor_func()
        except:
            return None
    
    def _extract_keywords(self, scraper) -> list:
        """Extract keywords with error handling"""
        try:
            keywords = scraper.keywords() or []
            if isinstance(keywords, str):
                return [k.strip() for k in keywords.split(',') if k.strip()]
            return keywords if isinstance(keywords, list) else []
        except:
            return []
