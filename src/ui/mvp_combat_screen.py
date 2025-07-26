"""
MVP Combat Screen - Layout Definitivo Stage-Action

Sistema de combate com:
- Cenário corredor widescreen (BG gerado por IA)
- Sprites (herói + inimigos) alinhados na linha do chão
- Mão de cartas em faixa baixa (≤18% da altura)
- HUD discreto nos cantos
"""

import pygame
import logging
import math
import random
from typing import Optional, Dict, Any, List
from pathlib import Path
from collections import deque

from ..utils.config import Config
from ..utils.asset_loader import get_asset
from ..utils.theme import Theme
from ..gameplay.mvp_cards import Card, CardType, Hand
from ..gameplay.mvp_deck import MVPDeck
from ..core.mvp_turn_engine import MVPTurnEngine, MVPPlayer, MVPEnemy

logger = logging.getLogger(__name__)


class FrameAnimation:
    """Sistema de animação por frames."""
    
    def __init__(self, frames: List[pygame.Surface], fps: int = 30, loop: bool = True):
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.current_frame = 0
        self.time_per_frame = 1000.0 / fps  # milliseconds
        self.last_update = 0
        self.done = False
    
    def update(self, dt: float):
        """Atualiza a animação."""
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_update >= self.time_per_frame:
            self.current_frame += 1
            self.last_update = current_time
            
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.done = True
    
    def current(self) -> pygame.Surface:
        """Retorna o frame atual."""
        if not self.frames:
            return pygame.Surface((64, 64), pygame.SRCALPHA)
        return self.frames[self.current_frame]
    
    def reset(self):
        """Reseta a animação."""
        self.current_frame = 0
        self.done = False
        self.last_update = pygame.time.get_ticks()


class Camera:
    """Simple camera shake system."""
    
    shake_offset = [0, 0]
    shake_timer = 0
    shake_intensity = 0
    
    @classmethod
    def shake(cls, intensity=5, frames=8):
        """Start camera shake."""
        cls.shake_intensity = intensity
        cls.shake_timer = frames
    
    @classmethod
    def update(cls):
        """Update camera shake."""
        if cls.shake_timer > 0:
            cls.shake_offset[0] = random.randint(-cls.shake_intensity, cls.shake_intensity)
            cls.shake_offset[1] = random.randint(-cls.shake_intensity, cls.shake_intensity)
            cls.shake_timer -= 1
        else:
            cls.shake_offset = [0, 0]
    
    @classmethod
    def apply_to_pos(cls, pos):
        """Apply shake to position."""
        return (pos[0] + cls.shake_offset[0], pos[1] + cls.shake_offset[1])


class MVPCombatScreen:
    """
    Tela de combate MVP - Layout Definitivo Stage-Action.
    
    Layout:
    - Background: Ambiente medieval frontal (catedral, sala do trono, etc)
    - Sprites: Herói e inimigos na linha do chão visível
    - Cartas: Faixa inferior (18% da altura) com pergaminhos IA
    - HUD: Cantos discretos
    """
    
    # === CONSTANTES DE LAYOUT VISUAL ===
    FLOOR_Y_RATIO = 0.75  # Altura do chão como porcentagem da tela (75%)
    CARD_AREA_HEIGHT_RATIO = 0.18  # Altura da área de cartas (18%)
    
    def __init__(self, screen: pygame.Surface, config: Config, character_id: str = "knight"):
        """Initialize MVP combat screen with definitive layout."""
        logger.info(f"🚀 INITIALIZING MVP COMBAT SCREEN - Character: {character_id}")
        self.screen = screen
        self.config = config
        self.character_id = character_id
        
        # Screen dimensions
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        
        # === CONSTANTES DE POSICIONAMENTO ===
        # Altura do chão onde os sprites ficam alinhados
        self.FLOOR_Y = int(self.screen_h * self.FLOOR_Y_RATIO)
        
        # Área das cartas (parte inferior)
        self.CARD_AREA_HEIGHT = int(self.screen_h * self.CARD_AREA_HEIGHT_RATIO)
        self.CARD_AREA_Y = self.screen_h - self.CARD_AREA_HEIGHT
        
        # Posições dos personagens no combate
        self.PLAYER_X = int(self.screen_w * 0.25)  # Lado esquerdo
        self.ENEMY_X = int(self.screen_w * 0.75)   # Lado direito
        
        # Initialize Theme
        Theme.init_fonts()
        
        # Create layer surfaces for proper draw order management
        self.layer_bg = pygame.Surface((self.screen_w, self.screen_h)).convert()
        self.layer_mid = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        self.layer_ui = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        
        # Layout zones using Theme
        self.zones = Theme.create_zones((self.screen_w, self.screen_h))
        self.ground_y = Theme.get_ground_y(self.screen_h)
        
        # Load background
        self.bg_corridor = self._load_background("combat_corridor")
        
        # Load and setup animations
        self._setup_animations()
        
        # Load intent icons
        self.intent_icons = self._load_intent_icons()
        
        # Game state
        self.biomes = {
            "cathedral": {
                "name": "Sacred Cathedral",
                "enemy_type": "Knight Guardian",
                "background": None  # Will be loaded
            },
            "goblin_cave": {
                "name": "Goblin Cave", 
                "enemy_type": "Goblin Scout",
                "background": None  # Will be loaded
            }
        }
        
        # Load biome backgrounds
        self._load_biome_backgrounds()
        
        self.current_biome = "cathedral"
        self.selected_card_index = 0
        
        # Initialize game systems
        self.deck = MVPDeck()
        self.hand = Hand()
        
        # Create player and enemy
        self.player = self._create_player_for_character(character_id)
        self.enemy = self._create_enemy_for_biome(self.current_biome)
        self.turn_engine = MVPTurnEngine(self.player, self.enemy)
        
        # Combat state
        self.game_over = False
        self.victory = False
        
        # Animation state
        self.card_animation = None
        self.float_numbers = []
        self.player_anim_state = "idle"
        self.player_anim_timer = 0
        
        # Start combat
        self._start_combat()
        
        logger.info(f"MVP Combat Screen initialized - Layout definitivo para {character_id}")
    
    def _setup_animations(self):
        """Setup sprite animations."""
        # Load sprite sheets or fallback to static sprites
        try:
            # Try to load sprite sheets
            knight_idle_frames = self._load_sprite_sheet("sheets/knight_idle.png", 10)
            knight_attack_frames = self._load_sprite_sheet("sheets/knight_attack.png", 10)
            goblin_idle_frames = self._load_sprite_sheet("sheets/goblin_idle.png", 10)
            goblin_attack_frames = self._load_sprite_sheet("sheets/goblin_attack.png", 10)
            
            # Create animations
            self.player_idle = FrameAnimation(knight_idle_frames, fps=30, loop=True)
            self.player_attack = FrameAnimation(knight_attack_frames, fps=30, loop=False)
            self.goblin_idle = FrameAnimation(goblin_idle_frames, fps=30, loop=True)
            self.goblin_attack = FrameAnimation(goblin_attack_frames, fps=30, loop=False)
            
            # Set current animation
            self.player_anim = self.player_idle
            self.enemy_anim = self.goblin_idle
            
        except Exception as e:
            logger.warning(f"Could not load sprite sheets, using static sprites: {e}")
            # Fallback to static sprites
            self._setup_static_sprites()
    
    def _load_sprite_sheet(self, path: str, frame_count: int) -> List[pygame.Surface]:
        """Load sprite sheet and split into frames."""
        try:
            full_path = Path("assets") / path
            if full_path.exists():
                return Theme.load_sprite_sheet(str(full_path), frame_count)
            else:
                raise FileNotFoundError(f"Sprite sheet not found: {full_path}")
        except Exception as e:
            logger.warning(f"Failed to load sprite sheet {path}: {e}")
            # Return placeholder frames
            return [pygame.Surface((128, 128), pygame.SRCALPHA) for _ in range(frame_count)]
    
    def _setup_static_sprites(self):
        """Setup static sprite fallbacks with proper floor positioning."""
        # Load static sprites from generated assets - use transparent versions when available
        knight_sprite = (get_asset("knight_transparent") or 
                        get_asset("knight_sprite_enhanced") or 
                        get_asset("knight_sprite"))
        
        goblin_sprite = (get_asset("goblin_sprite_enhanced") or 
                        get_asset("goblin_scout_sprite") or
                        get_asset("skeleton_sprite_enhanced"))
        
        # Ensure sprites have transparency
        if knight_sprite:
            knight_sprite = knight_sprite.convert_alpha()
        else:
            knight_sprite = pygame.Surface((128, 192), pygame.SRCALPHA)
            knight_sprite.fill(Theme.get_color("gold"))
        
        if goblin_sprite:
            goblin_sprite = goblin_sprite.convert_alpha()
        else:
            goblin_sprite = pygame.Surface((96, 144), pygame.SRCALPHA)
            goblin_sprite.fill(Theme.get_color("hp"))
        
        # Create single-frame animations
        self.player_idle = FrameAnimation([knight_sprite], fps=1, loop=True)
        self.player_attack = FrameAnimation([knight_sprite], fps=1, loop=False)
        self.goblin_idle = FrameAnimation([goblin_sprite], fps=1, loop=True)
        self.goblin_attack = FrameAnimation([goblin_sprite], fps=1, loop=False)
        
        self.player_anim = self.player_idle
        self.enemy_anim = self.goblin_idle
        
        # Setup sprite positioning rects for floor alignment
        self._setup_sprite_positions()
    
    def _load_intent_icons(self) -> Dict[str, pygame.Surface]:
        """Load intent icons."""
        icons = {}
        
        # Try to load generated icons
        sword_icon = get_asset("icon_sword")
        shield_icon = get_asset("icon_shield")
        
        if sword_icon:
            icons["attack"] = sword_icon
        else:
            # Create placeholder
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.polygon(icon, Theme.get_color("hp"), [(16, 4), (28, 28), (4, 28)])
            icons["attack"] = icon
        
        if shield_icon:
            icons["block"] = shield_icon
        else:
            # Create placeholder
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.ellipse(icon, Theme.get_color("mana"), (4, 4, 24, 24))
            icons["block"] = icon
        
        return icons
    
    def _setup_sprite_positions(self):
        """Setup sprite positioning rects aligned to floor."""
        # Get current sprite dimensions
        player_sprite = self.player_idle.get_current_frame()
        enemy_sprite = self.goblin_idle.get_current_frame()
        
        # Create rects with bottom aligned to FLOOR_Y
        self.player_rect = player_sprite.get_rect()
        self.player_rect.midbottom = (self.PLAYER_X, self.FLOOR_Y)
        
        self.enemy_rect = enemy_sprite.get_rect()
        self.enemy_rect.midbottom = (self.ENEMY_X, self.FLOOR_Y)
        
        logger.info(f"Sprites positioned - Player: {self.player_rect}, Enemy: {self.enemy_rect}, Floor Y: {self.FLOOR_Y}")
    
    def _create_simple_fallback_background(self) -> pygame.Surface:
        """Create simple gradient fallback background for old method."""
        bg = pygame.Surface((self.screen_w, self.screen_h))
        
        # Simple gradient
        for y in range(self.screen_h):
            progress = y / self.screen_h
            color_r = int(30 + progress * 20)
            color_g = int(25 + progress * 15)
            color_b = int(20 + progress * 10)
            color = (color_r, color_g, color_b)
            pygame.draw.line(bg, color, (0, y), (self.screen_w, y))
        
        return bg
        
        # Game state
        self.biomes = {
            "cathedral": {
                "name": "Sacred Cathedral",
                "background": self._load_background("bg_cathedral"),
                "enemy_type": "Knight Guardian"
            },
            "goblin_cave": {
                "name": "Goblin Cave",
                "background": self._load_background("bg_goblin_cave"), 
                "enemy_type": "Goblin Scout"
            }
        }
        
        self.current_biome = "cathedral"
        self.selected_card_index = 0
        
        # Initialize game systems
        self.deck = MVPDeck()
        self.hand = Hand()
        
        # Load intent icons
        try:
            self.intent_icons = {
                "attack": pygame.image.load("assets/ui/icon_sword.png").convert_alpha(),
                "block": pygame.image.load("assets/ui/icon_shield.png").convert_alpha()
            }
        except:
            self.intent_icons = None
        
        # Create player and enemy based on character
        self.player = self._create_player_for_character(character_id)
        self.enemy = self._create_enemy_for_biome(self.current_biome)
        self.turn_engine = MVPTurnEngine(self.player, self.enemy)
        
        # Combat state
        self.game_over = False
        self.victory = False
        
        # Animation state
        self.card_animation = None
        self.card_anim_timer = 0
        self.float_numbers = []  # For damage numbers
        self.emitters = []  # For particle effects - cleared to fix color issues
        self.player_anim_state = "idle"  # Track player animation state
        self.player_anim_timer = 0
        
        # Start combat
        self._start_combat()
        
        logger.info(f"MVP Combat Screen initialized for character: {character_id}")
        
    def _create_player_for_character(self, character_id: str) -> MVPPlayer:
        """Create player based on selected character."""
        if character_id == "wizard":
            return MVPPlayer(max_hp=80, max_mana=4)  # More mana, less HP
        elif character_id == "assassin":
            return MVPPlayer(max_hp=90, max_mana=3)  # Balanced
        else:  # knight
            return MVPPlayer(max_hp=120, max_mana=2)  # More HP, less mana
    
    def _create_enemy_for_biome(self, biome_name: str) -> MVPEnemy:
        """Create enemy for current biome."""
        if biome_name == "cathedral":
            enemy = MVPEnemy("Knight Guardian", hp=35, attack=8, enemy_type="knight")
        elif biome_name == "goblin_cave":
            enemy = MVPEnemy("Goblin Scout", hp=20, attack=6, enemy_type="goblin")
        else:
            enemy = MVPEnemy("Unknown Enemy", hp=25, attack=7, enemy_type="generic")
        
        # Prepare initial intent
        self._prepare_enemy_intent(enemy)
        return enemy
    
    def _prepare_enemy_intent(self, enemy) -> None:
        """Prepare enemy's next action intent."""
        import random
        if enemy.current_hp > 0:
            enemy.intent = random.choice(["attack", "block"])
            if enemy.intent == "attack":
                enemy.intent_value = enemy.attack
                enemy.intent_icon = "⚔"
            else:
                enemy.intent_value = 6
                enemy.intent_icon = "🛡"
    
    def _enemy_turn(self) -> None:
        """Execute enemy turn with proper block mechanics and camera shake."""
        if hasattr(self.enemy, 'intent') and self.enemy.intent == "attack":
            # Calculate damage after block
            damage = max(0, self.enemy.attack - self.player.block)
            self.player.current_hp -= damage
            
            # Reduce block (block absorbs damage then reduces)
            self.player.block = max(0, self.player.block - self.enemy.attack)
            
            # Add floating damage number for player
            if damage > 0:
                player_pos = (self.width // 2, self.height // 2 + 100)
                self.float_numbers.append({
                    "text": f"-{damage}",
                    "pos": list(player_pos),
                    "start_time": pygame.time.get_ticks(),
                    "duration": 1000,
                    "color": (255, 100, 100)
                })
                
                # Camera shake for high damage
                if damage > 5:
                    Camera.shake(intensity=6, frames=4)
            
            logger.info(f"Enemy attacked for {damage} damage (blocked: {self.enemy.attack - damage})")
        else:
            # Enemy blocks/defends
            logger.info("Enemy defends")
        
        # Check if player is defeated
        if self.player.current_hp <= 0:
            self.game_over = True
            self.victory = False
    
    def _load_background(self, bg_name: str) -> Optional[pygame.Surface]:
        """Load AI-generated background."""
        try:
            # Look for generated backgrounds
            generated_dir = Path("assets/generated")
            
            # First try direct file name
            direct_path = generated_dir / f"{bg_name}.png"
            if direct_path.exists():
                logger.info(f"Loading background directly: {direct_path}")
                bg_surface = pygame.image.load(direct_path)
                return pygame.transform.scale(bg_surface, (self.screen_w, self.screen_h))
            
            # Try different naming patterns
            patterns = [
                f"{bg_name}_*.png",
                f"bg_{bg_name.split('_')[-1]}_*.png"
            ]
            
            for pattern in patterns:
                bg_files = list(generated_dir.glob(pattern))
                if bg_files:
                    bg_path = bg_files[0]  # Use first match
                    logger.info(f"Loading background pattern match: {bg_path}")
                    bg_surface = pygame.image.load(bg_path)
                    return pygame.transform.scale(bg_surface, (self.screen_w, self.screen_h))
            
            logger.warning(f"Background not found for {bg_name}, using fallback")
            return None
            
        except Exception as e:
            logger.error(f"Error loading background {bg_name}: {e}")
            return None
    
    def _create_fallback_background(self) -> pygame.Surface:
        """Create fallback background with BRIGHT RED for testing."""
        bg = pygame.Surface((self.screen_w, self.screen_h))
        
        # BRIGHT RED BACKGROUND - IMPOSSIBLE TO MISS!
        bg.fill((255, 0, 0))  # Bright red for testing
        
        # Add some text to confirm this is working
        font = pygame.font.Font(None, 48)
        text = font.render("FALLBACK BACKGROUND - RED TEST", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen_w // 2, self.screen_h // 2))
        bg.blit(text, text_rect)
            
        return bg
    
    def _load_biome_backgrounds(self):
        """Load medieval environment backgrounds for immersive combat."""
        logger.info("🔄 LOADING BIOME BACKGROUNDS - Medieval environments...")
        
        # Priority list of medieval environment backgrounds (frontal perspective)
        medieval_environments = [
            "bg_cathedral_9ced699823efe904814979cef550eefe",  # Catedral - ambiente frontal ideal
            "knight_bg_throne_room",                          # Sala do trono
            "combat_bg_dark_tower",                          # Torre escura
            "combat_bg_dragon_lair",                         # Covil do dragão
            "combat_bg_skeleton_crypt",                      # Cripta
            "knight_bg",                                     # Background do cavaleiro
            "wizard_bg_sanctum",                             # Santuário do mago
            "assassin_bg_lair"                               # Covil do assassino
        ]
        
        # Try to load the best medieval environment background
        environment_bg = None
        for bg_name in medieval_environments:
            environment_bg = self._load_background(bg_name)
            if environment_bg:
                logger.info(f"Using medieval environment: {bg_name}")
                break
        
        # Fallback to corridor if no environment found
        if not environment_bg:
            environment_bg = self._load_background("corridor_stage_definitive")
            
        # Final fallback to generated gradient
        if not environment_bg:
            logger.info("🔴 USING BRIGHT RED FALLBACK BACKGROUND!")
            environment_bg = self._create_fallback_background()
        
        # Use same background for all biomes
        for biome_name in self.biomes:
            self.biomes[biome_name]["background"] = environment_bg
    
    def _start_combat(self) -> None:
        """Start a new combat."""
        # Reset player and enemy
        self.player.current_hp = self.player.max_hp
        self.player.current_mana = self.player.max_mana
        self.player.block = 0
        
        self.enemy = self._create_enemy_for_biome(self.current_biome)
        self.turn_engine.enemy = self.enemy
        
        # Clear hand and draw new cards
        self.hand.cards.clear()
        self.deck.shuffle()
        for _ in range(5):
            card = self.deck.draw_card()
            if card:
                self.hand.add_card(card)
        
        self.game_over = False
        self.victory = False
        
        logger.info(f"Combat started in {self.biomes[self.current_biome]['name']}")
        logger.info(f"Enemy: {self.enemy.name} ({self.enemy.current_hp} HP)")
        logger.info(f"Hand: {[f'{c.name}({c.mana_cost})' for c in self.hand.cards]}")
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events. Returns action string or None."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back_to_menu"
                
            elif event.key == pygame.K_TAB:
                # Switch biomes
                self.current_biome = "goblin_cave" if self.current_biome == "cathedral" else "cathedral"
                self.enemy = self._create_enemy_for_biome(self.current_biome)
                self.turn_engine.enemy = self.enemy
                logger.info(f"Switched to {self.biomes[self.current_biome]['name']}")
                
            elif event.key == pygame.K_LEFT:
                # Select previous card
                if self.hand.cards:
                    self.selected_card_index = max(0, self.selected_card_index - 1)
                    
            elif event.key == pygame.K_RIGHT:
                # Select next card
                if self.hand.cards:
                    self.selected_card_index = min(len(self.hand.cards) - 1, self.selected_card_index + 1)
                    
            elif event.key == pygame.K_SPACE:
                # Play selected card
                if not self.game_over and self.hand.cards and self.selected_card_index < len(self.hand.cards):
                    selected_card = self.hand.cards[self.selected_card_index]
                    self._play_card(selected_card)
                    
            elif event.key == pygame.K_RETURN:
                # End turn or restart if game over
                if self.game_over:
                    self._start_combat()
                else:
                    # Discard current hand
                    for card in self.hand.cards:
                        self.deck.discard_pile.append(card)
                    self.hand.cards.clear()
                    
                    # Draw new hand with reshuffle if needed
                    for _ in range(5):
                        # Check if draw pile is empty and reshuffle if needed
                        if not self.deck.draw_pile and self.deck.discard_pile:
                            # Reshuffle discard into draw pile
                            self.deck.draw_pile = deque(random.sample(self.deck.discard_pile, len(self.deck.discard_pile)))
                            self.deck.discard_pile.clear()
                            logger.info("Reshuffled discard pile into draw pile")
                        
                        card = self.deck.draw_card()
                        if card:
                            self.hand.add_card(card)
                    
                    # Recharge energy on turn end
                    self.player.current_mana = self.player.max_mana
                    self.turn_engine.end_player_turn()
                    
                    # Enemy takes their turn
                    self._enemy_turn()
                    
                    # Prepare next intent after enemy turn
                    self._prepare_enemy_intent(self.enemy)
                    
                    logger.info("Player turn ended, energy recharged, new hand drawn")
                    
            elif event.key == pygame.K_r:
                # Restart combat
                self._start_combat()
                
        return None
    
    def _play_card(self, card: Card) -> None:
        """Play a card with enhanced animation and particles."""
        try:
            # Start card animation to center
            center_pos = (self.width // 2, self.height // 2)
            self.card_animation = {
                "card": card,
                "start_time": pygame.time.get_ticks(),
                "duration": 250,  # 0.25 seconds
                "target_pos": center_pos
            }
            
            result = self.turn_engine.play_card(card)
            if result:
                self.hand.remove_card(card)
                # Adjust selection
                if self.selected_card_index >= len(self.hand.cards):
                    self.selected_card_index = max(0, len(self.hand.cards) - 1)
                    
                # Create floating damage number
                if card.damage > 0:
                    enemy_pos = (self.zones["enemy"].centerx, self.zones["enemy"].centery)
                    self.float_numbers.append({
                        "text": f"-{card.damage}",
                        "pos": list(enemy_pos),
                        "start_time": pygame.time.get_ticks(),
                        "duration": 1000,  # 1 second
                        "color": (255, 100, 100)  # Red for damage
                    })
                
                # Create healing number
                if card.heal > 0:
                    player_pos = (self.width // 2, self.height // 2 + 100)
                    self.float_numbers.append({
                        "text": f"+{card.heal}",
                        "pos": list(player_pos),
                        "start_time": pygame.time.get_ticks(),
                        "duration": 1000,
                        "color": (100, 255, 100)  # Green for healing
                    })
                    
                logger.info(f"Played {card.name}: {result}")
                
                # Check for game over conditions
                if self.enemy.current_hp <= 0:
                    self.game_over = True
                    self.victory = True
                    logger.info("Victory!")
                elif self.player.current_hp <= 0:
                    self.game_over = True
                    self.victory = False
                    logger.info("Defeat!")
            else:
                logger.warning(f"Could not play {card.name}")
                
        except Exception as e:
            logger.error(f"Error playing card {card.name}: {e}")
    
    def update(self, dt: float) -> None:
        """Update combat screen with all enhancements."""
        current_time = pygame.time.get_ticks()
        
        # Update camera shake
        Camera.update()
        
        # Update card animation
        if self.card_animation:
            elapsed = current_time - self.card_animation["start_time"]
            if elapsed >= self.card_animation["duration"]:
                # Set player to attack animation
                self.player_anim_state = "attack"
                self.player_anim_timer = current_time
                
                # Clear animation
                self.card_animation = None
        
        # Update player animation state - reset to idle after attack
        if self.player_anim_state == "attack":
            if current_time - self.player_anim_timer > 500:  # 0.5 seconds attack duration
                self.player_anim_state = "idle"
                self.player_anim_timer = current_time
        
        # Update floating numbers
        for float_num in self.float_numbers[:]:  # Copy list to avoid modification during iteration
            elapsed = current_time - float_num["start_time"]
            if elapsed >= float_num["duration"]:
                self.float_numbers.remove(float_num)
            else:
                # Move number up
                progress = elapsed / float_num["duration"]
                float_num["pos"][1] -= dt * 50  # Move up 50 pixels per second
    
    def draw(self) -> None:
        """Draw the combat screen with definitive stage-action layout."""
        # Apply camera shake
        shake_offset = Camera.shake_offset
        
        # Clear layers for new frame
        self.layer_bg.fill(Theme.get_color("bg_combat"))
        self.layer_mid.fill((0, 0, 0, 0))
        self.layer_ui.fill((0, 0, 0, 0))
        
        # === LAYER BG: Background corridor ===
        self._draw_background()
        
        # === LAYER MID: Sprites na linha do chão ===
        self._draw_player_sprite()
        self._draw_enemy_sprites()
        self._draw_floating_numbers()
        
        # Render card animation
        if self.card_animation:
            self._draw_card_animation()
        
        # === LAYER UI: Interface elements ===
        self._draw_hand_zone()
        self._draw_status_hud()
        
        # === COMPOSITING: Blend layers with shake ===
        self.screen.blit(self.layer_bg, shake_offset)
        self.screen.blit(self.layer_mid, shake_offset)
        self.screen.blit(self.layer_ui, shake_offset)
        
        # Game over overlay (no shake, always on top)
        if self.game_over:
            self._draw_game_over()
    
    def _draw_background(self):
        """Draw medieval environment background to background layer."""
        current_biome_data = self.biomes.get(self.current_biome, {})
        bg = current_biome_data.get("background")
        
        if bg:
            # Draw the medieval environment (cathedral, throne room, etc)
            self.layer_bg.blit(bg, (0, 0))
        else:
            # Fallback to dark medieval gradient
            self.layer_bg.fill(Theme.get_color("bg_combat"))
            
            # Add subtle medieval atmosphere if no background
            for y in range(0, self.screen_h, 4):
                alpha = int(20 * (1 - y / self.screen_h))
                if alpha > 0:
                    overlay = pygame.Surface((self.screen_w, 4), pygame.SRCALPHA)
                    overlay.fill((40, 30, 20, alpha))
                    self.layer_bg.blit(overlay, (0, y))
        
        # === DEBUG: LINHA VISUAL DO CHÃO ===
        # Linha amarela para mostrar onde está o FLOOR_Y
        pygame.draw.line(self.layer_bg, (255, 255, 0), (0, self.FLOOR_Y), (self.screen_w, self.FLOOR_Y), 3)
        
        # Texto debug
        if hasattr(pygame.font, 'Font'):
            debug_font = pygame.font.Font(None, 36)
            debug_text = debug_font.render(f"FLOOR Y: {self.FLOOR_Y} (75%)", True, (255, 255, 0))
            self.layer_bg.blit(debug_text, (50, self.FLOOR_Y - 40))
    
    def _draw_player_sprite(self):
        """Draw player sprite aligned to floor line with proper integration."""
        if hasattr(self, 'player_anim') and self.player_anim:
            frame = self.player_anim.current()
            
            # Use predefined position with FLOOR_Y alignment
            if hasattr(self, 'player_rect'):
                self.layer_mid.blit(frame, self.player_rect)
            else:
                # Fallback positioning
                sprite_rect = frame.get_rect(midbottom=(self.PLAYER_X, self.FLOOR_Y))
                self.layer_mid.blit(frame, sprite_rect)
    
    def _draw_enemy_sprites(self):
        """Draw enemy sprites aligned to floor line with proper integration."""
        if hasattr(self, 'enemy_anim') and self.enemy_anim:
            frame = self.enemy_anim.current()
            
            # Use predefined position with FLOOR_Y alignment
            if hasattr(self, 'enemy_rect'):
                self.layer_mid.blit(frame, self.enemy_rect)
            else:
                # Fallback positioning
                sprite_rect = frame.get_rect(midbottom=(self.ENEMY_X, self.FLOOR_Y))
                self.layer_mid.blit(frame, sprite_rect)
        
        # Draw enemy info above sprite
        self._draw_enemy_info()
    
    def _draw_enemy_info(self):
        """Draw enemy HP and intent above sprite."""
        enemy_center_x = self.screen_w // 2 + 200
        info_y = self.ground_y - 200
        
        # Enemy name
        name_text = Theme.FONT_SUBTITLE.render(self.enemy.name, True, Theme.get_color("gold"))
        name_rect = name_text.get_rect(centerx=enemy_center_x, y=info_y)
        self.layer_mid.blit(name_text, name_rect)
        
        # HP bar
        hp_bar_width = 120
        hp_bar_height = 12
        hp_rect = pygame.Rect(enemy_center_x - hp_bar_width//2, info_y + 35, hp_bar_width, hp_bar_height)
        
        # HP bar background
        pygame.draw.rect(self.layer_mid, (60, 20, 20), hp_rect)
        
        # HP bar fill
        hp_ratio = self.enemy.current_hp / self.enemy.max_hp
        fill_width = int(hp_bar_width * hp_ratio)
        fill_rect = pygame.Rect(hp_rect.x, hp_rect.y, fill_width, hp_bar_height)
        pygame.draw.rect(self.layer_mid, Theme.get_color("hp"), fill_rect)
        
        # HP text
        hp_text = f"{self.enemy.current_hp}/{self.enemy.max_hp}"
        hp_surf = Theme.FONT_SMALL.render(hp_text, True, Theme.get_color("text_light"))
        hp_text_rect = hp_surf.get_rect(centerx=enemy_center_x, y=info_y + 55)
        self.layer_mid.blit(hp_surf, hp_text_rect)
        
        # Intent
        if hasattr(self.enemy, 'intent'):
            intent_y = info_y + 80
            intent_icon = self.intent_icons.get(self.enemy.intent)
            
            if intent_icon:
                icon_rect = intent_icon.get_rect(centerx=enemy_center_x - 20, centery=intent_y)
                self.layer_mid.blit(intent_icon, icon_rect)
                
                # Intent value
                value_text = str(getattr(self.enemy, 'intent_value', '?'))
                value_surf = Theme.FONT_BODY.render(value_text, True, Theme.get_color("text_light"))
                value_rect = value_surf.get_rect(centerx=enemy_center_x + 20, centery=intent_y)
                self.layer_mid.blit(value_surf, value_rect)
    
    def _draw_hand_zone(self):
        """Draw hand zone to UI layer - definitive card layout."""
        hand_zone = self.zones["hand"]
        
        # CORREÇÃO CRÍTICA: Verificar se há cartas antes de processar
        if not self.hand.cards:
            # Mensagem discreta no rodapé
            no_cards_text = "No cards in hand - Press ENTER to draw"
            text_surf = Theme.FONT_SMALL.render(no_cards_text, True, Theme.get_color("gold"))
            text_rect = text_surf.get_rect(centerx=self.screen_w//2, y=hand_zone.centery)
            self.layer_ui.blit(text_surf, text_rect)
            return
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        
        # Use Theme constants for consistency
        card_w, card_h = Theme.CARD_SIZE
        spacing = Theme.CARD_GAP
        
        # Calculate positions - centralized in hand zone
        total_width = len(self.hand.cards) * card_w + (len(self.hand.cards) - 1) * spacing
        start_x = (self.screen_w - total_width) // 2
        card_y = hand_zone.y + (hand_zone.height - card_h) // 2
        
        for i, card in enumerate(self.hand.cards):
            x = start_x + i * (card_w + spacing)
            card_rect = pygame.Rect(x, card_y, card_w, card_h)
            
            # Check hover
            hover = card_rect.collidepoint(mouse_pos)
            selected = (i == self.selected_card_index)
            
            # Draw card using proper scaling
            self._draw_single_card(card_rect, card, hover, selected)
    
    def _draw_single_card(self, rect: pygame.Rect, card: Card, hover: bool, selected: bool):
        """Draw a single card with proper pergaminho frame scaling."""
        
        # Load card frame
        card_frame = get_asset("card_frame")
        if not card_frame:
            # Try UI directory
            try:
                card_frame = pygame.image.load("assets/ui/card_frame.png").convert_alpha()
            except:
                # Create simple frame
                card_frame = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                card_frame.fill((139, 69, 19, 200))
                pygame.draw.rect(card_frame, (101, 67, 33), card_frame.get_rect(), 3)
        
        # CORREÇÃO CRÍTICA: Scale frame to exact card size
        scaled_frame = pygame.transform.smoothscale(card_frame, (rect.width, rect.height))
        
        # Hover glow effect
        if hover:
            glow_size = 8
            glow = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
            alpha = int((math.sin(pygame.time.get_ticks() * 0.015) + 1) * 60)
            glow.fill((*Theme.get_color("glow_gold"), alpha))
            glow_rect = glow.get_rect(center=rect.center)
            self.layer_ui.blit(glow, glow_rect, special_flags=pygame.BLEND_ADD)
        
        # Draw frame
        self.layer_ui.blit(scaled_frame, rect)
        
        # Selection highlight
        if selected:
            highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            highlight.fill((*Theme.get_color("gold"), 80))
            self.layer_ui.blit(highlight, rect)
        
        # Card border
        border_color = Theme.get_color("gold") if selected else Theme.get_color("ui_border")
        border_width = 3 if selected else 2
        pygame.draw.rect(self.layer_ui, border_color, rect, border_width)
        
        # Card text content
        self._draw_card_text(rect, card)
    
    def _draw_card_text(self, rect: pygame.Rect, card: Card):
        """Draw card text content."""
        # Card name
        name_surf = Theme.FONT_SMALL.render(card.name, True, Theme.get_color("text_light"))
        name_rect = name_surf.get_rect(centerx=rect.centerx, y=rect.y + 15)
        self.layer_ui.blit(name_surf, name_rect)
        
        # Mana cost
        cost_text = f"⚡{card.mana_cost}"
        cost_color = Theme.get_color("mana") if self.player.current_mana >= card.mana_cost else (150, 50, 50)
        cost_surf = Theme.FONT_SMALL.render(cost_text, True, cost_color)
        cost_rect = cost_surf.get_rect(x=rect.x + 10, y=rect.y + 35)
        self.layer_ui.blit(cost_surf, cost_rect)
        
        # Card effects
        effects_y = rect.y + 55
        
        if card.damage > 0:
            dmg_text = f"⚔{card.damage}"
            dmg_surf = Theme.FONT_SMALL.render(dmg_text, True, Theme.get_color("hp"))
            dmg_rect = dmg_surf.get_rect(x=rect.x + 10, y=effects_y)
            self.layer_ui.blit(dmg_surf, dmg_rect)
        
        if card.block > 0:
            block_text = f"🛡{card.block}"
            block_surf = Theme.FONT_SMALL.render(block_text, True, Theme.get_color("mana"))
            block_rect = block_surf.get_rect(x=rect.x + 60, y=effects_y)
            self.layer_ui.blit(block_surf, block_rect)
        
        if card.heal > 0:
            heal_text = f"❤{card.heal}"
            heal_surf = Theme.FONT_SMALL.render(heal_text, True, (100, 255, 100))
            heal_rect = heal_surf.get_rect(x=rect.x + 110, y=effects_y)
            self.layer_ui.blit(heal_surf, heal_rect)
    
    def _draw_status_hud(self):
        """Draw status HUD to UI layer - discrete corners."""
        # Player status - top left corner
        hud_rect = pygame.Rect(10, 10, 200, 80)
        
        # HUD background
        hud_bg = pygame.Surface((hud_rect.width, hud_rect.height), pygame.SRCALPHA)
        hud_bg.fill((*Theme.get_color("ui_bg"), 180))
        self.layer_ui.blit(hud_bg, hud_rect)
        pygame.draw.rect(self.layer_ui, Theme.get_color("ui_border"), hud_rect, 2)
        
        # Player HP
        hp_text = f"HP: {self.player.current_hp}/{self.player.max_hp}"
        hp_surf = Theme.FONT_BODY.render(hp_text, True, Theme.get_color("text_light"))
        hp_rect = hp_surf.get_rect(x=hud_rect.x + 10, y=hud_rect.y + 10)
        self.layer_ui.blit(hp_surf, hp_rect)
        
        # Player Mana
        mana_text = f"Energy: {self.player.current_mana}/{self.player.max_mana}"
        mana_surf = Theme.FONT_BODY.render(mana_text, True, Theme.get_color("text_light"))
        mana_rect = mana_surf.get_rect(x=hud_rect.x + 10, y=hud_rect.y + 35)
        self.layer_ui.blit(mana_surf, mana_rect)
        
        # Block value
        if self.player.block > 0:
            block_text = f"Block: {self.player.block}"
            block_surf = Theme.FONT_SMALL.render(block_text, True, Theme.get_color("mana"))
            block_rect = block_surf.get_rect(x=hud_rect.x + 10, y=hud_rect.y + 60)
            self.layer_ui.blit(block_surf, block_rect)
    
    def update(self, dt: float) -> None:
        """Update combat screen with definitive animations."""
        current_time = pygame.time.get_ticks()
        
        # Update camera shake
        Camera.update()
        
        # Update sprite animations
        if hasattr(self, 'player_anim') and self.player_anim:
            self.player_anim.update(dt)
        
        if hasattr(self, 'enemy_anim') and self.enemy_anim:
            self.enemy_anim.update(dt)
        
        # Reset player to idle after attack animation
        if (self.player_anim_state == "attack" and 
            hasattr(self, 'player_attack') and 
            self.player_anim is self.player_attack and 
            self.player_attack.done):
            self.player_anim = self.player_idle
            self.player_anim_state = "idle"
            self.player_idle.reset()
        
        # Update card animation
        if self.card_animation:
            elapsed = current_time - self.card_animation["start_time"]
            if elapsed >= self.card_animation["duration"]:
                # Trigger attack animation
                if hasattr(self, 'player_attack'):
                    self.player_anim = self.player_attack
                    self.player_anim_state = "attack"
                    self.player_attack.reset()
                
                # Clear card animation
                self.card_animation = None
        
        # Update floating numbers
        for float_num in self.float_numbers[:]:
            elapsed = current_time - float_num["start_time"]
            if elapsed >= float_num["duration"]:
                self.float_numbers.remove(float_num)
            else:
                # Move number up
                float_num["pos"][1] -= dt * 50
    
    def _draw_floating_numbers(self):
        """Draw floating damage/heal numbers."""
        for float_num in self.float_numbers:
            text_surf = Theme.FONT_BODY.render(float_num["text"], True, float_num["color"])
            self.layer_mid.blit(text_surf, float_num["pos"])
    
    def _draw_card_animation(self):
        """Draw card animation in center."""
        if not self.card_animation:
            return
        
        card = self.card_animation["card"]
        center_pos = (self.screen_w // 2, self.screen_h // 2)
        
        # Create animated card surface
        card_surface = pygame.Surface(Theme.CARD_SIZE, pygame.SRCALPHA)
        card_surface.fill((139, 69, 19, 200))
        
        # Card name
        name_surf = Theme.FONT_SUBTITLE.render(card.name, True, Theme.get_color("text_light"))
        name_rect = name_surf.get_rect(centerx=Theme.CARD_SIZE[0]//2, y=20)
        card_surface.blit(name_surf, name_rect)
        
        # Position in center
        card_rect = card_surface.get_rect(center=center_pos)
        self.layer_mid.blit(card_surface, card_rect)
    
    def _draw_game_over(self):
        """Draw game over overlay."""
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        if self.victory:
            text = "VICTORY!"
            color = Theme.get_color("gold")
        else:
            text = "DEFEAT!"
            color = Theme.get_color("hp")
        
        text_surf = Theme.FONT_TITLE.render(text, True, color)
        text_rect = text_surf.get_rect(center=(self.screen_w//2, self.screen_h//2))
        self.screen.blit(text_surf, text_rect)
        
        # Restart instruction
        restart_text = "Press ENTER to restart"
        restart_surf = Theme.FONT_BODY.render(restart_text, True, Theme.get_color("text_light"))
        restart_rect = restart_surf.get_rect(center=(self.screen_w//2, self.screen_h//2 + 60))
        self.screen.blit(restart_surf, restart_rect)    # === NEW LAYER-BASED DRAWING METHODS ===
    def _draw_background(self) -> None:
        """Draw background to background layer."""
        current_bg = self.biomes[self.current_biome]["background"]
        if current_bg:
            self.layer_bg.blit(current_bg, (0, 0))
        else:
            self.layer_bg.fill(Theme.get_color("background"))
    
    def _draw_enemy_zone(self) -> None:
        """Draw enemy zone to mid layer."""
        self._render_enemy_zone_to_surface(self.layer_mid)
    
    def _draw_hand_zone(self) -> None:
        """Draw hand zone to UI layer."""
        hand_zone = self.zones["hand"]
        
        # CORREÇÃO: Verificar se há cartas antes de processar
        if not self.hand.cards:
            no_cards_text = "No cards in hand"
            self.draw_text_outline_to_surface(
                self.layer_ui,
                no_cards_text,
                (hand_zone.centerx, hand_zone.bottom - 10),
                Theme.FONT_BODY,
                (255, 215, 0),  # Gold text
                outline_color=(0, 0, 0),
                outline_width=2
            )
            return
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        
        # CORREÇÃO: Usar Theme.CARD_SIZE para consistência
        card_width, card_height = 140, 90  # Tamanhos específicos para hand zone
        spacing = 12
        total_width = len(self.hand.cards) * card_width + (len(self.hand.cards) - 1) * spacing
        start_x = hand_zone.centerx - total_width // 2
        
        for i, card in enumerate(self.hand.cards):
            x = start_x + i * (card_width + spacing)
            y = hand_zone.y + (hand_zone.height - card_height) // 2
            
            # Card rect
            card_rect = pygame.Rect(x, y, card_width, card_height)
            
            # Check hover
            hover = card_rect.collidepoint(mouse_pos)
            
            # CORREÇÃO: Usar CardView.draw com tamanho específico
            if hasattr(self, 'card_view'):
                self.card_view.draw(
                    self.layer_ui, 
                    pos=(card_rect.centerx, card_rect.centery), 
                    size=(card_width, card_height), 
                    hover=hover
                )
            else:
                # Fallback rendering
                self._draw_card_fallback(card_rect, card, hover, i == self.selected_card_index)
    
    def _draw_card_fallback(self, card_rect, card, hover, selected):
        """Fallback card drawing when CardView is not available."""
        # Get card background texture based on type
        card_bg_texture = None
        card_type = card.card_type.value.lower() if hasattr(card, 'card_type') else 'default'
        
        # Try to get specific card background from generated assets
        possible_backgrounds = [
            f"{card_type}_card_bg",
            f"card_bg_{card_type}",
            "scroll_parchment",
            "frame_ornate"
        ]
        
        for bg_name in possible_backgrounds:
            card_bg_texture = get_asset(bg_name)
            if card_bg_texture:
                break
        
        # Enhanced hover glow effect
        if hover:
            glow_size = 15
            glow = pygame.Surface((card_rect.width + glow_size * 2, card_rect.height + glow_size * 2), pygame.SRCALPHA)
            alpha = int((math.sin(pygame.time.get_ticks() * 0.015) + 1) * 80)
            glow_color = (255, 215, 0, alpha)  # Golden glow
            
            # Create glow gradient
            center = (glow.get_width() // 2, glow.get_height() // 2)
            for radius in range(glow_size, 0, -1):
                current_alpha = int(alpha * (1 - radius / glow_size))
                color_with_alpha = (*glow_color[:3], current_alpha)
                pygame.draw.ellipse(glow, color_with_alpha, 
                                  (center[0] - radius, center[1] - radius//2, 
                                   radius * 2, radius))
            
            glow_rect = glow.get_rect(center=card_rect.center)
            self.layer_ui.blit(glow, glow_rect.topleft, special_flags=pygame.BLEND_ADD)
        
        # Draw card background
        if card_bg_texture:
            # CORREÇÃO CRÍTICA: Scale texture to card size para evitar frames gigantes
            scaled_texture = pygame.transform.smoothscale(card_bg_texture, (card_rect.width, card_rect.height))
            self.layer_ui.blit(scaled_texture, card_rect)
            
            # Add selection highlight
            if selected:
                highlight = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                highlight.fill((255, 215, 0, 60))  # Golden highlight
                self.layer_ui.blit(highlight, card_rect)
        else:
            # Fallback: gradient background
            if selected:
                color1, color2 = (100, 80, 40), (80, 60, 30)  # Selected colors
            else:
                color1, color2 = (70, 55, 35), (50, 40, 25)   # Normal colors
            
            self._draw_gradient_rect(self.layer_ui, card_rect, color1, color2)
        
        # Card border
        border_color = (255, 215, 0) if selected else (120, 90, 60)
        border_width = 3 if selected else 2
        pygame.draw.rect(self.layer_ui, border_color, card_rect, border_width)
        
        # Card name
        self.draw_text_outline_to_surface(
            self.layer_ui,
            card.name,
            (card_rect.centerx, card_rect.y + 15),
            Theme.FONT_SMALL,
            Theme.get_color("text_light")
        )
        
        # Card cost
        cost_text = f"⚡{card.mana_cost}"
        cost_color = Theme.get_color("mana_blue") if self.player.current_mana >= card.mana_cost else (150, 50, 50)
        self.draw_text_outline_to_surface(
            self.layer_ui,
            cost_text,
            (card_rect.x + 15, card_rect.y + 35),
            Theme.FONT_SMALL,
            cost_color
        )
        
        # Card effect
        if card.damage > 0:
            dmg_text = f"⚔{card.damage}"
            self.draw_text_outline_to_surface(
                self.layer_ui,
                dmg_text,
                (card_rect.x + 15, card_rect.y + 50),
                Theme.FONT_SMALL,
                (255, 100, 100)
            )
        
        if card.block > 0:
            block_text = f"🛡{card.block}"
            self.draw_text_outline_to_surface(
                self.layer_ui,
                block_text,
                (card_rect.x + 60, card_rect.y + 50),
                Theme.FONT_SMALL,
                (100, 100, 255)
            )
        
        if card.heal > 0:
            heal_text = f"❤{card.heal}"
            self.draw_text_outline_to_surface(
                self.layer_ui,
                heal_text,
                (card_rect.x + 90, card_rect.y + 50),
                Theme.FONT_SMALL,
                (100, 255, 100)
            )
    
    def _draw_status_hud(self) -> None:
        """Draw status HUD to UI layer."""
        self._render_status_hud_to_surface(self.layer_ui)
    
    def _draw_floating_numbers(self) -> None:
        """Draw floating numbers to mid layer."""
        self._render_floating_numbers_to_surface(self.layer_mid)
    
    def _draw_card_animation(self) -> None:
        """Draw card animation to mid layer."""
        self._render_card_animation_to_surface(self.layer_mid)
    
    # Surface-based rendering methods for camera shake support
    def _render_enemy_zone_to_surface(self, surface):
        """Render enemy zone to a surface with enhanced medieval UI."""
        enemy_zone = self.zones["enemy"]
        
        # Get medieval UI textures
        frame_texture = get_asset("frame_ornate")
        stone_texture = get_asset("button_texture_stone") 
        
        # Draw ornate background panel for enemy zone
        if frame_texture:
            # Scale and draw ornate frame
            frame_scaled = pygame.transform.scale(frame_texture, (enemy_zone.width + 20, enemy_zone.height + 20))
            frame_rect = frame_scaled.get_rect(center=enemy_zone.center)
            surface.blit(frame_scaled, frame_rect)
        else:
            # Fallback: gradient background with medieval colors
            self._draw_gradient_rect(surface, enemy_zone, (60, 45, 30), (40, 30, 20))
            pygame.draw.rect(surface, (120, 90, 60), enemy_zone, 3)  # Bronze border
        
        # Enemy info
        biome_info = self.biomes[self.current_biome]
        enemy_name = biome_info["enemy_type"]
        
        # Enemy title with enhanced styling
        title_y = enemy_zone.y + 20
        self.draw_text_outline_to_surface(
            surface,
            enemy_name,
            (enemy_zone.centerx, title_y),
            Theme.FONT_TITLE,
            (255, 215, 0),  # Gold text
            outline_color=(0, 0, 0),
            outline_width=2
        )
        
        # Enemy stats
        enemy_hp = self.enemy.current_hp
        enemy_max_hp = self.enemy.max_hp
        
        # Enhanced HP bar with stone texture
        hp_bar_width = 220
        hp_bar_height = 25
        hp_rect = pygame.Rect(enemy_zone.centerx - hp_bar_width//2, enemy_zone.y + 65, hp_bar_width, hp_bar_height)
        
        # Draw HP bar background with stone texture
        if stone_texture:
            stone_bg = pygame.transform.scale(stone_texture, (hp_bar_width + 6, hp_bar_height + 6))
            stone_rect = stone_bg.get_rect(center=hp_rect.center)
            surface.blit(stone_bg, stone_rect)
        
        # HP bar with medieval styling
        self.draw_enhanced_health_bar_to_surface(surface, hp_rect, enemy_hp, enemy_max_hp)
        
        # HP text with gold outline
        hp_text = f"HP: {enemy_hp}/{enemy_max_hp}"
        self.draw_text_outline_to_surface(
            surface,
            hp_text,
            (enemy_zone.centerx, enemy_zone.y + 105),
            Theme.FONT_SUBTITLE,
            (255, 255, 255),
            outline_color=(0, 0, 0),
            outline_width=1
        )
        
        # Enemy intent with enhanced styling
        if hasattr(self.enemy, 'intent') and hasattr(self.enemy, 'intent_icon'):
            intent_y = enemy_zone.y + 135
            
            # Intent background
            intent_bg_rect = pygame.Rect(enemy_zone.centerx - 80, intent_y - 10, 160, 35)
            self._draw_gradient_rect(surface, intent_bg_rect, (80, 60, 40), (50, 35, 20))
            pygame.draw.rect(surface, (120, 90, 60), intent_bg_rect, 2)
            
            # Draw icon if available
            if self.intent_icons and self.enemy.intent in self.intent_icons:
                icon = self.intent_icons[self.enemy.intent]
                icon_rect = icon.get_rect(center=(enemy_zone.centerx - 25, intent_y + 5))
                surface.blit(icon, icon_rect)
                
                # Value text next to icon
                intent_color = (255, 100, 100) if self.enemy.intent == "attack" else (100, 100, 255)
                value_text = str(self.enemy.intent_value)
                self.draw_text_outline_to_surface(
                    surface,
                    value_text,
                    (enemy_zone.centerx + 10, intent_y),
                    Theme.FONT_SUBTITLE,
                    intent_color
                )
            else:
                # Fallback to text only
                intent_text = f"{self.enemy.intent_icon} {self.enemy.intent_value}"
                intent_color = (255, 100, 100) if self.enemy.intent == "attack" else (100, 100, 255)
                self.draw_text_outline_to_surface(
                    surface,
                    intent_text,
                    (enemy_zone.centerx, intent_y),
                    Theme.FONT_SUBTITLE,
                    intent_color
                )
    
    def _render_hand_to_surface(self, surface):
        """Render hand to a surface with enhanced medieval cards - LEGACY METHOD."""
        # REDIRECTION: Use new layer-based method instead
        logger.warning("Using legacy _render_hand_to_surface - should use _draw_hand_zone instead")
        # This is kept for compatibility but should not be called in new system
        pass
    
    def _render_status_hud_to_surface(self, surface):
        """Render status HUD to a surface with medieval styling."""
        # Get UI textures
        panel_texture = get_asset("button_texture_stone") or get_asset("frame_ornate")
        
        # Main HUD panel background
        hud_rect = pygame.Rect(10, 10, 280, 120)
        
        if panel_texture:
            # Scale and draw panel texture
            panel_scaled = pygame.transform.scale(panel_texture, (hud_rect.width, hud_rect.height))
            surface.blit(panel_scaled, hud_rect)
        else:
            # Fallback: gradient panel
            self._draw_gradient_rect(surface, hud_rect, (80, 60, 40), (50, 35, 20))
        
        # Panel border
        pygame.draw.rect(surface, (120, 90, 60), hud_rect, 3)
        
        # Player status
        player_hp = f"HP: {self.player.current_hp}/{self.player.max_hp}"
        player_mana = f"Energy: {self.player.current_mana}/{self.player.max_mana}"
        
        # Player HP with enhanced bar
        hp_rect = pygame.Rect(25, 35, 180, 22)
        self.draw_enhanced_health_bar_to_surface(surface, hp_rect, self.player.current_hp, self.player.max_hp)
        
        # HP label with golden text
        self.draw_text_outline_to_surface(
            surface,
            "Health",
            (hp_rect.centerx, hp_rect.y - 15),
            Theme.FONT_BODY,
            (255, 215, 0),  # Gold
            outline_color=(0, 0, 0),
            outline_width=1
        )
        
        # HP value
        self.draw_text_outline_to_surface(
            surface,
            f"{self.player.current_hp}/{self.player.max_hp}",
            (hp_rect.centerx, hp_rect.centery),
            Theme.FONT_BODY,
            (255, 255, 255),
            outline_color=(0, 0, 0),
            outline_width=1
        )
        
        # Player Energy/Mana with enhanced bar
        mana_rect = pygame.Rect(25, 70, 180, 22)
        
        # Energy bar background
        pygame.draw.rect(surface, (40, 30, 20), mana_rect)
        pygame.draw.rect(surface, (120, 90, 60), mana_rect, 2)
        
        # Energy fill with blue gradient
        if self.player.max_mana > 0:
            fill_width = int((self.player.current_mana / self.player.max_mana) * mana_rect.width)
            fill_rect = pygame.Rect(mana_rect.left, mana_rect.top, fill_width, mana_rect.height)
            self._draw_gradient_rect(surface, fill_rect, (100, 150, 255), (60, 100, 200))
        
        # Energy label
        self.draw_text_outline_to_surface(
            surface,
            "Energy",
            (mana_rect.centerx, mana_rect.y - 15),
            Theme.FONT_BODY,
            (100, 200, 255),  # Light blue
            outline_color=(0, 0, 0),
            outline_width=1
        )
        
        # Energy value
        self.draw_text_outline_to_surface(
            surface,
            f"{self.player.current_mana}/{self.player.max_mana}",
            (mana_rect.centerx, mana_rect.centery),
            Theme.FONT_BODY,
            (255, 255, 255),
            outline_color=(0, 0, 0),
            outline_width=1
        )
        
        # Block display with shield icon effect
        if self.player.block > 0:
            block_rect = pygame.Rect(220, 35, 60, 25)
            
            # Block background
            self._draw_gradient_rect(surface, block_rect, (150, 150, 200), (100, 100, 150))
            pygame.draw.rect(surface, (200, 200, 255), block_rect, 2)
            
            # Block text
            block_text = f"🛡️ {self.player.block}"
            self.draw_text_outline_to_surface(
                surface,
                block_text,
                block_rect.center,
                Theme.FONT_BODY,
                (255, 255, 255),
                outline_color=(0, 0, 0),
                outline_width=1
            )
    
    def _render_floating_numbers_to_surface(self, surface):
        """Render floating damage numbers to a surface with enhanced effects."""
        for float_num in self.float_numbers:
            # Calculate alpha and scale based on remaining time
            elapsed = pygame.time.get_ticks() - float_num["start_time"]
            progress = elapsed / float_num["duration"]
            alpha = int(255 * (1 - progress))
            
            # Scale effect: larger at start, normal at end
            scale = 1.0 + (1 - progress) * 0.5
            
            # Enhanced colors based on damage type
            base_color = float_num["color"]
            if base_color == (255, 100, 100):  # Damage - red with fire effect
                glow_color = (255, 150, 0)  # Orange glow
                text_color = (255, 200, 200)
            elif base_color == (100, 255, 100):  # Healing - green with nature effect
                glow_color = (150, 255, 150)
                text_color = (200, 255, 200)
            elif base_color == (100, 100, 255):  # Block - blue with shield effect
                glow_color = (150, 150, 255)
                text_color = (200, 200, 255)
            else:  # Default - gold
                glow_color = (255, 215, 0)
                text_color = (255, 235, 150)
            
            # Create text with outline and glow
            text = float_num["text"]
            font = Theme.FONT_TITLE
            
            # Calculate text size with scale
            text_size = font.size(text)
            scaled_width = int(text_size[0] * scale)
            scaled_height = int(text_size[1] * scale)
            
            # Create surface for the number with glow
            text_surface = pygame.Surface((scaled_width + 20, scaled_height + 20), pygame.SRCALPHA)
            
            # Draw glow effect (multiple passes with decreasing alpha)
            glow_alpha = int(alpha * 0.6)
            for offset in range(8, 0, -2):
                # Ensure alpha is valid (0-255)
                current_alpha = max(0, min(255, glow_alpha // max(1, offset // 2)))
                glow_color_rgba = (*glow_color, current_alpha)
                
                glow_text = font.render(text, True, glow_color)  # Use RGB only for render
                if scale != 1.0:
                    glow_text = pygame.transform.scale(glow_text, (scaled_width, scaled_height))
                
                # Apply alpha after rendering
                glow_text.set_alpha(current_alpha)
                glow_rect = glow_text.get_rect(center=(text_surface.get_width() // 2, text_surface.get_height() // 2))
                
                # Draw glow in multiple positions
                for dx in range(-offset, offset + 1, offset):
                    for dy in range(-offset, offset + 1, offset):
                        if dx != 0 or dy != 0:
                            pos = (glow_rect.x + dx, glow_rect.y + dy)
                            text_surface.blit(glow_text, pos, special_flags=pygame.BLEND_ADD)
            
            # Draw main text with outline
            main_text = font.render(text, True, text_color)
            if scale != 1.0:
                main_text = pygame.transform.scale(main_text, (scaled_width, scaled_height))
            
            # Black outline
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx != 0 or dy != 0:
                        outline_pos = (text_surface.get_width() // 2 + dx - scaled_width // 2,
                                     text_surface.get_height() // 2 + dy - scaled_height // 2)
                        outline_text = font.render(text, True, (0, 0, 0))
                        if scale != 1.0:
                            outline_text = pygame.transform.scale(outline_text, (scaled_width, scaled_height))
                        text_surface.blit(outline_text, outline_pos)
            
            # Draw main text
            main_pos = (text_surface.get_width() // 2 - scaled_width // 2,
                       text_surface.get_height() // 2 - scaled_height // 2)
            text_surface.blit(main_text, main_pos)
            
            # Apply overall alpha
            text_surface.set_alpha(alpha)
            
            # Draw at current position
            text_rect = text_surface.get_rect(center=float_num["pos"])
            surface.blit(text_surface, text_rect)
    
    def _render_card_animation_to_surface(self, surface):
        """Render animated card moving to center on a surface."""
        if not self.card_animation:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.card_animation["start_time"]
        progress = min(1.0, elapsed / self.card_animation["duration"])
        
        # Interpolate position (simple linear for now)
        target_pos = self.card_animation["target_pos"]
        
        # Draw card at animated position
        card_rect = pygame.Rect(0, 0, 120, 80)
        card_rect.center = target_pos
        
        # Draw animated card
        pygame.draw.rect(surface, (255, 215, 0), card_rect)
        pygame.draw.rect(surface, (255, 255, 255), card_rect, 2)
        
        # Card name
        card_name = self.card_animation["card"].name
        name_surface = Theme.FONT_SUBTITLE.render(card_name, True, (0, 0, 0))
        name_rect = name_surface.get_rect(center=card_rect.center)
        surface.blit(name_surface, name_rect)
    
    def _render_game_over(self):
        """Render game over screen."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        result_text = "Victory!" if self.victory else "Defeat!"
        result_color = (100, 255, 100) if self.victory else (255, 100, 100)
        
        self.draw_text_outline_to_surface(
            self.screen,
            result_text,
            (self.width // 2, self.height // 2 - 50),
            Theme.FONT_TITLE,
            result_color
        )
        
        restart_text = "Press R to restart or ESC to return to menu"
        self.draw_text_outline_to_surface(
            self.screen,
            restart_text,
            (self.screen_w // 2, self.screen_h // 2 + 20),
            Theme.FONT_SUBTITLE,
            Theme.get_color("text_light")
        )
    
    # Helper methods
    def _draw_gradient_rect(self, surface, rect, color1, color2):
        """Draw a vertical gradient rectangle."""
        for y in range(rect.height):
            progress = y / rect.height
            r = int(color1[0] * (1 - progress) + color2[0] * progress)
            g = int(color1[1] * (1 - progress) + color2[1] * progress)
            b = int(color1[2] * (1 - progress) + color2[2] * progress)
            pygame.draw.line(surface, (r, g, b), 
                           (rect.left, rect.top + y), 
                           (rect.right, rect.top + y))
    
    def draw_enhanced_health_bar_to_surface(self, surface, rect, current, maximum):
        """Draw enhanced health bar with medieval styling."""
        # Background with dark stone
        pygame.draw.rect(surface, (40, 30, 20), rect)
        pygame.draw.rect(surface, (120, 90, 60), rect, 2)  # Bronze border
        
        # Health fill with gradient
        if current > 0 and maximum > 0:
            fill_width = int(rect.width * (current / maximum))
            fill_rect = pygame.Rect(rect.left, rect.top, fill_width, rect.height)
            
            # Health color based on percentage
            health_percent = current / maximum
            if health_percent > 0.6:
                color1, color2 = (100, 200, 100), (60, 150, 60)  # Green
            elif health_percent > 0.3:
                color1, color2 = (200, 200, 100), (150, 150, 60)  # Yellow
            else:
                color1, color2 = (200, 100, 100), (150, 60, 60)   # Red
            
            self._draw_gradient_rect(surface, fill_rect, color1, color2)
            
        # Inner shadow
        pygame.draw.rect(surface, (20, 15, 10), rect, 1)
    
    def draw_text_outline_to_surface(self, surface, text, pos, font, color, outline_color=(0, 0, 0), outline_width=2):
        """Draw text with outline to surface."""
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_surface = font.render(text, True, outline_color)
                    outline_rect = outline_surface.get_rect(center=(pos[0] + dx, pos[1] + dy))
                    surface.blit(outline_surface, outline_rect)
        
        # Draw main text
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=pos)
        surface.blit(text_surface, text_rect)
    
    # === SCREEN LIFECYCLE METHODS ===
    
    def enter_screen(self) -> None:
        """Called when screen becomes active."""
        logger.info(f"Entering MVP Combat Screen - Layout definitivo para {self.character_id}")
        
    def exit_screen(self) -> None:
        """Called when screen becomes inactive."""
        logger.info("Exiting MVP Combat Screen")
    
    # === EVENT HANDLING ===
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back_to_menu"
                
            elif event.key == pygame.K_TAB:
                # Switch biomes
                self.current_biome = "goblin_cave" if self.current_biome == "cathedral" else "cathedral"
                self.enemy = self._create_enemy_for_biome(self.current_biome)
                self.turn_engine.enemy = self.enemy
                
            elif event.key == pygame.K_LEFT:
                # Select previous card
                if self.hand.cards:
                    self.selected_card_index = max(0, self.selected_card_index - 1)
                    
            elif event.key == pygame.K_RIGHT:
                # Select next card
                if self.hand.cards:
                    self.selected_card_index = min(len(self.hand.cards) - 1, self.selected_card_index + 1)
                    
            elif event.key == pygame.K_SPACE:
                # Play selected card
                if not self.game_over and self.hand.cards and self.selected_card_index < len(self.hand.cards):
                    selected_card = self.hand.cards[self.selected_card_index]
                    self._play_card(selected_card)
                    
            elif event.key == pygame.K_RETURN:
                # End turn or restart if game over
                if self.game_over:
                    self._start_combat()
                else:
                    self._end_turn()
                    
            elif event.key == pygame.K_r:
                # Restart combat
                self._start_combat()
                
        return None
    
    # === CARD GAMEPLAY ===
    
    def _play_card(self, card: Card) -> None:
        """Play a card with animation."""
        try:
            # Start card animation
            self.card_animation = {
                "card": card,
                "start_time": pygame.time.get_ticks(),
                "duration": 250,
                "target_pos": (self.screen_w // 2, self.screen_h // 2)
            }
            
            result = self.turn_engine.play_card(card)
            if result:
                self.hand.remove_card(card)
                # Adjust selection
                if self.selected_card_index >= len(self.hand.cards):
                    self.selected_card_index = max(0, len(self.hand.cards) - 1)
                    
                # Create floating numbers
                if card.damage > 0:
                    enemy_pos = [self.screen_w // 2 + 200, self.ground_y - 100]
                    self.float_numbers.append({
                        "text": f"-{card.damage}",
                        "pos": enemy_pos,
                        "start_time": pygame.time.get_ticks(),
                        "duration": 1000,
                        "color": Theme.get_color("hp")
                    })
                
                if card.heal > 0:
                    player_pos = [self.screen_w // 2 - 200, self.ground_y - 100]
                    self.float_numbers.append({
                        "text": f"+{card.heal}",
                        "pos": player_pos,
                        "start_time": pygame.time.get_ticks(),
                        "duration": 1000,
                        "color": (100, 255, 100)
                    })
                
                # Check game over
                if self.enemy.current_hp <= 0:
                    self.game_over = True
                    self.victory = True
                elif self.player.current_hp <= 0:
                    self.game_over = True
                    self.victory = False
                    
        except Exception as e:
            logger.error(f"Error playing card {card.name}: {e}")
    
    def _end_turn(self):
        """End player turn."""
        # Discard current hand
        for card in self.hand.cards:
            self.deck.discard_pile.append(card)
        self.hand.cards.clear()
        
        # Draw new hand
        for _ in range(5):
            if not self.deck.draw_pile and self.deck.discard_pile:
                # Reshuffle
                self.deck.draw_pile = deque(random.sample(self.deck.discard_pile, len(self.deck.discard_pile)))
                self.deck.discard_pile.clear()
            
            card = self.deck.draw_card()
            if card:
                self.hand.add_card(card)
        
        # Recharge energy
        self.player.current_mana = self.player.max_mana
        self.turn_engine.end_player_turn()
        
        # Enemy turn
        self._enemy_turn()
        self._prepare_enemy_intent(self.enemy)
    
    def _enemy_turn(self) -> None:
        """Execute enemy turn."""
        if hasattr(self.enemy, 'intent') and self.enemy.intent == "attack":
            damage = max(0, self.enemy.attack - self.player.block)
            self.player.current_hp -= damage
            self.player.block = max(0, self.player.block - self.enemy.attack)
            
            if damage > 0:
                player_pos = [self.screen_w // 2 - 200, self.ground_y - 100]
                self.float_numbers.append({
                    "text": f"-{damage}",
                    "pos": player_pos,
                    "start_time": pygame.time.get_ticks(),
                    "duration": 1000,
                    "color": Theme.get_color("hp")
                })
                
                if damage > 5:
                    Camera.shake(intensity=6, frames=4)
        
        # Check if player is defeated
        if self.player.current_hp <= 0:
            self.game_over = True
            self.victory = False
