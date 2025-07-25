"""
Menu principal redesenhado com estética clean e pintura digital.

Features:
- Background cinematográfico com parallax sutil
- Botões com texturas IA e micro-animações
- Tipografia medieval elegante
- Partículas atmosféricas
- Transições suaves
"""

import pygame
import logging
from typing import Optional, Dict, Any

from ..ui.painted_ui import (
    initialize_painted_ui, 
    create_painted_button,
    parallax_bg,
    atmospheric_particles,
    PaintedButton
)
from ..ui.animation import animate_to, EasingType, animation_manager
from ..ui.theme import theme
from ..utils.asset_loader import get_asset

logger = logging.getLogger(__name__)


class CleanMenuScreen:
    """
    Menu principal com design clean e estética de pintura digital.
    
    Layout:
    - Background: grande sala de banquetes medieval (asset IA)
    - Título: "Medieval Deck" centralizado com tipografia elegante
    - Botões: texturas metálicas com estados hover/pressed
    - Partículas: atmosfera neutra com motas flutuantes
    - Parallax: movimento sutil baseado no mouse
    """
    
    def __init__(self, screen: pygame.Surface, config, asset_generator=None):
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        # Dimensões da tela
        self.screen_width = config.ui.window_width
        self.screen_height = config.ui.window_height
        
        # Estado da tela
        self.initialized = False
        self.intro_complete = False
        self.pending_action = None
        
        # Elementos UI
        self.buttons: Dict[str, PaintedButton] = {}
        self.title_alpha = 0
        self.buttons_alpha = 0
        
        # Configuração visual
        self.title_font = None
        self.subtitle_font = None
        
        # Inicializar
        self._initialize_ui()
        self._load_assets()
        self._create_buttons()
        
        logger.info("CleanMenuScreen inicializado")
    
    def _initialize_ui(self):
        """Inicializa sistema de UI painted."""
        if not self.initialized:
            initialize_painted_ui(self.screen_width, self.screen_height)
            self.initialized = True
    
    def _load_assets(self):
        """Carrega assets IA para o menu."""
        # Tentar carregar o novo background melhorado primeiro
        from pathlib import Path
        from ..utils.asset_loader import asset_loader
        
        try:
            # Verificar se existe o novo background melhorado
            main_menu_bg_path = Path("assets/generated/main_menu_bg.png")
            
            if main_menu_bg_path.exists():
                logger.info(f"🎨 Carregando background melhorado: {main_menu_bg_path}")
                # Carregar background melhorado diretamente
                main_menu_surface = pygame.image.load(str(main_menu_bg_path)).convert()
                
                # Redimensionar se necessário
                if main_menu_surface.get_size() != (self.screen_width, self.screen_height):
                    main_menu_surface = pygame.transform.scale(
                        main_menu_surface, (self.screen_width, self.screen_height)
                    )
                
                # Aplicar ao sistema de parallax se disponível
                if parallax_bg:
                    # Criar um asset temporário no loader para o parallax
                    if hasattr(asset_loader, 'assets'):
                        asset_loader.assets["main_menu_bg"] = type('AssetInfo', (), {
                            'surface': main_menu_surface,
                            'name': 'main_menu_bg'
                        })()
                    parallax_bg.set_background("main_menu_bg")
                    logger.info("✅ Background melhorado carregado no parallax")
                else:
                    # Armazenar para uso direto
                    self.menu_background = main_menu_surface
                    logger.info("✅ Background melhorado carregado diretamente")
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar background melhorado: {e}")
            
            # Fallback para o sistema antigo
            menu_bg = get_asset("menu_bg")
            if menu_bg and parallax_bg:
                parallax_bg.set_background("menu_bg")
                logger.info("Background do menu carregado (fallback)")
            else:
                if not menu_bg:
                    logger.warning("Background do menu não encontrado")
                if not parallax_bg:
                    logger.warning("ParallaxBackground não está inicializado")
        
        # Configurar partículas neutras
        if atmospheric_particles:
            atmospheric_particles.set_theme("neutral")
        
        # Carregar fontes
        self.title_font = theme.typography.get_font('title_large')
        self.subtitle_font = theme.typography.get_font('title_medium')
    
    def _create_buttons(self):
        """Cria botões do menu com layout centralizado."""
        # Configuração dos botões
        button_width = 300
        button_height = 70
        button_spacing = 20
        
        # Calcular posição central
        total_height = 4 * button_height + 3 * button_spacing
        start_y = (self.screen_height - total_height) // 2 + 100  # Offset para título
        center_x = self.screen_width // 2 - button_width // 2
        
        # Definir botões
        button_configs = [
            ("start_game", "Start Game", lambda: self._trigger_action("new_game")),
            ("continue", "Continue", lambda: self._trigger_action("continue_game")),
            ("settings", "Settings", lambda: self._trigger_action("settings")),
            ("quit", "Quit Game", lambda: self._trigger_action("quit_game"))
        ]
        
        # Crear botões
        for i, (key, text, callback) in enumerate(button_configs):
            y = start_y + i * (button_height + button_spacing)
            
            try:
                button = create_painted_button(
                    center_x, y, button_width, button_height,
                    text, callback
                )
                
                # Configurar alpha inicial para animação de entrada
                button.alpha = 0
                
                self.buttons[key] = button
                
                logger.info(f"✅ Botão painted criado: {text} em ({center_x}, {y})")
                
            except Exception as e:
                logger.warning(f"❌ Falha ao criar botão painted, usando fallback: {e}")
                # Fallback: criar botão simples
                self.buttons[key] = {
                    'rect': pygame.Rect(center_x, y, button_width, button_height),
                    'text': text,
                    'callback': callback,
                    'alpha': 255,  # Fallback sempre visível
                    'is_fallback': True
                }
                logger.info(f"🔧 Botão fallback criado: {text} em ({center_x}, {y})")
        
        logger.info(f"📊 Total de botões criados: {len(self.buttons)}")
    
    def enter_screen(self):
        """Chamado quando a tela é exibida."""
        if not self.intro_complete:
            self.start_intro_animations()
    
    def start_intro_animations(self):
        """Inicia animações de introdução."""
        logger.info("🎬 Iniciando animações de introdução...")
        try:
            # Fade in do título
            logger.info(f"📝 Título alpha inicial: {self.title_alpha}")
            animate_to(self, 'title_alpha', 255, 0.8, EasingType.EASE_OUT)
            
            # Stagger dos botões com delay
            painted_buttons = 0
            fallback_buttons = 0
            for i, button in enumerate(self.buttons.values()):
                if hasattr(button, 'alpha'):  # Painted button
                    painted_buttons += 1
                    delay = 0.3 + i * 0.1  # 300ms + 100ms por botão
                    logger.info(f"🎨 Animando botão painted {i}: alpha {button.alpha} -> 255")
                    animate_to(button, 'alpha', 255, 0.5, EasingType.EASE_OUT, delay=delay)
                else:  # Fallback button
                    fallback_buttons += 1
                    logger.info(f"🔧 Botão fallback {i} já visível")
            
            logger.info(f"📊 Botões: {painted_buttons} painted, {fallback_buttons} fallback")
            
            # Marcar intro como completo após todas as animações
            def mark_complete():
                self.intro_complete = True
                logger.info("✅ Animações de introdução completas")
            
            # Agendar callback após última animação
            total_time = 0.3 + len(self.buttons) * 0.1 + 0.5
            animate_to(self, 'buttons_alpha', 255, 0.1, EasingType.LINEAR, delay=total_time, on_complete=mark_complete)
            
        except Exception as e:
            logger.error(f"❌ Falha nas animações, usando fallback: {e}")
            # Fallback: tornar tudo visível imediatamente
            self.title_alpha = 255
            for button in self.buttons.values():
                if hasattr(button, 'alpha'):
                    button.alpha = 255
            self.intro_complete = True
            logger.info("🔧 Fallback ativado: tudo visível imediatamente")
        
        logger.info("Animações de intro iniciadas")
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos do menu.
        
        Args:
            event: Evento pygame
            
        Returns:
            Ação a ser executada ou None
        """
        # Atualizar posição do mouse para parallax
        if event.type == pygame.MOUSEMOTION:
            if parallax_bg:
                parallax_bg.update_mouse_position(event.pos)
        
        # Processar eventos dos botões
        for button in self.buttons.values():
            if hasattr(button, 'handle_event'):  # Painted button
                if button.handle_event(event):
                    # Verificar se há ação pendente
                    if self.pending_action:
                        action = self.pending_action
                        self.pending_action = None
                        return action
                    return None  # Evento processado pelo botão
            elif isinstance(button, dict) and button.get('is_fallback'):  # Fallback button
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and button['rect'].collidepoint(event.pos):
                        button['callback']()
                        # Verificar se há ação pendente
                        if self.pending_action:
                            action = self.pending_action
                            self.pending_action = None
                            return action
        
        # Teclas de atalho
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return "new_game"
            elif event.key == pygame.K_ESCAPE:
                return "quit_game"
        
        return None
    
    def _trigger_action(self, action: str):
        """Armazena ação para ser retornada no próximo handle_event."""
        self.pending_action = action
    
    def update(self, dt: float):
        """
        Atualiza animações e estado do menu.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar animações globais
        animation_manager.update()
        
        # Atualizar partículas
        if atmospheric_particles:
            atmospheric_particles.update(dt)
        
        # Atualizar botões
        for button in self.buttons.values():
            if hasattr(button, 'update'):  # Painted button
                button.update(dt)
            # Fallback buttons não precisam de update
    
    def draw(self):
        """Desenha o menu completo."""
        # Limpar tela
        self.screen.fill((10, 10, 15))  # Azul escuro muito sutil
        
        # Desenhar background com parallax
        if parallax_bg:
            parallax_bg.draw(self.screen)
        
        # Desenhar partículas atmosféricas
        if atmospheric_particles:
            atmospheric_particles.draw(self.screen)
        
        # Desenhar título
        self._draw_title()
        
        # Desenhar botões
        for button in self.buttons.values():
            if hasattr(button, 'draw'):  # Painted button
                if button.alpha > 0:
                    button.draw(self.screen)
            elif isinstance(button, dict) and button.get('is_fallback'):  # Fallback button
                self._draw_fallback_button(button)
        
        # Desenhar overlay sutil para profundidade
        self._draw_atmospheric_overlay()
    
    def _draw_fallback_button(self, button):
        """Desenha botão fallback simples."""
        rect = button['rect']
        text = button['text']
        alpha = button['alpha']
        
        # Cor do botão
        button_color = (60, 45, 30)  # Marrom medieval
        border_color = (120, 90, 60)  # Marrom claro para borda
        text_color = (245, 245, 220)  # Cor pergaminho
        
        # Desenhar botão
        pygame.draw.rect(self.screen, button_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)
        
        # Desenhar texto
        font = pygame.font.Font(None, 36)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_title(self):
        """Desenha título do jogo com tipografia elegante."""
        if self.title_alpha <= 0:
            return
        
        # Título principal
        title_text = "Medieval Deck"
        title_color = theme.colors.GOLD_PRIMARY
        
        title_surface = self.title_font.render(title_text, True, title_color)
        
        # Aplicar alpha
        if self.title_alpha < 255:
            title_surface = title_surface.copy()
            title_surface.set_alpha(int(self.title_alpha))
        
        # Posição centralizada no terço superior
        title_rect = title_surface.get_rect(
            center=(self.screen_width // 2, self.screen_height // 4)
        )
        
        # Sombra do título
        shadow_color = (0, 0, 0, 120)
        shadow_surface = self.title_font.render(title_text, True, shadow_color)
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        
        # Desenhar sombra e título
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # Subtítulo
        subtitle_text = "AI-Generated Medieval Card Game"
        subtitle_color = theme.colors.PARCHMENT
        
        subtitle_surface = self.subtitle_font.render(subtitle_text, True, subtitle_color)
        
        if self.title_alpha < 255:
            subtitle_surface = subtitle_surface.copy()
            subtitle_surface.set_alpha(int(self.title_alpha * 0.8))
        
        subtitle_rect = subtitle_surface.get_rect(
            center=(self.screen_width // 2, title_rect.bottom + 20)
        )
        
        self.screen.blit(subtitle_surface, subtitle_rect)
    
    def _draw_atmospheric_overlay(self):
        """Desenha overlay atmosférico para profundidade."""
        # Gradient sutil nas bordas
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # Vinheta sutil
        center = (self.screen_width // 2, self.screen_height // 2)
        max_distance = max(self.screen_width, self.screen_height) // 2
        
        for y in range(0, self.screen_height, 4):  # Skip pixels para performance
            for x in range(0, self.screen_width, 4):
                distance = ((x - center[0]) ** 2 + (y - center[1]) ** 2) ** 0.5
                
                if distance > max_distance * 0.7:
                    alpha = min(30, int((distance - max_distance * 0.7) / (max_distance * 0.3) * 30))
                    overlay.set_at((x, y), (0, 0, 0, alpha))
        
        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _start_game(self):
        """Callback para iniciar novo jogo."""
        logger.info("Iniciando novo jogo...")
    
    def _continue_game(self):
        """Callback para continuar jogo."""
        logger.info("Continuando jogo...")
    
    def _open_settings(self):
        """Callback para abrir configurações."""
        logger.info("Abrindo configurações...")
    
    def _quit_game(self):
        """Callback para sair do jogo."""
        logger.info("Saindo do jogo...")
