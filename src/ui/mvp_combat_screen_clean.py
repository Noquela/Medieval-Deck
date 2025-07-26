"""
MVP Combat Screen - Layout Definitivo Stage-Action.

Implementação limpa com:
- Background de corredor medieval
- Sprites alinhados na linha do chão 
- Cartas na zona inferior (18%)
- HUD discreto nos cantos
"""

import logging
import math
import random
from collections import deque
from pathlib import Path
from typing import Optional, List, Dict, Any

import pygame

from ..utils.config import Config
from ..utils.theme import Theme
from ..utils.asset_loader import get_asset
from ..gameplay.mvp_deck import MVPDeck
from ..gameplay.mvp_cards import Hand
from ..core.turn_engine import Player, Enemy

logger = logging.getLogger(__name__)


class MVPCombatScreen:
    """
    MVP Combat Screen - Layout Definitivo Stage-Action.
    
    Layout:
    - Background: Corredor medieval widescreen
    - Sprites: Herói e inimigos na linha do chão (55% da altura)
    - Cartas: Faixa inferior (18% da altura) com pergaminhos IA
    - HUD: Cantos discretos
    """
    
    def __init__(self, screen: pygame.Surface, config: Config, character_id: str = "knight"):
        """Initialize MVP combat screen with definitive layout."""
        self.screen = screen
        self.config = config
        self.character_id = character_id
        
        # Screen dimensions
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        
        # Initialize Theme
        Theme.init_fonts()
        
        # Create layer surfaces for proper draw order management
        self.layer_bg = pygame.Surface((self.screen_w, self.screen_h)).convert()
        self.layer_mid = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        self.layer_ui = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        
        # Layout zones using Theme
        self.zones = Theme.create_zones((self.screen_w, self.screen_h))
        self.ground_y = Theme.get_ground_y(self.screen_h)
        
        # Load assets
        self.bg_corridor = self._load_background("corridor_stage_definitive")
        self.intent_icons = self._load_intent_icons()
        
        # Setup animations
        self._setup_animations()
        
        # Game state
        self.biomes = {
            "cathedral": {"name": "Sacred Cathedral", "enemy_type": "Knight Guardian"},
            "goblin_cave": {"name": "Goblin Cave", "enemy_type": "Goblin Scout"}
        }
        self.current_biome = "cathedral"
        self.selected_card_index = 0
        
        # Initialize game systems
        self.deck = MVPDeck()
        self.hand = Hand()
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
        
        # Start combat
        self._start_combat()
        
        logger.info(f"MVP Combat Screen initialized - Layout definitivo para {character_id}")
    
    # === ASSET LOADING ===
    
    def _load_background(self, bg_name: str) -> pygame.Surface:
        """Load corridor background."""
        try:
            # Try to load generated corridor background
            bg_path = Path("assets/generated") / f"{bg_name}.png"
            if bg_path.exists():
                bg = pygame.image.load(bg_path).convert()
                return pygame.transform.scale(bg, (self.screen_w, self.screen_h))
            
            # Fallback to existing combat backgrounds
            fallback_names = ["combat_bg_dark_tower", "bg_cathedral", "combat_bg_dragon_lair"]
            for fallback in fallback_names:
                fallback_asset = get_asset(fallback)
                if fallback_asset:
                    return pygame.transform.scale(fallback_asset, (self.screen_w, self.screen_h))
            
            logger.warning(f"No background found for {bg_name}, using fallback")
            return self._create_fallback_background()
            
        except Exception as e:
            logger.error(f"Error loading background {bg_name}: {e}")
            return self._create_fallback_background()
    
    def _create_fallback_background(self) -> pygame.Surface:
        """Create simple gradient fallback background."""
        bg = pygame.Surface((self.screen_w, self.screen_h))
        
        # Medieval gradient
        for y in range(self.screen_h):
            progress = y / self.screen_h
            color_r = int(30 + progress * 20)
            color_g = int(25 + progress * 15) 
            color_b = int(20 + progress * 10)
            pygame.draw.line(bg, (color_r, color_g, color_b), (0, y), (self.screen_w, y))
        
        return bg
    
    def _load_intent_icons(self) -> Dict[str, pygame.Surface]:
        """Load intent icons."""
        icons = {}
        
        # Try to load generated definitive icons
        icon_names = ["attack", "block", "special"]
        for icon_name in icon_names:
            icon_asset = get_asset(f"intent_icon_{icon_name}_definitive")
            if icon_asset:
                icons[icon_name] = pygame.transform.scale(icon_asset, (32, 32))
            else:
                # Create simple placeholder
                icon = pygame.Surface((32, 32), pygame.SRCALPHA)
                if icon_name == "attack":
                    pygame.draw.polygon(icon, Theme.get_color("hp"), [(16, 4), (28, 28), (4, 28)])
                else:
                    pygame.draw.ellipse(icon, Theme.get_color("mana"), (4, 4, 24, 24))
                icons[icon_name] = icon
        
        return icons
    
    def _setup_animations(self):
        """Setup sprite animations."""
        try:
            # Load enhanced character sprites
            knight_sprite = get_asset("knight_sprite_enhanced") or get_asset("knight_sprite")
            goblin_sprite = get_asset("goblin_sprite_enhanced") or get_asset("goblin_scout_sprite")
            
            # Create fallback sprites if needed
            if not knight_sprite:
                knight_sprite = pygame.Surface((128, 128), pygame.SRCALPHA)
                knight_sprite.fill(Theme.get_color("gold"))
            
            if not goblin_sprite:
                goblin_sprite = pygame.Surface((96, 96), pygame.SRCALPHA)  
                goblin_sprite.fill(Theme.get_color("hp"))
            
            # Create single-frame animations (expandable to sprite sheets later)
            self.player_idle = FrameAnimation([knight_sprite], fps=1, loop=True)
            self.player_attack = FrameAnimation([knight_sprite], fps=1, loop=False)
            self.goblin_idle = FrameAnimation([goblin_sprite], fps=1, loop=True)
            self.goblin_attack = FrameAnimation([goblin_sprite], fps=1, loop=False)
            
            self.player_anim = self.player_idle
            self.enemy_anim = self.goblin_idle
            
        except Exception as e:
            logger.warning(f"Error setting up animations: {e}")
            # Create minimal fallback animations
            default_sprite = pygame.Surface((64, 64), pygame.SRCALPHA)
            default_sprite.fill((100, 100, 100))
            self.player_anim = FrameAnimation([default_sprite], fps=1, loop=True)
            self.enemy_anim = FrameAnimation([default_sprite], fps=1, loop=True)
    
    # === GAME LOGIC ===
    
    def _create_player_for_character(self, character_id: str) -> MVPPlayer:
        """Create player based on selected character."""
        if character_id == "wizard":
            return MVPPlayer(max_hp=80, max_mana=4)
        elif character_id == "assassin":
            return MVPPlayer(max_hp=90, max_mana=3)
        else:  # knight
            return MVPPlayer(max_hp=120, max_mana=2)
    
    def _create_enemy_for_biome(self, biome_name: str) -> MVPEnemy:
        """Create enemy for current biome."""
        if biome_name == "cathedral":
            enemy = MVPEnemy("Knight Guardian", hp=35, attack=8, enemy_type="knight")
        elif biome_name == "goblin_cave":
            enemy = MVPEnemy("Goblin Scout", hp=20, attack=6, enemy_type="goblin")
        else:
            enemy = MVPEnemy("Unknown Enemy", hp=25, attack=7, enemy_type="generic")
        
        self._prepare_enemy_intent(enemy)
        return enemy
    
    def _prepare_enemy_intent(self, enemy) -> None:
        """Prepare enemy's next action intent."""
        if enemy.current_hp > 0:
            enemy.intent = random.choice(["attack", "block"])
            if enemy.intent == "attack":
                enemy.intent_value = enemy.attack
            else:
                enemy.intent_value = 6
    
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
    
    # === UPDATE ===
    
    def update(self, dt: float) -> None:
        """Update combat screen."""
        current_time = pygame.time.get_ticks()
        
        # Update camera shake
        Camera.update()
        
        # Update sprite animations
        if hasattr(self, 'player_anim') and self.player_anim:
            self.player_anim.update(dt)
        
        if hasattr(self, 'enemy_anim') and self.enemy_anim:
            self.enemy_anim.update(dt)
        
        # Update card animation
        if self.card_animation:
            elapsed = current_time - self.card_animation["start_time"]
            if elapsed >= self.card_animation["duration"]:
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
    
    # === DRAWING ===
    
    def draw(self) -> None:
        """Draw the combat screen with definitive stage-action layout."""
        # Apply camera shake
        shake_offset = Camera.shake_offset
        
        # Clear layers for new frame
        self.layer_bg.fill(Theme.get_color("background"))
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
        """Draw corridor background to background layer."""
        if self.bg_corridor:
            self.layer_bg.blit(self.bg_corridor, (0, 0))
        else:
            self.layer_bg.fill(Theme.get_color("background"))
    
    def _draw_player_sprite(self):
        """Draw player sprite aligned to ground line."""
        if hasattr(self, 'player_anim') and self.player_anim:
            frame = self.player_anim.current()
            # Position sprite on ground line, left side
            sprite_rect = frame.get_rect(midbottom=(self.screen_w // 2 - 200, self.ground_y))
            self.layer_mid.blit(frame, sprite_rect)
    
    def _draw_enemy_sprites(self):
        """Draw enemy sprites aligned to ground line."""
        if hasattr(self, 'enemy_anim') and self.enemy_anim:
            frame = self.enemy_anim.current()
            # Position enemy on ground line, right side
            sprite_rect = frame.get_rect(midbottom=(self.screen_w // 2 + 200, self.ground_y))
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
        
        # Check if there are cards
        if not self.hand.cards:
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
            
            # Check hover and selection
            hover = card_rect.collidepoint(mouse_pos)
            selected = (i == self.selected_card_index)
            
            # Draw card
            self._draw_single_card(card_rect, card, hover, selected)
    
    def _draw_single_card(self, rect: pygame.Rect, card: Card, hover: bool, selected: bool):
        """Draw a single card with proper scaling."""
        
        # Load card frame
        card_frame = get_asset("card_frame_generic_definitive") or get_asset("frame_ornate")
        if not card_frame:
            # Create simple frame
            card_frame = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            card_frame.fill((139, 69, 19, 200))
            pygame.draw.rect(card_frame, (101, 67, 33), card_frame.get_rect(), 3)
        
        # Scale frame to exact card size
        scaled_frame = pygame.transform.smoothscale(card_frame, (rect.width, rect.height))
        
        # Hover glow effect
        if hover:
            glow_size = 8
            glow = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
            alpha = int((math.sin(pygame.time.get_ticks() * 0.015) + 1) * 60)
            glow.fill((*Theme.get_color("gold"), alpha))
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
        self.screen.blit(restart_surf, restart_rect)
    
    # === LIFECYCLE ===
    
    def enter_screen(self) -> None:
        """Called when screen becomes active."""
        logger.info(f"Entering MVP Combat Screen - Layout definitivo para {self.character_id}")
        
    def exit_screen(self) -> None:
        """Called when screen becomes inactive."""
        logger.info("Exiting MVP Combat Screen")
