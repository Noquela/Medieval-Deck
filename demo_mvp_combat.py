"""
Demo MVP Combat - Sistema de combate básico com 2 biomas e cards simples

Demonstra:
- 2 biomas (Cathedral, Goblin Cave)
- 3 cartas básicas (Strike, Guard, Heal)
- 3 inimigos (Knight, Goblin, Skeleton)
- Sistema de turnos simples
- Interface minimalista com assets gerados por IA
"""

import pygame
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.config import Config
from src.gameplay.mvp_cards import Card, CardType, Hand
from src.gameplay.mvp_deck import MVPDeck
from src.core.mvp_turn_engine import MVPTurnEngine, MVPPlayer, MVPEnemy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MVPCombatDemo:
    """Demo de combate MVP com assets IA e interface simplificada."""
    
    def __init__(self):
        """Inicializa o demo MVP."""
        pygame.init()
        
        # Config and theme
        self.config = Config()
        
        # Theme colors and fonts
        pygame.font.init()
        self.colors = {
            "background": (25, 20, 15),
            "text_light": (245, 240, 230),
            "border": (100, 100, 100),
            "card_bg": (60, 50, 40),
            "accent": (212, 180, 106),
            "hp_red": (220, 68, 58),
            "mana_blue": (39, 131, 221)
        }
        
        self.fonts = {
            "large": pygame.font.Font(None, 36),
            "medium": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 18)
        }
        
        # Screen setup
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Medieval Deck - MVP Combat Demo")
        
        # Create layout zones
        self.zones = {
            "enemy": pygame.Rect(0, 0, self.screen_width, int(self.screen_height * 0.25)),
            "hand": pygame.Rect(0, int(self.screen_height * 0.8), self.screen_width, int(self.screen_height * 0.2)),
            "status_hud": pygame.Rect(self.screen_width - 280, 20, 260, 120),
            "player": pygame.Rect(int(self.screen_width * 0.1), int(self.screen_height * 0.4), 
                                int(self.screen_width * 0.3), int(self.screen_height * 0.4))
        }
        
        # Clock
        self.clock = pygame.time.Clock()
        
        # Game state
        self.biomes = {
            "cathedral": {
                "name": "Sacred Cathedral",
                "background": self._load_background("bg_cathedral"),
                "enemy_type": "Knight"
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
        
        # Create player and enemy
        self.player = MVPPlayer(max_hp=100, max_mana=3)
        self.enemy = self._create_enemy_for_biome(self.current_biome)
        self.turn_engine = MVPTurnEngine(self.player, self.enemy)
        
        # Start game
        self._start_combat()
    
    def _start_combat(self):
        """Inicia um combate."""
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
        
        logger.info(f"Combat started in {self.biomes[self.current_biome]['name']}")
        logger.info(f"Enemy: {self.enemy.name} ({self.enemy.current_hp} HP)")
        logger.info(f"Hand: {[f'{c.name}({c.mana_cost})' for c in self.hand.cards]}")
    
    def _load_background(self, bg_name: str) -> Optional[pygame.Surface]:
        """Carrega background gerado por IA."""
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
                    return pygame.transform.scale(bg_surface, (self.screen_width, self.screen_height))
            
            logger.warning(f"Background not found for {bg_name}, using fallback")
            return self._create_fallback_background()
            
        except Exception as e:
            logger.error(f"Error loading background {bg_name}: {e}")
            return self._create_fallback_background()
    
    def _create_fallback_background(self) -> pygame.Surface:
        """Cria background de fallback."""
        bg = pygame.Surface((self.screen_width, self.screen_height))
        bg.fill(self.colors["background"])
        return bg
    
    def _create_enemy_for_biome(self, biome_name: str) -> MVPEnemy:
        """Cria um inimigo apropriado para o bioma."""
        if biome_name == "cathedral":
            return MVPEnemy("Knight Guardian", hp=35, attack=8, enemy_type="knight")
        elif biome_name == "goblin_cave":
            return MVPEnemy("Goblin Scout", hp=20, attack=6, enemy_type="goblin")
        else:
            return MVPEnemy("Unknown Enemy", hp=25, attack=7, enemy_type="generic")
    
    def draw_text_outline(self, surface, text, pos, font, color):
        """Desenha texto com contorno."""
        x, y = pos
        # Contorno
        outline_color = (0, 0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    surface.blit(outline_surf, (x + dx, y + dy))
        # Texto principal
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, pos)
    
    def draw_health_bar(self, surface, rect, current, maximum):
        """Desenha barra de vida."""
        # Fundo
        pygame.draw.rect(surface, (100, 50, 50), rect)
        pygame.draw.rect(surface, self.colors["border"], rect, 2)
        
        # Preenchimento
        if maximum > 0:
            fill_width = int((current / maximum) * (rect.width - 4))
            fill_rect = pygame.Rect(rect.x + 2, rect.y + 2, fill_width, rect.height - 4)
            pygame.draw.rect(surface, self.colors["hp_red"], fill_rect)
    
    def _start_combat(self):
        """Inicia um combate."""
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
        
        logger.info(f"Combat started in {self.biomes[self.current_biome]['name']}")
        logger.info(f"Enemy: {self.enemy.name} ({self.enemy.current_hp} HP)")
        logger.info(f"Hand: {[f'{c.name}({c.mana_cost})' for c in self.hand.cards]}")
    
    def handle_events(self) -> bool:
        """Processa eventos. Retorna False para sair."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                    
                elif event.key == pygame.K_TAB:
                    # Switch biomes
                    self.current_biome = "goblin_cave" if self.current_biome == "cathedral" else "cathedral"
                    # Create new enemy for new biome
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
                    if self.hand.cards and self.selected_card_index < len(self.hand.cards):
                        selected_card = self.hand.cards[self.selected_card_index]
                        self._play_card(selected_card)
                        
                elif event.key == pygame.K_RETURN:
                    # End turn
                    self.turn_engine.end_player_turn()
                    logger.info("Player turn ended")
                    
                elif event.key == pygame.K_r:
                    # Restart combat
                    self._start_combat()
                    
        return True
    
    def _play_card(self, card: Card):
        """Joga uma carta."""
        try:
            result = self.turn_engine.play_card(card)
            if result:
                self.hand.remove_card(card)
                # Adjust selection
                if self.selected_card_index >= len(self.hand.cards):
                    self.selected_card_index = max(0, len(self.hand.cards) - 1)
                    
                logger.info(f"Played {card.name}: {result}")
            else:
                logger.warning(f"Could not play {card.name}")
                
        except Exception as e:
            logger.error(f"Error playing card {card.name}: {e}")
    
    def render(self):
        """Renderiza a tela."""
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
        
        pygame.display.flip()
    
    def _render_enemy_zone(self):
        """Renderiza zona do inimigo."""
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
    
    def _render_hand(self):
        """Renderiza mão do jogador."""
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
            
            # Card background (different color if selected)
            if i == self.selected_card_index:
                color = self.colors["accent"]
            else:
                color = self.colors["card_bg"]
            
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
        """Renderiza HUD de status."""
        status_zone = self.zones["status_hud"]
        
        # Player stats
        player_hp = self.player.current_hp
        player_max_hp = self.player.max_hp
        player_mana = self.player.current_mana
        player_max_mana = self.player.max_mana
        
        # HP
        hp_text = f"HP: {player_hp}/{player_max_hp}"
        self.draw_text_outline(
            self.screen,
            hp_text,
            (status_zone.x + 10, status_zone.y + 10),
            self.fonts["medium"],
            self.colors["hp_red"]
        )
        
        # Mana
        mana_text = f"Mana: {player_mana}/{player_max_mana}"
        self.draw_text_outline(
            self.screen,
            mana_text,
            (status_zone.x + 10, status_zone.y + 40),
            self.fonts["medium"],
            self.colors["mana_blue"]
        )
        
        # Current biome
        biome_text = f"Biome: {self.biomes[self.current_biome]['name']}"
        self.draw_text_outline(
            self.screen,
            biome_text,
            (status_zone.x + 10, status_zone.y + 70),
            self.fonts["medium"],
            self.colors["text_light"]
        )
    
    def _render_controls(self):
        """Renderiza controles de ajuda."""
        controls = [
            "Controls:",
            "← → : Select card",
            "SPACE : Play card",
            "ENTER : End turn",
            "TAB : Switch biome",
            "R : Restart combat",
            "ESC : Exit"
        ]
        
        y_start = self.screen_height - len(controls) * 20 - 10
        
        for i, control in enumerate(controls):
            self.draw_text_outline(
                self.screen,
                control,
                (10, y_start + i * 20),
                self.fonts["small"],
                self.colors["text_light"]
            )
    
    def run(self) -> bool:
        """Executa o demo. Retorna True se sucesso."""
        logger.info("Starting MVP Combat Demo")
        logger.info("Generated assets loaded successfully")
        
        running = True
        while running:
            # Events
            running = self.handle_events()
            
            # Render
            self.render()
            
            # Timing
            self.clock.tick(60)
        
        pygame.quit()
        logger.info("MVP Combat Demo ended")
        return True

def main() -> bool:
    """Executa o demo MVP."""
    try:
        demo = MVPCombatDemo()
        return demo.run()
    except Exception as e:
        logger.error(f"Error in MVP Combat Demo: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
