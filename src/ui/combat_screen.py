"""
Medieval Deck - Combat Screen UI Profissional

Interface de combate cinematográfica com design moderno, animações fluidas e integração IA.
Implementa a Fase 4 do roadmap com experiência visual premium.
"""

import pygame
import logging
import math
import time
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from ..core.turn_engine import Player
from ..gameplay.cards import Card, CardType
from ..gameplay.gameplay_engine import GameplayEngine
from ..enemies.smart_enemies import SmartEnemy
from ..enemies.intelligent_combat import IntelligentCombatEngine
from ..ui.theme import UITheme, theme
from ..ui.animation import AnimationManager, EasingType
from ..ui.particles import ParticleSystem, ParticleEmitter, ParticleType
from ..ui.helpers import fit_height, fit_width, create_gradient_surface, draw_outlined_text, apply_glow_effect
from ..components.button import Button
from ..generators.asset_generator import AssetGenerator
from ..utils.asset_loader import AssetLoader
from ..gameplay.animation import animation_manager
from ..utils.sprite_loader import load_character_animations, scale_animation_frames

logger = logging.getLogger(__name__)


class CombatState(Enum):
    """Estados da tela de combate."""
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn" 
    CARD_SELECTION = "card_selection"
    TARGET_SELECTION = "target_selection"
    ANIMATION = "animation"
    VICTORY = "victory"
    DEFEAT = "defeat"
    PAUSED = "paused"


class CombatZone:
    """Representa uma zona de combate com grid para cartas/inimigos."""
    
    def __init__(self, rect: pygame.Rect, grid_size: Tuple[int, int], zone_type: str):
        self.rect = rect
        self.grid_cols, self.grid_rows = grid_size
        self.zone_type = zone_type  # "player" ou "enemy"
        self.slots = []
        self.background_surface = None
        self.border_texture = None
        self._setup_grid()
        
    def _setup_grid(self):
        """Configura o grid de slots da zona."""
        slot_width = (self.rect.width - theme.spacing.MARGIN_LARGE * (self.grid_cols + 1)) // self.grid_cols
        slot_height = (self.rect.height - theme.spacing.MARGIN_MEDIUM * (self.grid_rows + 1)) // self.grid_rows
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.rect.x + theme.spacing.MARGIN_LARGE + col * (slot_width + theme.spacing.MARGIN_LARGE)
                y = self.rect.y + theme.spacing.MARGIN_MEDIUM + row * (slot_height + theme.spacing.MARGIN_MEDIUM)
                
                slot = CombatSlot(x, y, slot_width, slot_height, len(self.slots))
                self.slots.append(slot)


class CombatSlot:
    """Slot individual para carta ou inimigo com animações."""
    
    def __init__(self, x: int, y: int, width: int, height: int, index: int):
        self.base_rect = pygame.Rect(x, y, width, height)
        self.rect = self.base_rect.copy()
        self.index = index
        self.entity = None  # Card ou Enemy
        self.is_hovered = False
        self.is_selected = False
        
        # Animações
        self.hover_offset_y = 0
        self.target_hover_y = 0
        self.glow_alpha = 0
        self.target_glow_alpha = 0
        self.scale = 1.0
        self.target_scale = 1.0
        
        # Estado de animação de tween para centro
        self.tween_active = False
        self.tween_start_pos = None
        self.tween_target_pos = None
        self.tween_progress = 0
        self.tween_duration = 300  # ms
        
    def update(self, dt: float):
        """Atualiza animações do slot."""
        # Animação de hover (y offset)
        if self.is_hovered:
            self.target_hover_y = -15
            self.target_glow_alpha = 255
            self.target_scale = 1.05
        else:
            self.target_hover_y = 0
            self.target_glow_alpha = 0
            self.target_scale = 1.0
            
        # Interpolação suave para hover
        self.hover_offset_y += (self.target_hover_y - self.hover_offset_y) * dt * 8
        self.glow_alpha += (self.target_glow_alpha - self.glow_alpha) * dt * 6
        self.scale += (self.target_scale - self.scale) * dt * 10
        
        # Atualizar posição do rect
        self.rect = self.base_rect.copy()
        self.rect.y += int(self.hover_offset_y)
        
        # Animação de tween para centro (quando carta é jogada)
        if self.tween_active:
            self.tween_progress += dt * 1000  # converter para ms
            progress = min(self.tween_progress / self.tween_duration, 1.0)
            
            # Easing out cubic
            eased_progress = 1 - (1 - progress) ** 3
            
            if self.tween_start_pos and self.tween_target_pos:
                current_x = self.tween_start_pos[0] + (self.tween_target_pos[0] - self.tween_start_pos[0]) * eased_progress
                current_y = self.tween_start_pos[1] + (self.tween_target_pos[1] - self.tween_start_pos[1]) * eased_progress
                self.rect.center = (int(current_x), int(current_y))
                
            if progress >= 1.0:
                self.tween_active = False
                
    def start_center_tween(self, screen_center: Tuple[int, int]):
        """Inicia animação de tween para o centro da tela."""
        self.tween_active = True
        self.tween_start_pos = self.rect.center
        self.tween_target_pos = screen_center
        self.tween_progress = 0
        
    def get_display_rect(self) -> pygame.Rect:
        """Retorna retângulo para desenho considerando escala."""
        if self.scale != 1.0:
            scaled_width = int(self.rect.width * self.scale)
            scaled_height = int(self.rect.height * self.scale)
            scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
            scaled_rect.center = self.rect.center
            return scaled_rect
        return self.rect

class CombatScreen:
    """
    Tela de combate profissional com design cinematográfico.
    
    Funcionalidades avançadas:
    - Background dinâmico com parallax
    - Zonas de combate organizadas em grid
    - Animações fluidas de hover/click
    - Painel de estado flutuante
    - Botões com texturas IA
    - Sistema de partículas
    - Transições suaves entre turnos
    """
    
    def __init__(self, screen: pygame.Surface, combat_engine: IntelligentCombatEngine, 
                 asset_generator: Optional[AssetGenerator] = None):
        """
        Inicializa a tela de combate profissional.
        
        Args:
            screen: Surface principal do pygame
            combat_engine: Engine de combate inteligente
            asset_generator: Gerador de assets IA (opcional)
        """
        self.screen = screen
        self.combat_engine = combat_engine
        self.asset_generator = asset_generator
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Estado da tela
        self.state = CombatState.PLAYER_TURN
        self.running = True
        self.selected_card: Optional[Card] = None
        self.targeted_enemy: Optional[SmartEnemy] = None
        
        # Mouse tracking para parallax
        self.mouse_pos = (0, 0)
        self.last_mouse_pos = (0, 0)
        
        # Sistema de Drag & Drop (P1)
        self.dragging_card = None
        self.drag_start_pos = None
        self.drag_offset = (0, 0)
        self.is_dragging = False
        self.drag_threshold = 5  # pixels mínimos para iniciar drag
        
        # Cartas na mão do jogador (simulação para demo P1)
        self.player_hand = []
        
        # Assets IA carregados
        self.assets = {}
        
        # Inicialização dos componentes
        self._load_ia_assets()
        self._load_sprite_animations()
        
    def get_asset(self, asset_name: str, category: str = None) -> pygame.Surface:
        """
        Busca um asset na estrutura hierárquica.
        
        Args:
            asset_name: Nome do asset ou variante
            category: Categoria específica (opcional)
            
        Returns:
            pygame.Surface do asset encontrado ou None
        """
        # Primeiro, tentar buscar na estrutura hierárquica
        if category and category in self.assets:
            if asset_name in self.assets[category]:
                return self.assets[category][asset_name]
        
        # Buscar em todas as categorias
        for cat_name, assets in self.assets.items():
            if isinstance(assets, dict):
                if asset_name in assets:
                    return assets[asset_name]
                # Tentar buscar por nome parcial
                for variant_name, asset in assets.items():
                    if asset_name in variant_name or variant_name in asset_name:
                        return asset
        
        # Fallback: buscar diretamente (compatibilidade com estrutura antiga)
        if asset_name in self.assets:
            return self.assets[asset_name]
            
        return None
        self._setup_zones()
        self._init_demo_hand()  # Mover para depois de _setup_zones
        self._setup_buttons()
        self._setup_particles()
        self._setup_player_panel()
        self._generate_background()
        
        # Transições e overlays
        self.turn_transition_alpha = 0
        self.turn_transition_active = False
        self.turn_transition_timer = 0
        
        # Sistema de animação P2
        from ..gameplay.animation import animation_manager, load_character_animations, FrameAnimation
        self.animation_manager = animation_manager
        
        # Sprint 2-b: Initialize real-time 30fps animations
        self.player_animation = None
        self.enemy_animations = {}
        self.anim_reset_time = 0
        self._setup_realtime_animations()
        
        # Sprint 2-b: Initialize TurnEngine integration
        from ..core.turn_engine import TurnEngine, Player
        
        # Create player for turn engine
        self.turn_engine_player = Player(max_hp=50, max_mana=10)
        
        # Get enemies from combat engine
        enemies = getattr(self.combat_engine, 'enemies', [])
        
        # Initialize turn engine with proper parameters
        self.turn_engine = TurnEngine(self.turn_engine_player, enemies[:2])  # Limit to 2 enemies for testing
        self._setup_turn_engine_callbacks()
        
        # Sprint 2-b: Enhanced particle system integration
        from ..ui.particles import particle_manager
        self.particle_manager = particle_manager
        
        logger.info("Professional CombatScreen initialized with P2 Animation System")
        
    def _load_ia_assets(self):
        """Carrega todos os assets gerados por IA usando o AssetLoader."""
        try:
            # Usar o novo AssetLoader para carregar assets gerados
            asset_loader = AssetLoader()
            generated_assets = asset_loader.load_all_assets()
            self.assets.update(generated_assets)
            
            # Escalar background para o tamanho da tela
            if "background" in generated_assets.get("background", {}):
                self.background = pygame.transform.smoothscale(
                    generated_assets["background"]["main"], 
                    self.screen.get_size()
                )
            elif "background" in generated_assets.get("background", {}):
                # Fallback para o primeiro background disponível
                bg_variants = generated_assets["background"]
                first_bg = next(iter(bg_variants.values()))
                self.background = pygame.transform.smoothscale(
                    first_bg, 
                    self.screen.get_size()
                )
            else:
                # Criar background fallback se não existir
                self.background = create_gradient_surface(
                    self.screen.get_size(),
                    (40, 35, 25),    # Marrom escuro medieval no topo
                    (20, 15, 10),    # Marrom mais escuro na base
                    255
                )
            
            # Verificar assets carregados na nova estrutura
            asset_categories = generated_assets.keys()
            total_assets = sum(len(category) for category in generated_assets.values())
            
            logger.info(f"Assets IA carregados: {total_assets} assets em {len(asset_categories)} categorias")
            for category, assets in generated_assets.items():
                logger.debug(f"📁 {category}: {len(assets)} assets ({list(assets.keys())})")
            
            # Configurar background de combate
            # Verificar se temos combat_bg na estrutura hierárquica
            combat_bg = self.get_asset("combat_bg", "background")
            if combat_bg:
                self.background_surface = combat_bg
                logger.info("✅ Background de combate configurado")
            
            # Configurar sprites de inimigos da categoria 'sprite'
            self.enemy_sprites = {}
            if 'sprite' in generated_assets:
                for sprite_name, sprite_surface in generated_assets['sprite'].items():
                    if sprite_name != 'player':  # Excluir sprite do jogador
                        self.enemy_sprites[sprite_name] = sprite_surface
                        logger.debug(f"✅ Enemy sprite: {sprite_name}")
            
            # Configurar sprite do jogador
            player_sprite = self.get_asset("knight", "sprite") or self.get_asset("player", "sprite")
            if player_sprite:
                self.player_sprite = player_sprite
                logger.info("✅ Player sprite configurado")
            
        except Exception as e:
            logger.error(f"Erro ao carregar assets IA: {e}")
            # Fallback para assets padrão se necessário
    
    def _load_sprite_animations(self):
        """Carrega sprite sheets de animação para personagens."""
        try:
            # Lista de personagens para carregar
            characters = ["knight", "goblin", "orc", "skeleton", "mage", "dragon"]
            
            # Carregar animações para cada personagem
            loaded_count = 0
            for char_id in characters:
                if load_character_animations(char_id):
                    loaded_count += 1
                    
                    # Escalar animações para tamanhos apropriados
                    if char_id == "knight":  # Jogador
                        target_height = int(self.height * 0.35)
                        scale_animation_frames(char_id, "idle", target_height)
                        scale_animation_frames(char_id, "attack", target_height)
                        scale_animation_frames(char_id, "cast", target_height)
                    else:  # Inimigos
                        target_height = int(300 * 0.7)  # 70% da zona de inimigos
                        scale_animation_frames(char_id, "idle", target_height)
                        scale_animation_frames(char_id, "attack", target_height)
                        scale_animation_frames(char_id, "hurt", target_height)
                        
            logger.info(f"✅ Animações carregadas: {loaded_count}/{len(characters)} personagens")
            
            # Inicializar animações dos personagens ativos
            self._initialize_character_animations()
            
        except Exception as e:
            logger.error(f"Erro ao carregar animações: {e}")
            
    def _initialize_character_animations(self):
        """Inicializa animações para personagens ativos na batalha."""
        try:
            # Jogador sempre usa knight
            animation_manager.play_animation("knight", "idle")
            
            # Inimigos baseados no combat engine
            if hasattr(self.combat_engine, 'enemies'):
                for i, enemy in enumerate(self.combat_engine.enemies):
                    # Mapear tipo de inimigo para ID de animação
                    enemy_type_mapping = {
                        'goblin': 'goblin',
                        'orc': 'orc',
                        'skeleton': 'skeleton',
                        'wizard': 'mage',
                        'dragon': 'dragon'
                    }
                    
                    # Converter enum para string
                    if hasattr(enemy.enemy_type, 'value'):
                        enemy_type_str = enemy.enemy_type.value.lower()
                    elif hasattr(enemy.enemy_type, 'name'):
                        enemy_type_str = enemy.enemy_type.name.lower()
                    else:
                        enemy_type_str = str(enemy.enemy_type).lower()
                        
                    # Usar mapeamento ou fallback para goblin
                    anim_id = enemy_type_mapping.get(enemy_type_str, 'goblin')
                    
                    # Usar índice como ID único para múltiplos inimigos do mesmo tipo
                    unique_id = f"{anim_id}_{i}"
                    
                    # Copiar animações do tipo base para ID único
                    if anim_id in animation_manager.animations:
                        for action, animation in animation_manager.animations[anim_id].items():
                            animation_manager.add_animation(
                                entity_id=unique_id,
                                action=action,
                                frames=animation.frames.copy(),
                                fps=animation.fps,
                                loop=animation.loop
                            )
                    
                    # Iniciar animação idle
                    animation_manager.play_animation(unique_id, "idle")
                    
        except Exception as e:
            logger.error(f"Erro ao inicializar animações de personagens: {e}")
            
    def _setup_realtime_animations(self):
        """Sprint 2-b: Setup 30fps realtime animations for combat."""
        try:
            from ..gameplay.animation import FrameAnimation, load_sprite_sheet
            
            # Load player idle animation (30fps)
            try:
                knight_idle_frames = load_sprite_sheet("assets/ia/knight_idle_sheet.png", 10)
                if knight_idle_frames:
                    self.player_animation = FrameAnimation(knight_idle_frames, fps=30, loop=True)
                    logger.info("✅ Player idle animation loaded (30fps)")
                else:
                    # Fallback: create simple animation
                    self.player_animation = self._create_fallback_animation("player")
                    logger.warning("Using fallback player animation")
            except Exception as e:
                logger.warning(f"Failed to load knight animation: {e}")
                self.player_animation = self._create_fallback_animation("player")
                
            # Load enemy animations
            enemy_types = ["goblin", "orc", "skeleton", "mage"]
            for enemy_type in enemy_types:
                try:
                    enemy_frames = load_sprite_sheet(f"assets/ia/{enemy_type}_idle_sheet.png", 8)
                    if enemy_frames:
                        self.enemy_animations[enemy_type] = FrameAnimation(enemy_frames, fps=30, loop=True)
                        logger.debug(f"✅ {enemy_type} animation loaded")
                    else:
                        self.enemy_animations[enemy_type] = self._create_fallback_animation(enemy_type)
                except Exception as e:
                    logger.debug(f"Failed to load {enemy_type} animation: {e}")
                    self.enemy_animations[enemy_type] = self._create_fallback_animation(enemy_type)
                    
        except Exception as e:
            logger.error(f"Failed to setup realtime animations: {e}")
            
    def _create_fallback_animation(self, entity_type: str):
        """Create simple fallback animation when sprite sheets are not available."""
        try:
            from ..gameplay.animation import FrameAnimation
            
            # Create simple 2-frame animation from static sprites
            if entity_type == "player" and self.player_sprite:
                frame1 = self.player_sprite.copy()
                frame2 = self.player_sprite.copy()
                return FrameAnimation([frame1, frame2], fps=2, loop=True)
            elif entity_type in self.enemy_sprites:
                sprite = list(self.enemy_sprites.values())[0]  # Use first available
                frame1 = sprite.copy()
                frame2 = sprite.copy()
                return FrameAnimation([frame1, frame2], fps=2, loop=True)
            else:
                # Create minimal placeholder
                placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
                placeholder.fill((100, 100, 100, 128))
                return FrameAnimation([placeholder], fps=1, loop=True)
        except Exception as e:
            logger.error(f"Failed to create fallback animation: {e}")
            from ..gameplay.animation import FrameAnimation
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((128, 128, 128))
            return FrameAnimation([placeholder], fps=1, loop=True)
            
    def _setup_turn_engine_callbacks(self):
        """Sprint 2-b: Setup TurnEngine event callbacks."""
        try:
            # TurnEngine already has enemies from initialization
            logger.info("✅ TurnEngine callbacks configured")
        except Exception as e:
            logger.error(f"Failed to setup turn engine callbacks: {e}")
    
    def _setup_zones(self):
        """Configura as zonas de combate seguindo as diretrizes de design."""
        # Zona de inimigos (topo) - 50px de margem, altura 300px
        self.enemy_zone = pygame.Rect(50, 30, self.width - 100, 300)
        
        # Zona da mão do jogador (base) - altura 190px
        self.player_hand_zone = pygame.Rect(50, self.height - 220, self.width - 100, 190)
        
        # Zona de status card (canto superior direito) - 280x150px
        status_width, status_height = 280, 150
        self.status_card_zone = pygame.Rect(
            self.width - status_width - 20,  # 20px margem direita
            20,  # 20px margem superior
            status_width,
            status_height
        )
        
        # Cache dos sprites escalados
        self.enemy_sprites = {}
        self.player_sprite = None
        
        # Carregar e escalar sprites dos inimigos
        self._load_and_scale_enemy_sprites()
        
        # Carregar e escalar sprite do jogador
        self._load_and_scale_player_sprite()
        
    def _load_and_scale_enemy_sprites(self):
        """Carrega e escala sprites melhorados dos inimigos para a zona apropriada."""
        if not hasattr(self.combat_engine, 'enemies'):
            return
            
        max_enemy_height = int(self.enemy_zone.height * 0.7)  # 70% da zona
        
        for i, enemy in enumerate(self.combat_engine.enemies):
            # Mapear tipos de inimigo para sprites melhorados
            enemy_type_mapping = {
                'goblin': 'goblin_sprite_enhanced.png',
                'orc': 'orc_sprite_enhanced.png', 
                'skeleton': 'skeleton_sprite_enhanced.png',
                'wizard': 'dark_mage_sprite_enhanced.png',
                'dark_mage': 'dark_mage_sprite_enhanced.png',
                'dragon': 'dragon_sprite_enhanced.png'
            }
            
            # Fallback para sprites originais se os melhorados não existirem
            enemy_type_fallback = {
                'goblin': 'goblin_scout_sprite',
                'orc': 'orc_berserker_sprite', 
                'skeleton': 'skeleton_archer_sprite',
                'wizard': 'dark_mage_sprite',
                'dragon': 'dragon_sprite'
            }
            
            # Converter enum para string
            if hasattr(enemy.enemy_type, 'value'):
                enemy_type_str = enemy.enemy_type.value.lower()
            elif hasattr(enemy.enemy_type, 'name'):
                enemy_type_str = enemy.enemy_type.name.lower()
            else:
                enemy_type_str = str(enemy.enemy_type).lower()
                
            # Usar índice como ID se não existir
            enemy_id = getattr(enemy, 'id', f"enemy_{i}")
            
            # Tentar carregar sprite melhorado primeiro
            enhanced_sprite_filename = enemy_type_mapping.get(enemy_type_str)
            sprite_loaded = False
            
            if enhanced_sprite_filename:
                enhanced_sprite_path = Path("assets/generated") / enhanced_sprite_filename
                if enhanced_sprite_path.exists():
                    logger.info(f"🎨 Carregando sprite melhorado: {enhanced_sprite_path}")
                    original_sprite = pygame.image.load(str(enhanced_sprite_path)).convert_alpha()
                    scaled_sprite = fit_height(original_sprite, max_enemy_height)
                    self.enemy_sprites[enemy_id] = scaled_sprite
                    sprite_loaded = True
                    logger.info(f"✅ Sprite melhorado carregado para {enemy_type_str}")
            
            # Fallback para sprite original se melhorado não existe
            if not sprite_loaded:
                fallback_sprite_key = enemy_type_fallback.get(enemy_type_str, f"{enemy_type_str}_sprite")
                
                if fallback_sprite_key in self.assets:
                    original_sprite = self.assets[fallback_sprite_key]
                    scaled_sprite = fit_height(original_sprite, max_enemy_height)
                    self.enemy_sprites[enemy_id] = scaled_sprite
                    logger.info(f"✅ Sprite original carregado para {enemy_type_str}: {fallback_sprite_key}")
                else:
                    logger.warning(f"❌ Nenhum sprite encontrado para inimigo: {enemy_type_str}")
                    # Criar sprite placeholder se não existir
                    placeholder = pygame.Surface((80, max_enemy_height), pygame.SRCALPHA)
                    placeholder.fill((100, 0, 0, 150))  # Vermelho translúcido
                    self.enemy_sprites[enemy_id] = placeholder
                
    def _load_and_scale_player_sprite(self):
        """Carrega e escala sprite melhorado e transparente do jogador para 35% da altura da tela."""
        try:
            # Tentar carregar sprite melhorado baseado no personagem
            player = getattr(self.combat_engine, 'player', None)
            character_id = getattr(player, 'character_class', 'knight').lower()
            
            # Verificar sprites melhorados primeiro
            enhanced_sprite_paths = [
                f"assets/generated/{character_id}_sprite_enhanced.png",
                f"assets/generated/{character_id}_transparent.png",
                f"assets/generated/{character_id}_sprite.png"
            ]
            
            for sprite_path in enhanced_sprite_paths:
                if Path(sprite_path).exists():
                    logger.info(f"🎭 Carregando sprite melhorado para combate: {sprite_path}")
                    sprite_image = pygame.image.load(sprite_path).convert_alpha()
                    
                    target_height = int(self.height * 0.35)
                    self.player_sprite = fit_height(sprite_image, target_height)
                    
                    logger.info("✅ Sprite melhorado do personagem carregado para combate")
                    return
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar sprite melhorado: {e}")
        
        # Fallback: usar sprite original se disponível
        player_sprite = self.get_asset("knight", "sprite") or self.get_asset("player", "sprite")
        if player_sprite:
            target_height = int(self.height * 0.35)
            self.player_sprite = fit_height(player_sprite, target_height)
            logger.info("Sprite original carregado como fallback")
        else:
            logger.warning("❌ Nenhum sprite do jogador encontrado")
    
    def _setup_buttons(self):
        """Configura os botões da interface seguindo as diretrizes de design."""
        # Botão End Turn - maior, central-direita, cor roxa tema
        button_width = 180
        button_height = 45
        
        self.end_turn_button = Button(
            x=self.width - 220,  # 220px da borda direita
            y=self.player_hand_zone.top - 60,  # 60px acima da zona da mão
            width=button_width,
            height=button_height,
            text="End Turn",
            on_click=self._end_turn,
            style="medieval"
        )
        
        # Aplicar texturas IA nos botões se disponíveis
        button_texture = self.get_asset("mystical", "button")
        if button_texture:
            scaled_texture = pygame.transform.scale(button_texture, (button_width, button_height))
            self.end_turn_button.textures = {
                "normal": scaled_texture,
                "hover": apply_glow_effect(scaled_texture, (138, 43, 226), 3),  # Roxo
                "pressed": scaled_texture
            }
        
        logger.info("Botões configurados com texturas IA")
        
    def _init_demo_hand(self):
        """Inicializa mão de demonstração com cartas para P2 com CardSprite system."""
        # P2-6: Usar draw_initial_hand em vez de demo estático
        self.draw_initial_hand()
            
    # ========== P2-6: HAND LOGIC ==========
    
    def draw_initial_hand(self):
        """P2-6: Draw initial 5 cards para iniciar o combate."""
        self.player_hand.clear()
        
        # Simular deck de cartas (expandir no futuro)
        available_cards = [
            {"name": "Fireball", "cost": 3, "damage": 4, "type": "spell"},
            {"name": "Sword Strike", "cost": 2, "damage": 3, "type": "attack"},
            {"name": "Heal", "cost": 2, "heal": 3, "type": "heal"},
            {"name": "Lightning Bolt", "cost": 4, "damage": 5, "type": "spell"},
            {"name": "Shield Block", "cost": 1, "defense": 2, "type": "defense"},
            {"name": "Ice Shard", "cost": 2, "damage": 2, "type": "spell"},
            {"name": "Power Strike", "cost": 3, "damage": 4, "type": "attack"},
            {"name": "Minor Heal", "cost": 1, "heal": 2, "type": "heal"}
        ]
        
        # Draw 5 cartas aleatórias
        import random
        selected_cards = random.sample(available_cards, min(5, len(available_cards)))
        
        for i, card_data in enumerate(selected_cards):
            self._add_card_to_hand(card_data, i)
            
        logger.info(f"P2-6: Drew initial hand of {len(self.player_hand)} cards")
        
    def draw_card_from_deck(self, animate=True):
        """Sprint 2: Draw a single card from deck with animation."""
        if len(self.player_hand) >= 10:  # Max hand size
            logger.warning("Hand is full, cannot draw card")
            return None
            
        available_cards = [
            {"name": "Fireball", "cost": 3, "damage": 4, "type": "spell"},
            {"name": "Sword Strike", "cost": 2, "damage": 3, "type": "attack"},
            {"name": "Heal", "cost": 2, "heal": 3, "type": "heal"},
            {"name": "Lightning Bolt", "cost": 4, "damage": 5, "type": "spell"},
            {"name": "Shield Block", "cost": 1, "defense": 2, "type": "defense"},
            {"name": "Ice Shard", "cost": 2, "damage": 2, "type": "spell"},
            {"name": "Power Strike", "cost": 3, "damage": 4, "type": "attack"},
            {"name": "Minor Heal", "cost": 1, "heal": 2, "type": "heal"}
        ]
        
        import random
        new_card = random.choice(available_cards)
        position = len(self.player_hand)
        
        self._add_card_to_hand(new_card, position)
        self._reorganize_hand()  # Reposition all cards
        
        logger.info(f"Drew {new_card['name']} from deck")
        return new_card
        
    def discard_card(self, card_index: int, animate=True):
        """Sprint 2: Discard a card from hand with animation."""
        if card_index < 0 or card_index >= len(self.player_hand):
            logger.warning(f"Invalid card index for discard: {card_index}")
            return False
            
        discarded_card = self.player_hand.pop(card_index)
        
        # Trigger discard animation if card has sprite
        if animate and discarded_card.get("sprite"):
            # Could add discard animation here
            pass
            
        self._reorganize_hand()  # Reposition remaining cards
        
        logger.info(f"Discarded {discarded_card['data']['name']}")
        return True
        
    def _reorganize_hand(self):
        """Sprint 2: Reorganize hand positions after draw/discard."""
        for i, card in enumerate(self.player_hand):
            slot_width = self.player_hand_zone.width // max(5, len(self.player_hand))
            slot_x = self.player_hand_zone.left + i * slot_width + 10
            slot_y = self.player_hand_zone.top + 10
            
            # Update card position
            card["original_pos"] = (slot_x, slot_y)
            card["slot_index"] = i
            card["rect"].x = slot_x
            card["rect"].y = slot_y
            
            # Update sprite position if available
            if card.get("sprite"):
                card["sprite"].set_position((slot_x, slot_y))
                
    def get_hand_size(self) -> int:
        """Sprint 2: Get current hand size."""
        return len(self.player_hand)
        
    def can_play_card(self, card_index: int) -> bool:
        """Sprint 2: Check if a card can be played (mana cost, etc)."""
        if card_index < 0 or card_index >= len(self.player_hand):
            return False
            
        card = self.player_hand[card_index]
        card_cost = card["data"].get("cost", 0)
        
        return self.turn_engine.player.mana >= card_cost
        
    def _add_card_to_hand(self, card_data: dict, position: int):
        """P2-6: Adiciona uma carta na mão na posição especificada com CardSprite."""
        slot_width = self.player_hand_zone.width // 5
        slot_height = self.player_hand_zone.height - 20
        
        slot_x = self.player_hand_zone.left + position * slot_width + 10
        slot_y = self.player_hand_zone.top + 10
        
        # P2: Criar CardSprite para animações avançadas
        from .card_sprite import CardSprite
        card_sprite = None
        try:
            # Sprint 2: Create card surface without text to avoid duplication
            card_surface = self._create_card_surface(card_data, slot_width - 20, slot_height, include_text=False)
            card_sprite = CardSprite(card_surface, (slot_x, slot_y))  # Posição como tupla
        except Exception as e:
            logger.warning(f"Failed to create CardSprite: {e}")
        
        card = {
            "data": card_data,
            "rect": pygame.Rect(slot_x, slot_y, slot_width - 20, slot_height),
            "original_pos": (slot_x, slot_y),
            "is_hovered": False,
            "is_selected": False,
            "slot_index": position,
            # P2: CardSprite integration
            "sprite": card_sprite,
            # P2: Propriedades de animação aprimoradas (fallback)
            "hover_offset_y": 0,
            "target_hover_y": 0,
            "scale": 1.0,
            "target_scale": 1.0,
            "glow_alpha": 0,
            "target_glow_alpha": 0,
            "rotation": 0,
            "target_rotation": 0,
            "animation_time": 0,
            "bob_offset": position * 0.5,
            # P2: Card draw animation
            "draw_animation": True,
            "draw_progress": 0.0
        }
        self.player_hand.append(card)
        
    def _create_card_surface(self, card_data: dict, width: int, height: int, include_text: bool = True) -> pygame.Surface:
        """P2: Cria surface visual para carta."""
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Background da carta
        card_color = {
            "spell": (120, 80, 200),     # Roxo para spells
            "attack": (200, 80, 80),     # Vermelho para ataques
            "heal": (80, 200, 120),      # Verde para cura
            "defense": (80, 120, 200)    # Azul para defesa
        }.get(card_data.get("type", "spell"), (150, 150, 150))
        
        # Desenhar background com gradiente simples
        pygame.draw.rect(surface, card_color, surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), width=2, border_radius=8)
        
        # Sprint 2: Only include text if requested (for CardSprite, we skip text to avoid duplication)
        if include_text and hasattr(pygame, 'font') and pygame.font.get_init():
            font = pygame.font.Font(None, 24)
            text = font.render(card_data["name"], True, (255, 255, 255))
            text_rect = text.get_rect(centerx=width//2, y=10)
            surface.blit(text, text_rect)
            
            # Renderizar cost/damage
            info_font = pygame.font.Font(None, 20)
            cost_text = info_font.render(f"Cost: {card_data.get('cost', 0)}", True, (255, 255, 255))
            surface.blit(cost_text, (5, height - 40))
            
            if "damage" in card_data:
                dmg_text = info_font.render(f"Dmg: {card_data['damage']}", True, (255, 255, 255))
                surface.blit(dmg_text, (5, height - 20))
            elif "heal" in card_data:
                heal_text = info_font.render(f"Heal: {card_data['heal']}", True, (255, 255, 255))
                surface.blit(heal_text, (5, height - 20))
        
        return surface
        
    def discard_card(self, card: dict):
        """P2-6: Descarta uma carta da mão."""
        if card in self.player_hand:
            self.player_hand.remove(card)
            self._reorganize_hand()
            logger.info(f"P2-6: Discarded {card['data']['name']}")
            
    def draw_card(self) -> bool:
        """P2-6: Compra uma carta se há espaço na mão (máx 5)."""
        if len(self.player_hand) >= 5:
            logger.warning("P2-6: Cannot draw card - hand is full")
            return False
            
        # Simular draw de carta aleatória
        available_cards = [
            {"name": "Fireball", "cost": 3, "damage": 4, "type": "spell"},
            {"name": "Sword Strike", "cost": 2, "damage": 3, "type": "attack"},
            {"name": "Heal", "cost": 2, "heal": 3, "type": "heal"},
            {"name": "Lightning Bolt", "cost": 4, "damage": 5, "type": "spell"},
            {"name": "Shield Block", "cost": 1, "defense": 2, "type": "defense"}
        ]
        
        import random
        new_card = random.choice(available_cards)
        self._add_card_to_hand(new_card, len(self.player_hand))
        
        logger.info(f"P2-6: Drew {new_card['name']} (hand size: {len(self.player_hand)})")
        return True
        
    def end_turn_draw(self):
        """P2-6: Compra carta no final do turno se há espaço."""
        self.draw_card()
        
    def _setup_particles(self):
        """Configura o sistema de partículas."""
        self.particle_system = ParticleSystem()
        
        # Configurar emissores para diferentes efeitos
        # Criar emissor simples para efeitos de dano (será atualizado dinamicamente)
        self.damage_emitter = ParticleEmitter(
            x=0, y=0,  # Posição será atualizada dinamicamente
            width=50, height=50,  # Área de emissão
            particle_type=ParticleType.GOLDEN_SPARKS,  # Usar tipo que existe
            emission_rate=10.0,
            max_particles=50
        )
        
    def _setup_player_panel(self):
        """Configura o painel flutuante de estado do jogador."""
        panel_width = 300
        panel_height = 80
        
        # Posição centralizada na parte inferior
        self.player_panel_rect = pygame.Rect(
            (self.width - panel_width) // 2,
            self.height - panel_height - theme.spacing.MARGIN_SMALL,
            panel_width,
            panel_height
        )
        
        # Criar surface do painel com alpha
        self.player_panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
    def _generate_background(self):
        """Gera background dinâmico baseado no tipo de inimigo predominante e personagem."""
        try:
            # 1. Primeiro, verificar se há inimigos específicos para usar seu background
            enemy_background = self._get_enemy_specific_background()
            if enemy_background:
                self.background = enemy_background
                logger.info("✅ Background específico do inimigo carregado para combate")
                return
            
            # 2. Fallback: usar background do personagem selecionado
            character_background = self._get_character_background()
            if character_background:
                self.background = character_background
                logger.info("✅ Background do personagem carregado para combate")
                return
                
            # 3. Último fallback: background genérico
            self._create_fallback_background()
            logger.info("Background fallback criado para combate")
            
        except Exception as e:
            logger.error(f"Erro ao gerar background: {e}")
            self._create_fallback_background()
    
    def _get_enemy_specific_background(self):
        """Obtém background específico baseado no tipo de inimigo predominante."""
        if not hasattr(self.combat_engine, 'enemies') or not self.combat_engine.enemies:
            return None
            
        # Mapear tipos de inimigo para backgrounds específicos
        enemy_bg_mapping = {
            'goblin': 'combat_bg_goblin_cave.png',
            'orc': 'combat_bg_orc_camp.png', 
            'skeleton': 'combat_bg_skeleton_crypt.png',
            'dragon': 'combat_bg_dragon_lair.png',
            'wizard': 'combat_bg_dark_tower.png',
            'dark_mage': 'combat_bg_dark_tower.png'
        }
        
        # Contar tipos de inimigos para encontrar o predominante
        enemy_counts = {}
        for enemy in self.combat_engine.enemies:
            # Converter enum para string
            if hasattr(enemy.enemy_type, 'value'):
                enemy_type_str = enemy.enemy_type.value.lower()
            elif hasattr(enemy.enemy_type, 'name'):
                enemy_type_str = enemy.enemy_type.name.lower()
            else:
                enemy_type_str = str(enemy.enemy_type).lower()
                
            enemy_counts[enemy_type_str] = enemy_counts.get(enemy_type_str, 0) + 1
        
        # Encontrar tipo predominante
        if enemy_counts:
            predominant_type = max(enemy_counts, key=enemy_counts.get)
            bg_filename = enemy_bg_mapping.get(predominant_type)
            
            if bg_filename:
                bg_path = Path("assets/generated") / bg_filename
                if bg_path.exists():
                    logger.info(f"🎨 Carregando background do inimigo: {bg_path}")
                    background = pygame.image.load(str(bg_path)).convert()
                    
                    # Redimensionar para fit screen
                    if background.get_size() != (self.width, self.height):
                        background = pygame.transform.scale(background, (self.width, self.height))
                    
                    # Aplicar overlay sutil para atmosfera de combate
                    overlay = pygame.Surface((self.width, self.height))
                    overlay.set_alpha(60)  # Overlay mais sutil
                    overlay.fill((80, 0, 0))  # Tom avermelhado para combate
                    background.blit(overlay, (0, 0))
                    
                    return background
        
        return None
    
    def _get_character_background(self):
        """Obtém background específico do personagem selecionado."""
        try:
            # Obter player através do combat_engine
            player = getattr(self.combat_engine, 'player', None)
            character_id = getattr(player, 'character_class', 'knight').lower()
            
            # Verificar backgrounds melhorados dos personagens (novos backgrounds únicos)
            character_bg_paths = [
                f"assets/generated/{character_id}_bg_throne_room.png" if character_id == "knight" else None,
                f"assets/generated/{character_id}_bg_sanctum.png" if character_id == "wizard" else None,
                f"assets/generated/{character_id}_bg_lair.png" if character_id == "assassin" else None,
                f"assets/generated/{character_id}_bg_hd_3440x1440.png",
                f"assets/generated/{character_id}_bg.png"
            ]
            
            # Filtrar None values
            character_bg_paths = [path for path in character_bg_paths if path]
            
            for bg_path in character_bg_paths:
                if Path(bg_path).exists():
                    logger.info(f"🎨 Carregando background do personagem: {bg_path}")
                    background = pygame.image.load(bg_path).convert()
                    
                    # Redimensionar para fit screen se necessário
                    if background.get_size() != (self.width, self.height):
                        background = pygame.transform.scale(background, (self.width, self.height))
                    
                    # Aplicar overlay sutil para atmosfera de combate
                    overlay = pygame.Surface((self.width, self.height))
                    overlay.set_alpha(40)  # Overlay bem sutil para personagem
                    overlay.fill((60, 60, 60))  # Tom neutro
                    background.blit(overlay, (0, 0))
                    
                    return background
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar background do personagem: {e}")
        
        return None
    
    def _create_fallback_background(self):
        """Cria background fallback se nenhum específico for encontrado."""
        # Fallback: tentar background genérico
        if "combat_bg" in self.assets:
            self.background = self.assets["combat_bg"]
            # Redimensionar para fit screen se necessário
            if self.background.get_size() != (self.width, self.height):
                self.background = pygame.transform.scale(self.background, (self.width, self.height))
        else:
            # Criar background placeholder melhorado
            self.background = pygame.Surface((self.width, self.height))
            
            # Gradiente medieval escuro
            for y in range(self.height):
                progress = y / self.height
                # Cores mais ricas para combate
                r = int(40 + progress * 20)  # Vermelho base
                g = int(30 + progress * 15)  # Verde sutil
                b = int(20 + progress * 25)  # Azul para profundidade
                color = (r, g, b)
                pygame.draw.line(self.background, color, (0, y), (self.width, y))
    
    def update(self, dt: float):
        """
        Atualiza todos os componentes da tela de combate.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar posição do mouse para parallax
        self.last_mouse_pos = self.mouse_pos
        self.mouse_pos = pygame.mouse.get_pos()
        
        # Atualizar sistema de animações
        animation_manager.update(dt)
        
        # Sprint 2-b: Update 30fps realtime animations
        if self.player_animation:
            self.player_animation.update(dt)
        
        for enemy_anim in self.enemy_animations.values():
            enemy_anim.update(dt)
            
        # Sprint 2-b: Handle animation reset after attack
        if hasattr(self, 'anim_reset_time') and self.anim_reset_time > 0:
            self.anim_reset_time -= dt * 1000  # Convert to milliseconds
            if self.anim_reset_time <= 0:
                # Reset to idle animation
                try:
                    from ..gameplay.animation import FrameAnimation, load_sprite_sheet
                    knight_idle_frames = load_sprite_sheet("assets/ia/knight_idle_sheet.png", 10)
                    if knight_idle_frames:
                        self.player_animation = FrameAnimation(knight_idle_frames, fps=30, loop=True)
                    self.anim_reset_time = 0
                except Exception as e:
                    logger.warning(f"Failed to reset player animation: {e}")
        
        # Sprint 2-b: Update particle system
        if hasattr(self, 'particle_manager'):
            self.particle_manager.update(dt)
        
        # P2: Atualizar animation manager integrado
        if hasattr(self, 'animation_manager'):
            self.animation_manager.update(dt)
        
        # Atualizar botões
        if hasattr(self, 'end_turn_button'):
            self.end_turn_button.update(dt)
        
        # P1: Atualizar animações das cartas
        self._update_card_animations(dt)
        
        # Atualizar transições de turno
        if self.turn_transition_active:
            self.turn_transition_timer += dt
            # Animação de fade in/out: 0->0.5->0 em 400ms
            progress = self.turn_transition_timer / 0.4  # 400ms
            if progress <= 0.5:
                self.turn_transition_alpha = int(255 * progress * 2)  # 0 to 255 in first half
            elif progress <= 1.0:
                self.turn_transition_alpha = int(255 * (2 - progress * 2))  # 255 to 0 in second half
            else:
                self.turn_transition_active = False
                self.turn_transition_alpha = 0
                self.turn_transition_timer = 0
        
        # Atualizar estado do combate
        self._update_combat_state()
        
    def _update_card_animations(self, dt: float):
        """Atualiza animações avançadas das cartas - P1 implementação."""
        for card in self.player_hand:
            # Atualizar timer de animação
            card["animation_time"] += dt
            
            # Efeito de "breathing" sutil para cartas não interagidas
            if not card["is_hovered"] and not card["is_selected"] and not self.is_dragging:
                bob_amplitude = 2.0  # pixels
                bob_speed = 1.5 + card["bob_offset"]  # Velocidade ligeiramente diferente para cada carta
                card["target_hover_y"] = math.sin(card["animation_time"] * bob_speed) * bob_amplitude
            
            # Animações de hover
            if card["is_hovered"] and not self.is_dragging:
                card["target_hover_y"] = -15  # Subir carta
                card["target_scale"] = 1.08   # Escalar ligeiramente
                card["target_glow_alpha"] = 100  # Brilho sutil
                card["target_rotation"] = math.sin(card["animation_time"] * 3) * 1.5  # Leve oscilação
            elif card["is_selected"]:
                card["target_hover_y"] = -10
                card["target_scale"] = 1.05
                card["target_glow_alpha"] = 150
                card["target_rotation"] = 0
            else:
                # Reset para estado normal
                if not card.get("breathing_active", True):  # Manter breathing se não estiver interagindo
                    card["target_hover_y"] = 0
                card["target_scale"] = 1.0
                card["target_glow_alpha"] = 0
                card["target_rotation"] = 0
            
            # Suavização das animações (interpolação exponencial)
            smooth_factor = 8.0
            card["hover_offset_y"] += (card["target_hover_y"] - card["hover_offset_y"]) * dt * smooth_factor
            card["scale"] += (card["target_scale"] - card["scale"]) * dt * smooth_factor
            card["glow_alpha"] += (card["target_glow_alpha"] - card["glow_alpha"]) * dt * smooth_factor
            card["rotation"] += (card["target_rotation"] - card["rotation"]) * dt * smooth_factor
            
            # Atualizar posição da carta baseada nas animações
            original_x, original_y = card["original_pos"]
            card["rect"].x = original_x
            card["rect"].y = original_y + int(card["hover_offset_y"])
        
    def _update_combat_state(self):
        """Atualiza o estado interno do combate."""
        # Verificar se combate terminou
        if hasattr(self.combat_engine, 'is_game_over') and self.combat_engine.is_game_over():
            if hasattr(self.combat_engine, 'is_victory') and self.combat_engine.is_victory():
                self.state = CombatState.VICTORY
            else:
                self.state = CombatState.DEFEAT
                
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos da tela de combate.
        
        Args:
            event: Evento do pygame
            
        Returns:
            String de ação se alguma ação deve ser executada, None caso contrário
        """
        # Check for combat end states
        if self.state == CombatState.VICTORY:
            return "victory"
        elif self.state == CombatState.DEFEAT:
            return "defeat"
            
        if event.type == pygame.QUIT:
            self.running = False
            return "exit"
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == CombatState.CARD_SELECTION:
                    self._cancel_card_selection()
                elif self.state == CombatState.TARGET_SELECTION:
                    self._cancel_target_selection()
                elif self.state == CombatState.PAUSED:
                    return "exit"
                else:
                    self.state = CombatState.PAUSED
                return None
                
            elif event.key == pygame.K_SPACE:
                if self.state == CombatState.PLAYER_TURN:
                    self._end_turn()
                return None
                
            elif event.key == pygame.K_p:
                self._toggle_pause()
                return None
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_left_click(event.pos)
                return None
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
                return None
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                self._handle_left_click_release(event.pos)
                return None
                
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            
        return None
        
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Processa clique esquerdo na interface - P1 drag & drop implementado."""
        x, y = pos
        
        # Verificar clique nos botões primeiro
        if self.end_turn_button.rect.collidepoint(x, y):
            if self.state == CombatState.PLAYER_TURN:
                self._end_turn()
            return
            
        # P1: Verificar clique em cartas da mão para iniciar drag
        if self.state == CombatState.PLAYER_TURN and self.player_hand_zone.collidepoint(x, y):
            clicked_card = self._get_card_at_position(pos)
            if clicked_card:
                self._start_drag(clicked_card, pos)
            return
                    
        # Verificar clique nos sprites de inimigos (para targeting)
        if self.state == CombatState.TARGET_SELECTION and hasattr(self.combat_engine, 'enemies'):
            # TODO: Implementar targeting de inimigos
            pass
                    
    def _handle_right_click(self, pos: Tuple[int, int]):
        """Processa clique direito (cancelar seleções)."""
        if self.state == CombatState.CARD_SELECTION:
            self._cancel_card_selection()
        elif self.state == CombatState.TARGET_SELECTION:
            self._cancel_target_selection()
            
    def _handle_mouse_motion(self, pos: Tuple[int, int]):
        """Processa movimento do mouse - P1 drag & drop e hover effects."""
        x, y = pos
        
        # Armazenar posição do mouse para futuros efeitos de hover
        self.mouse_pos = pos
        
        # P1: Processar drag se estiver arrastando uma carta
        if self.is_dragging and self.dragging_card:
            self._update_drag(pos)
        else:
            # Processar hover effects nas cartas
            self._update_card_hover(pos)
        
    def _select_card(self, slot: CombatSlot):
        """Seleciona uma carta para uso."""
        self.selected_card = slot.entity
        self.state = CombatState.CARD_SELECTION
        
        # Iniciar animação de tween para centro
        screen_center = (self.width // 2, self.height // 2)
        slot.start_center_tween(screen_center)
        
        # Se a carta não precisa de target, usar imediatamente
        if hasattr(self.selected_card, 'needs_target') and not self.selected_card.needs_target:
            self._use_card_no_target()
        else:
            self.state = CombatState.TARGET_SELECTION
            
    def _target_enemy(self, slot: CombatSlot):
        """Seleciona um inimigo como alvo."""
        if self.selected_card and self.state == CombatState.TARGET_SELECTION:
            self.targeted_enemy = slot.entity
            self._use_card_with_target(slot)
            
    def _use_card_no_target(self):
        """Usa carta que não precisa de alvo."""
        if self.selected_card:
            # Aplicar efeito da carta
            self._apply_card_effect(self.selected_card, None)
            self._finish_card_use()
            
    def _use_card_with_target(self, target_slot: CombatSlot):
        """Usa carta com alvo específico."""
        if self.selected_card and self.targeted_enemy:
            # P2: Disparar partículas de ataque no alvo
            self._trigger_attack_particles(target_slot.rect.center)
            
            # P2: Trigger animação de ataque do jogador
            self.animation_manager.play_animation("knight", "attack", force_restart=True)
            
            # P2: Trigger animação de hurt do inimigo alvo
            target_index = self.combat_engine.enemies.index(self.targeted_enemy)
            enemy_anim_id = f"{self._get_enemy_anim_id(self.targeted_enemy)}_{target_index}"
            self.animation_manager.play_animation(enemy_anim_id, "hurt", force_restart=True)
            
            # Aplicar efeito da carta
            self._apply_card_effect(self.selected_card, self.targeted_enemy)
            self._finish_card_use()
            
    def _apply_card_effect(self, card: Card, target):
        """
        Aplica o efeito da carta no combate.
        Sprint 2: Enhanced with particle effects and TurnEngine integration.
        """
        try:
            # Get card data from player hand
            card_data = None
            for hand_card in self.player_hand:
                if hand_card.get("selected") or hand_card == card:
                    card_data = hand_card.get("data", {})
                    break
                    
            if not card_data:
                # Fallback: try to get data from card object
                card_data = getattr(card, '__dict__', {})
            
            # Sprint 2-b: Enhanced TurnEngine integration with particles and animations
            if target:  # Card targets an enemy
                target_pos = self._get_target_position(target)
                
                # Apply damage with particle effects
                if card_data.get("damage"):
                    damage = card_data["damage"]
                    
                    # Sprint 2-b: Trigger attack animation
                    self._trigger_attack_animation(card_data.get("type", "attack"))
                    
                    # Apply damage through TurnEngine
                    actual_damage = self.turn_engine.apply_damage(
                        target, damage, 
                        particle_emitter=getattr(self, 'particle_manager', None),
                        target_pos=target_pos
                    )
                    
                    # Sprint 2-b: Spawn hit particles
                    if hasattr(self, 'particle_manager'):
                        self.particle_manager.spawn_hit_particles(target_pos, count=15)
                    
                    logger.info(f"Card dealt {actual_damage} damage to {getattr(target, 'name', 'target')}")
                    
            else:  # Card affects player
                player_pos = (400, 300)  # Default player position
                
                # Apply healing with particle effects
                if card_data.get("heal"):
                    heal_amount = card_data["heal"]
                    
                    # Sprint 2-b: Trigger heal animation
                    self._trigger_heal_animation()
                    
                    actual_healing = self.turn_engine.apply_healing(
                        self.turn_engine.player, heal_amount,
                        particle_emitter=getattr(self, 'particle_manager', None),
                        target_pos=player_pos
                    )
                    
                    # Sprint 2-b: Spawn heal particles
                    if hasattr(self, 'particle_manager'):
                        heal_emitter = self.particle_manager.emitters[0] if self.particle_manager.emitters else None
                        if heal_emitter:
                            heal_emitter.emit_heal(count=8)
                    
                    logger.info(f"Card healed player for {actual_healing} HP")
                    
            # Deduct mana cost
            if card_data.get("cost"):
                cost = card_data["cost"]
                self.turn_engine.player.mana = max(0, self.turn_engine.player.mana - cost)
                logger.debug(f"Spent {cost} mana, remaining: {self.turn_engine.player.mana}")
            
            # Fallback to combat engine if available
            if hasattr(self.combat_engine, 'use_card'):
                self.combat_engine.use_card(card, target)
                
        except Exception as e:
            logger.error(f"Failed to apply card effect: {e}")
            
    def _get_target_position(self, target) -> Tuple[int, int]:
        """Sprint 2: Get screen position for a target entity."""
        try:
            # Try to find target in enemy slots
            if hasattr(self, 'enemy_slots') and hasattr(self.combat_engine, 'enemies'):
                for i, enemy in enumerate(self.combat_engine.enemies):
                    if enemy == target and i < len(self.enemy_slots):
                        slot = self.enemy_slots[i]
                        return slot.rect.center
                        
            # Default enemy position
            return (600, 200)
        except Exception as e:
            logger.warning(f"Failed to get target position: {e}")
            return (600, 200)
            
    def _trigger_attack_animation(self, card_type: str = "attack"):
        """Sprint 2-b: Trigger player attack animation with auto-reset."""
        try:
            from ..gameplay.animation import FrameAnimation, load_sprite_sheet
            
            # Load attack animation based on card type
            if card_type in ["spell", "magic"]:
                # Use cast animation for spells
                attack_frames = load_sprite_sheet("assets/ia/knight_cast_sheet.png", 8)
                reset_duration = 250  # 250ms for cast
            else:
                # Use attack animation for physical attacks
                attack_frames = load_sprite_sheet("assets/ia/knight_attack_sheet.png", 8)
                reset_duration = 300  # 300ms for attack
                
            if attack_frames:
                self.player_animation = FrameAnimation(attack_frames, fps=30, loop=False)
                self.anim_reset_time = reset_duration  # Auto-reset to idle
                logger.debug(f"Triggered {card_type} animation")
            else:
                logger.warning(f"No animation frames found for {card_type}")
                
        except Exception as e:
            logger.warning(f"Failed to trigger attack animation: {e}")
            
    def _trigger_heal_animation(self):
        """Sprint 2-b: Trigger player heal animation."""
        try:
            from ..gameplay.animation import FrameAnimation, load_sprite_sheet
            
            # Try to load heal/cast animation
            heal_frames = load_sprite_sheet("assets/ia/knight_cast_sheet.png", 8)
            if heal_frames:
                self.player_animation = FrameAnimation(heal_frames, fps=30, loop=False)
                self.anim_reset_time = 250  # Auto-reset to idle after 250ms
                logger.debug("Triggered heal animation")
            else:
                logger.warning("No heal animation frames found")
                
        except Exception as e:
            logger.warning(f"Failed to trigger heal animation: {e}")
            
    def _finish_card_use(self):
        """Finaliza o uso da carta."""
        self.selected_card = None
        self.targeted_enemy = None
        self.state = CombatState.PLAYER_TURN
        
        # Repovoar zonas para refletir mudanças
        self._populate_zones()
        
    def _trigger_damage_particles(self, position: Tuple[int, int]):
        """Dispara partículas de dano na posição especificada."""
        self.damage_emitter.position = position
        self.particle_system.add_emitter(self.damage_emitter)
        
    def _trigger_attack_particles(self, position: Tuple[int, int]):
        """P2: Dispara partículas de ataque com efeitos aprimorados."""
        if hasattr(self, 'particle_system'):
            # Usar o novo sistema P2 de partículas
            self.particle_system.emit_impact(position)
            self.particle_system.emit_damage(position)
        else:
            # Fallback para sistema antigo
            self._trigger_damage_particles(position)
            
    def _get_enemy_anim_id(self, enemy) -> str:
        """P2: Retorna ID de animação baseado no tipo do inimigo."""
        if hasattr(enemy, 'enemy_type'):
            return enemy.enemy_type.lower()
        elif hasattr(enemy, 'type'):
            return enemy.type.lower()
        else:
            return "goblin"  # Fallback padrão
        
    def _cancel_card_selection(self):
        """Cancela seleção de carta."""
        self.selected_card = None
        self.state = CombatState.PLAYER_TURN
        
    def _cancel_target_selection(self):
        """Cancela seleção de alvo."""
        self.targeted_enemy = None
        self.state = CombatState.CARD_SELECTION
        
    # ========== P1 DRAG & DROP SYSTEM ==========
    
    def _get_card_at_position(self, pos: Tuple[int, int]) -> Optional[dict]:
        """Retorna a carta na posição especificada."""
        for card in self.player_hand:
            if card["rect"].collidepoint(pos):
                return card
        return None
        
    def _start_drag(self, card: dict, pos: Tuple[int, int]):
        """Inicia o drag de uma carta."""
        self.dragging_card = card
        self.drag_start_pos = pos
        self.is_dragging = False  # Só ativa após mover além do threshold
        
        # Calcular offset do mouse relativo ao centro da carta
        card_center = card["rect"].center
        self.drag_offset = (pos[0] - card_center[0], pos[1] - card_center[1])
        
        # Marcar carta como selecionada visualmente
        card["is_selected"] = True
        
    def _update_drag(self, pos: Tuple[int, int]):
        """Atualiza a posição da carta sendo arrastada."""
        if not self.dragging_card or not self.drag_start_pos:
            return
            
        # Verificar se passou do threshold para iniciar drag
        if not self.is_dragging:
            distance = ((pos[0] - self.drag_start_pos[0])**2 + (pos[1] - self.drag_start_pos[1])**2)**0.5
            if distance >= self.drag_threshold:
                self.is_dragging = True
                self.state = CombatState.CARD_SELECTION
                
        # Atualizar posição da carta (ajustando pelo offset)
        if self.is_dragging:
            new_x = pos[0] - self.drag_offset[0] - self.dragging_card["rect"].width // 2
            new_y = pos[1] - self.drag_offset[1] - self.dragging_card["rect"].height // 2
            self.dragging_card["rect"].x = new_x
            self.dragging_card["rect"].y = new_y
            
    def _handle_left_click_release(self, pos: Tuple[int, int]):
        """Processa soltar o botão esquerdo - finaliza drag & drop."""
        if self.is_dragging and self.dragging_card:
            self._end_drag(pos)
        elif self.dragging_card:
            # Foi um clique simples, não drag - selecionar carta
            self._select_card_simple(self.dragging_card)
            
        # Reset drag state
        self._reset_drag_state()
        
    def _end_drag(self, pos: Tuple[int, int]):
        """Finaliza o drag e verifica onde a carta foi solta."""
        if not self.dragging_card:
            return
            
        # Verificar se foi solta numa zona válida
        if self.enemy_zone.collidepoint(pos):
            # Carta solta na zona de inimigos - iniciar targeting
            self._start_targeting_from_drag(self.dragging_card, pos)
        else:
            # Carta solta em local inválido - retornar para posição original
            self._return_card_to_hand(self.dragging_card)
            
    def _start_targeting_from_drag(self, card: dict, pos: Tuple[int, int]):
        """Inicia sistema de targeting após drag & drop."""
        # Selecionar a carta para uso
        self.selected_card = card
        self.state = CombatState.TARGET_SELECTION
        
        # Verificar se há inimigo na posição
        target_enemy = self._get_enemy_at_position(pos)
        if target_enemy:
            # Usar carta diretamente no inimigo
            self._use_card_on_enemy(card, target_enemy)
        else:
            # Entrar em modo de targeting manual
            logger.info(f"Card {card['data']['name']} requires manual targeting")
            
    def _get_enemy_at_position(self, pos: Tuple[int, int]) -> Optional[dict]:
        """Retorna o inimigo na posição especificada."""
        if hasattr(self.combat_engine, 'enemies') and self.combat_engine.enemies:
            # Calcular posições dos inimigos baseado no layout atual
            enemies = self.combat_engine.enemies
            col_width = self.enemy_zone.width // len(enemies)
            
            for i, enemy in enumerate(enemies):
                enemy_x = self.enemy_zone.left + col_width // 2 + i * col_width
                enemy_rect = pygame.Rect(enemy_x - 50, self.enemy_zone.y, 100, self.enemy_zone.height)
                
                if enemy_rect.collidepoint(pos):
                    return {"enemy": enemy, "index": i}
        return None
        
    def _use_card_on_enemy(self, card: dict, target: dict):
        """Usa carta diretamente em um inimigo."""
        try:
            enemy = target["enemy"]
            logger.info(f"Using {card['data']['name']} on {enemy}")
            
            # P2: Trigger animação de ataque do jogador
            self.animation_manager.play_animation("knight", "attack", force_restart=True)
            
            # P2: Trigger animação de hurt do inimigo alvo
            enemy_anim_id = f"{self._get_enemy_anim_id(enemy)}_{target['index']}"
            self.animation_manager.play_animation(enemy_anim_id, "hurt", force_restart=True)
            
            # Simular efeito da carta (implementação simples para P1)
            if card["data"]["type"] == "spell" or card["data"]["type"] == "attack":
                damage = card["data"].get("damage", 1)
                if hasattr(enemy, 'hp'):
                    enemy.hp = max(0, enemy.hp - damage)
                    logger.info(f"Enemy took {damage} damage, HP: {enemy.hp}")
                    
            # Remover carta da mão
            self._remove_card_from_hand(card)
            
            # P2: Trigger efeitos visuais com partículas P2
            enemy_pos = self._get_enemy_screen_position(target["index"])
            self._trigger_attack_particles(enemy_pos)
            
        except Exception as e:
            logger.error(f"Error using card on enemy: {e}")
        finally:
            self.state = CombatState.PLAYER_TURN
            
    def _get_enemy_screen_position(self, enemy_index: int) -> Tuple[int, int]:
        """Retorna a posição na tela do inimigo especificado."""
        if hasattr(self.combat_engine, 'enemies') and self.combat_engine.enemies:
            enemies = self.combat_engine.enemies
            col_width = self.enemy_zone.width // len(enemies)
            enemy_x = self.enemy_zone.left + col_width // 2 + enemy_index * col_width
            enemy_y = self.enemy_zone.centery
            return (enemy_x, enemy_y)
        return (self.enemy_zone.centerx, self.enemy_zone.centery)
        
    def _remove_card_from_hand(self, card: dict):
        """Remove carta da mão do jogador."""
        if card in self.player_hand:
            self.player_hand.remove(card)
            self._reorganize_hand()
            
    def _reorganize_hand(self):
        """Reorganiza as cartas na mão após remoção."""
        slot_width = self.player_hand_zone.width // 5
        slot_height = self.player_hand_zone.height - 20
        
        for i, card in enumerate(self.player_hand):
            slot_x = self.player_hand_zone.left + i * slot_width + 10
            slot_y = self.player_hand_zone.top + 10
            
            card["rect"].x = slot_x
            card["rect"].y = slot_y
            card["original_pos"] = (slot_x, slot_y)
            card["slot_index"] = i
            
    def _return_card_to_hand(self, card: dict):
        """Retorna carta para sua posição original na mão."""
        card["rect"].x, card["rect"].y = card["original_pos"]
        card["is_selected"] = False
        
    def _select_card_simple(self, card: dict):
        """Seleciona carta com clique simples (sem drag)."""
        # Implementação simples - destacar carta selecionada
        for c in self.player_hand:
            c["is_selected"] = False
        card["is_selected"] = True
        self.selected_card = card
        logger.info(f"Selected card: {card['data']['name']}")
        
    def _update_card_hover(self, pos: Tuple[int, int]):
        """Atualiza efeitos de hover nas cartas."""
        for card in self.player_hand:
            was_hovered = card["is_hovered"]
            card["is_hovered"] = card["rect"].collidepoint(pos)
            
            # Log hover changes for debugging
            if card["is_hovered"] and not was_hovered:
                logger.debug(f"Hovering: {card['data']['name']}")
                
    def _update_card_animations(self, dt: float):
        """Sprint 2: Enhanced card animations using CardSprite system."""
        import math
        
        for card in self.player_hand:
            # Sprint 2: Use CardSprite if available
            if card.get('sprite'):
                # CardSprite handles its own animations with enhanced pulsing
                card_sprite = card['sprite']
                card_sprite.update(self.mouse_pos, dt)
                
                # Sync position from CardSprite back to card rect
                card["rect"] = card_sprite.rect.copy()
            else:
                # Fallback to original animation system (enhanced)
                card["animation_time"] += dt
                
                # Enhanced hover effects
                if card["is_hovered"] and not self.is_dragging:
                    card["target_hover_y"] = -25  # More pronounced hover
                    card["target_scale"] = 1.15   # Larger scale
                    card["target_glow_alpha"] = 200  # Stronger glow
                    card["target_rotation"] = 3   # More visible rotation
                elif card["is_selected"]:
                    card["target_hover_y"] = -15
                    card["target_scale"] = 1.08
                    card["target_glow_alpha"] = 120
                    card["target_rotation"] = 1.5
                else:
                    card["target_hover_y"] = 0
                    card["target_scale"] = 1.0
                    card["target_glow_alpha"] = 0
                    card["target_rotation"] = 0
                    
                # Smoother interpolation
                ease_speed = 10.0
                card["hover_offset_y"] += (card["target_hover_y"] - card["hover_offset_y"]) * dt * ease_speed
                card["scale"] += (card["target_scale"] - card["scale"]) * dt * ease_speed
                card["glow_alpha"] += (card["target_glow_alpha"] - card["glow_alpha"]) * dt * ease_speed
                card["rotation"] += (card["target_rotation"] - card["rotation"]) * dt * ease_speed
                
                # P2: Efeito de "pulsing" mais sutil quando idle
                if not card["is_hovered"] and not card["is_selected"]:
                    # P2: Pulsing senoidal como especificado
                    pulse_intensity = 3
                    pulse_speed = 2.0
                    time_offset = card["bob_offset"]
                    pulse_offset = math.sin((card["animation_time"] + time_offset) * pulse_speed) * pulse_intensity
                    card["hover_offset_y"] += pulse_offset
                    
                # P2: Animação de draw para cartas novas
                if card.get("draw_animation", False):
                    card["draw_progress"] = min(1.0, card["draw_progress"] + dt * 3.0)
                    if card["draw_progress"] >= 1.0:
                        card["draw_animation"] = False
                        
                # Atualizar posição do rect com offset
                card["rect"].x = card["original_pos"][0]
                card["rect"].y = card["original_pos"][1] + int(card["hover_offset_y"])
                
    def _reset_drag_state(self):
        """Reseta o estado de drag & drop."""
        if self.dragging_card:
            self.dragging_card["is_selected"] = False
        self.dragging_card = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_offset = (0, 0)
        
    # ========== END P1 DRAG & DROP SYSTEM ==========
        
    def _end_turn(self):
        """Sprint 2-b: Enhanced turn ending with TurnEngine integration."""
        try:
            # Trigger turn transition animation
            self._start_turn_transition()
            
            # Sprint 2-b: Use TurnEngine for proper turn management
            if hasattr(self, 'turn_engine'):
                # Process mini turn loop
                game_continues = self.turn_engine.mini_turn_loop(
                    particle_emitter=getattr(self, 'particle_manager', None)
                )
                
                if not game_continues:
                    # Game over - check win/loss
                    if self.turn_engine.player.hp <= 0:
                        self.state = CombatState.DEFEAT
                        logger.info("Player defeated!")
                    elif all(e.hp <= 0 for e in self.turn_engine.enemies):
                        self.state = CombatState.VICTORY
                        logger.info("All enemies defeated!")
                else:
                    # Continue to enemy turn
                    self.state = CombatState.ENEMY_TURN
                    logger.info("Player turn ended, enemy turn starting")
                    
                    # Sprint 2-b: Use deck system for discard/redraw
                    if hasattr(self.combat_engine, 'deck_manager'):
                        cards_drawn = self.combat_engine.deck_manager.end_turn()
                        logger.info(f"End turn: Drew {cards_drawn} new cards from deck")
                    else:
                        # Fallback: simple card draw
                        if hasattr(self, 'draw_card_from_deck'):
                            self.draw_card_from_deck(animate=True)
            else:
                # Fallback to combat engine
                if hasattr(self.combat_engine, 'end_turn'):
                    self.combat_engine.end_turn()
                    
                self.state = CombatState.ENEMY_TURN
                logger.info("Player turn ended (fallback)")
                
        except Exception as e:
            logger.error(f"Failed to end turn: {e}")
            # Fallback behavior
            self.state = CombatState.ENEMY_TURN
            
    def _start_turn_transition(self):
        """Inicia animação de transição de turno."""
        self.turn_transition_active = True
        self.turn_transition_timer = 0
        self.turn_transition_alpha = 0
        
    def _toggle_pause(self):
        """Alterna entre pausado e não pausado."""
        if self.state == CombatState.PAUSED:
            self.state = CombatState.PLAYER_TURN
        else:
            self.state = CombatState.PAUSED
            
    def draw(self):
        """
        Desenha toda a interface de combate profissional seguindo as diretrizes de design.
        
        Ordem de renderização otimizada:
        1. Background IA escalado
        2. Zona de inimigos com overlay escuro
        3. Sprites de inimigos escalados com grid flexível
        4. Sprite do jogador centralizado
        5. Status card com informações do jogador
        6. Zona da mão com slots definidos
        7. Botões polidos
        8. Overlays finais
        """
        # 1. Background IA escalado para tela
        self.screen.blit(self.background, (0, 0))
        
        # 2. Zona de inimigos com overlay escuro + sprites
        self._draw_enemy_zone()
        
        # 3. Sprite do jogador centralizado
        self._draw_player_sprite()
        
        # 4. Status card do jogador
        self._draw_status_card()
        
        # 5. Zona da mão do jogador
        self._draw_player_hand()
        
        # 6. Botões
        self._draw_buttons()
        
        # 7. Debug info (se necessário)
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self._draw_debug_info()
            
        # Sprint 2-b: Draw particles (last for proper layering)
        if hasattr(self, 'particle_manager'):
            self.particle_manager.draw(self.screen)
            
    def _draw_enemy_zone(self):
        """Desenha zona de inimigos com overlay escuro e sprites escalados."""
        # Criar overlay escuro para a zona
        zone_surf = pygame.Surface(self.enemy_zone.size, pygame.SRCALPHA)
        zone_surf.fill((0, 0, 0, 140))  # 55% opacidade
        self.screen.blit(zone_surf, self.enemy_zone.topleft)
        
        # Desenhar sprites dos inimigos em grid flexível usando animações
        if hasattr(self.combat_engine, 'enemies') and self.combat_engine.enemies:
            enemies = self.combat_engine.enemies
            
            # Calcular grid flexível baseado no número de inimigos
            col_width = self.enemy_zone.width // len(enemies)
            
            for i, enemy in enumerate(enemies):
                # Usar ID único para animação
                unique_id = f"{self._get_enemy_anim_id(enemy)}_{i}"
                
                # Obter frame atual da animação
                current_frame = animation_manager.get_current_frame(unique_id)
                
                if current_frame:
                    # Posicionar sprite na coluna correspondente
                    pos_x = self.enemy_zone.left + col_width // 2 - current_frame.get_width() // 2 + i * col_width
                    pos_y = self.enemy_zone.bottom - current_frame.get_height()
                    
                    sprite_rect = self.screen.blit(current_frame, (pos_x, pos_y))
                    
                    # Desenhar healthbar acima do sprite
                    self._draw_enemy_healthbar(enemy, sprite_rect)
                else:
                    # Fallback para sprite estático se animação não disponível
                    enemy_id = getattr(enemy, 'id', f"enemy_{i}")
                    if enemy_id in self.enemy_sprites:
                        sprite = self.enemy_sprites[enemy_id]
                        pos_x = self.enemy_zone.left + col_width // 2 - sprite.get_width() // 2 + i * col_width
                        pos_y = self.enemy_zone.bottom - sprite.get_height()
                        sprite_rect = self.screen.blit(sprite, (pos_x, pos_y))
                        self._draw_enemy_healthbar(enemy, sprite_rect)
                    
    def _draw_enemy_healthbar(self, enemy, sprite_rect):
        """Desenha barra de vida do inimigo acima do sprite."""
        # Posicionar barra acima do sprite
        bar_rect = pygame.Rect(
            sprite_rect.left, 
            sprite_rect.top - 12, 
            sprite_rect.width, 
            8
        )
        
        # Fundo da barra (escuro)
        pygame.draw.rect(self.screen, (40, 40, 40), bar_rect)
        
        # Barra de vida (proporcional ao HP)
        if hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp') and enemy.max_hp > 0:
            hp_ratio = enemy.hp / enemy.max_hp
            hp_width = int((sprite_rect.width - 2) * hp_ratio)
            
            if hp_width > 0:
                hp_rect = pygame.Rect(
                    bar_rect.left + 1,
                    bar_rect.top + 1, 
                    hp_width,
                    6
                )
                
                # Cor da barra baseada no HP (verde -> amarelo -> vermelho)
                if hp_ratio > 0.6:
                    hp_color = (0, 200, 0)  # Verde
                elif hp_ratio > 0.3:
                    hp_color = (255, 255, 0)  # Amarelo
                else:
                    hp_color = (200, 0, 0)  # Vermelho
                    
                pygame.draw.rect(self.screen, hp_color, hp_rect)
                
    def _get_enemy_anim_id(self, enemy) -> str:
        """Retorna ID de animação para um inimigo."""
        enemy_type_mapping = {
            'goblin': 'goblin',
            'orc': 'orc', 
            'skeleton': 'skeleton',
            'wizard': 'mage',
            'dragon': 'dragon'
        }
        
        # Converter enum para string
        if hasattr(enemy.enemy_type, 'value'):
            enemy_type_str = enemy.enemy_type.value.lower()
        elif hasattr(enemy.enemy_type, 'name'):
            enemy_type_str = enemy.enemy_type.name.lower()
        else:
            enemy_type_str = str(enemy.enemy_type).lower()
            
        return enemy_type_mapping.get(enemy_type_str, 'goblin')
                
    def _draw_player_sprite(self):
        """Sprint 2-b: Desenha sprite do jogador usando animação 30fps realtime."""
        # Sprint 2-b: Use realtime 30fps animation
        if hasattr(self, 'player_animation') and self.player_animation:
            try:
                current_frame = self.player_animation.current()
                if current_frame:
                    # Position sprite centered above hand zone
                    sprite_rect = current_frame.get_rect(
                        midbottom=(self.width // 2, self.player_hand_zone.top - 10)
                    )
                    self.screen.blit(current_frame, sprite_rect)
                    return
            except Exception as e:
                logger.warning(f"Failed to draw player animation: {e}")
        
        # Fallback: Use old animation system
        current_frame = animation_manager.get_current_frame("knight")
        
        if current_frame:
            # Position sprite centered above hand zone
            sprite_rect = current_frame.get_rect(
                midbottom=(self.width // 2, self.player_hand_zone.top - 10)
            )
            self.screen.blit(current_frame, sprite_rect)
        elif self.player_sprite:
            # Final fallback to static sprite
            sprite_rect = self.player_sprite.get_rect(
                midbottom=(self.width // 2, self.player_hand_zone.top - 10)
            )
            self.screen.blit(self.player_sprite, sprite_rect)
            
    def _draw_status_card(self):
        """Desenha status card do jogador com HP, mana e recursos."""
        if not hasattr(self, 'status_card_zone'):
            return
            
        # Fundo do status card com bordas arredondadas
        status_surface = pygame.Surface(self.status_card_zone.size, pygame.SRCALPHA)
        
        # Fundo principal do card (azul-escuro translúcido)
        pygame.draw.rect(status_surface, (20, 30, 80, 220), status_surface.get_rect(), border_radius=10)
        
        # Borda dourada
        pygame.draw.rect(status_surface, (200, 180, 0), status_surface.get_rect(), 3, border_radius=10)
        
        # Blitar o fundo do status card
        self.screen.blit(status_surface, self.status_card_zone.topleft)
        
        # Obter dados do jogador
        player = None
        if hasattr(self.combat_engine, 'player'):
            player = self.combat_engine.player
        elif hasattr(self, 'player'):
            player = self.player
            
        # Configurações de texto
        font_large = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 20)
        font_small = pygame.font.Font(None, 16)
        
        # Título do card
        title_text = font_large.render("Status", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=self.status_card_zone.centerx, y=self.status_card_zone.y + 10)
        self.screen.blit(title_text, title_rect)
        
        # Linha divisória
        line_y = self.status_card_zone.y + 35
        pygame.draw.line(self.screen, (200, 180, 0), 
                        (self.status_card_zone.x + 10, line_y), 
                        (self.status_card_zone.right - 10, line_y), 2)
        
        # Desenhar informações do jogador
        y_offset = 45
        
        if player:
            # HP do jogador
            if hasattr(player, 'hp') and hasattr(player, 'max_hp'):
                hp_text = f"HP: {player.hp}/{player.max_hp}"
                hp_color = self._get_hp_color(player.hp / player.max_hp if player.max_hp > 0 else 0)
                hp_surface = font_medium.render(hp_text, True, hp_color)
                self.screen.blit(hp_surface, (self.status_card_zone.x + 15, self.status_card_zone.y + y_offset))
                
                # Barra de HP
                bar_width = self.status_card_zone.width - 30
                bar_height = 8
                bar_x = self.status_card_zone.x + 15
                bar_y = self.status_card_zone.y + y_offset + 20
                
                # Fundo da barra
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                
                # Barra de HP
                if player.max_hp > 0:
                    hp_ratio = player.hp / player.max_hp
                    fill_width = int(bar_width * hp_ratio)
                    if fill_width > 0:
                        pygame.draw.rect(self.screen, hp_color, (bar_x, bar_y, fill_width, bar_height))
                
                y_offset += 35
            
            # Mana/Energia (se existir)
            if hasattr(player, 'mana') and hasattr(player, 'max_mana'):
                mana_text = f"Mana: {player.mana}/{player.max_mana}"
                mana_surface = font_medium.render(mana_text, True, (100, 150, 255))
                self.screen.blit(mana_surface, (self.status_card_zone.x + 15, self.status_card_zone.y + y_offset))
                
                # Barra de Mana
                bar_x = self.status_card_zone.x + 15
                bar_y = self.status_card_zone.y + y_offset + 20
                
                # Fundo da barra
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                
                # Barra de Mana
                if player.max_mana > 0:
                    mana_ratio = player.mana / player.max_mana
                    fill_width = int(bar_width * mana_ratio)
                    if fill_width > 0:
                        pygame.draw.rect(self.screen, (100, 150, 255), (bar_x, bar_y, fill_width, bar_height))
                
                y_offset += 35
            
            # Turno atual
            turn_text = f"Turno: {getattr(self.combat_engine, 'turn_count', 1) if hasattr(self.combat_engine, 'turn_count') else 1}"
            turn_surface = font_small.render(turn_text, True, (200, 200, 200))
            self.screen.blit(turn_surface, (self.status_card_zone.x + 15, self.status_card_zone.y + y_offset))
        else:
            # Fallback quando não há dados do jogador
            no_data_text = font_medium.render("Carregando...", True, (150, 150, 150))
            self.screen.blit(no_data_text, (self.status_card_zone.x + 15, self.status_card_zone.y + y_offset))
    
    def _get_hp_color(self, hp_ratio):
        """Retorna cor baseada na porcentagem de HP."""
        if hp_ratio > 0.6:
            return (0, 200, 0)  # Verde
        elif hp_ratio > 0.3:
            return (255, 200, 0)  # Amarelo
        else:
            return (255, 50, 50)  # Vermelho
            
    def _draw_player_hand(self):
        """
        Desenha zona da mão do jogador com cartas - Sprint 2 Enhanced.
        Uses CardSprite system with pulsing glow and enhanced animations.
        """
        # Painel azul-escuro translúcido para a mão
        hand_overlay = pygame.Surface(self.player_hand_zone.size, pygame.SRCALPHA)
        hand_overlay.fill((30, 40, 90, 200))  # Azul-escuro translúcido
        self.screen.blit(hand_overlay, self.player_hand_zone.topleft)
        
        # Sprint 2: Use CardSprite system for enhanced visuals
        for card in self.player_hand:
            # Sprint 2: Use CardSprite if available
            if card.get("sprite"):
                # Enhanced CardSprite with pulsing glow
                card_sprite = card["sprite"]
                card_sprite.draw(self.screen)
                
                # Draw card info on top
                self._draw_card_info_overlay(card, card_sprite.rect)
            else:
                # Fallback to original rendering
                self._draw_card_fallback(card)
                
    def _draw_card_info_overlay(self, card, card_rect):
        """Sprint 2: Draw card information overlay on CardSprite."""
        data = card["data"]
        
        # Fonts for card info
        font = pygame.font.Font(None, 20)
        font_small = pygame.font.Font(None, 16)
        
        # Card name
        if "name" in data:
            name_surface = font.render(data["name"], True, (255, 255, 255))
            name_rect = name_surface.get_rect(centerx=card_rect.centerx, y=card_rect.y + 10)
            self.screen.blit(name_surface, name_rect)
        
        # Card cost (top-left corner)
        if "cost" in data:
            cost_surface = font_small.render(str(data["cost"]), True, (100, 200, 255))
            cost_rect = pygame.Rect(card_rect.x + 5, card_rect.y + 5, 25, 25)
            pygame.draw.circle(self.screen, (20, 30, 60), cost_rect.center, 12)
            pygame.draw.circle(self.screen, (100, 200, 255), cost_rect.center, 12, 2)
            cost_text_rect = cost_surface.get_rect(center=cost_rect.center)
            self.screen.blit(cost_surface, cost_text_rect)
        
        # Card effects (center)
        y_offset = card_rect.centery
        if "damage" in data:
            damage_text = font_small.render(f"⚔️ {data['damage']}", True, (255, 100, 100))
            damage_rect = damage_text.get_rect(centerx=card_rect.centerx, y=y_offset)
            self.screen.blit(damage_text, damage_rect)
            y_offset += 20
            
        if "heal" in data:
            heal_text = font_small.render(f"❤️ {data['heal']}", True, (100, 255, 100))
            heal_rect = heal_text.get_rect(centerx=card_rect.centerx, y=y_offset)
            self.screen.blit(heal_text, heal_rect)
            y_offset += 20
            
        if "defense" in data:
            defense_text = font_small.render(f"🛡️ {data['defense']}", True, (100, 100, 255))
            defense_rect = defense_text.get_rect(centerx=card_rect.centerx, y=y_offset)
            self.screen.blit(defense_text, defense_rect)
    
    def _draw_card_fallback(self, card):
        """Fallback card rendering when CardSprite is not available."""
        # Aplicar transformações de animação
        original_rect = card["rect"]
        scale = max(0.1, card.get("scale", 1.0))  # Garantir escala mínima
        rotation = card.get("rotation", 0)
        glow_alpha = card.get("glow_alpha", 0)
        
        # Calcular rect escalado com validação
        scaled_width = max(1, int(original_rect.width * scale))
        scaled_height = max(1, int(original_rect.height * scale))
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = original_rect.center
        
        data = card["data"]
        
        # Cores dinâmicas com glow
        if card["is_selected"]:
            border_color = (255, 215, 0)  # Dourado para selecionada
            bg_color = (70, 80, 120, 220)
            border_width = 3
        elif card["is_hovered"]:
            border_color = (150, 200, 255)  # Azul claro para hover
            bg_color = (60, 70, 110, 220)
            border_width = 2
        else:
            border_color = (80, 80, 80)  # Cinza normal
            bg_color = (50, 50, 50, 180)
            border_width = 1
            
        # Criar surface da carta com animações
        card_surface = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        
        # Efeito de glow se necessário
        if glow_alpha > 5:
            glow_width = max(1, scaled_rect.width + 10)
            glow_height = max(1, scaled_rect.height + 10)
            glow_surface = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
            glow_color = (*border_color, int(min(255, max(0, glow_alpha))))
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=8)
            glow_rect = glow_surface.get_rect(center=scaled_rect.center)
            self.screen.blit(glow_surface, glow_rect.topleft)
        
        # Fundo da carta
        card_surface.fill(bg_color)
        
        # Aplicar rotação se necessário
        if abs(rotation) > 0.1:
            card_surface = pygame.transform.rotate(card_surface, rotation)
            rotated_rect = card_surface.get_rect(center=scaled_rect.center)
            self.screen.blit(card_surface, rotated_rect.topleft)
            display_rect = rotated_rect
        else:
            self.screen.blit(card_surface, scaled_rect.topleft)
            display_rect = scaled_rect
        
        # Borda da carta
        pygame.draw.rect(self.screen, border_color, display_rect, border_width, border_radius=5)
        
        # Desenhar informações da carta
        self._draw_card_info_overlay(card, display_rect)
        
    def _draw_buttons(self):
        """Desenha todos os botões da interface."""
        # Desenhar botão End Turn
        if hasattr(self, 'end_turn_button'):
            self.end_turn_button.draw(self.screen)
            
    def _draw_background_with_parallax(self):
        """Desenha background de combate épico com efeito parallax."""
        # Verificar se temos background IA carregado
        if not hasattr(self, 'background_surface') or self.background_surface is None:
            # Fallback: fundo preto simples
            self.screen.fill(theme.colors.SHADOW_BLACK)
            return
        
        # Escalar background para tela mantendo proporção
        screen_size = self.screen.get_size()
        background_scaled = pygame.transform.smoothscale(self.background_surface, screen_size)
        
        # Calcular offset de parallax
        mouse_x, mouse_y = self.mouse_pos
        center_x, center_y = self.width // 2, self.height // 2
        
        # Parallax sutil - 2% de movimento
        parallax_strength = 0.02
        offset_x = (mouse_x - center_x) * parallax_strength
        offset_y = (mouse_y - center_y) * parallax_strength
        
        # Desenhar background com offset
        bg_rect = background_scaled.get_rect()
        bg_rect.center = (center_x + offset_x, center_y + offset_y)
        
        self.screen.blit(background_scaled, bg_rect)
        
        # Adicionar overlay sutil para melhor contraste
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 20))  # Muito sutil
        self.screen.blit(overlay, (0, 0))
        
    def _draw_zones(self):
        """Desenha as zonas de combate com painéis semi-transparentes."""
        # Zona de inimigos
        self._draw_zone_panel(self.enemy_zone.rect, "enemy")
        
        # Zona do jogador  
        self._draw_zone_panel(self.player_zone.rect, "player")
        
    def _draw_zone_panel(self, rect: pygame.Rect, zone_type: str):
        """
        Desenha painel semi-transparente para uma zona.
        
        Args:
            rect: Retângulo da zona
            zone_type: Tipo da zona ("enemy" ou "player")
        """
        # Criar surface semi-transparente
        panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Cor base baseada no tipo
        if zone_type == "enemy":
            base_color = (80, 40, 40, 120)  # Vermelho escuro
        else:
            base_color = (40, 40, 80, 120)  # Azul escuro
            
        panel_surface.fill(base_color)
        
        # Desenhar borda decorativa
        border_color = (200, 180, 100, 180)  # Dourado
        pygame.draw.rect(panel_surface, border_color, 
                        (0, 0, rect.width, rect.height), 3)
        
        # Adicionar textura se disponível
        if "zone_panel_texture" in self.assets:
            texture = self.assets["zone_panel_texture"]
            texture = pygame.transform.scale(texture, (rect.width, rect.height))
            texture.set_alpha(60)  # Muito sutil
            panel_surface.blit(texture, (0, 0))
            
        # Desenhar no screen
        self.screen.blit(panel_surface, rect.topleft)
        
    def _draw_cards(self):
        """Desenha todas as cartas na zona do jogador."""
        for slot in self.player_zone.slots:
            if slot.entity:
                self._draw_card_in_slot(slot)
                
    def _draw_card_in_slot(self, slot: CombatSlot):
        """
        Desenha uma carta individual com todas as animações.
        
        Args:
            slot: Slot contendo a carta
        """
        card = slot.entity
        display_rect = slot.get_display_rect()
        
        # Surface da carta
        card_surface = pygame.Surface((display_rect.width, display_rect.height), pygame.SRCALPHA)
        
        # Background da carta
        if slot.is_selected:
            bg_color = (100, 100, 150, 200)
        elif slot.is_hovered:
            bg_color = (80, 80, 120, 180)
        else:
            bg_color = (60, 60, 90, 160)
            
        card_surface.fill(bg_color)
        
        # Borda da carta
        border_color = (200, 180, 100) if slot.is_hovered else (150, 130, 80)
        pygame.draw.rect(card_surface, border_color, 
                        (0, 0, display_rect.width, display_rect.height), 2)
        
        # Glow effect durante hover
        if slot.is_hovered and slot.glow_alpha > 0:
            glow_surface = pygame.Surface((display_rect.width + 10, display_rect.height + 10), pygame.SRCALPHA)
            glow_color = (255, 215, 0, int(slot.glow_alpha * 0.3))  # Dourado pulsante
            pygame.draw.rect(glow_surface, glow_color, 
                           (0, 0, display_rect.width + 10, display_rect.height + 10), 5)
            
            glow_rect = glow_surface.get_rect()
            glow_rect.center = display_rect.center
            self.screen.blit(glow_surface, glow_rect.topleft)
        
        # Texto da carta
        if hasattr(card, 'name'):
            font = pygame.font.Font(None, 24)
            text_surface = font.render(card.name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(display_rect.width//2, 20))
            card_surface.blit(text_surface, text_rect)
            
        # Custo da carta
        if hasattr(card, 'cost'):
            cost_font = pygame.font.Font(None, 20)
            cost_text = cost_font.render(str(card.cost), True, (100, 200, 255))
            card_surface.blit(cost_text, (5, 5))
            
        # Desenhar carta no screen
        self.screen.blit(card_surface, display_rect.topleft)
        
    def _draw_enemies(self):
        """Desenha todos os inimigos na zona de inimigos usando sprites IA."""
        # Zona inimigos (topo) - posições fixas
        screen_width = self.screen.get_width()
        
        # Obter inimigos do combat engine
        enemies = getattr(self.combat_engine, 'enemies', [])
        alive_enemies = [e for e in enemies if hasattr(e, 'hp') and e.hp > 0]
        
        for i, enemy in enumerate(alive_enemies[:2]):  # Max 2 inimigos na tela
            # Posição horizontal distribuída
            x_pos = 200 + i * 500
            y_pos = 40
            
            # Determinar sprite do inimigo
            enemy_sprite = self._get_enemy_sprite(enemy)
            
            if enemy_sprite:
                # Escalar sprite para tamanho apropriado
                sprite_scaled = pygame.transform.scale(enemy_sprite, (200, 300))
                sprite_rect = sprite_scaled.get_rect(midtop=(x_pos, y_pos))
                
                # Efeito de hover
                mouse_pos = pygame.mouse.get_pos()
                if sprite_rect.collidepoint(mouse_pos):
                    # Glow effect para hover
                    glow_surface = pygame.Surface((sprite_rect.width + 20, sprite_rect.height + 20), pygame.SRCALPHA)
                    glow_surface.fill((255, 100, 100, 60))  # Brilho vermelho
                    glow_rect = glow_surface.get_rect(center=sprite_rect.center)
                    self.screen.blit(glow_surface, glow_rect)
                
                # Desenhar sprite
                self.screen.blit(sprite_scaled, sprite_rect)
                
                # HP bar acima do inimigo
                self._draw_enemy_hp_bar(enemy, sprite_rect.centerx, sprite_rect.top - 20)
                
            else:
                # Fallback: retângulo simples
                self._draw_enemy_placeholder(enemy, x_pos, y_pos)
    
    def _get_enemy_sprite(self, enemy) -> Optional[pygame.Surface]:
        """
        Obtém sprite IA de um inimigo baseado no tipo/nome.
        
        Args:
            enemy: Objeto inimigo
            
        Returns:
            Surface do sprite ou None
        """
        if not hasattr(self, 'enemy_sprites'):
            return None
            
        # Mapear tipos de inimigos para sprites
        enemy_type_map = {
            'goblin': 'goblin_scout',
            'orc': 'orc_berserker', 
            'skeleton': 'skeleton_archer',
            'mage': 'dark_mage'
        }
        
        # Tentar identificar tipo do inimigo
        enemy_name = getattr(enemy, 'name', '').lower()
        enemy_id = getattr(enemy, 'id', '').lower()
        
        for enemy_type, sprite_key in enemy_type_map.items():
            if enemy_type in enemy_name or enemy_type in enemy_id:
                return self.enemy_sprites.get(sprite_key)
        
        # Fallback: primeiro sprite disponível
        if self.enemy_sprites:
            return list(self.enemy_sprites.values())[0]
            
        return None
    
    def _draw_enemy_hp_bar(self, enemy, center_x: int, y: int):
        """
        Desenha barra de HP de um inimigo.
        
        Args:
            enemy: Objeto inimigo
            center_x: Posição X central
            y: Posição Y
        """
        if not (hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp')):
            return
            
        bar_width = 120
        bar_height = 8
        bar_x = center_x - bar_width // 2
        
        # Background da barra
        bg_rect = pygame.Rect(bar_x, y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (60, 0, 0), bg_rect)
        
        # Barra de HP
        hp_percent = enemy.hp / enemy.max_hp
        hp_width = int(bar_width * hp_percent)
        hp_rect = pygame.Rect(bar_x, y, hp_width, bar_height)
        pygame.draw.rect(self.screen, (200, 60, 60), hp_rect)
        
        # Borda
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 1)
        
        # Texto de HP
        font = pygame.font.Font(None, 20)
        hp_text = font.render(f"{enemy.hp}/{enemy.max_hp}", True, (255, 255, 255))
        text_rect = hp_text.get_rect(center=(center_x, y - 12))
        self.screen.blit(hp_text, text_rect)
    
    def _draw_enemy_placeholder(self, enemy, x: int, y: int):
        """
        Desenha placeholder para inimigo sem sprite.
        
        Args:
            enemy: Objeto inimigo
            x, y: Posição
        """
        rect = pygame.Rect(x - 75, y, 150, 200)
        pygame.draw.rect(self.screen, (120, 60, 60), rect)
        pygame.draw.rect(self.screen, (200, 100, 100), rect, 2)
        
        # Nome do inimigo
        font = pygame.font.Font(None, 24)
        name = getattr(enemy, 'name', 'Enemy')
        text = font.render(name, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x, y + 100))
        self.screen.blit(text, text_rect)
        
    def _draw_player_sprite(self):
        """Desenha sprite do jogador na zona do jogador usando IA."""
        if not hasattr(self, 'player_sprite') or self.player_sprite is None:
            return
            
        # Zona jogador (base da tela)
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Escalar sprite do jogador
        player_scaled = pygame.transform.scale(self.player_sprite, (180, 280))
        player_rect = player_scaled.get_rect(midbottom=(screen_width // 2, screen_height - 100))
        
        # Efeito de hover
        mouse_pos = pygame.mouse.get_pos()
        if player_rect.collidepoint(mouse_pos):
            # Glow effect para hover
            glow_surface = pygame.Surface((player_rect.width + 20, player_rect.height + 20), pygame.SRCALPHA)
            glow_surface.fill((100, 150, 255, 60))  # Brilho azul
            glow_rect = glow_surface.get_rect(center=player_rect.center)
            self.screen.blit(glow_surface, glow_rect)
        
        # Desenhar sprite do jogador
        self.screen.blit(player_scaled, player_rect)
        
    def _draw_player_panel(self):
        """Desenha o painel flutuante de estado do jogador."""
        # Limpar surface do painel
        self.player_panel_surface.fill((0, 0, 0, 0))
        
        # Background do painel com transparência
        panel_bg = pygame.Surface((self.player_panel_rect.width, self.player_panel_rect.height), pygame.SRCALPHA)
        panel_bg.fill((40, 40, 60, 180))
        
        # Borda dourada
        pygame.draw.rect(panel_bg, (200, 180, 100, 200), 
                        (0, 0, self.player_panel_rect.width, self.player_panel_rect.height), 2)
        
        # Sombra (se asset disponível)
        if "panel_shadow" in self.assets:
            shadow = self.assets["panel_shadow"]
            shadow = pygame.transform.scale(shadow, 
                                          (self.player_panel_rect.width + 20, self.player_panel_rect.height + 20))
            shadow_rect = shadow.get_rect()
            shadow_rect.center = (self.player_panel_rect.centerx + 3, self.player_panel_rect.centery + 3)
            self.screen.blit(shadow, shadow_rect.topleft)
        
        self.player_panel_surface.blit(panel_bg, (0, 0))
        
        # Obter dados do jogador
        player = getattr(self.combat_engine, 'current_player', None)
        if player:
            self._draw_player_stats(player)
            
        # Desenhar painel no screen
        self.screen.blit(self.player_panel_surface, self.player_panel_rect.topleft)
        
    def _draw_player_stats(self, player):
        """Desenha as estatísticas do jogador no painel."""
        panel_width = self.player_panel_rect.width
        panel_height = self.player_panel_rect.height
        
        # HP Bar
        if hasattr(player, 'hp') and hasattr(player, 'max_hp'):
            hp_width = panel_width // 2 - 20
            hp_height = 12
            hp_x = 10
            hp_y = 15
            
            # Background da barra
            hp_bg = pygame.Rect(hp_x, hp_y, hp_width, hp_height)
            pygame.draw.rect(self.player_panel_surface, (60, 0, 0), hp_bg)
            
            # Preenchimento da barra
            hp_percent = player.hp / player.max_hp if player.max_hp > 0 else 0
            hp_fill_width = int(hp_width * hp_percent)
            hp_fill = pygame.Rect(hp_x, hp_y, hp_fill_width, hp_height)
            pygame.draw.rect(self.player_panel_surface, (200, 50, 50), hp_fill)
            
            # Texto HP
            font = pygame.font.Font(None, 20)
            hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, (255, 255, 255))
            self.player_panel_surface.blit(hp_text, (hp_x, hp_y - 15))
            
        # Mana Bar
        if hasattr(player, 'mana') and hasattr(player, 'max_mana'):
            mana_width = panel_width // 2 - 20  
            mana_height = 12
            mana_x = panel_width // 2 + 10
            mana_y = 15
            
            # Background da barra
            mana_bg = pygame.Rect(mana_x, mana_y, mana_width, mana_height)
            pygame.draw.rect(self.player_panel_surface, (0, 0, 60), mana_bg)
            
            # Preenchimento da barra
            mana_percent = player.mana / player.max_mana if player.max_mana > 0 else 0
            mana_fill_width = int(mana_width * mana_percent)
            mana_fill = pygame.Rect(mana_x, mana_y, mana_fill_width, mana_height)
            pygame.draw.rect(self.player_panel_surface, (50, 50, 200), mana_fill)
            
            # Texto Mana
            mana_text = font.render(f"Mana: {player.mana}/{player.max_mana}", True, (255, 255, 255))
            self.player_panel_surface.blit(mana_text, (mana_x, mana_y - 15))
            
        # Informações de cartas
        deck_count = len(getattr(player, 'deck', []))
        hand_count = len(getattr(player, 'hand', []))
        
        info_font = pygame.font.Font(None, 18)
        deck_text = info_font.render(f"Deck: {deck_count}", True, (200, 200, 200))
        hand_text = info_font.render(f"Hand: {hand_count}", True, (200, 200, 200))
        
        self.player_panel_surface.blit(deck_text, (10, panel_height - 25))
        self.player_panel_surface.blit(hand_text, (80, panel_height - 25))
        
        # Ícone de carta (se disponível)
        if "icon_card" in self.assets:
            icon = self.assets["icon_card"]
            icon = pygame.transform.scale(icon, (16, 16))
            self.player_panel_surface.blit(icon, (panel_width - 25, panel_height - 25))
            
    def _draw_particles(self):
        """Desenha o sistema de partículas."""
        # self.particle_system.draw(self.screen)  # Temporarily disabled
        
    def _draw_overlays(self):
        """Desenha overlays e transições especiais."""
        # Overlay de transição de turno
        if self.turn_transition_active and self.turn_transition_alpha > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.turn_transition_alpha))
            self.screen.blit(overlay, (0, 0))
            
            # Texto de transição
            if self.turn_transition_alpha > 100:
                font = pygame.font.Font(None, 48)
                text = font.render("Enemy Turn", True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.width//2, self.height//2))
                self.screen.blit(text, text_rect)
                
        # Overlay de pause
        if self.state == CombatState.PAUSED:
            pause_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 100))
            self.screen.blit(pause_overlay, (0, 0))
            
            # Texto de pause
            font = pygame.font.Font(None, 64)
            pause_text = font.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(pause_text, text_rect)
            
            # Instrução
            inst_font = pygame.font.Font(None, 24)
            inst_text = inst_font.render("Press ESC to exit or P to resume", True, (200, 200, 200))
            inst_rect = inst_text.get_rect(center=(self.width//2, self.height//2 + 50))
            self.screen.blit(inst_text, inst_rect)
            
    def _draw_debug_info(self):
        """Desenha informações de debug."""
        debug_font = pygame.font.Font(None, 20)
        
        debug_lines = [
            f"State: {self.state.value}",
            f"Mouse: {self.mouse_pos}",
            f"Selected Card: {self.selected_card}",
            f"Targeted Enemy: {self.targeted_enemy}",
            f"Turn Transition: {self.turn_transition_active}"
        ]
        
        for i, line in enumerate(debug_lines):
            debug_surface = debug_font.render(line, True, (255, 255, 0))
            self.screen.blit(debug_surface, (10, 10 + i * 22))

    def run(self) -> bool:
        """
        Main combat loop.
        
        Returns:
            True if player wins, False if player loses or exits
        """
        # Initialize pygame clock for this combat session
        clock = pygame.time.Clock()
        
        try:
            while True:
                # Calculate delta time
                dt = clock.tick(60) / 1000.0
                
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                        
                    result = self.handle_event(event)
                    if result == "victory":
                        return True
                    elif result == "defeat":
                        return False
                    elif result == "exit":
                        return False
                
                # Update
                self.update(dt)
                
                # Draw
                self.draw()
                
                # Update display
                pygame.display.flip()
                
        except Exception as e:
            logger.error(f"Error in combat loop: {e}", exc_info=True)
            return False
