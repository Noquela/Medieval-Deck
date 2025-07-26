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
        self.assets_dir = Path(self.config.assets_dir)  # Usar assets_dir do config
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / "ia").mkdir(parents=True, exist_ok=True)  # Criar diretório ia
        
        # Initialize components
        self.sdxl_pipeline = sdxl_pipeline or SDXLPipeline(
            cache_dir=str(self.cache_dir),
            memory_efficient=self.config.ai.memory_efficient
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
    
    def _generate_image_from_prompt(self, prompt: str, width: int = 1024, height: int = 1024, cache_key: str = None) -> PIL.Image.Image:
        """
        Gera imagem usando SDXL pipeline com parâmetros otimizados.
        
        Args:
            prompt: Prompt para geração
            width: Largura da imagem
            height: Altura da imagem
            cache_key: Chave para cache (opcional)
            
        Returns:
            Imagem PIL gerada
        """
        if not self.sdxl_pipeline:
            raise RuntimeError("SDXL pipeline não disponível")
        
        # Carregar modelos se necessário
        self.sdxl_pipeline.load_models()
        
        # Gerar imagem
        image = self.sdxl_pipeline.generate_image(
            prompt=prompt,
            num_inference_steps=80,
            guidance_scale=8.5,
            width=width,
            height=height
        )
        
        return image
            
    def _generate_prompt_hash(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate hash for prompt and parameters for caching."""
        cache_key = f"{prompt}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_key.encode()).hexdigest()
        
    def _get_card_base_prompt(self, card: Card) -> str:
        """
        Generate base prompt for card based on its properties.
        Foca apenas em cenários medievais, sem personagens.
        
        Args:
            card: Card to generate prompt for
            
        Returns:
            Base prompt string
        """
        prompts = []
        
        # Card type specific prompts - APENAS CENÁRIOS
        type_prompts = {
            CardType.CREATURE: [
                "medieval castle courtyard", "dark forest clearing", "ancient stone ruins",
                "misty swampland", "dragon's lair cavern", "abandoned battlefield"
            ],
            CardType.SPELL: [
                "mystical library interior", "ancient wizard tower room", "magical ritual chamber",
                "enchanted forest glade", "floating magical islands", "arcane observatory"
            ],
            CardType.ARTIFACT: [
                "royal treasure chamber", "sacred temple interior", "ancient armory",
                "forgotten tomb chamber", "golden palace hall", "mystical shrine"
            ],
            CardType.LAND: [
                "medieval landscape", "fantasy kingdom vista", "ancient castle on hill",
                "rolling green hills", "dark enchanted forest", "mountain pass road"
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
        
        # Adicionar prompts que garantem apenas cenário
        scene_prompts = [
            "environment only", "landscape view", "architectural interior",
            "scenic background", "empty scene", "no people"
        ]
        prompts.extend(scene_prompts)
            
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
        
        # Generation parameters - com negative prompt específico para cenários
        background_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "people, person, human, character, figure, portrait, "
            "knight, wizard, warrior, mage, assassin, soldiers, "
            "face, body, arms, legs, hands, creatures, monsters, "
            "dragons, beings, entities"
        )
        
        params = {
            "num_inference_steps": 80,
            "guidance_scale": 8.5,
            "width": 1024,
            "height": 1024,
            "negative_prompt": background_negative_prompt,
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

    def generate_menu_background(self, force_regenerate: bool = False) -> PIL.Image.Image:
        """
        Gera background do menu principal com IA.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Imagem PIL do background do menu
        """
        cache_key = "menu_bg"
        
        # Verificar cache primeiro
        if not force_regenerate and cache_key in self.asset_cache:
            cached_path = Path(self.asset_cache[cache_key]["path"])
            if cached_path.exists():
                logger.info(f"Usando background de menu do cache: {cached_path}")
                return PIL.Image.open(cached_path)
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de menu")
            return self._create_fallback_menu_background()
        
        # Prompt otimizado para menu principal
        prompt = "medieval castle great hall, stone walls, banners, dramatic lighting"
        
        logger.info("Gerando background do menu principal com IA...")
        
        try:
            # Gerar imagem ultrawide para o menu
            image = self.sdxl_pipeline.generate_image(
                prompt=prompt,
                num_inference_steps=80,
                guidance_scale=8.5,
                width=1024,  # Será redimensionado para ultrawide depois
                height=1024
            )
            
            # Salvar no cache
            menu_path = self.config.assets_generated_dir / "menu_background.png"
            image.save(menu_path, "PNG", quality=95)
            
            # Atualizar cache
            self.asset_cache[cache_key] = {
                "prompt": prompt,
                "path": str(menu_path),
                "generated_at": datetime.now().isoformat(),
                "type": "menu_background"
            }
            self._save_asset_cache()
            
            logger.info("Background do menu gerado com sucesso!")
            return image
            
        except Exception as e:
            logger.error(f"Erro ao gerar background do menu: {e}")
            return self._create_fallback_menu_background()

    def generate_character_sprite(self, character_name: str, force_regenerate: bool = False) -> PIL.Image.Image:
        """
        Gera sprite de personagem com IA.
        
        Args:
            character_name: Nome do personagem (Cavaleiro, Mago, Assassino)
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Imagem PIL do sprite do personagem
        """
        # Mapear nomes para prompts específicos (máximo 77 tokens)
        prompt_map = {
            "Cavaleiro Valente": "medieval knight in golden armor, heroic pose, cape, masterpiece",
            "Mestre Arcano": "wizard in blue robes, magical staff, glowing orb, mystical aura",
            "Assassino das Sombras": "shadow assassin, dark hood, leather armor, daggers, shadows",
            "Goblin Scout": "green goblin scout, tribal warrior, crude weapons, menacing",
            "Skeleton Warrior": "skeleton warrior, bone armor, undead fighter, ancient"
        }
        
        cache_key = f"{character_name}_sprite"
        
        # Verificar cache primeiro
        if not force_regenerate and cache_key in self.asset_cache:
            cached_path = Path(self.asset_cache[cache_key]["path"])
            if cached_path.exists():
                logger.info(f"Usando sprite de {character_name} do cache: {cached_path}")
                return PIL.Image.open(cached_path)
        
        if character_name not in prompt_map:
            logger.warning(f"Personagem {character_name} não reconhecido")
            return self._create_fallback_character_sprite(character_name)
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de sprite")
            return self._create_fallback_character_sprite(character_name)
        
        prompt = prompt_map[character_name]
        logger.info(f"Gerando sprite de {character_name} com IA...")
        
        try:
            # Gerar sprite do personagem
            image = self.sdxl_pipeline.generate_image(
                prompt=prompt,
                num_inference_steps=80,
                guidance_scale=8.5,
                width=768,   # Proporção mais adequada para personagem
                height=1024
            )
            
            # Salvar no cache
            sprite_filename = f"{character_name.lower().replace(' ', '_')}_sprite.png"
            sprite_path = self.config.assets_generated_dir / sprite_filename
            image.save(sprite_path, "PNG", quality=95)
            
            # Atualizar cache
            self.asset_cache[cache_key] = {
                "prompt": prompt,
                "path": str(sprite_path),
                "generated_at": datetime.now().isoformat(),
                "type": "character_sprite"
            }
            self._save_asset_cache()
            
            logger.info(f"Sprite de {character_name} gerado com sucesso!")
            return image
            
        except Exception as e:
            logger.error(f"Erro ao gerar sprite de {character_name}: {e}")
            return self._create_fallback_character_sprite(character_name)

    def _create_fallback_menu_background(self) -> PIL.Image.Image:
        """Cria background de menu fallback quando IA não está disponível."""
        logger.info("Criando background de menu fallback")
        
        # Criar gradiente medieval como fallback
        image = PIL.Image.new("RGB", (1024, 1024), (40, 35, 25))  # Marrom escuro
        
        # Adicionar textura simples (pode ser expandido)
        import PIL.ImageDraw
        draw = PIL.ImageDraw.Draw(image)
        
        # Gradiente simples
        for y in range(1024):
            color_intensity = int(40 + (y / 1024) * 30)
            draw.line([(0, y), (1024, y)], fill=(color_intensity, color_intensity - 5, color_intensity - 10))
        
        return image

    def _create_fallback_character_sprite(self, character_name: str) -> PIL.Image.Image:
        """Cria sprite de personagem fallback quando IA não está disponível."""
        logger.info(f"Criando sprite fallback para {character_name}")
        
        # Cores temáticas por personagem
        theme_colors = {
            "Cavaleiro Valente": (255, 215, 0),      # Dourado
            "Mestre Arcano": (138, 43, 226),         # Roxo
            "Assassino das Sombras": (105, 105, 105), # Cinza escuro
            "Goblin Scout": (34, 139, 34),           # Verde
            "Skeleton Warrior": (220, 220, 220)      # Branco osso
        }
        
        color = theme_colors.get(character_name, (128, 128, 128))
        
        # Criar placeholder colorido
        image = PIL.Image.new("RGBA", (768, 1024), (0, 0, 0, 0))  # Transparente
        
        import PIL.ImageDraw
        draw = PIL.ImageDraw.Draw(image)
        
        # Desenhar silhueta simples do personagem
        center_x, center_y = 384, 512
        
        # Corpo básico
        draw.ellipse([center_x-80, center_y-200, center_x+80, center_y+200], fill=color)
        
        # Cabeça
        draw.ellipse([center_x-40, center_y-280, center_x+40, center_y-200], fill=color)
        
        return image

    def preload_menu_assets(self) -> Dict[str, Any]:
        """
        Pré-carrega todos os assets do menu para melhor performance.
        
        Returns:
            Dicionário com assets carregados
        """
        logger.info("Pré-carregando assets do menu...")
        
        assets = {}
        
        try:
            # Background do menu
            assets["menu_background"] = self.generate_menu_background()
            
            # Sprites dos personagens
            characters = ["Cavaleiro Valente", "Mestre Arcano", "Assassino das Sombras"]
            assets["character_sprites"] = {}
            
            for character in characters:
                assets["character_sprites"][character] = self.generate_character_sprite(character)
            
            logger.info("Assets do menu pré-carregados com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro no pré-carregamento de assets: {e}")
        
        return assets

    def generate_character_backgrounds(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera backgrounds específicos para os personagens da tela de seleção.
        Foca apenas em cenários medievais sem personagens.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos backgrounds gerados
        """
        character_prompts = {
            "knight": "medieval castle courtyard, stone walls, banners, training ground",
            "wizard": "wizard tower interior, floating books, magical crystals, arcane symbols", 
            "assassin": "dark medieval alley at night, stone buildings, shadows, moonlight"
        }
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de backgrounds")
            return {}
            
        generated_paths = {}
        
        # Negative prompt específico para cenários sem personagens
        character_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "people, person, human, character, figure, portrait, "
            "knight, wizard, warrior, mage, assassin, soldiers, "
            "face, body, arms, legs, hands, creatures, monsters, "
            "dragons, beings, entities, characters"
        )
        
        for character_id, prompt in character_prompts.items():
            cache_key = f"{character_id}_bg_new"
            bg_path = self.config.assets_generated_dir / f"{character_id}_bg.png"
            
            # Verificar se precisa regenerar
            if not force_regenerate and bg_path.exists() and cache_key in self.asset_cache:
                logger.info(f"Usando background de {character_id} do cache: {bg_path}")
                generated_paths[character_id] = str(bg_path)
                continue
            
            try:
                logger.info(f"Gerando background para personagem {character_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Gerar background do personagem
                image = self.sdxl_pipeline.generate_image(
                    prompt=prompt,
                    negative_prompt=character_negative_prompt,
                    num_inference_steps=80,
                    guidance_scale=8.5,
                    width=1024,
                    height=1024
                )
                
                # Redimensionar para ultrawide (3440x1440)
                ultrawide_image = image.resize((3440, 1440), PIL.Image.LANCZOS)
                
                # Salvar background
                ultrawide_image.save(bg_path, "PNG", quality=95)
                
                # Atualizar cache
                self.asset_cache[cache_key] = {
                    "prompt": prompt,
                    "path": str(bg_path),
                    "generated_at": datetime.now().isoformat(),
                    "type": "character_background",
                    "resolution": "3440x1440"
                }
                
                generated_paths[character_id] = str(bg_path)
                logger.info(f"✅ Background de {character_id} gerado: {bg_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar background de {character_id}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def generate_cinematic_backgrounds(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera backgrounds cinematográficos de alta qualidade para todas as telas.
        Focado em ambientes épicos e atmosféricos sem personagens.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos backgrounds gerados
        """
        cinematic_prompts = {
            "menu_cinematic": "castle great hall, cathedral ceiling, dramatic lighting, golden sunbeams",
            
            "knight_cinematic": "castle courtyard sunrise, cobblestone, golden light, banners",
            
            "wizard_cinematic": "arcane library tower, floating books, glowing runes, crystal orbs",
            
            "assassin_cinematic": "moonlit medieval alley, cobblestone passage, fog, lantern light"
        }
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de backgrounds cinematográficos")
            return {}
            
        generated_paths = {}
        
        # Negative prompt otimizado para cenários puros
        cinematic_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "people, person, human, character, figure, portrait, "
            "knight, wizard, warrior, mage, assassin, soldiers, "
            "face, body, arms, legs, hands, creatures, monsters, "
            "dragons, beings, entities, characters, crowd, "
            "silhouettes of people, human shapes"
        )
        
        for background_id, prompt in cinematic_prompts.items():
            cache_key = f"{background_id}_4k"
            bg_path = self.config.assets_generated_dir / f"{background_id}.png"
            
            # Verificar se precisa regenerar
            if not force_regenerate and bg_path.exists() and cache_key in self.asset_cache:
                logger.info(f"Usando background cinematográfico {background_id} do cache: {bg_path}")
                generated_paths[background_id] = str(bg_path)
                continue
            
            try:
                logger.info(f"Gerando background cinematográfico {background_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Gerar background em resolução 4K
                image = self.sdxl_pipeline.generate_image(
                    prompt=prompt,
                    negative_prompt=cinematic_negative_prompt,
                    num_inference_steps=100,  # Mais steps para qualidade cinematográfica
                    guidance_scale=9.0,       # CFG mais alto para melhor aderência ao prompt
                    width=1024,
                    height=1024
                )
                
                # Redimensionar para ultrawide (3440x1440) com qualidade máxima
                ultrawide_image = image.resize((3440, 1440), PIL.Image.LANCZOS)
                
                # Salvar com qualidade máxima
                ultrawide_image.save(bg_path, "PNG", quality=100, optimize=False)
                
                # Atualizar cache
                self.asset_cache[cache_key] = {
                    "prompt": prompt,
                    "path": str(bg_path),
                    "generated_at": datetime.now().isoformat(),
                    "type": "cinematic_background",
                    "resolution": "3440x1440",
                    "quality": "4K_cinematic"
                }
                
                generated_paths[background_id] = str(bg_path)
                logger.info(f"✅ Background cinematográfico {background_id} gerado: {bg_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar background cinematográfico {background_id}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def generate_character_sprites(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera sprites de personagens transparentes em full-body.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos sprites gerados
        """
        character_prompts = {
            "knight_sprite": "medieval knight standing, golden armor, noble stance, heroic",
            
            "wizard_sprite": "arcane wizard standing, blue robes, staff, glowing crystal",
            
            "assassin_sprite": "shadow assassin standing, leather armor, cloak, daggers"
        }
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de sprites")
            return {}
            
        generated_paths = {}
        
        # Negative prompt para sprites limpos
        sprite_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "background, scenery, landscape, room, environment, "
            "furniture, objects, extra limbs, multiple people, "
            "cropped, partial body, incomplete"
        )
        
        for character_id, prompt in character_prompts.items():
            cache_key = f"{character_id}_transparent"
            sprite_path = self.config.assets_generated_dir / f"{character_id}.png"
            
            # Verificar se precisa regenerar
            if not force_regenerate and sprite_path.exists() and cache_key in self.asset_cache:
                logger.info(f"Usando sprite {character_id} do cache: {sprite_path}")
                generated_paths[character_id] = str(sprite_path)
                continue
            
            try:
                logger.info(f"Gerando sprite {character_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Gerar sprite
                image = self.sdxl_pipeline.generate_image(
                    prompt=prompt,
                    negative_prompt=sprite_negative_prompt,
                    num_inference_steps=80,
                    guidance_scale=8.5,
                    width=512,   # Menor para sprites
                    height=768   # Mais alto para full-body
                )
                
                # Aplicar remoção de background (simulada por enquanto)
                # Em implementação real, usaria algo como rembg ou similar
                sprite_image = self._remove_background_simple(image)
                
                # Redimensionar para tamanho padrão de sprite
                sprite_image = sprite_image.resize((400, 600), PIL.Image.LANCZOS)
                
                # Salvar como PNG com transparência
                sprite_image.save(sprite_path, "PNG")
                
                # Atualizar cache
                self.asset_cache[cache_key] = {
                    "prompt": prompt,
                    "path": str(sprite_path),
                    "generated_at": datetime.now().isoformat(),
                    "type": "character_sprite",
                    "resolution": "400x600",
                    "has_transparency": True
                }
                
                generated_paths[character_id] = str(sprite_path)
                logger.info(f"✅ Sprite {character_id} gerado: {sprite_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar sprite {character_id}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def generate_enhanced_sprites(self, sprite_configs: Dict[str, Dict[str, Any]], force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera sprites melhorados baseados em configurações personalizadas.
        
        Args:
            sprite_configs: Dicionário com configurações dos sprites {sprite_id: config}
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos sprites gerados
        """
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de sprites melhorados")
            return {}
            
        generated_paths = {}
        
        # Negative prompt padrão para sprites limpos
        sprite_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "background, scenery, landscape, room, environment, "
            "furniture, objects, extra limbs, multiple people, "
            "cropped, partial body, incomplete, floating parts"
        )
        
        for sprite_id, config in sprite_configs.items():
            filename = config["filename"]
            sprite_path = self.config.assets_generated_dir / filename
            cache_key = f"enhanced_{sprite_id}"
            
            # Verificar se precisa regenerar
            if not force_regenerate and sprite_path.exists() and cache_key in self.asset_cache:
                logger.info(f"✅ Usando sprite melhorado {sprite_id} do cache: {sprite_path}")
                generated_paths[sprite_id] = str(sprite_path)
                continue
            
            try:
                logger.info(f"🎨 Gerando sprite melhorado {sprite_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Usar negative prompt personalizado se fornecido, senão usar padrão
                negative_prompt = config.get("negative", sprite_negative_prompt)
                
                # Gerar sprite com configurações personalizadas
                image = self.sdxl_pipeline.generate_image(
                    prompt=config["prompt"],
                    negative_prompt=negative_prompt,
                    num_inference_steps=80,  # Alta qualidade
                    guidance_scale=8.5,     # Balanceado
                    width=config["width"],
                    height=config["height"]
                )
                
                if image:
                    # Salvar como PNG de alta qualidade
                    image.save(sprite_path, "PNG", quality=95, optimize=True)
                    
                    # Atualizar cache
                    self.asset_cache[cache_key] = {
                        "prompt": config["prompt"],
                        "path": str(sprite_path),
                        "generated_at": datetime.now().isoformat(),
                        "type": "enhanced_sprite",
                        "resolution": f"{config['width']}x{config['height']}",
                        "sprite_id": sprite_id
                    }
                    
                    generated_paths[sprite_id] = str(sprite_path)
                    logger.info(f"✅ Sprite melhorado {sprite_id} gerado: {sprite_path}")
                else:
                    logger.error(f"❌ Falha ao gerar sprite melhorado {sprite_id}")
                
            except Exception as e:
                logger.error(f"💥 Erro ao gerar sprite melhorado {sprite_id}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def generate_ui_assets(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera assets de interface: botões, ícones, texturas.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos assets gerados
        """
        ui_prompts = {
            "button_texture_gold": "medieval golden button, ornate border, metallic texture",
            
            "button_texture_stone": "medieval stone button, carved details, weathered granite",
            
            "button_texture_mystical": "mystical button, glowing runes, purple magical aura",
            
            "arrow_left_icon": "medieval arrow left, golden metallic, decorative heraldic style",
            
            "arrow_right_icon": "medieval arrow right, golden metallic, decorative heraldic style", 
            
            "scroll_texture": "ancient parchment scroll, aged paper, decorative borders",
            
            "frame_ornate": "ornate medieval frame, golden filigree, decorative corners"
        }
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de assets UI")
            return {}
            
        generated_paths = {}
        
        # Negative prompt para assets de UI
        ui_negative_prompt = (
            "blurry, low quality, pixelated, "
            "text, watermark, signature, logo, "
            "people, characters, faces, landscape, "
            "3d, photorealistic, overly complex"
        )
        
        for asset_id, prompt in ui_prompts.items():
            cache_key = f"{asset_id}_ui"
            asset_path = self.config.assets_generated_dir / f"{asset_id}.png"
            
            # Verificar se precisa regenerar
            if not force_regenerate and asset_path.exists() and cache_key in self.asset_cache:
                logger.info(f"Usando asset UI {asset_id} do cache: {asset_path}")
                generated_paths[asset_id] = str(asset_path)
                continue
            
            try:
                logger.info(f"Gerando asset UI {asset_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Tamanho baseado no tipo
                if "icon" in asset_id:
                    width, height = 64, 64
                elif "button" in asset_id:
                    width, height = 256, 64
                elif "frame" in asset_id:
                    width, height = 512, 512
                else:
                    width, height = 256, 256
                
                # Gerar asset
                image = self.sdxl_pipeline.generate_image(
                    prompt=prompt,
                    negative_prompt=ui_negative_prompt,
                    num_inference_steps=60,
                    guidance_scale=8.0,
                    width=width,
                    height=height
                )
                
                # Salvar asset
                image.save(asset_path, "PNG", quality=95)
                
                # Atualizar cache
                self.asset_cache[cache_key] = {
                    "prompt": prompt,
                    "path": str(asset_path),
                    "generated_at": datetime.now().isoformat(),
                    "type": "ui_asset",
                    "resolution": f"{width}x{height}"
                }
                
                generated_paths[asset_id] = str(asset_path)
                logger.info(f"Asset UI {asset_id} gerado: {asset_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar asset UI {asset_id}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def _remove_background_simple(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Remoção simples de background (placeholder).
        Em implementação real, usaria rembg ou algoritmo similar.
        
        Args:
            image: Imagem original
            
        Returns:
            Imagem com background removido
        """
        # Por enquanto, apenas converte para RGBA e retorna
        # TODO: Implementar remoção real de background
        return image.convert("RGBA")

    def generate_all_cinematic_assets(self, force_regenerate: bool = False) -> Dict[str, Dict[str, str]]:
        """
        Gera todos os assets cinematográficos: backgrounds, sprites e UI.
        
        Args:
            force_regenerate: Força regeneração de todos os assets
            
        Returns:
            Dicionário organizado por categoria com paths dos assets
        """
        logger.info("🎬 Iniciando geração completa de assets cinematográficos...")
        
        results = {
            "backgrounds": {},
            "sprites": {},
            "ui_assets": {}
        }
        
        try:
            # Gerar backgrounds cinematográficos
            logger.info("Gerando backgrounds cinematográficos...")
            results["backgrounds"] = self.generate_cinematic_backgrounds(force_regenerate)
            
            # Gerar sprites de personagens
            logger.info("Gerando sprites de personagens...")
            results["sprites"] = self.generate_character_sprites(force_regenerate)
            
            # Gerar assets de UI
            logger.info("Gerando assets de interface...")
            results["ui_assets"] = self.generate_ui_assets(force_regenerate)
            
            # Estatísticas
            total_generated = sum(len(category) for category in results.values())
            logger.info(f"🎉 Geração cinematográfica completa! {total_generated} assets gerados:")
            for category, assets in results.items():
                logger.info(f"  {category}: {len(assets)} assets")
                
        except Exception as e:
            logger.error(f"Erro durante geração cinematográfica: {e}")
        
        return results

    def regenerate_all_backgrounds_hd_ultrawide(self, force_regenerate: bool = True) -> Dict[str, str]:
        """
        Regenera todos os backgrounds existentes em 3440x1440 ultrawide com prompts melhorados.
        
        Args:
            force_regenerate: Força regeneração de todos os backgrounds
            
        Returns:
            Dicionário com paths dos backgrounds regenerados
        """
        logger.info("🎬 Iniciando regeneração HD ultrawide (3440x1440)...")
        
        # Prompts melhorados para personagens (só cenários)
        enhanced_character_prompts = {
            "knight": {
                "prompt": "castle courtyard golden hour, stone walls, banners, training grounds",
                "negative": "people, person, human, character, figure, knight, warrior, armor, weapons, face, body"
            },
            "wizard": {
                "prompt": "magical tower library, floating orbs, glowing symbols, crystal formations",
                "negative": "people, person, human, character, figure, wizard, mage, face, body, hands"
            },
            "assassin": {
                "prompt": "dark medieval alley night, stone buildings, shadows, moonlight, fog",
                "negative": "people, person, human, character, figure, assassin, rogue, face, body, weapons"
            }
        }
        
        # Prompts para outros backgrounds
        enhanced_general_prompts = {
            "menu": {
                "prompt": "medieval throne room, ornate stone, stained glass, royal banners",
                "negative": "people, person, human, character, figure, face, body"
            },
            "castle": {
                "prompt": "medieval castle hilltop sunset, stone walls, towers, flags",
                "negative": "people, person, human, character, figure, face, body"
            },
            "forest": {
                "prompt": "enchanted forest, massive oak trees, mystical fog, sunlight",
                "negative": "people, person, human, character, figure, face, body"
            }
        }
        
        generated_paths = {}
        
        # Parâmetros para geração HD ultrawide
        hd_params = {
            "width": 3440,
            "height": 1440,
            "num_inference_steps": 35,  # Balanceando qualidade e velocidade
            "guidance_scale": 8.5
        }
        
        # Regenerar backgrounds de personagens
        logger.info("🏰 Regenerando backgrounds de personagens...")
        for char_name, prompts in enhanced_character_prompts.items():
            try:
                logger.info(f"Gerando background HD para {char_name}...")
                
                # Usar prompt diretamente (já está otimizado para cenários)
                optimized_prompt = prompts["prompt"]
                
                # Gerar hash para caching
                prompt_hash = self._generate_prompt_hash(optimized_prompt, hd_params)
                
                # Definir path de saída
                output_filename = f"{char_name}_bg_hd_3440x1440.png"
                output_path = self.generated_dir / output_filename
                
                # Verificar se precisa gerar
                if not force_regenerate and output_path.exists():
                    logger.info(f"Background HD {char_name} já existe, pulando...")
                    generated_paths[char_name] = str(output_path)
                    continue
                
                # Gerar imagem
                logger.info(f"🎨 Gerando {char_name} em 3440x1440...")
                image = self.sdxl_pipeline.generate_image(
                    prompt=optimized_prompt,
                    negative_prompt=prompts["negative"],
                    **hd_params
                )
                
                # Salvar
                image.save(output_path, quality=95, optimize=True)
                
                # Atualizar cache
                cache_entry = {
                    "prompt": optimized_prompt,
                    "negative_prompt": prompts["negative"],
                    "params": hd_params,
                    "generated_at": datetime.now().isoformat(),
                    "file_path": str(output_path),
                    "resolution": "3440x1440",
                    "type": "character_background_hd"
                }
                self.asset_cache[prompt_hash] = cache_entry
                
                generated_paths[char_name] = str(output_path)
                logger.info(f"✅ Background HD {char_name} gerado: {output_path}")
                
                # Copiar para arquivo padrão do jogo (substituindo o antigo)
                standard_path = self.generated_dir / f"{char_name}_bg.png"
                if standard_path.exists():
                    # Backup do antigo
                    backup_path = self.generated_dir / f"{char_name}_bg_backup_1024.png"
                    standard_path.rename(backup_path)
                    logger.info(f"📦 Backup criado: {backup_path}")
                
                # Copiar HD como padrão
                image.save(standard_path, quality=95, optimize=True)
                logger.info(f"🔄 Substituído background padrão: {standard_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar background HD {char_name}: {e}")
        
        # Regenerar outros backgrounds importantes
        logger.info("🎭 Regenerando backgrounds gerais...")
        for bg_name, prompts in enhanced_general_prompts.items():
            try:
                logger.info(f"Gerando background HD para {bg_name}...")
                
                # Usar prompt diretamente (já está otimizado para cenários)
                optimized_prompt = prompts["prompt"]
                
                # Gerar hash para caching
                prompt_hash = self._generate_prompt_hash(optimized_prompt, hd_params)
                
                # Definir path de saída
                output_filename = f"{bg_name}_hd_3440x1440.png"
                output_path = self.generated_dir / output_filename
                
                # Verificar se precisa gerar
                if not force_regenerate and output_path.exists():
                    logger.info(f"Background HD {bg_name} já existe, pulando...")
                    generated_paths[bg_name] = str(output_path)
                    continue
                
                # Gerar imagem
                logger.info(f"🎨 Gerando {bg_name} em 3440x1440...")
                image = self.sdxl_pipeline.generate_image(
                    prompt=optimized_prompt,
                    negative_prompt=prompts["negative"],
                    **hd_params
                )
                
                # Salvar
                image.save(output_path, quality=95, optimize=True)
                
                # Atualizar cache
                cache_entry = {
                    "prompt": optimized_prompt,
                    "negative_prompt": prompts["negative"],
                    "params": hd_params,
                    "generated_at": datetime.now().isoformat(),
                    "file_path": str(output_path),
                    "resolution": "3440x1440",
                    "type": "general_background_hd"
                }
                self.asset_cache[prompt_hash] = cache_entry
                
                generated_paths[bg_name] = str(output_path)
                logger.info(f"✅ Background HD {bg_name} gerado: {output_path}")
                
                # Para menu_background, também substituir o padrão
                if bg_name == "menu":
                    standard_path = self.generated_dir / "menu_background.png"
                    if standard_path.exists():
                        backup_path = self.generated_dir / "menu_background_backup_1024.png"
                        standard_path.rename(backup_path)
                        logger.info(f"📦 Backup menu criado: {backup_path}")
                    
                    image.save(standard_path, quality=95, optimize=True)
                    logger.info(f"🔄 Substituído menu background: {standard_path}")
                
            except Exception as e:
                logger.error(f"Erro ao gerar background HD {bg_name}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        
        # Relatório final
        total_generated = len(generated_paths)
        logger.info(f"🎉 Regeneração HD ultrawide completa!")
        logger.info(f"📊 {total_generated} backgrounds regenerados em 3440x1440")
        logger.info(f"🎯 Arquivos padrão do jogo atualizados automaticamente")
        logger.info(f"📦 Backups dos arquivos antigos criados")
        
        return generated_paths

    def generate_transparent_character_sprites(self, force_regenerate: bool = False) -> Dict[str, str]:
        """
        Gera sprites de personagens com fundo completamente transparente para integração ao background.
        
        Args:
            force_regenerate: Força regeneração mesmo se existir no cache
            
        Returns:
            Dicionário com paths dos sprites transparentes gerados
        """
        transparent_sprite_prompts = {
            "knight_transparent": "medieval knight standing, golden armor, sword, heroic stance",
            
            "wizard_transparent": "arcane wizard standing, blue robes, staff, glowing crystal",
            
            "assassin_transparent": "shadow assassin standing, leather armor, hooded cloak, daggers"
        }
        
        if not self.sdxl_pipeline:
            logger.warning("SDXL pipeline não disponível para geração de sprites transparentes")
            return {}
            
        generated_paths = {}
        
        # Negative prompt específico para sprites transparentes - remove backgrounds
        transparent_negative_prompt = (
            "blurry, low quality, pixelated, cartoon, anime, "
            "text, watermark, signature, logo, bad anatomy, "
            "deformed, distorted, ugly, poorly drawn, "
            "background, scenery, landscape, room, environment, "
            "furniture, objects, extra limbs, multiple people, "
            "cropped, partial body, incomplete, white background, "
            "colored background, gradient background, wall, floor, "
            "sky, clouds, ground, grass, stone, wood, any background"
        )
        
        for sprite_id, prompt in transparent_sprite_prompts.items():
            cache_key = f"{sprite_id}_transparent"
            sprite_path = self.generated_dir / f"{sprite_id}.png"
            
            # Verificar se precisa regenerar
            if not force_regenerate and sprite_path.exists() and cache_key in self.asset_cache:
                logger.info(f"Usando sprite transparente {sprite_id} do cache: {sprite_path}")
                generated_paths[sprite_id] = str(sprite_path)
                continue
            
            try:
                logger.info(f"🎨 Gerando sprite transparente {sprite_id}...")
                
                # Carregar modelos se necessário
                self.sdxl_pipeline.load_models()
                
                # Gerar sprite em alta resolução
                image = self.sdxl_pipeline.generate_image(
                    prompt=prompt,
                    negative_prompt=transparent_negative_prompt,
                    num_inference_steps=80,   # Boa qualidade
                    guidance_scale=8.5,      # CFG padrão para characters
                    width=768,               # Aspect ratio vertical para personagem
                    height=1024
                )
                
                # Aplicar remoção de fundo usando técnicas de processamento de imagem
                transparent_image = self._remove_background_advanced(image)
                
                # Salvar como PNG com transparência
                transparent_image.save(sprite_path, "PNG", quality=95)
                
                # Atualizar cache
                self.asset_cache[cache_key] = {
                    "prompt": prompt,
                    "path": str(sprite_path),
                    "generated_at": datetime.now().isoformat(),
                    "type": "transparent_sprite",
                    "resolution": f"{transparent_image.size[0]}x{transparent_image.size[1]}"
                }
                
                generated_paths[sprite_id] = str(sprite_path)
                logger.info(f"✅ Sprite transparente {sprite_id} gerado: {sprite_path}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao gerar sprite transparente {sprite_id}: {e}")
                
        # Salvar cache
        self._save_asset_cache()
        return generated_paths

    def _remove_background_advanced(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Remove fundo da imagem usando rembg - biblioteca especializada em remoção de fundo.
        Inclui pós-processamento para limpar contornos residuais.
        
        Args:
            image: Imagem PIL original
            
        Returns:
            Imagem PIL com fundo transparente limpo
        """
        try:
            from rembg import remove
            
            # Converter para bytes para processar com rembg
            import io
            input_buffer = io.BytesIO()
            image.save(input_buffer, format='PNG')
            input_bytes = input_buffer.getvalue()
            
            # Aplicar remoção de fundo usando rembg
            logger.info("Aplicando remoção de fundo com AI (rembg)...")
            output_bytes = remove(input_bytes)
            
            # Converter de volta para PIL Image
            output_buffer = io.BytesIO(output_bytes)
            result = PIL.Image.open(output_buffer).convert("RGBA")
            
            # Pós-processamento para limpar contornos
            result = self._clean_edge_artifacts(result)
            
            logger.info("✅ Fundo removido com sucesso usando AI")
            return result
            
        except ImportError:
            logger.warning("rembg não disponível, usando remoção manual de fundo")
            return self._remove_background_simple(image)
        except Exception as e:
            logger.warning(f"Falha na remoção de fundo com rembg: {e}")
            # Fallback: tentar remoção simples
            return self._remove_background_simple(image)

    def _remove_background_simple(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Remoção simples de fundo baseada em cor.
        
        Args:
            image: Imagem PIL original
            
        Returns:
            Imagem PIL com fundo transparente
        """
        try:
            # Converter para RGBA
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            
            # Obter dados dos pixels
            pixels = image.load()
            width, height = image.size
            
            # Remover pixels brancos e cinzas claros
            for y in range(height):
                for x in range(width):
                    r, g, b, a = pixels[x, y]
                    
                    # Se o pixel for muito claro ou muito próximo de branco/cinza
                    if (r > 240 and g > 240 and b > 240) or \
                       (r > 200 and g > 200 and b > 200 and abs(r-g) < 20 and abs(r-b) < 20):
                        pixels[x, y] = (r, g, b, 0)  # Tornar transparente
            
            return image
            
        except Exception as e:
            logger.error(f"Falha na remoção simples de fundo: {e}")
            return image

    def _clean_edge_artifacts(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """
        Remove artefatos de borda e contornos residuais da remoção de fundo.
        
        Args:
            image: Imagem PIL com fundo removido
            
        Returns:
            Imagem PIL com bordas limpas
        """
        try:
            import numpy as np
            from PIL import ImageFilter, ImageEnhance
            
            # Converter para RGBA se necessário
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            
            # 1. Aplicar erosão suave para remover bordas finas
            alpha = image.split()[-1]  # Canal alpha
            
            # Aplicar erosão no canal alpha para remover bordas finas
            eroded_alpha = alpha.filter(ImageFilter.MinFilter(3))
            
            # Suavizar bordas do alpha com blur
            smooth_alpha = eroded_alpha.filter(ImageFilter.GaussianBlur(radius=1))
            
            # 2. Limpar pixels de borda com baixa opacidade
            pixels = np.array(smooth_alpha)
            
            # Remover pixels com alpha muito baixo (artefatos)
            pixels[pixels < 50] = 0
            
            # Suavizar transição nas bordas
            mask = (pixels > 0) & (pixels < 200)
            pixels[mask] = np.clip(pixels[mask] * 1.2, 0, 255)
            
            # Reconverter para PIL
            clean_alpha = PIL.Image.fromarray(pixels.astype(np.uint8), mode='L')
            
            # 3. Aplicar o alpha limpo de volta à imagem
            r, g, b, _ = image.split()
            clean_image = PIL.Image.merge("RGBA", (r, g, b, clean_alpha))
            
            # 4. Aplicar filtro de nitidez suave para melhorar definição
            enhancer = ImageEnhance.Sharpness(clean_image)
            clean_image = enhancer.enhance(1.1)
            
            logger.debug("✅ Contornos residuais removidos")
            return clean_image
            
        except ImportError:
            logger.warning("NumPy não disponível, pulando limpeza de bordas")
            return image
        except Exception as e:
            logger.warning(f"Erro na limpeza de bordas: {e}")
            return image

    def process_existing_sprites_remove_background(self, force_regenerate: bool = True) -> Dict[str, str]:
        """
        Processa sprites existentes para remover fundo usando rembg.
        
        Args:
            force_regenerate: Força processamento mesmo se arquivo transparente já existe
            
        Returns:
            Dicionário com paths dos sprites processados
        """
        sprite_mappings = {
            "knight_sprite.png": "knight_transparent.png",
            "wizard_sprite.png": "wizard_transparent.png", 
            "assassin_sprite.png": "assassin_transparent.png"
        }
        
        processed_paths = {}
        
        for original_filename, transparent_filename in sprite_mappings.items():
            original_path = self.generated_dir / original_filename
            transparent_path = self.generated_dir / transparent_filename
            
            # Verificar se precisa processar
            if not force_regenerate and transparent_path.exists():
                logger.info(f"Sprite transparente já existe: {transparent_path}")
                processed_paths[transparent_filename.replace('.png', '')] = str(transparent_path)
                continue
            
            if not original_path.exists():
                logger.warning(f"Sprite original não encontrado: {original_path}")
                continue
                
            try:
                logger.info(f"🎨 Processando {original_filename} para remover fundo...")
                
                # Carregar sprite original
                original_image = PIL.Image.open(original_path)
                
                # Aplicar remoção de fundo
                transparent_image = self._remove_background_advanced(original_image)
                
                # Salvar sprite transparente
                transparent_image.save(transparent_path, "PNG", quality=95)
                
                # Atualizar cache
                cache_key = transparent_filename.replace('.png', '_processed')
                self.asset_cache[cache_key] = {
                    "original_path": str(original_path),
                    "transparent_path": str(transparent_path),
                    "processed_at": datetime.now().isoformat(),
                    "type": "background_removal"
                }
                
                processed_paths[transparent_filename.replace('.png', '')] = str(transparent_path)
                logger.info(f"✅ Sprite transparente criado: {transparent_path}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {original_filename}: {e}")
        
        # Salvar cache
        self._save_asset_cache()
        return processed_paths

    def generate_combat_bg(self) -> str:
        """
        Gera background de combate épico em ultra-wide 3440x1440.
        
        Returns:
            Caminho do arquivo gerado
        """
        prompt = ("epic medieval courtyard at sunset, cinematic, ultra-wide 16:9, "
                 "digital painting, dramatic lighting, atmospheric, high quality")
        
        try:
            # Usar o diretório de assets gerados
            output_path = self.generated_dir / "combat_bg.png"
            
            if output_path.exists():
                logger.info(f"✅ Combat background já existe: {output_path}")
                return str(output_path)
            
            # Gerar com resolução ultra-wide
            image = self._generate_image_from_prompt(
                prompt=prompt,
                width=1024,  # Usar resolução menor para teste
                height=1024,
                cache_key="combat_bg"
            )
            
            # Redimensionar para ultra-wide depois
            from PIL import Image
            ultrawide_image = image.resize((3440, 1440), Image.LANCZOS)
            
            # Salvar
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ultrawide_image.save(output_path, "PNG", quality=95, optimize=True)
            
            # Também salvar na pasta ia para o AssetLoader
            ia_path = self.assets_dir / "assets" / "ia" / "combat_bg.png"
            ia_path.parent.mkdir(parents=True, exist_ok=True)
            ultrawide_image.save(ia_path, "PNG", quality=95, optimize=True)
            
            logger.info(f"✅ Combat background salvo: {output_path}")
            logger.info(f"✅ Combat background copiado para: {ia_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar combat background: {e}")
            return ""

    def generate_enemy_sprite(self, enemy_id: str, description: str) -> str:
        """
        Gera sprite de inimigo com fundo transparente.
        
        Args:
            enemy_id: ID único do inimigo (ex: "goblin_scout")
            description: Descrição do inimigo (ex: "goblin warrior with axe")
            
        Returns:
            Caminho do arquivo gerado
        """
        prompt = (f"full body portrait of {description}, medieval fantasy, "
                 f"painterly style, transparent background, digital art, high quality")
        
        try:
            # Usar o diretório de assets gerados
            output_path = self.generated_dir / f"{enemy_id}_sprite.png"
            
            if output_path.exists():
                logger.info(f"✅ Enemy sprite já existe: {output_path}")
                return str(output_path)
            
            # Gerar sprite
            image = self._generate_image_from_prompt(
                prompt=prompt,
                width=512,
                height=768,
                cache_key=f"{enemy_id}_sprite"
            )
            
            # Salvar
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG", quality=95, optimize=True)
            
            # Também salvar na pasta ia para o AssetLoader
            ia_path = self.assets_dir / "assets" / "ia" / f"{enemy_id}_sprite.png"
            ia_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(ia_path, "PNG", quality=95, optimize=True)
            
            logger.info(f"✅ Enemy sprite salvo: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar sprite {enemy_id}: {e}")
            return ""

    def generate_player_sprite(self, description: str = "knight in golden armor") -> str:
        """
        Gera sprite do jogador com fundo transparente.
        
        Args:
            description: Descrição do personagem jogador
            
        Returns:
            Caminho do arquivo gerado
        """
        prompt = (f"full body heroic {description}, medieval fantasy, "
                 f"transparent background, painterly style, digital art, high quality")
        
        try:
            # Usar o diretório de assets gerados
            output_path = self.generated_dir / "player_sprite.png"
            
            if output_path.exists():
                logger.info(f"✅ Player sprite já existe: {output_path}")
                return str(output_path)
            
            # Gerar sprite
            image = self._generate_image_from_prompt(
                prompt=prompt,
                width=512,
                height=768,
                cache_key="player_sprite"
            )
            
            # Salvar
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG", quality=95, optimize=True)
            
            # Também salvar na pasta ia para o AssetLoader
            ia_path = self.assets_dir / "assets" / "ia" / "player_sprite.png"
            ia_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(ia_path, "PNG", quality=95, optimize=True)
            
            logger.info(f"✅ Player sprite salvo: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar player sprite: {e}")
            return ""

    def __del__(self):
        """Cleanup resources when object is destroyed."""
        if hasattr(self, 'sdxl_pipeline') and self.sdxl_pipeline:
            try:
                self.sdxl_pipeline.unload_models()
            except:
                pass
        """Cleanup on deletion."""
        try:
            if hasattr(self, 'asset_cache'):
                self._save_asset_cache()
        except Exception:
            pass
