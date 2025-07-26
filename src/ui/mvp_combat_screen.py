"""
MVP Combat Screen - Sistema de combate integrado ao jogo principal

Usa os sistemas MVP mas integrado ao fluxo normal do jogo.
"""

import pygame
import logging
import math
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..utils.config import Config
from ..gameplay.mvp_cards import Card, CardType, Hand
from ..gameplay.mvp_deck import MVPDeck
from ..core.mvp_turn_engine import MVPTurnEngine, MVPPlayer, MVPEnemy

logger = logging.getLogger(__name__)


class MVPCombatScreen:
    """
    Tela de combate MVP integrada ao jogo principal.
    
    Usa os sistemas MVP testados mas dentro do fluxo normal do jogo.
    """
    
    def __init__(self, screen: pygame.Surface, config: Config, character_id: str = "knight"):
        """
        Initialize MVP combat screen.
        
        Args:
            screen: Pygame screen surface
            config: Configuration object
            character_id: Selected character (knight, wizard, assassin)
        """
        self.screen = screen
        self.config = config
        self.character_id = character_id
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Theme colors and fonts
        pygame.font.init()
        self.colors = {
            "background": (25, 20, 15),
            "text_light": (245, 240, 230),
            "border": (100, 100, 100),
            "card_bg": (60, 50, 40),
            "accent": (212, 180, 106),
            "hp_red": (220, 68, 58),
            "mana_blue": (39, 131, 221),
            "selected": (255, 215, 0)  # Golden
        }
        
        self.fonts = {
            "large": pygame.font.Font(None, 36),
            "medium": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 18)
        }
        
        # Create layout zones
        self.zones = {
            "enemy": pygame.Rect(0, 0, self.width, int(self.height * 0.25)),
            "hand": pygame.Rect(0, int(self.height * 0.8), self.width, int(self.height * 0.2)),
            "status_hud": pygame.Rect(self.width - 280, 20, 260, 120),
            "player": pygame.Rect(int(self.width * 0.1), int(self.height * 0.4), 
                                int(self.width * 0.3), int(self.height * 0.4))
        }
        
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
        """Execute enemy turn with proper block mechanics."""
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
            
            # Try different naming patterns
            patterns = [
                f"{bg_name}_*.png",
                f"bg_{bg_name.split('_')[-1]}_*.png"
            ]
            
            for pattern in patterns:
                bg_files = list(generated_dir.glob(pattern))
                if bg_files:
                    bg_path = bg_files[0]  # Use first match
                    logger.info(f"Loading background: {bg_path}")
                    bg_surface = pygame.image.load(bg_path)
                    return pygame.transform.scale(bg_surface, (self.width, self.height))
            
            logger.warning(f"Background not found for {bg_name}, using fallback")
            return self._create_fallback_background()
            
        except Exception as e:
            logger.error(f"Error loading background {bg_name}: {e}")
            return self._create_fallback_background()
    
    def _create_fallback_background(self) -> pygame.Surface:
        """Create fallback background."""
        bg = pygame.Surface((self.width, self.height))
        bg.fill(self.colors["background"])
        return bg
    
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
                        # Recharge energy on turn end
                        self.player.current_mana = self.player.max_mana
                        self.turn_engine.end_player_turn()
                        
                        # Enemy takes their turn
                        self._enemy_turn()
                        
                        # Prepare next intent after enemy turn
                        self._prepare_enemy_intent(self.enemy)
                        
                        logger.info("Player turn ended, energy recharged")
                    
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
    
    def draw_text_outline(self, surface, text, pos, font, color):
        """Draw text with outline."""
        x, y = pos
        # Outline
        outline_color = (0, 0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    surface.blit(outline_surf, (x + dx, y + dy))
        # Main text
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, pos)
    
    def draw_health_bar(self, surface, rect, current, maximum):
        """Draw health bar."""
        # Background
        pygame.draw.rect(surface, (100, 50, 50), rect)
        pygame.draw.rect(surface, self.colors["border"], rect, 2)
        
        # Fill
        if maximum > 0:
            fill_width = int((current / maximum) * (rect.width - 4))
            fill_rect = pygame.Rect(rect.x + 2, rect.y + 2, fill_width, rect.height - 4)
            pygame.draw.rect(surface, self.colors["hp_red"], fill_rect)
    
    def update(self, dt: float) -> None:
        """Update combat screen."""
        current_time = pygame.time.get_ticks()
        
        # Update card animation
        if self.card_animation:
            elapsed = current_time - self.card_animation["start_time"]
            if elapsed >= self.card_animation["duration"]:
                self.card_animation = None
        
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
        """Draw the combat screen."""
        # Background
        current_bg = self.biomes[self.current_biome]["background"]
        if current_bg:
            self.screen.blit(current_bg, (0, 0))
        else:
            self.screen.fill(self.colors["background"])
        
        # Enemy zone
        self._render_enemy_zone()
        
        # Player hand
        self._render_hand()
        
        # Status HUD
        self._render_status_hud()
        
        # Controls help
        self._render_controls()
        
        # Game over overlay
        if self.game_over:
            self._render_game_over()
        
        # Render floating numbers
        self._render_floating_numbers()
        
        # Render card animation
        if self.card_animation:
            self._render_card_animation()
    
    def _render_enemy_zone(self):
        """Render enemy zone."""
        enemy_zone = self.zones["enemy"]
        
        # Enemy info
        biome_info = self.biomes[self.current_biome]
        enemy_name = biome_info["enemy_type"]
        
        # Enemy title
        self.draw_text_outline(
            self.screen,
            enemy_name,
            (enemy_zone.centerx, enemy_zone.y + 20),
            self.fonts["large"],
            self.colors["text_light"]
        )
        
        # Enemy stats
        enemy_hp = self.enemy.current_hp
        enemy_max_hp = self.enemy.max_hp
        
        # HP bar
        hp_rect = pygame.Rect(enemy_zone.centerx - 100, enemy_zone.y + 60, 200, 20)
        self.draw_health_bar(self.screen, hp_rect, enemy_hp, enemy_max_hp)
        
        # HP text
        hp_text = f"HP: {enemy_hp}/{enemy_max_hp}"
        self.draw_text_outline(
            self.screen,
            hp_text,
            (enemy_zone.centerx, enemy_zone.y + 90),
            self.fonts["medium"],
            self.colors["text_light"]
        )
        
        # Enemy intent (shows next action)
        if hasattr(self.enemy, 'intent') and hasattr(self.enemy, 'intent_icon'):
            intent_y = enemy_zone.y + 120
            
            # Draw icon if available
            if self.intent_icons and self.enemy.intent in self.intent_icons:
                icon = self.intent_icons[self.enemy.intent]
                icon_rect = icon.get_rect(center=(enemy_zone.centerx - 20, intent_y))
                self.screen.blit(icon, icon_rect)
                
                # Value text next to icon
                intent_color = (255, 100, 100) if self.enemy.intent == "attack" else (100, 100, 255)
                value_text = str(self.enemy.intent_value)
                self.draw_text_outline(
                    self.screen,
                    value_text,
                    (enemy_zone.centerx + 10, intent_y),
                    self.fonts["medium"],
                    intent_color
                )
            else:
                # Fallback to text only
                intent_text = f"{self.enemy.intent_icon} {self.enemy.intent_value}"
                intent_color = (255, 100, 100) if self.enemy.intent == "attack" else (100, 100, 255)
                self.draw_text_outline(
                    self.screen,
                    intent_text,
                    (enemy_zone.centerx, intent_y),
                    self.fonts["medium"],
                    intent_color
                )
    
    def _render_hand(self):
        """Render player hand."""
        hand_zone = self.zones["hand"]
        
        if not self.hand.cards:
            no_cards_text = "No cards in hand"
            self.draw_text_outline(
                self.screen,
                no_cards_text,
                hand_zone.center,
                self.fonts["medium"],
                self.colors["text_light"]
            )
            return
        
        # Get mouse position for hover detection
        mouse_pos = pygame.mouse.get_pos()
        
        # Calculate card positions
        card_width = 120
        card_height = 80
        spacing = 10
        total_width = len(self.hand.cards) * card_width + (len(self.hand.cards) - 1) * spacing
        start_x = hand_zone.centerx - total_width // 2
        
        for i, card in enumerate(self.hand.cards):
            x = start_x + i * (card_width + spacing)
            y = hand_zone.y + (hand_zone.height - card_height) // 2
            
            # Card rect
            card_rect = pygame.Rect(x, y, card_width, card_height)
            
            # Check hover
            hover = card_rect.collidepoint(mouse_pos)
            
            # Card background (different color if selected)
            if i == self.selected_card_index:
                color = self.colors["selected"]
            else:
                color = self.colors["card_bg"]
            
            # Hover glow effect
            if hover:
                glow = pygame.Surface((card_width + 10, card_height + 10), pygame.SRCALPHA)
                alpha = int((math.sin(pygame.time.get_ticks() * 0.02) + 1) * 60)
                glow.fill((212, 180, 106, alpha))
                glow_rect = glow.get_rect(center=card_rect.center)
                self.screen.blit(glow, glow_rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)
            
            pygame.draw.rect(self.screen, color, card_rect)
            pygame.draw.rect(self.screen, self.colors["border"], card_rect, 2)
            
            # Card name
            self.draw_text_outline(
                self.screen,
                card.name,
                (card_rect.centerx, card_rect.y + 15),
                self.fonts["small"],
                self.colors["text_light"]
            )
            
            # Card cost
            cost_text = f"Mana: {card.mana_cost}"
            self.draw_text_outline(
                self.screen,
                cost_text,
                (card_rect.centerx, card_rect.y + 35),
                self.fonts["small"],
                self.colors["mana_blue"]
            )
            
            # Card effect
            effect_text = ""
            if card.damage > 0:
                effect_text = f"Damage: {card.damage}"
            elif card.block > 0:
                effect_text = f"Block: {card.block}"
            elif card.heal > 0:
                effect_text = f"Heal: {card.heal}"
                
            if effect_text:
                self.draw_text_outline(
                    self.screen,
                    effect_text,
                    (card_rect.centerx, card_rect.y + 55),
                    self.fonts["small"],
                    self.colors["text_light"]
                )
    
    def _render_status_hud(self):
        """Render status HUD."""
        status_zone = self.zones["status_hud"]
        
        # Player stats
        player_hp = self.player.current_hp
        player_max_hp = self.player.max_hp
        player_mana = self.player.current_mana
        player_max_mana = self.player.max_mana
        
        # Character info
        char_text = f"Character: {self.character_id.title()}"
        self.draw_text_outline(
            self.screen,
            char_text,
            (status_zone.x + 10, status_zone.y + 10),
            self.fonts["medium"],
            self.colors["text_light"]
        )
        
        # HP
        hp_text = f"HP: {player_hp}/{player_max_hp}"
        self.draw_text_outline(
            self.screen,
            hp_text,
            (status_zone.x + 10, status_zone.y + 35),
            self.fonts["medium"],
            self.colors["hp_red"]
        )
        
        # Mana with visual bar
        mana_text = f"Mana: {player_mana}/{player_max_mana}"
        self.draw_text_outline(
            self.screen,
            mana_text,
            (status_zone.x + 10, status_zone.y + 60),
            self.fonts["medium"],
            self.colors["mana_blue"]
        )
        
        # Mana bar
        bar_width = 200
        bar_height = 8
        bar_x = status_zone.x + 10
        bar_y = status_zone.y + 80
        
        # Background
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Fill based on current mana
        if player_max_mana > 0:
            mana_ratio = player_mana / player_max_mana
            fill_width = int(bar_width * mana_ratio)
            pygame.draw.rect(self.screen, self.colors["mana_blue"], (bar_x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, self.colors["border"], (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Block (if any)
        if hasattr(self.player, 'block') and self.player.block > 0:
            block_text = f"Block: {self.player.block}"
            self.draw_text_outline(
                self.screen,
                block_text,
                (status_zone.x + 150, status_zone.y + 35),
                self.fonts["medium"],
                (150, 150, 255)  # Blue for block
            )
        
        # Current biome
        biome_text = f"Biome: {self.biomes[self.current_biome]['name']}"
        self.draw_text_outline(
            self.screen,
            biome_text,
            (status_zone.x + 10, status_zone.y + 105),
            self.fonts["medium"],
            self.colors["text_light"]
        )
    
    def _render_controls(self):
        """Render controls help."""
        controls = [
            "Controls:",
            "← → : Select card",
            "SPACE : Play card",
            "ENTER : End turn",
            "TAB : Switch biome",
            "R : Restart combat",
            "ESC : Back to menu"
        ]
        
        y_start = self.height - len(controls) * 20 - 10
        
        for i, control in enumerate(controls):
            self.draw_text_outline(
                self.screen,
                control,
                (10, y_start + i * 20),
                self.fonts["small"],
                self.colors["text_light"]
            )
    
    def _render_game_over(self):
        """Render game over overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        if self.victory:
            main_text = "VICTORY!"
            sub_text = "You defeated the enemy!"
            color = (0, 255, 0)
        else:
            main_text = "DEFEAT!"
            sub_text = "You have been defeated!"
            color = (255, 0, 0)
        
        # Main text
        self.draw_text_outline(
            self.screen,
            main_text,
            (self.width // 2, self.height // 2 - 50),
            self.fonts["large"],
            color
        )
        
        # Sub text
        self.draw_text_outline(
            self.screen,
            sub_text,
            (self.width // 2, self.height // 2),
            self.fonts["medium"],
            self.colors["text_light"]
        )
        
        # Restart instruction
        restart_text = "Press ENTER to restart or ESC to return to menu"
        self.draw_text_outline(
            self.screen,
            restart_text,
            (self.width // 2, self.height // 2 + 50),
            self.fonts["medium"],
            self.colors["text_light"]
        )
    
    def _render_floating_numbers(self):
        """Render floating damage/heal numbers."""
        current_time = pygame.time.get_ticks()
        
        for float_num in self.float_numbers:
            elapsed = current_time - float_num["start_time"]
            progress = elapsed / float_num["duration"]
            
            # Fade out over time
            alpha = int(255 * (1 - progress))
            color = (*float_num["color"][:3], alpha)
            
            # Create surface with alpha
            text_surface = self.fonts["large"].render(float_num["text"], True, float_num["color"])
            text_surface.set_alpha(alpha)
            
            # Draw at current position
            text_rect = text_surface.get_rect(center=float_num["pos"])
            self.screen.blit(text_surface, text_rect)
    
    def _render_card_animation(self):
        """Render animated card moving to center."""
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
        pygame.draw.rect(self.screen, (255, 215, 0), card_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), card_rect, 2)
        
        # Card name
        card_name = self.card_animation["card"].name
        name_surface = self.fonts["medium"].render(card_name, True, (0, 0, 0))
        name_rect = name_surface.get_rect(center=card_rect.center)
        self.screen.blit(name_surface, name_rect)
    
    def enter_screen(self) -> None:
        """Called when screen becomes active."""
        logger.info(f"Entering MVP Combat Screen with character: {self.character_id}")
        
    def exit_screen(self) -> None:
        """Called when screen becomes inactive."""
        logger.info("Exiting MVP Combat Screen")
