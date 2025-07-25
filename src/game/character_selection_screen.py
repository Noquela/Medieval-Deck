"""
Character Selection Screen for Medieval Deck.

Tela única de personagem detalhado com navegação por setas e fundos gerados por IA.
"""

import pygame
import math
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from PIL import Image, ImageFilter

from ..utils.config import Config

# Import AssetGenerator opcionalmente para evitar dependências problemáticas
try:
    from ..generators.asset_generator import AssetGenerator
except ImportError:
    AssetGenerator = None

logger = logging.getLogger(__name__)


class CharacterSelectionScreen:
    """
    Tela de seleção com personagem único detalhado e navegação por setas.
    
    Features:
    - Navegação por setas entre personagens
    - Fundo gerado por IA específico para cada personagem
    - Informações detalhadas (imagem, história, atributos)
    - Animações suaves de transição
    - Resolução ultrawide (3440x1440)
    """
    
    def __init__(self, 
                 screen: pygame.Surface, 
                 config: Config,
                 asset_generator: Optional[Any] = None):
        """
        Inicializa a tela de seleção de personagens.
        
        Args:
            screen: Surface principal do Pygame
            config: Configurações do jogo
            asset_generator: Gerador de assets IA (opcional)
        """
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator if AssetGenerator else None
        
        # Dimensões da tela ultrawide
        self.width = 3440
        self.height = 1440
        
        # Dados dos personagens
        self.characters = [
            {
                "id": "knight",
                "name": "Cavaleiro Valente",
                "title": "Defensor do Reino",
                "attributes": {
                    "Vida": 30,
                    "Ataque": 8,
                    "Defesa": 12,
                    "Magia": 3,
                    "Velocidade": 6
                },
                "abilities": ["Muralha de Escudos", "Ataque Carregado", "Provocar"],
                "story": "Um bravo cavaleiro em armadura reluzente, defensor do reino. Nascido na nobreza, dedicou sua vida a proteger os inocentes e manter a paz nas terras medievais. Sua honra é inabalável e sua coragem lendária entre os súditos do reino.",
                "prompt": "epic medieval knight in golden armor, cathedral courtyard at sunset, dramatic cinematic lighting, castle banners flying, masterpiece, high quality, detailed",
                "theme_colors": {
                    "primary": (255, 215, 0),      # Dourado
                    "secondary": (184, 134, 11),   # Dourado escuro
                    "accent": (255, 255, 255),     # Branco
                    "background": (40, 35, 25),    # Marrom escuro
                    "text": (255, 255, 255)       # Branco
                }
            },
            {
                "id": "wizard",
                "name": "Mestre Arcano",
                "title": "Guardião dos Segredos",
                "attributes": {
                    "Vida": 20,
                    "Ataque": 5,
                    "Defesa": 6,
                    "Magia": 15,
                    "Velocidade": 8
                },
                "abilities": ["Bola de Fogo", "Escudo de Gelo", "Teletransporte"],
                "story": "Um poderoso mago que domina as artes místicas e conhecimentos proibidos. Estudioso incansável dos segredos do universo, ele manipula as forças elementais com maestria incomparável. Sua torre se ergue solitária, repleta de tomos antigos e artefatos mágicos.",
                "prompt": "arcane mage in dark blue robes, ancient library with glowing runes, floating magic particles, mystical atmosphere, purple and blue lighting, masterpiece, high quality, detailed",
                "theme_colors": {
                    "primary": (138, 43, 226),     # Roxo
                    "secondary": (75, 0, 130),     # Índigo
                    "accent": (186, 85, 211),      # Orchid
                    "background": (25, 25, 40),    # Azul escuro
                    "text": (255, 255, 255)       # Branco
                }
            },
            {
                "id": "assassin",
                "name": "Assassino das Sombras",
                "title": "Lâmina Silenciosa",
                "attributes": {
                    "Vida": 25,
                    "Ataque": 12,
                    "Defesa": 7,
                    "Magia": 6,
                    "Velocidade": 14
                },
                "abilities": ["Furtividade", "Lâmina Envenenada", "Ataque Crítico"],
                "story": "Um assassino mortal que ataca das sombras com precisão letal. Mestre da furtividade e venenos, ele se move como fantasma pelas ruas escuras, executando sua justiça silenciosa. Ninguém conhece seu verdadeiro rosto, apenas o medo que sua presença inspira.",
                "prompt": "dark rogue assassin in hood, purple misty fog, medieval stone alley at night, moonlight shadows, mysterious atmosphere, masterpiece, high quality, detailed",
                "theme_colors": {
                    "primary": (50, 205, 50),      # Verde lima
                    "secondary": (34, 139, 34),    # Verde floresta
                    "accent": (144, 238, 144),     # Verde claro
                    "background": (15, 15, 15),    # Preto
                    "text": (255, 255, 255)       # Branco
                }
            }
        ]
        
        # Estado atual
        self.current_character_index = 0
        self.current_character = self.characters[0]
        
        # Estado de transição
        self.transitioning = False
        self.transition_alpha = 255
        self.transition_direction = 0  # -1 para esquerda, 1 para direita
        self.transition_speed = 400.0  # alpha por segundo
        
        # Animação
        self.animation_time = 0
        
        # Assets carregados
        self.character_backgrounds = {}
        self.character_portraits = {}
        
        # Inicializar fontes para ultrawide
        self._setup_fonts()
        
        # Configurar layout
        self._setup_layout()
        
        # Configurar botões
        self._setup_buttons()
        
        # Carregar assets iniciais
        self._load_initial_assets()
        
        logger.info("Character selection screen initialized with navigation")
    
    def _setup_fonts(self):
        """Configura as fontes para resolução ultrawide."""
        try:
            # Fontes maiores para ultrawide
            self.title_font = pygame.font.Font(None, 96)      # Nome do personagem
            self.subtitle_font = pygame.font.Font(None, 64)   # Título do personagem
            self.header_font = pygame.font.Font(None, 56)     # Seções
            self.text_font = pygame.font.Font(None, 42)       # Texto geral
            self.stat_font = pygame.font.Font(None, 48)       # Estatísticas
            self.button_font = pygame.font.Font(None, 64)     # Botões
            self.arrow_font = pygame.font.Font(None, 120)     # Setas de navegação
        except:
            # Fallback para fonte padrão
            self.title_font = pygame.font.Font(None, 96)
            self.subtitle_font = pygame.font.Font(None, 64)
            self.header_font = pygame.font.Font(None, 56)
            self.text_font = pygame.font.Font(None, 42)
            self.stat_font = pygame.font.Font(None, 48)
            self.button_font = pygame.font.Font(None, 64)
            self.arrow_font = pygame.font.Font(None, 120)
    
    def _setup_layout(self):
        """Configura o layout para ultrawide."""
        # Área da imagem do personagem (lado esquerdo)
        self.portrait_area = pygame.Rect(200, 200, 800, 1000)
        
        # Área do painel de informações (lado direito)
        self.info_panel_area = pygame.Rect(1200, 150, 2000, 1100)
        
        # Área das setas de navegação
        self.left_arrow_area = pygame.Rect(50, 650, 100, 140)
        self.right_arrow_area = pygame.Rect(3290, 650, 100, 140)
    
    def _setup_buttons(self):
        """Configura os botões da tela."""
        # Botão "Selecionar Personagem"
        self.select_button = {
            'rect': pygame.Rect(2750, 1250, 400, 100),
            'text': 'Selecionar',
            'hovered': False,
            'action': 'select_character'
        }
        
        # Botão "Voltar"
        self.back_button = {
            'rect': pygame.Rect(100, 1250, 300, 100),
            'text': 'Voltar',
            'hovered': False,
            'action': 'back_to_menu'
        }
        
        # Estado de hover das setas
        self.left_arrow_hovered = False
        self.right_arrow_hovered = False
    
    def enter_screen(self) -> None:
        """Chamado quando a tela é ativada - carrega assets se necessário."""
        logger.info("Entrando na tela de seleção de personagens")
        # Garantir que os assets do personagem atual estão carregados
        self._load_character_assets(self.current_character)
        
        # Carregar assets dos outros personagens também
        for character in self.characters:
            if character["id"] != self.current_character["id"]:
                self._load_character_assets(character)
    
    def _load_initial_assets(self):
        """Carrega assets iniciais (fundo e retrato do personagem atual)."""
        # Carregar background principal da tela de seleção melhorado
        self._load_selection_background()
        
        # Carregar assets do personagem atual
        self._load_character_assets(self.current_character)
    
    def _load_selection_background(self):
        """Carrega o background principal melhorado da tela de seleção."""
        try:
            # Tentar carregar o novo background melhorado da tela de seleção
            selection_bg_path = self.config.assets_generated_dir / "character_selection_bg.png"
            
            if selection_bg_path.exists():
                logger.info(f"🎨 Carregando background melhorado da seleção: {selection_bg_path}")
                # Carregar background melhorado diretamente
                self.selection_background = pygame.image.load(str(selection_bg_path)).convert()
                
                # Redimensionar para resolução da tela se necessário
                screen_size = (self.screen.get_width(), self.screen.get_height())
                if self.selection_background.get_size() != screen_size:
                    self.selection_background = pygame.transform.scale(
                        self.selection_background, screen_size
                    )
                
                # Aplicar overlay sutil para melhorar legibilidade
                overlay = pygame.Surface(screen_size)
                overlay.set_alpha(40)  # Overlay bem sutil
                overlay.fill((0, 0, 0))
                self.selection_background.blit(overlay, (0, 0))
                
                logger.info("✅ Background melhorado da seleção carregado com sucesso")
                return
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar background melhorado da seleção: {e}")
        
        # Fallback: sem background específico da seleção
        self.selection_background = None
        logger.info("⚪ Usando backgrounds individuais dos personagens")
    
    def _load_character_assets(self, character: Dict[str, Any]):
        """
        Carrega ou gera assets para um personagem específico.
        
        Args:
            character: Dados do personagem
        """
        character_id = character["id"]
        logger.info(f"🎭 Carregando assets para personagem: {character['name']} (ID: {character_id})")
        
        # Carregar fundo já gerado
        if character_id not in self.character_backgrounds:
            bg_path = self.config.assets_generated_dir / f"{character_id}_bg.png"
            logger.info(f"📁 Tentando carregar background: {bg_path}")
            logger.info(f"📁 Arquivo existe: {bg_path.exists()}")
            
            if bg_path.exists():
                try:
                    # Carregar imagem gerada
                    bg_surface = pygame.image.load(str(bg_path)).convert()  # Usar convert() para backgrounds
                    logger.info(f"📐 Tamanho original da imagem: {bg_surface.get_size()}")
                    
                    # Redimensionar para resolução da tela
                    screen_size = (self.screen.get_width(), self.screen.get_height())
                    logger.info(f"📐 Tamanho da tela: {screen_size}")
                    
                    if bg_surface.get_size() != screen_size:
                        bg_surface = pygame.transform.scale(bg_surface, screen_size)
                        logger.info(f"📐 Imagem redimensionada para: {bg_surface.get_size()}")
                    
                    # Aplicar escurecimento suave
                    overlay = pygame.Surface(screen_size)
                    overlay.set_alpha(120)  # Um pouco mais escuro para melhor legibilidade
                    overlay.fill((0, 0, 0))
                    
                    bg_surface.blit(overlay, (0, 0))
                    
                    self.character_backgrounds[character_id] = bg_surface
                    logger.info(f"✅ Fundo carregado e processado para {character['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Falha ao carregar fundo para {character['name']}: {e}")
                    # Criar background fallback
                    bg_surface = pygame.Surface(screen_size)
                    bg_surface.fill(character.get("theme_colors", {}).get("background", (40, 35, 25)))
                    self.character_backgrounds[character_id] = bg_surface
            else:
                logger.warning(f"⚠️ Background não encontrado para {character['name']}: {bg_path}")
                # Criar background fallback
                bg_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
                bg_surface.fill(character.get("theme_colors", {}).get("background", (40, 35, 25)))
                self.character_backgrounds[character_id] = bg_surface
        else:
            logger.info(f"🎯 Background já carregado para {character['name']}")
        
        # Fallback: criar fundo gradiente se não encontrou a imagem
        if character_id not in self.character_backgrounds:
            self.character_backgrounds[character_id] = self._create_gradient_background(character)
        
        # Carregar sprite do personagem transparente gerado por IA
        if character_id not in self.character_portraits:
            # Primeiro tentar carregar sprite transparente específico
            transparent_sprite_path = self.config.assets_generated_dir / f"{character_id}_transparent.png"
            
            if transparent_sprite_path.exists():
                try:
                    logger.info(f"🎭 Carregando sprite transparente: {transparent_sprite_path}")
                    
                    # Carregar com transparência preservada
                    sprite_surface = pygame.image.load(str(transparent_sprite_path)).convert_alpha()
                    self.character_portraits[character_id] = sprite_surface
                    logger.info(f"✅ Sprite transparente carregado para {character['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar sprite transparente: {e}")
            
            # Fallback: tentar sprite normal existente
            elif (self.config.assets_generated_dir / f"{character_id}_sprite.png").exists():
                sprite_path = self.config.assets_generated_dir / f"{character_id}_sprite.png"
                try:
                    logger.info(f"� Carregando sprite normal: {sprite_path}")
                    
                    # Carregar com transparência preservada
                    sprite_surface = pygame.image.load(str(sprite_path)).convert_alpha()
                    self.character_portraits[character_id] = sprite_surface
                    logger.info(f"✅ Sprite normal carregado para {character['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar sprite normal: {e}")
            
            # Se não encontrou sprites, tentar gerar sprite transparente com IA
            elif self.asset_generator:
                try:
                    logger.info(f"🎨 Gerando sprite transparente de {character['name']} com IA...")
                    
                    # Gerar sprites transparentes usando nova função
                    results = self.asset_generator.generate_transparent_character_sprites(force_regenerate=True)
                    
                    # Carregar o sprite recém-gerado
                    sprite_key = f"{character_id}_transparent"
                    if sprite_key in results:
                        sprite_surface = pygame.image.load(results[sprite_key]).convert_alpha()
                        self.character_portraits[character_id] = sprite_surface
                        logger.info(f"✅ Sprite transparente de {character['name']} gerado e carregado!")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao gerar sprite transparente de {character['name']}: {e}")
            
            # Fallback: criar placeholder se não conseguiu carregar nem gerar sprite
            if character_id not in self.character_portraits:
                self.character_portraits[character_id] = self._create_character_placeholder(character)
    
    def _create_gradient_background(self, character: Dict[str, Any]) -> pygame.Surface:
        """Cria um fundo com gradiente temático como fallback."""
        surface = pygame.Surface((self.width, self.height))
        
        primary = character["theme_colors"]["primary"]
        background = character["theme_colors"]["background"]
        
        # Criar gradiente diagonal
        for y in range(self.height):
            for x in range(self.width):
                ratio_x = x / self.width
                ratio_y = y / self.height
                ratio = (ratio_x + ratio_y) / 2
                
                color = [
                    int(background[i] + (primary[i] - background[i]) * ratio * 0.2)
                    for i in range(3)
                ]
                surface.set_at((x, y), color)
        
        return surface.convert()
    
    def _create_character_placeholder(self, character: Dict[str, Any]) -> pygame.Surface:
        """Cria um placeholder para o retrato do personagem."""
        surface = pygame.Surface((800, 1000), pygame.SRCALPHA)
        
        primary_color = character["theme_colors"]["primary"]
        
        # Desenhar silhueta simples baseada no tipo
        if character["id"] == "knight":
            # Cavaleiro: escudo e espada
            pygame.draw.ellipse(surface, primary_color, (300, 100, 200, 250))  # Cabeça
            pygame.draw.rect(surface, primary_color, (250, 350, 300, 500))    # Corpo
            pygame.draw.ellipse(surface, primary_color, (150, 400, 100, 200)) # Escudo
            
        elif character["id"] == "wizard":
            # Mago: chapéu pontudo
            pygame.draw.ellipse(surface, primary_color, (300, 150, 200, 250))  # Cabeça
            pygame.draw.polygon(surface, primary_color, [(350, 150), (450, 150), (400, 50)]) # Chapéu
            pygame.draw.rect(surface, primary_color, (250, 400, 300, 500))    # Robes
            
        elif character["id"] == "assassin":
            # Assassino: capuz
            pygame.draw.ellipse(surface, primary_color, (300, 150, 200, 250))  # Cabeça
            pygame.draw.ellipse(surface, primary_color, (250, 100, 300, 300))  # Capuz
            pygame.draw.rect(surface, primary_color, (270, 400, 260, 500))    # Corpo magro
        
        return surface
    
    def _navigate_character(self, direction: int):
        """
        Navega para o próximo/anterior personagem.
        
        Args:
            direction: -1 para anterior, 1 para próximo
        """
        if self.transitioning:
            return
        
        # Calcular novo índice
        new_index = (self.current_character_index + direction) % len(self.characters)
        
        if new_index != self.current_character_index:
            # Iniciar transição
            self.transitioning = True
            self.transition_direction = direction
            self.transition_alpha = 255
            
            # Atualizar personagem atual
            self.current_character_index = new_index
            self.current_character = self.characters[new_index]
            
            # Carregar assets do novo personagem
            self._load_character_assets(self.current_character)
            
            logger.info(f"Navegando para: {self.current_character['name']}")
    
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
            
            # Verificar hover nas setas
            self.left_arrow_hovered = self.left_arrow_area.collidepoint(mouse_pos)
            self.right_arrow_hovered = self.right_arrow_area.collidepoint(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo
                mouse_pos = event.pos
                
                # Cliques nos botões
                if self.select_button['rect'].collidepoint(mouse_pos):
                    return self.select_button['action']
                elif self.back_button['rect'].collidepoint(mouse_pos):
                    return self.back_button['action']
                
                # Cliques nas setas
                elif self.left_arrow_area.collidepoint(mouse_pos):
                    self._navigate_character(-1)
                elif self.right_arrow_area.collidepoint(mouse_pos):
                    self._navigate_character(1)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self._navigate_character(-1)
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self._navigate_character(1)
            elif event.key == pygame.K_ESCAPE:
                return 'back_to_menu'
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return 'select_character'
        
        return None
    
    def update(self, dt: float):
        """
        Atualiza a lógica da tela.
        
        Args:
            dt: Delta time em segundos
        """
        self.animation_time += dt
        
        # Atualizar transição
        if self.transitioning:
            self.transition_alpha -= self.transition_speed * dt
            
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.transitioning = False
    
    def get_selected_character(self) -> Optional[str]:
        """Retorna o tipo do personagem selecionado."""
        return self.current_character["id"]
    
    def draw(self) -> None:
        """Desenha a tela de seleção de personagens."""
        
        # Usar sempre o background específico do personagem atual
        current_bg = self.character_backgrounds.get(self.current_character["id"])
        
        if current_bg:
            self.screen.blit(current_bg, (0, 0))
            logger.debug(f"🎨 Background específico desenhado para {self.current_character['name']}")
        else:
            logger.warning(f"❌ Background não encontrado para {self.current_character['name']} (ID: {self.current_character['id']})")
            logger.info(f"🗂️ Backgrounds disponíveis: {list(self.character_backgrounds.keys())}")
            # Fallback: usar cor temática do personagem
            self.screen.fill(self.current_character["theme_colors"]["background"])
        
        # Desenhar retrato do personagem
        self._draw_character_portrait()
        
        # Desenhar painel de informações
        self._draw_info_panel()
        
        # Desenhar setas de navegação
        self._draw_navigation_arrows()
        
        # Desenhar botões
        self._draw_buttons()
        
        # Aplicar efeito de transição se necessário
        if self.transitioning and self.transition_alpha > 0:
            fade_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, int(self.transition_alpha)))
            self.screen.blit(fade_overlay, (0, 0))
    
    def _draw_character_portrait(self):
        """Desenha o personagem integrado ao background sem moldura."""
        character_id = self.current_character["id"]
        portrait = self.character_portraits.get(character_id)
        
        if portrait:
            # Posição do personagem (lado esquerdo da tela, um pouco mais à direita)
            character_x = 200  # Mais à direita para dar espaço
            character_y = self.height - portrait.get_height() - 50  # No chão
            
            # Redimensionar o personagem para tamanho adequado (um pouco maior)
            target_height = min(900, int(self.height * 0.65))  # 65% da altura da tela
            scale_factor = target_height / portrait.get_height()
            new_width = int(portrait.get_width() * scale_factor)
            
            scaled_portrait = pygame.transform.scale(portrait, (new_width, target_height))
            
            # Ajustar posição Y para o personagem ficar no chão
            character_y = self.height - target_height - 30
            
            # Criar sombra elíptica sutil no chão
            shadow_width = int(new_width * 0.8)
            shadow_height = int(shadow_width * 0.3)  # Sombra achatada
            shadow_x = character_x + (new_width - shadow_width) // 2
            shadow_y = self.height - 40  # Próximo ao chão
            
            # Surface para a sombra com transparência
            shadow_surface = pygame.Surface((shadow_width, shadow_height), pygame.SRCALPHA)
            
            # Criar gradiente de sombra (mais escuro no centro)
            for i in range(shadow_height):
                alpha = int(50 * (1 - (i / shadow_height) * 0.5))  # Gradiente vertical suave
                pygame.draw.ellipse(shadow_surface, (0, 0, 0, alpha), 
                                  (0, i, shadow_width, shadow_height - i))
            
            # Desenhar a sombra no chão
            self.screen.blit(shadow_surface, (shadow_x, shadow_y))
            
            # Efeito de aura sutil ao redor do personagem (opcional)
            if hasattr(self, 'animation_time'):
                aura_intensity = int(15 + 10 * math.sin(self.animation_time * 1.5))
                primary_color = self.current_character["theme_colors"]["primary"]
                
                # Aura muito sutil
                aura_surface = pygame.Surface((new_width + 20, target_height + 20), pygame.SRCALPHA)
                aura_rect = pygame.Rect(10, 10, new_width, target_height)
                
                # Aura com bordas suaves
                for i in range(5):
                    alpha = max(0, aura_intensity - i * 3)
                    expanded_rect = aura_rect.inflate(i * 4, i * 4)
                    pygame.draw.rect(aura_surface, (*primary_color, alpha), expanded_rect, 2)
                
                # Desenhar aura
                aura_pos = (character_x - 10, character_y - 10)
                self.screen.blit(aura_surface, aura_pos)
            
            # Desenhar o personagem (sem moldura, integrado ao cenário)
            self.screen.blit(scaled_portrait, (character_x, character_y))
    
    def _draw_info_panel(self):
        """Desenha o painel de informações do personagem."""
        char = self.current_character
        colors = char["theme_colors"]
        
        # Fundo do painel com transparência
        panel_surface = pygame.Surface((self.info_panel_area.width, self.info_panel_area.height), pygame.SRCALPHA)
        panel_surface.fill((*colors["background"], 200))
        
        # Borda do painel
        pygame.draw.rect(panel_surface, colors["primary"], 
                        (0, 0, self.info_panel_area.width, self.info_panel_area.height), 4)
        
        self.screen.blit(panel_surface, self.info_panel_area)
        
        # Conteúdo do painel
        y_offset = 50
        x_base = self.info_panel_area.x + 50
        
        # Nome do personagem
        name_text = self.title_font.render(char["name"], True, colors["accent"])
        self.screen.blit(name_text, (x_base, self.info_panel_area.y + y_offset))
        y_offset += 100
        
        # Título do personagem
        title_text = self.subtitle_font.render(char["title"], True, colors["primary"])
        self.screen.blit(title_text, (x_base, self.info_panel_area.y + y_offset))
        y_offset += 80
        
        # História
        story_header = self.header_font.render("História", True, colors["primary"])
        self.screen.blit(story_header, (x_base, self.info_panel_area.y + y_offset))
        y_offset += 60
        
        # Quebrar texto da história
        story_lines = self._wrap_text(char["story"], self.info_panel_area.width - 100)
        for line in story_lines[:6]:  # Limitar a 6 linhas
            line_text = self.text_font.render(line, True, colors["text"])
            self.screen.blit(line_text, (x_base, self.info_panel_area.y + y_offset))
            y_offset += 45
        
        y_offset += 40
        
        # Atributos
        attrs_header = self.header_font.render("Atributos", True, colors["primary"])
        self.screen.blit(attrs_header, (x_base, self.info_panel_area.y + y_offset))
        y_offset += 60
        
        for attr_name, attr_value in char["attributes"].items():
            # Nome do atributo
            attr_text = self.stat_font.render(f"{attr_name}:", True, colors["text"])
            self.screen.blit(attr_text, (x_base, self.info_panel_area.y + y_offset))
            
            # Valor do atributo
            value_text = self.stat_font.render(str(attr_value), True, colors["accent"])
            self.screen.blit(value_text, (x_base + 200, self.info_panel_area.y + y_offset))
            
            # Barra de progresso
            bar_x = x_base + 300
            bar_y = self.info_panel_area.y + y_offset + 10
            bar_width = 400
            bar_height = 25
            
            # Fundo da barra
            pygame.draw.rect(self.screen, (50, 50, 50), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Preenchimento da barra (assumindo max 30)
            fill_width = int((attr_value / 30.0) * bar_width)
            bar_color = self._get_stat_color(attr_name)
            pygame.draw.rect(self.screen, bar_color,
                           (bar_x, bar_y, fill_width, bar_height))
            
            # Borda da barra
            pygame.draw.rect(self.screen, colors["text"],
                           (bar_x, bar_y, bar_width, bar_height), 2)
            
            y_offset += 55
        
        y_offset += 30
        
        # Habilidades
        abilities_header = self.header_font.render("Habilidades", True, colors["primary"])
        self.screen.blit(abilities_header, (x_base, self.info_panel_area.y + y_offset))
        y_offset += 60
        
        for ability in char["abilities"]:
            ability_text = self.text_font.render(f"• {ability}", True, colors["text"])
            self.screen.blit(ability_text, (x_base, self.info_panel_area.y + y_offset))
            y_offset += 45
    
    def _draw_navigation_arrows(self):
        """Desenha as setas de navegação."""
        colors = self.current_character["theme_colors"]
        
        # Seta esquerda
        left_color = colors["accent"] if self.left_arrow_hovered else colors["primary"]
        left_arrow = self.arrow_font.render("◀", True, left_color)
        left_rect = left_arrow.get_rect(center=self.left_arrow_area.center)
        self.screen.blit(left_arrow, left_rect)
        
        # Seta direita
        right_color = colors["accent"] if self.right_arrow_hovered else colors["primary"]
        right_arrow = self.arrow_font.render("▶", True, right_color)
        right_rect = right_arrow.get_rect(center=self.right_arrow_area.center)
        self.screen.blit(right_arrow, right_rect)
        
        # Indicador de posição (pontos)
        indicator_y = self.height - 100
        indicator_spacing = 40
        total_width = len(self.characters) * indicator_spacing
        start_x = (self.width - total_width) // 2
        
        for i, _ in enumerate(self.characters):
            color = colors["accent"] if i == self.current_character_index else colors["secondary"]
            center = (start_x + i * indicator_spacing, indicator_y)
            pygame.draw.circle(self.screen, color, center, 12)
    
    def _draw_buttons(self):
        """Desenha os botões da tela."""
        colors = self.current_character["theme_colors"]
        buttons = [self.select_button, self.back_button]
        
        for button in buttons:
            # Cor do botão baseada no hover
            if button['hovered']:
                button_color = colors["primary"]
                text_color = colors["background"]
                border_width = 6
            else:
                button_color = colors["background"]
                text_color = colors["text"]
                border_width = 3
            
            # Desenhar fundo do botão
            pygame.draw.rect(self.screen, button_color, button['rect'])
            
            # Desenhar borda
            pygame.draw.rect(self.screen, colors["primary"], 
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
            "Vida": (220, 60, 60),       # Vermelho
            "Ataque": (220, 120, 60),    # Laranja  
            "Defesa": (60, 120, 220),    # Azul
            "Magia": (160, 60, 220),     # Roxo
            "Velocidade": (60, 220, 120), # Verde
        }
        return colors.get(stat_name, self.current_character["theme_colors"]["primary"])
