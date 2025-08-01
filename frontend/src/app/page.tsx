'use client';

import { useState } from 'react';
import { RecipeCard } from '@/components/RecipeCard';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface Recipe {
  title: string;
  description?: string;
  image?: string;
  ingredients: string[];
  instructions: string[];
  prep_time?: string;
  cook_time?: string;
  servings?: string;
  cuisine?: string;
  category?: string;
  keywords: string[];
  found_structured_data: boolean;
  used_ai: boolean;
  raw_ingredients: string[];
  raw_ingredients_detailed: Array<{
    name: string;
    quantity?: string;
    unit?: string;
    descriptors: string[];
    original: string;
    confidence: number;
    shopping_display: string;
  }>;
  
  // AI categorization fields
  health_tags: string[];
  dish_type: string[];
  cuisine_type: string[];
  meal_type: string[];
  season: string[];
  ai_confidence_notes?: string;
  ai_enhanced: boolean;
  ai_model_used?: string;
  
  // NEW: Adaptability fields
  easily_veganizable?: boolean;
  vegan_adaptations?: string;
  easily_vegetarianizable?: boolean;
  vegetarian_adaptations?: string;
  easily_healthified?: boolean;
  healthy_adaptations?: string;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false); // separate loading state for AI re-categorization
  const [error, setError] = useState<string | null>(null);

  const parseRecipe = async () => {
    if (!url.trim()) {
      setError('Please enter a recipe URL');
      return;
    }

    setLoading(true);
    setError(null);
    setRecipe(null);

    try {
      const response = await fetch('http://localhost:4321/parse-recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: Recipe = await response.json();
      setRecipe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse recipe');
    } finally {
      setLoading(false);
    }
  };

  // Function to re-categorize recipe with AI (now includes adaptability analysis)
  const reCategorizeRecipe = async () => {
    if (!recipe) return;

    setAiLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/categorize-recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recipe),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedRecipe: Recipe = await response.json();
      setRecipe(updatedRecipe);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to re-categorize recipe');
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    parseRecipe();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold text-white mb-4">
            🍳 Recipe Parser
          </h1>
          <p className="text-xl text-white/90 mb-2">
            Paste any recipe URL and get clean, structured recipe data
          </p>
          {/* NEW: Updated subtitle to mention adaptability features */}
          <p className="text-sm text-white/80">
            ✨ Now with AI-powered adaptability suggestions for vegan, vegetarian, and healthier versions!
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-lg font-semibold text-gray-700 mb-2">
                Recipe URL
              </label>
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/recipe-page"
                className="w-full p-4 text-lg border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:outline-none transition-colors text-gray-600"
                disabled={loading}
              />
            </div>
            
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white text-lg font-semibold py-4 px-6 rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]"
            >
              {loading ? 'Parsing Recipe...' : 'Parse Recipe & Analyze Adaptability'}
            </button>
          </form>

          {/* Quick Examples */}
          <div className="mt-6 p-4 bg-gray-50 rounded-xl">
            <p className="text-sm text-gray-600 mb-2">Try these example URLs:</p>
            <div className="space-y-1">
              <button
                onClick={() => setUrl('https://www.loveandlemons.com/grilled-ratatouille-tartines/')}
                className="block text-blue-600 hover:text-blue-800 text-sm underline"
                disabled={loading}
              >
                Love and Lemons - Grilled Ratatouille
              </button>
              <button
                onClick={() => setUrl('https://asianinspirations.com.au/recipes/braised-chicken-with-radish/')}
                className="block text-blue-600 hover:text-blue-800 text-sm underline"
                disabled={loading}
              >
                Asian Inspirations - Braised Chicken
              </button>
              {/* NEW: Example that should show good adaptability options */}
              <button
                onClick={() => setUrl('https://www.loveandlemons.com/spaghetti-carbonara-recipe/')}
                className="block text-blue-600 hover:text-blue-800 text-sm underline"
                disabled={loading}
              >
                Love and Lemons - Spaghetti Carbonara (Great for adaptability!)
              </button>
            </div>
          </div>

          {/* NEW: Feature highlight */}
          <div className="mt-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
            <div className="flex items-center mb-2">
              <span className="text-green-600 text-lg mr-2">✨</span>
              <h4 className="font-semibold text-green-800">New: Recipe Adaptability Analysis</h4>
            </div>
            <p className="text-sm text-green-700">
              Our AI will analyze each recipe and suggest easy ways to make it vegan, vegetarian, or healthier with simple ingredient swaps!
            </p>
          </div>
        </div>

        {/* Loading State */}
        {loading && <LoadingSpinner />}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-center">
              <span className="text-2xl mr-3">❌</span>
              <div>
                <h3 className="text-lg font-semibold text-red-800">Error</h3>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Recipe Result */}
        {recipe && (
          <RecipeCard 
            recipe={recipe} 
            onReCategorize={reCategorizeRecipe}
            aiLoading={aiLoading}
          />
        )}
      </div>
    </div>
  );
}
