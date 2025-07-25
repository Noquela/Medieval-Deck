"""
Asset Generator for Medieval Deck backgrounds using SDXL.

Handles AI generation of card backgrounds with prompt optimization and caching.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import hashlib
import json
from datetime import datetime
import PIL.Image

from ..models.sdxl_pipeline import SDXLPipeline
from ..models.card_models import Card, CardType, Rarity
from .prompt_optimizer import PromptOptimizer
from ..utils.config import Config

logger = logging.getLogger(__name__)


class AssetGenerator:
    """
    Generates and manages AI-created backgrounds for medieval cards.
    
    Features:
    - SDXL-based background generation
    - Intelligent prompt optimization
    - Asset caching and management
    - Quality-focused generation parameters
    - Batch processing capabilities
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        sdxl_pipeline: Optional[SDXLPipeline] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize asset generator.
        
        Args:
            config: Configuration object
            sdxl_pipeline: Pre-initialized SDXL pipeline
            cache_dir: Directory for caching generated assets
        """
        self.config = config or Config()
        self.cache_dir = Path(cache_dir or self.config.assets_cache_dir)
        self.generated_dir = Path(self.config.assets_generated_dir)
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.sdxl_pipeline = sdxl_pipeline or SDXLPipeline(
            cache_dir=str(self.cache_dir),
            memory_efficient=self.config.memory_efficient
        )
        self.prompt_optimizer = PromptOptimizer()
        
        # Asset cache
        self.asset_cache = self._load_asset_cache()
        
        logger.info(f"Asset Generator initialized with cache: {self.cache_dir}")
        
    def _load_asset_cache(self) -> Dict[str, Any]:
        """Load asset cache from disk."""
        cache_file = self.cache_dir / "asset_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load asset cache: {e}")
        return {}
        
    def _save_asset_cache(self) -> None:
        """Save asset cache to disk."""
        cache_file = self.cache_dir / "asset_cache.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.asset_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save asset cache: {e}")
            
    def _generate_prompt_hash(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate hash for prompt and parameters for caching."""
        cache_key = f"{prompt}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_key.encode()).hexdigest()
        
    def _get_card_base_prompt(self, card: Card) -> str:
        """
        Generate base prompt for card based on its properties.
        
        Args:
            card: Card to generate prompt for
            
        Returns:
            Base prompt string
        """
        prompts = []
        
        # Card type specific prompts
        type_prompts = {
            CardType.CREATURE: [
                "medieval fantasy creature", "monster", "beast",
                "dark forest", "ancient ruins", "mystical cavern"
            ],
            CardType.SPELL: [
                "magical energy", "spell casting", "arcane symbols",
                "wizard tower", "enchanted library", "mystical ritual"
            ],
            CardType.ARTIFACT: [
                "ancient relic", "magical item", "ornate weapon",
                "treasure chamber", "sacred temple", "royal vault"
            ],
            CardType.LAND: [
                "medieval landscape", "fantasy realm", "ancient kingdom",
                "rolling hills", "dark forest", "mountain pass"
            ]
        }
        
        if card.type in type_prompts:
            prompts.extend(type_prompts[card.type])
            
        # Rarity specific prompts
        rarity_prompts = {
            Rarity.COMMON: ["rustic", "simple", "weathered"],
            Rarity.UNCOMMON: ["ornate", "decorated", "refined"],
            Rarity.RARE: ["magnificent", "golden", "jeweled", "majestic"],
            Rarity.LEGENDARY: ["epic", "divine", "legendary", "mythical", "godlike"]
        }
        
        if card.rarity in rarity_prompts:
            prompts.extend(rarity_prompts[card.rarity])
            
        # Add card-specific prompt if available
        if card.background_prompt:
            prompts.append(card.background_prompt)
            
        return ", ".join(prompts)
        
    def generate_card_background(
        self,
        card: Card,
        force_regenerate: bool = False,
        save_to_card: bool = True,
        **generation_params
    ) -> PIL.Image.Image:
        """
        Generate background image for a card.
        
        Args:
            card: Card to generate background for
            force_regenerate: Force regeneration even if cached
            save_to_card: Save path to card object
            **generation_params: Additional generation parameters
            
        Returns:
            Generated PIL Image
        """
        # Build prompt
        base_prompt = self._get_card_base_prompt(card)
        optimized_prompt = self.prompt_optimizer.optimize_prompt(
            base_prompt,
            card_type=card.type,
            rarity=card.rarity
        )
        
        # Generation parameters
        params = {
            "num_inference_steps": 80,
            "guidance_scale": 8.5,
            "width": 1024,
            "height": 1024,
            **generation_params
        }
        
        # Check cache
        prompt_hash = self._generate_prompt_hash(optimized_prompt, params)
        cached_path = self.generated_dir / f"{card.id}_{prompt_hash}.png"
        
        if cached_path.exists() and not force_regenerate:
            logger.info(f"Using cached background for card {card.id}")
            image = PIL.Image.open(cached_path)
        else:
            logger.info(f"Generating new background for card {card.id}")
            
            # Ensure models are loaded
            self.sdxl_pipeline.load_models()
            
            # Generate image
            image = self.sdxl_pipeline.generate_image(
                prompt=optimized_prompt,
                **params
            )
            
            # Save generated image
            image.save(cached_path, "PNG", quality=95)
            
            # Update cache
            self.asset_cache[card.id] = {
                "prompt": optimized_prompt,
                "params": params,
                "hash": prompt_hash,
                "path": str(cached_path),
                "generated_at": datetime.now().isoformat(),
                "card_name": card.name,
                "card_type": card.type.value,
                "card_rarity": card.rarity.value
            }
            self._save_asset_cache()
            
        # Update card with background path
        if save_to_card:
            card.background_path = str(cached_path)
            
        return image
        
    def generate_batch_backgrounds(
        self,
        cards: List[Card],
        force_regenerate: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, PIL.Image.Image]:
        """
        Generate backgrounds for multiple cards in batch.
        
        Args:
            cards: List of cards to generate backgrounds for
            force_regenerate: Force regeneration even if cached
            progress_callback: Callback for progress updates
            
        Returns:
            Dictionary mapping card IDs to generated images
        """
        results = {}
        total_cards = len(cards)
        
        logger.info(f"Starting batch generation for {total_cards} cards")
        
        # Ensure models are loaded once
        self.sdxl_pipeline.load_models()
        
        try:
            for i, card in enumerate(cards):
                logger.info(f"Processing card {i+1}/{total_cards}: {card.name}")
                
                try:
                    image = self.generate_card_background(
                        card,
                        force_regenerate=force_regenerate,
                        save_to_card=True
                    )
                    results[card.id] = image
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(i + 1, total_cards, card.name)
                        
                except Exception as e:
                    logger.error(f"Failed to generate background for {card.name}: {e}")
                    
        finally:
            # Clean up memory after batch
            if self.config.memory_efficient:
                memory_info = self.sdxl_pipeline.get_memory_usage()
                logger.info(f"Memory usage after batch: {memory_info}")
                
        logger.info(f"Batch generation complete: {len(results)}/{total_cards} successful")
        return results
        
    def regenerate_card_background(
        self,
        card: Card,
        new_prompt: Optional[str] = None,
        **generation_params
    ) -> PIL.Image.Image:
        """
        Regenerate background for a card with new parameters.
        
        Args:
            card: Card to regenerate background for
            new_prompt: New prompt to use (optional)
            **generation_params: New generation parameters
            
        Returns:
            Newly generated PIL Image
        """
        if new_prompt:
            card.background_prompt = new_prompt
            
        return self.generate_card_background(
            card,
            force_regenerate=True,
            **generation_params
        )
        
    def get_cached_backgrounds(self) -> List[Dict[str, Any]]:
        """Get list of all cached backgrounds."""
        return list(self.asset_cache.values())
        
    def cleanup_unused_backgrounds(self, active_cards: List[Card]) -> int:
        """
        Clean up background files for cards no longer in use.
        
        Args:
            active_cards: List of cards currently in use
            
        Returns:
            Number of files cleaned up
        """
        active_card_ids = {card.id for card in active_cards}
        cleaned_count = 0
        
        # Find unused cached entries
        unused_entries = [
            card_id for card_id in self.asset_cache.keys()
            if card_id not in active_card_ids
        ]
        
        for card_id in unused_entries:
            try:
                # Remove file
                cached_info = self.asset_cache[card_id]
                cached_path = Path(cached_info["path"])
                if cached_path.exists():
                    cached_path.unlink()
                    
                # Remove from cache
                del self.asset_cache[card_id]
                cleaned_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to cleanup background for {card_id}: {e}")
                
        if cleaned_count > 0:
            self._save_asset_cache()
            logger.info(f"Cleaned up {cleaned_count} unused background files")
            
        return cleaned_count
        
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about generated assets."""
        if not self.asset_cache:
            return {"total_generated": 0}
            
        type_counts = {}
        rarity_counts = {}
        
        for info in self.asset_cache.values():
            card_type = info.get("card_type", "unknown")
            card_rarity = info.get("card_rarity", "unknown")
            
            type_counts[card_type] = type_counts.get(card_type, 0) + 1
            rarity_counts[card_rarity] = rarity_counts.get(card_rarity, 0) + 1
            
        # Calculate total file size
        total_size = 0
        for info in self.asset_cache.values():
            try:
                path = Path(info["path"])
                if path.exists():
                    total_size += path.stat().st_size
            except Exception:
                pass
                
        return {
            "total_generated": len(self.asset_cache),
            "by_type": type_counts,
            "by_rarity": rarity_counts,
            "total_size_mb": total_size / 1024 / 1024,
            "cache_dir": str(self.cache_dir),
            "generated_dir": str(self.generated_dir)
        }
        
    def generate_all_card_backgrounds_from_config(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Generate backgrounds for all cards defined in the cards.json configuration.
        
        Args:
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Dictionary mapping card IDs to generated image paths
        """
        logger.info("Starting generation of all card backgrounds from configuration...")
        
        # Load cards configuration
        import json
        cards_config_path = self.config.get_cards_config_path()
        
        if not cards_config_path.exists():
            logger.error("Cards configuration file not found")
            return {}
            
        try:
            with open(cards_config_path, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cards configuration: {e}")
            return {}
            
        cards = cards_data.get('cards', [])
        generated_paths = {}
        total_cards = len(cards)
        
        if total_cards == 0:
            logger.warning("No cards found in configuration")
            return {}
            
        logger.info(f"Found {total_cards} cards to generate backgrounds for")
        
        # Ensure models are loaded once for batch
        self.sdxl_pipeline.load_models()
        
        try:
            for i, card_data in enumerate(cards, 1):
                card_id = card_data.get('id')
                card_name = card_data.get('name', card_id)
                background_prompt = card_data.get('background_prompt')
                card_type = card_data.get('type', 'unknown')
                card_rarity = card_data.get('rarity', 'common')
                
                if not card_id or not background_prompt:
                    logger.warning(f"Skipping card with missing id or background_prompt: {card_data}")
                    continue
                    
                logger.info(f"[{i}/{total_cards}] Generating background for '{card_name}' ({card_id})...")
                
                # Check cache first
                prompt_hash = self._generate_prompt_hash(background_prompt, {
                    "width": 512, "height": 768, "guidance_scale": 8.5, "num_inference_steps": 50
                })
                cached_path = self.generated_dir / f"{card_id}_{prompt_hash}.png"
                
                if cached_path.exists() and not force_regenerate:
                    logger.info(f"✅ Using cached background for {card_id}")
                    generated_paths[card_id] = str(cached_path)
                    
                    # Update cache info
                    self.asset_cache[card_id] = {
                        "prompt": background_prompt,
                        "params": {"width": 512, "height": 768, "guidance_scale": 8.5, "num_inference_steps": 50},
                        "hash": prompt_hash,
                        "path": str(cached_path),
                        "generated_at": datetime.now().isoformat(),
                        "card_name": card_name,
                        "card_type": card_type,
                        "card_rarity": card_rarity
                    }
                    continue
                
                try:
                    # Optimize prompt for better results
                    optimized_prompt = self.prompt_optimizer.optimize_prompt(
                        background_prompt,
                        card_type=card_type,
                        rarity=card_rarity
                    )
                    
                    # Generate image with card-optimized dimensions (portrait format for cards)
                    image = self.sdxl_pipeline.generate_image(
                        prompt=optimized_prompt,
                        width=512,
                        height=768,
                        guidance_scale=8.5,
                        num_inference_steps=50
                    )
                    
                    if image is None:
                        logger.error(f"❌ Failed to generate image for {card_id}")
                        continue
                        
                    # Save generated image
                    image.save(cached_path, "PNG", quality=95)
                    generated_paths[card_id] = str(cached_path)
                    
                    # Update cache
                    self.asset_cache[card_id] = {
                        "prompt": optimized_prompt,
                        "params": {"width": 512, "height": 768, "guidance_scale": 8.5, "num_inference_steps": 50},
                        "hash": prompt_hash,
                        "path": str(cached_path),
                        "generated_at": datetime.now().isoformat(),
                        "card_name": card_name,
                        "card_type": card_type,
                        "card_rarity": card_rarity
                    }
                    
                    logger.info(f"✅ Generated: {card_name} ({card_id})")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate background for {card_id}: {e}")
                    
        finally:
            # Save cache after batch
            self._save_asset_cache()
            
            # Memory cleanup
            if self.config.memory_efficient:
                memory_info = self.sdxl_pipeline.get_memory_usage()
                logger.info(f"Memory usage after batch generation: {memory_info}")
                
        logger.info(f"🎉 Completed background generation: {len(generated_paths)}/{total_cards} successful")
        logger.info(f"Generated images saved to: {self.generated_dir}")
        
        return generated_paths

    def generate_background(self, force_regenerate: bool = False) -> PIL.Image.Image:
        """
        Generate main menu background image.
        
        Args:
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Generated PIL Image
        """
        background_path = self.generated_dir / "background.png"
        
        if background_path.exists() and not force_regenerate:
            logger.info("Using cached background image")
            return PIL.Image.open(background_path)
            
        logger.info("Generating main background image...")
        
        # Ensure models are loaded
        self.sdxl_pipeline.load_models()
        
        # Generate background with specific prompt
        prompt = "gothic cathedral courtyard, high stone arches, soft mist, golden sunset, cinematic"
        
        image = self.sdxl_pipeline.generate_image(
            prompt=prompt,
            num_inference_steps=80,
            guidance_scale=8.5,
            width=1024,
            height=1024
        )
        
        # Save background
        image.save(background_path, "PNG", quality=95)
        
        # Update cache
        self.asset_cache["background"] = {
            "prompt": prompt,
            "path": str(background_path),
            "generated_at": datetime.now().isoformat(),
            "type": "background"
        }
        self._save_asset_cache()
        
        logger.info("Background image generated successfully")
        return image
        
    def generate_card_image(self, card_type: str, force_regenerate: bool = False) -> PIL.Image.Image:
        """
        Generate card image with specific prompts for each type.
        
        Args:
            card_type: Type of card ('warrior', 'wizard', 'assassin')
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Generated PIL Image
        """
        # Specific prompts for each card type
        prompts = {
            "warrior": "heroic warrior portrait, red banners, high detail, medieval armor, noble stance",
            "wizard": "arcane wizard, purple and blue energy, mystical runes, flowing robes, magical aura",
            "assassin": "dark assassin, black hood, soft shadows, moody lighting, stealth pose"
        }
        
        if card_type not in prompts:
            raise ValueError(f"Unknown card type: {card_type}")
            
        card_path = self.generated_dir / f"{card_type}.png"
        
        if card_path.exists() and not force_regenerate:
            logger.info(f"Using cached {card_type} image")
            return PIL.Image.open(card_path)
            
        if not force_regenerate:
            logger.info(f"Skipping generation of {card_type} - using placeholder")
            # Create a simple placeholder image
            placeholder = PIL.Image.new('RGB', (512, 512), color=(100, 100, 100))
            return placeholder
            
        logger.info(f"Generating {card_type} card image...")
        
        # Ensure models are loaded
        self.sdxl_pipeline.load_models()
        
        # Generate image
        prompt = prompts[card_type]
        image = self.sdxl_pipeline.generate_image(
            prompt=prompt,
            num_inference_steps=80,
            guidance_scale=8.5,
            width=1024,
            height=1024
        )
        
        # Save image
        image.save(card_path, "PNG", quality=95)
        
        # Update cache
        self.asset_cache[f"{card_type}_card"] = {
            "prompt": prompt,
            "path": str(card_path),
            "generated_at": datetime.now().isoformat(),
            "type": "card_image"
        }
        self._save_asset_cache()
        
        logger.info(f"{card_type.capitalize()} card image generated successfully")
        return image

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self._save_asset_cache()
        except Exception:
            pass
