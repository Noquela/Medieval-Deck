"""
Medieval Deck - Arquivo Principal Simplificado

Ponto de entrada do jogo com sistema de gameplay completo e tela de seleção.
"""
import pygame
import sys
import logging
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('medieval_deck.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Função principal do jogo."""
    try:
        logger.info("Iniciando Medieval Deck")
        
        # Inicializar pygame
        pygame.init()
        pygame.mixer.init()
        
        # Configurar tela
        screen_width = 1280
        screen_height = 720
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Medieval Deck - Card Game")
        
        # Carregar ícone do jogo se disponível
        icon_path = Path("assets/generated/icon.png")
        if icon_path.exists():
            icon = pygame.image.load(icon_path)
            pygame.display.set_icon(icon)
        
        # Importar e inicializar a tela de gameplay
        from src.ui.gameplay_screen import GameplayScreen
        
        # Criar tela de gameplay
        gameplay_screen = GameplayScreen(screen)
        
        logger.info("Medieval Deck iniciado com sucesso")
        
        # Executar loop principal
        gameplay_screen.run()
        
        logger.info("Medieval Deck finalizado")
        
    except Exception as e:
        logger.error(f"Erro no jogo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
