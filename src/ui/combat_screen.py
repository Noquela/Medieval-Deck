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
from ..utils.asset_loader import load_ia_assets
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
        
        # Assets IA carregados
        self.assets = {}
        
        # Inicialização dos componentes
        self._load_ia_assets()
        self._load_sprite_animations()
        self._setup_zones()
        self._setup_buttons()
        self._setup_particles()
        self._setup_player_panel()
        self._generate_background()
        
        # Transições e overlays
        self.turn_transition_alpha = 0
        self.turn_transition_active = False
        self.turn_transition_timer = 0
        
        logger.info("Professional CombatScreen initialized")
        
    def _load_ia_assets(self):
        """Carrega todos os assets gerados por IA usando o AssetLoader."""
        try:
            # Usar a função automática do AssetLoader
            self.assets.update(load_ia_assets("assets/ia"))
            
            # Escalar background para o tamanho da tela
            if "combat_bg" in self.assets:
                self.background = pygame.transform.smoothscale(
                    self.assets["combat_bg"], 
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
            
            # Assets principais que precisamos
            required_assets = [
                "combat_bg",  # Background de combate épico
                "player_sprite",  # Sprite do jogador
                "goblin_scout_sprite", "orc_berserker_sprite",  # Sprites de inimigos
                "skeleton_archer_sprite", "dark_mage_sprite",
                "button_idle", "button_hover", "button_pressed",
                "icon_arrow_left", "icon_arrow_right"
            ]
            
            # Verificar assets carregados
            loaded_count = 0
            for asset_name in required_assets:
                if asset_name in self.assets:
                    loaded_count += 1
                    logger.debug(f"✅ Asset carregado: {asset_name}")
                else:
                    logger.warning(f"❌ Asset faltando: {asset_name}")
            
            logger.info(f"Assets IA carregados: {loaded_count}/{len(required_assets)} ({len(self.assets)} total)")
            
            # Configurar background de combate
            if "combat_bg" in self.assets:
                self.background_surface = self.assets["combat_bg"]
                logger.info("✅ Background de combate configurado")
            
            # Configurar sprites de inimigos
            self.enemy_sprites = {}
            for asset_name in self.assets:
                if asset_name.endswith('_sprite') and asset_name != 'player_sprite':
                    enemy_id = asset_name.replace('_sprite', '')
                    self.enemy_sprites[enemy_id] = self.assets[asset_name]
                    logger.debug(f"✅ Enemy sprite: {enemy_id}")
            
            # Configurar sprite do jogador
            if "player_sprite" in self.assets:
                self.player_sprite = self.assets["player_sprite"]
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
    
    def _setup_zones(self):
        """Configura as zonas de combate seguindo as diretrizes de design."""
        # Zona de inimigos (topo) - 50px de margem, altura 300px
        self.enemy_zone = pygame.Rect(50, 30, self.width - 100, 300)
        
        # Zona da mão do jogador (base) - altura 190px
        self.player_hand_zone = pygame.Rect(50, self.height - 220, self.width - 100, 190)
        
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
        if "player_sprite" in self.assets:
            target_height = int(self.height * 0.35)
            self.player_sprite = fit_height(self.assets["player_sprite"], target_height)
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
        if "button_texture_mystical" in self.assets:
            button_texture = pygame.transform.scale(
                self.assets["button_texture_mystical"], (button_width, button_height)
            )
            self.end_turn_button.textures = {
                "normal": button_texture,
                "hover": apply_glow_effect(button_texture, (138, 43, 226), 3),  # Roxo
                "pressed": button_texture
            }
        
        logger.info("Botões configurados com texturas IA")
        
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
        
        # Atualizar botões
        if hasattr(self, 'end_turn_button'):
            self.end_turn_button.update(dt)
        
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
                
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            
        return None
        
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Processa clique esquerdo na interface."""
        x, y = pos
        
        # Verificar clique nos botões
        if self.end_turn_button.rect.collidepoint(x, y):
            if self.state == CombatState.PLAYER_TURN:
                self._end_turn()
            return
            
        # Verificar clique nos botões
        if hasattr(self, 'end_turn_button') and self.end_turn_button.rect.collidepoint(x, y):
            if self.state == CombatState.PLAYER_TURN:
                self._end_turn()
            return
            
        # Verificar clique na zona da mão do jogador (para futuras implementações)
        if self.state == CombatState.PLAYER_TURN and self.player_hand_zone.collidepoint(x, y):
            # TODO: Implementar seleção de cartas quando sistema de cartas estiver pronto
            pass
                    
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
        """Processa movimento do mouse para hover effects."""
        x, y = pos
        
        # Armazenar posição do mouse para futuros efeitos de hover
        self.mouse_pos = pos
        
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
            # Disparar partículas de dano no alvo
            self._trigger_damage_particles(target_slot.rect.center)
            
            # Trigger animação de ataque do jogador
            animation_manager.play_animation("knight", "attack", force_restart=True)
            
            # Trigger animação de hurt do inimigo alvo
            target_index = self.combat_engine.enemies.index(self.targeted_enemy)
            enemy_anim_id = f"{self._get_enemy_anim_id(self.targeted_enemy)}_{target_index}"
            animation_manager.play_animation(enemy_anim_id, "hurt", force_restart=True)
            
            # Aplicar efeito da carta
            self._apply_card_effect(self.selected_card, self.targeted_enemy)
            self._finish_card_use()
            
    def _apply_card_effect(self, card: Card, target):
        """Aplica o efeito da carta no combate."""
        try:
            # Usar o combat engine para aplicar a carta
            if hasattr(self.combat_engine, 'use_card'):
                self.combat_engine.use_card(card, target)
            logger.info(f"Applied card effect: {card} on {target}")
        except Exception as e:
            logger.error(f"Failed to apply card effect: {e}")
            
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
        
    def _cancel_card_selection(self):
        """Cancela seleção de carta."""
        self.selected_card = None
        self.state = CombatState.PLAYER_TURN
        
    def _cancel_target_selection(self):
        """Cancela seleção de alvo."""
        self.targeted_enemy = None
        self.state = CombatState.CARD_SELECTION
        
    def _end_turn(self):
        """Finaliza o turno do jogador."""
        try:
            # Trigger turn transition animation
            self._start_turn_transition()
            
            # Usar combat engine para processar fim de turno
            if hasattr(self.combat_engine, 'end_turn'):
                self.combat_engine.end_turn()
                
            self.state = CombatState.ENEMY_TURN
            logger.info("Player turn ended")
        except Exception as e:
            logger.error(f"Failed to end turn: {e}")
            
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
        5. Zona da mão com slots definidos
        6. Botões polidos
        7. Overlays finais
        """
        # 1. Background IA escalado para tela
        self.screen.blit(self.background, (0, 0))
        
        # 2. Zona de inimigos com overlay escuro + sprites
        self._draw_enemy_zone()
        
        # 3. Sprite do jogador centralizado
        self._draw_player_sprite()
        
        # 4. Zona da mão do jogador
        self._draw_player_hand()
        
        # 5. Botões
        self._draw_buttons()
        
        # 6. Debug info (se necessário)
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self._draw_debug_info()
            
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
        """Desenha sprite do jogador centralizado usando animação 30fps."""
        # Obter frame atual da animação do knight
        current_frame = animation_manager.get_current_frame("knight")
        
        if current_frame:
            # Posicionar sprite do jogador no centro-base, acima da zona da mão
            sprite_rect = current_frame.get_rect(
                midbottom=(self.width // 2, self.player_hand_zone.top - 10)
            )
            self.screen.blit(current_frame, sprite_rect)
        elif self.player_sprite:
            # Fallback para sprite estático
            sprite_rect = self.player_sprite.get_rect(
                midbottom=(self.width // 2, self.player_hand_zone.top - 10)
            )
            self.screen.blit(self.player_sprite, sprite_rect)
            
    def _draw_player_hand(self):
        """Desenha zona da mão do jogador com painel e slots."""
        # Painel azul-escuro translúcido para a mão
        hand_overlay = pygame.Surface(self.player_hand_zone.size, pygame.SRCALPHA)
        hand_overlay.fill((30, 40, 90, 200))  # Azul-escuro translúcido
        self.screen.blit(hand_overlay, self.player_hand_zone.topleft)
        
        # Desenhar 5 slots para cartas
        slot_width = self.player_hand_zone.width // 5
        slot_height = self.player_hand_zone.height - 20  # Margem interna
        
        for i in range(5):
            slot_x = self.player_hand_zone.left + i * slot_width + 10
            slot_y = self.player_hand_zone.top + 10
            
            slot_rect = pygame.Rect(slot_x, slot_y, slot_width - 20, slot_height)
            
            # Outline do slot
            pygame.draw.rect(self.screen, (80, 80, 80), slot_rect, 2)
            
            # Fundo do slot
            pygame.draw.rect(self.screen, (50, 50, 50, 100), slot_rect)
            
    def _draw_buttons(self):
        """Desenha botões da interface."""
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
        self.particle_system.draw(self.screen)
        
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
