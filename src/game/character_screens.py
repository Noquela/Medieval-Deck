"""
Telas individuais de personagens para Medieval Deck.

Cada personagem (Knight, Wizard, Assassin) tem sua própria tela dedicada
com fundo temático, estatísticas detalhadas e história/lore.
"""

import pygame
import math
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PIL import Image, ImageFilter
from ..utils.config import Config
from ..generators.asset_generator import AssetGenerator

logger = logging.getLogger(__name__)


class CharacterScreen:
    """
    Tela individual de personagem com fundo temático e informações detalhadas.
    
    Features:
    - Fundo gerado por IA específico para cada personagem
    - Painel lateral com estatísticas e lore
    - Animações de transição suaves
    - Botão de seleção estilizado
    """
    
    def __init__(self, 
                 screen: pygame.Surface, 
                 config: Config,
                 character_data: Dict[str, Any],
                 asset_generator: Optional[AssetGenerator] = None):
        """
        Inicializa a tela do personagem.
        
        Args:
            screen: Surface principal do Pygame
            config: Configurações do jogo
            character_data: Dados do personagem (stats, lore, etc.)
            asset_generator: Gerador de assets IA (opcional)
        """
        self.screen = screen
        self.config = config
        self.character_data = character_data
        self.asset_generator = asset_generator
        
        # Dimensões da tela
        self.width = config.ui.window_width
        self.height = config.ui.window_height
        
        # Estado da animação
        self.fade_alpha = 0
        self.fade_direction = 1  # 1 para fade in, -1 para fade out
        self.fade_duration = config.ui.character_screen_fade_duration
        self.animation_time = 0
        self.transitioning = False
        
        # Cores temáticas baseadas no personagem
        self.theme_colors = self._get_theme_colors()
        
        # Inicializar fontes
        self._setup_fonts()
        
        # Carregar assets
        self._load_assets()
        
        # Configurar painel lateral
        self._setup_panel()
        
        # Configurar botões
        self._setup_buttons()
        
        logger.info(f"Tela do personagem {character_data['name']} inicializada")
    
    def _get_theme_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Retorna cores temáticas baseadas no tipo de personagem."""
        character_type = self.character_data.get('type', 'knight_01')
        
        if 'knight' in character_type:
            return {
                'primary': (255, 215, 0),      # Dourado
                'secondary': (184, 134, 11),   # Dourado escuro
                'accent': (255, 255, 255),     # Branco
                'background': (40, 35, 25),    # Marrom escuro
                'panel': (60, 50, 35),         # Marrom médio
                'text': (255, 255, 255),       # Branco
                'glow': (255, 215, 0)          # Dourado brilhante
            }
        elif 'wizard' in character_type:
            return {
                'primary': (138, 43, 226),     # Roxo
                'secondary': (75, 0, 130),     # Índigo
                'accent': (186, 85, 211),      # Orchid
                'background': (25, 25, 40),    # Azul escuro
                'panel': (35, 35, 60),         # Azul médio
                'text': (255, 255, 255),       # Branco
                'glow': (138, 43, 226)         # Roxo brilhante
            }
        elif 'assassin' in character_type:
            return {
                'primary': (50, 205, 50),      # Verde lima
                'secondary': (34, 139, 34),    # Verde floresta
                'accent': (144, 238, 144),     # Verde claro
                'background': (15, 15, 15),    # Preto
                'panel': (25, 25, 25),         # Cinza escuro
                'text': (255, 255, 255),       # Branco
                'glow': (50, 205, 50)          # Verde brilhante
            }
        else:
            # Cores padrão
            return {
                'primary': (100, 100, 100),
                'secondary': (70, 70, 70),
                'accent': (150, 150, 150),
                'background': (30, 30, 30),
                'panel': (50, 50, 50),
                'text': (255, 255, 255),
                'glow': (100, 100, 100)
            }
    
    def _setup_fonts(self):
        """Configura as fontes para diferentes elementos."""
        try:
            # Fontes em tamanhos diferentes para ultrawide
            self.title_font = pygame.font.Font(None, 84)      # Nome do personagem
            self.header_font = pygame.font.Font(None, 48)     # Seções (Stats, Lore)
            self.text_font = pygame.font.Font(None, 36)       # Texto geral
            self.stat_font = pygame.font.Font(None, 42)       # Estatísticas
            self.button_font = pygame.font.Font(None, 54)     # Botões
        except:
            # Fallback para fonte padrão
            self.title_font = pygame.font.Font(None, 84)
            self.header_font = pygame.font.Font(None, 48)
            self.text_font = pygame.font.Font(None, 36)
            self.stat_font = pygame.font.Font(None, 42)
            self.button_font = pygame.font.Font(None, 54)
    
    def _load_assets(self):
        """Carrega os assets do personagem (fundo e imagem)."""
        self.background_surface = None
        self.character_portrait = None
        
        # Tentar carregar fundo gerado por IA
        if self.asset_generator:
            try:
                background_type = self.character_data.get('background_type', 'castle')
                bg_image = self.asset_generator.generate_card_image(
                    background_type, 
                    force_regenerate=False
                )
                
                if bg_image:
                    # Redimensionar para ultrawide
                    bg_resized = bg_image.resize((self.width, self.height), Image.LANCZOS)
                    
                    # Aplicar desfoque sutil
                    bg_blurred = bg_resized.filter(ImageFilter.GaussianBlur(radius=3))
                    
                    # Converter para surface do Pygame
                    self.background_surface = pygame.image.fromstring(
                        bg_blurred.tobytes(), bg_blurred.size, bg_blurred.mode
                    ).convert()
                    
                    logger.info(f"Fundo carregado para {self.character_data['name']}")
                    
            except Exception as e:
                logger.warning(f"Falha ao carregar fundo IA: {e}")
        
        # Fundo de fallback com gradiente temático
        if self.background_surface is None:
            self.background_surface = self._create_gradient_background()
        
        # Tentar carregar retrato do personagem
        try:
            character_type = self.character_data.get('type', 'knight_01')
            if self.asset_generator:
                char_image = self.asset_generator.generate_card_image(
                    character_type,
                    force_regenerate=False
                )
                
                if char_image:
                    # Redimensionar para portrait
                    portrait_size = (400, 600)
                    char_resized = char_image.resize(portrait_size, Image.LANCZOS)
                    
                    self.character_portrait = pygame.image.fromstring(
                        char_resized.tobytes(), char_resized.size, char_resized.mode
                    ).convert_alpha()
                    
        except Exception as e:
            logger.warning(f"Falha ao carregar retrato: {e}")
            # Criar placeholder
            self.character_portrait = self._create_character_placeholder()
    
    def _create_gradient_background(self) -> pygame.Surface:
        """Cria um fundo com gradiente temático como fallback."""
        surface = pygame.Surface((self.width, self.height))
        
        primary = self.theme_colors['primary']
        background = self.theme_colors['background']
        
        # Criar gradiente vertical
        for y in range(self.height):
            ratio = y / self.height
            color = [
                int(background[i] + (primary[i] - background[i]) * ratio * 0.3)
                for i in range(3)
            ]
            pygame.draw.line(surface, color, (0, y), (self.width, y))
        
        return surface.convert()
    
    def _create_character_placeholder(self) -> pygame.Surface:
        """Cria um placeholder para o retrato do personagem."""
        surface = pygame.Surface((400, 600), pygame.SRCALPHA)
        
        # Desenhar silhueta simples
        pygame.draw.ellipse(surface, self.theme_colors['primary'], 
                          (100, 50, 200, 250))  # Cabeça
        pygame.draw.rect(surface, self.theme_colors['primary'],
                        (120, 300, 160, 300))   # Corpo
        
        return surface
    
    def _setup_panel(self):
        """Configura o painel lateral com informações."""
        panel_width = self.config.ui.character_panel_width
        panel_height = self.height - 200
        panel_x = self.width - panel_width - 50
        panel_y = 100
        
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Surface do painel com transparência
        self.panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
    def _setup_buttons(self):
        """Configura os botões da tela."""
        button_width = 300
        button_height = 80
        
        # Botão "Selecionar Personagem"
        select_x = self.width - button_width - 50
        select_y = self.height - button_height - 50
        self.select_button = {
            'rect': pygame.Rect(select_x, select_y, button_width, button_height),
            'text': 'Selecionar Personagem',
            'hovered': False,
            'action': 'select_character'
        }
        
        # Botão "Voltar"
        back_x = 50
        back_y = self.height - button_height - 50
        self.back_button = {
            'rect': pygame.Rect(back_x, back_y, 200, button_height),
            'text': 'Voltar',
            'hovered': False,
            'action': 'back_to_selection'
        }
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos da tela.
        
        Args:
            event: Evento do Pygame
            
        Returns:
            Ação a ser executada ou None
        """
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # Verificar hover nos botões
            self.select_button['hovered'] = self.select_button['rect'].collidepoint(mouse_pos)
            self.back_button['hovered'] = self.back_button['rect'].collidepoint(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo
                mouse_pos = event.pos
                
                if self.select_button['rect'].collidepoint(mouse_pos):
                    self.start_fade_out()
                    return self.select_button['action']
                elif self.back_button['rect'].collidepoint(mouse_pos):
                    self.start_fade_out()
                    return self.back_button['action']
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.start_fade_out()
                return 'back_to_selection'
            elif event.key == pygame.K_RETURN:
                self.start_fade_out()
                return 'select_character'
        
        return None
    
    def start_fade_in(self):
        """Inicia animação de fade in."""
        self.fade_alpha = 0
        self.fade_direction = 1
        self.transitioning = True
    
    def start_fade_out(self):
        """Inicia animação de fade out."""
        self.fade_alpha = 255
        self.fade_direction = -1
        self.transitioning = True
    
    def update(self, dt: float):
        """
        Atualiza a lógica da tela.
        
        Args:
            dt: Delta time em segundos
        """
        self.animation_time += dt
        
        # Atualizar fade
        if self.transitioning:
            fade_speed = 255 / self.fade_duration
            self.fade_alpha += self.fade_direction * fade_speed * dt
            
            if self.fade_direction == 1 and self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.transitioning = False
            elif self.fade_direction == -1 and self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.transitioning = False
    
    def draw(self):
        """Desenha a tela do personagem."""
        # Desenhar fundo
        if self.background_surface:
            self.screen.blit(self.background_surface, (0, 0))
        else:
            self.screen.fill(self.theme_colors['background'])
        
        # Aplicar overlay escuro para melhorar legibilidade
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        # Desenhar retrato do personagem (lado esquerdo)
        if self.character_portrait:
            # Posição centralizada verticalmente, lado esquerdo
            portrait_x = 200
            portrait_y = (self.height - self.character_portrait.get_height()) // 2
            
            # Efeito de brilho pulsante
            glow_intensity = int(30 + 20 * math.sin(self.animation_time * 2))
            glow_surface = pygame.Surface(
                (self.character_portrait.get_width() + 20, 
                 self.character_portrait.get_height() + 20), 
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surface, 
                           (*self.theme_colors['glow'], glow_intensity),
                           glow_surface.get_rect())
            
            self.screen.blit(glow_surface, (portrait_x - 10, portrait_y - 10))
            self.screen.blit(self.character_portrait, (portrait_x, portrait_y))
        
        # Desenhar painel de informações
        self._draw_info_panel()
        
        # Desenhar botões
        self._draw_buttons()
        
        # Aplicar fade se necessário
        if self.fade_alpha < 255:
            fade_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, 255 - self.fade_alpha))
            self.screen.blit(fade_overlay, (0, 0))
    
    def _draw_info_panel(self):
        """Desenha o painel lateral com informações do personagem."""
        # Limpar painel
        self.panel_surface.fill((0, 0, 0, 0))
        
        # Fundo do painel com transparência
        panel_bg = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
        panel_bg.fill((*self.theme_colors['panel'], self.config.ui.character_panel_alpha))
        self.panel_surface.blit(panel_bg, (0, 0))
        
        # Borda do painel
        pygame.draw.rect(self.panel_surface, self.theme_colors['primary'], 
                        (0, 0, self.panel_rect.width, self.panel_rect.height), 3)
        
        y_offset = 30
        
        # Nome do personagem
        name_text = self.title_font.render(self.character_data['name'], True, 
                                         self.theme_colors['accent'])
        name_rect = name_text.get_rect(centerx=self.panel_rect.width // 2)
        self.panel_surface.blit(name_text, (name_rect.x, y_offset))
        y_offset += 100
        
        # Descrição
        desc_header = self.header_font.render("História", True, self.theme_colors['primary'])
        self.panel_surface.blit(desc_header, (20, y_offset))
        y_offset += 50
        
        # Quebrar texto da descrição
        description = self.character_data.get('description', 'Descrição não disponível.')
        desc_lines = self._wrap_text(description, self.panel_rect.width - 40)
        for line in desc_lines:
            line_text = self.text_font.render(line, True, self.theme_colors['text'])
            self.panel_surface.blit(line_text, (20, y_offset))
            y_offset += 35
        
        y_offset += 30
        
        # Estatísticas
        stats_header = self.header_font.render("Atributos", True, self.theme_colors['primary'])
        self.panel_surface.blit(stats_header, (20, y_offset))
        y_offset += 50
        
        stats = self.character_data.get('stats', {})
        for stat_name, stat_value in stats.items():
            # Nome do atributo
            stat_text = self.stat_font.render(f"{stat_name}:", True, self.theme_colors['text'])
            self.panel_surface.blit(stat_text, (30, y_offset))
            
            # Valor do atributo
            value_text = self.stat_font.render(str(stat_value), True, self.theme_colors['accent'])
            self.panel_surface.blit(value_text, (200, y_offset))
            
            # Barra de progresso
            bar_x = 280
            bar_y = y_offset + 8
            bar_width = 250
            bar_height = 20
            
            # Fundo da barra
            pygame.draw.rect(self.panel_surface, (50, 50, 50), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Preenchimento da barra (assumindo max 30)
            fill_width = int((stat_value / 30.0) * bar_width)
            bar_color = self._get_stat_color(stat_name)
            pygame.draw.rect(self.panel_surface, bar_color,
                           (bar_x, bar_y, fill_width, bar_height))
            
            # Borda da barra
            pygame.draw.rect(self.panel_surface, self.theme_colors['text'],
                           (bar_x, bar_y, bar_width, bar_height), 2)
            
            y_offset += 45
        
        y_offset += 20
        
        # Habilidades
        abilities_header = self.header_font.render("Habilidades", True, self.theme_colors['primary'])
        self.panel_surface.blit(abilities_header, (20, y_offset))
        y_offset += 50
        
        abilities = self.character_data.get('abilities', [])
        for ability in abilities:
            ability_text = self.text_font.render(f"• {ability}", True, self.theme_colors['text'])
            self.panel_surface.blit(ability_text, (30, y_offset))
            y_offset += 35
        
        # Desenhar painel na tela
        self.screen.blit(self.panel_surface, self.panel_rect)
    
    def _draw_buttons(self):
        """Desenha os botões da tela."""
        buttons = [self.select_button, self.back_button]
        
        for button in buttons:
            # Cor do botão baseada no hover
            if button['hovered']:
                button_color = self.theme_colors['primary']
                text_color = self.theme_colors['background']
                border_width = 4
            else:
                button_color = self.theme_colors['background']
                text_color = self.theme_colors['text']
                border_width = 2
            
            # Desenhar fundo do botão
            pygame.draw.rect(self.screen, button_color, button['rect'])
            
            # Desenhar borda
            pygame.draw.rect(self.screen, self.theme_colors['primary'], 
                           button['rect'], border_width)
            
            # Desenhar texto
            text = self.button_font.render(button['text'], True, text_color)
            text_rect = text.get_rect(center=button['rect'].center)
            self.screen.blit(text, text_rect)
    
    def _wrap_text(self, text: str, max_width: int) -> list:
        """Quebra texto para caber na largura especificada."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = self.text_font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_stat_color(self, stat_name: str) -> Tuple[int, int, int]:
        """Retorna cor da barra baseada no tipo de atributo."""
        colors = {
            "Health": (220, 60, 60),     # Vermelho
            "Attack": (220, 120, 60),    # Laranja  
            "Defense": (60, 120, 220),   # Azul
            "Magic": (160, 60, 220),     # Roxo
            "Speed": (60, 220, 120),     # Verde
        }
        return colors.get(stat_name, self.theme_colors['primary'])
    
    def is_transitioning(self) -> bool:
        """Retorna se está em transição."""
        return self.transitioning


class CharacterScreenManager:
    """
    Gerenciador das telas individuais de personagens.
    
    Controla a criação, navegação e transições entre as telas de personagens.
    """
    
    def __init__(self, 
                 screen: pygame.Surface, 
                 config: Config,
                 asset_generator: Optional[AssetGenerator] = None):
        """
        Inicializa o gerenciador.
        
        Args:
            screen: Surface principal do Pygame
            config: Configurações do jogo
            asset_generator: Gerador de assets IA (opcional)
        """
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        # Dados dos personagens
        self.characters_data = {
            'knight_01': {
                'name': 'Cavaleiro Valente',
                'type': 'knight_01',
                'description': 'Um bravo cavaleiro em armadura reluzente, defensor do reino. Sua honra é inabalável e sua coragem lendária. Nascido na nobreza, dedicou sua vida a proteger os inocentes e manter a paz nas terras medievais.',
                'stats': {
                    'Vida': 30,
                    'Ataque': 8,
                    'Defesa': 12,
                    'Magia': 3,
                    'Velocidade': 6
                },
                'abilities': ['Muralha de Escudos', 'Ataque Carregado', 'Provocar'],
                'background_type': 'castle'
            },
            'wizard_01': {
                'name': 'Mestre Arcano',
                'type': 'wizard_01',
                'description': 'Um poderoso mago que domina as artes místicas e conhecimentos proibidos. Estudioso incansável dos segredos do universo, ele manipula as forças elementais com maestria incomparável.',
                'stats': {
                    'Vida': 20,
                    'Ataque': 5,
                    'Defesa': 6,
                    'Magia': 15,
                    'Velocidade': 8
                },
                'abilities': ['Bola de Fogo', 'Escudo de Gelo', 'Teletransporte'],
                'background_type': 'wizard'
            },
            'assassin_01': {
                'name': 'Assassino das Sombras',
                'type': 'assassin_01',
                'description': 'Um assassino mortal que ataca das sombras com precisão letal. Mestre da furtividade e venenos, ele se move como fantasma pelas ruas escuras, executando sua justiça silenciosa.',
                'stats': {
                    'Vida': 25,
                    'Ataque': 12,
                    'Defesa': 7,
                    'Magia': 6,
                    'Velocidade': 14
                },
                'abilities': ['Furtividade', 'Lâmina Envenenada', 'Ataque Crítico'],
                'background_type': 'forest'
            }
        }
        
        self.current_character_screen = None
        
        logger.info("Gerenciador de telas de personagens inicializado")
    
    def show_character(self, character_type: str) -> CharacterScreen:
        """
        Mostra a tela de um personagem específico.
        
        Args:
            character_type: Tipo do personagem (knight_01, wizard_01, assassin_01)
            
        Returns:
            Tela do personagem criada
        """
        if character_type in self.characters_data:
            character_data = self.characters_data[character_type]
            
            self.current_character_screen = CharacterScreen(
                screen=self.screen,
                config=self.config,
                character_data=character_data,
                asset_generator=self.asset_generator
            )
            
            # Iniciar fade in
            self.current_character_screen.start_fade_in()
            
            logger.info(f"Exibindo tela do personagem: {character_data['name']}")
            return self.current_character_screen
        else:
            logger.error(f"Tipo de personagem desconhecido: {character_type}")
            return None
    
    def get_current_screen(self) -> Optional[CharacterScreen]:
        """Retorna a tela atual do personagem."""
        return self.current_character_screen
    
    def clear_current_screen(self):
        """Limpa a tela atual do personagem."""
        self.current_character_screen = None
