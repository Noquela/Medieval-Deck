"""
Configuration management for Medieval Deck game.

Centralized configuration for game settings, AI parameters, and file paths.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os


@dataclass
class AIConfig:
    """AI generation configuration."""
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    refiner_id: str = "stabilityai/stable-diffusion-xl-refiner-1.0"
    enable_refiner: bool = True
    num_inference_steps: int = 80
    guidance_scale: float = 8.5
    width: int = 1024
    height: int = 1024
    memory_efficient: bool = True
    cuda_memory_fraction: float = 0.8


@dataclass
class GameConfig:
    """Game mechanics configuration."""
    max_deck_size: int = 60
    min_deck_size: int = 40
    starting_health: int = 30
    max_mana: int = 10
    hand_size: int = 7
    max_players: int = 2


@dataclass
class UIConfig:
    """User interface configuration."""
    window_width: int = 3440
    window_height: int = 1440
    fullscreen: bool = False
    fps: int = 60
    card_width: int = 150
    card_height: int = 210
    card_hover_scale: float = 1.1
    animation_speed: float = 1.0
    # Configurações específicas para telas de personagem
    character_screen_fade_duration: float = 0.5
    character_panel_width: int = 600
    character_panel_alpha: int = 200
    
    def __post_init__(self):
        """Initialize theme colors."""
        self.theme = {
            "background_color": (20, 20, 30),      # Dark blue-gray
            "primary_color": (150, 100, 50),       # Medieval brown
            "secondary_color": (100, 80, 60),      # Light brown
            "text_color": (220, 220, 200),         # Light cream
            "accent_color": (200, 150, 50),        # Gold accent
        }


class Config:
    """
    Main configuration class for Medieval Deck.
    
    Manages all configuration settings including AI, game mechanics, and UI.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_dir: Directory containing config files
        """
        # Set up paths
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to config/ in project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
            
        self.assets_dir = self.config_dir.parent / "assets"
        self.assets_generated_dir = self.assets_dir / "generated"
        self.assets_static_dir = self.assets_dir / "static"
        self.assets_cache_dir = self.assets_dir / "cache"
        
        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)
        self.assets_generated_dir.mkdir(exist_ok=True)
        self.assets_static_dir.mkdir(exist_ok=True)
        self.assets_cache_dir.mkdir(exist_ok=True)
        
        # Configuration objects
        self.ai = AIConfig()
        self.game = GameConfig()
        self.ui = UIConfig()
        
        # Load configuration files
        self._load_configs()
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Configuration initialized")
        
    def _load_configs(self) -> None:
        """Load configuration from files."""
        # Load AI config
        ai_config_path = self.config_dir / "ai_settings.json"
        if ai_config_path.exists():
            self._load_ai_config(ai_config_path)
            
        # Load game config
        game_config_path = self.config_dir / "game_settings.json"
        if game_config_path.exists():
            self._load_game_config(game_config_path)
            
        # Load UI config
        ui_config_path = self.config_dir / "ui_settings.json"
        if ui_config_path.exists():
            self._load_ui_config(ui_config_path)
            
    def _load_ai_config(self, config_path: Path) -> None:
        """Load AI configuration from file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update AI config with loaded data
            for key, value in data.items():
                if hasattr(self.ai, key):
                    setattr(self.ai, key, value)
                    
        except Exception as e:
            logging.warning(f"Failed to load AI config: {e}")
            
    def _load_game_config(self, config_path: Path) -> None:
        """Load game configuration from file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update game config with loaded data
            for key, value in data.items():
                if hasattr(self.game, key):
                    setattr(self.game, key, value)
                    
        except Exception as e:
            logging.warning(f"Failed to load game config: {e}")
            
    def _load_ui_config(self, config_path: Path) -> None:
        """Load UI configuration from file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update UI config with loaded data
            for key, value in data.items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)
                    
        except Exception as e:
            logging.warning(f"Failed to load UI config: {e}")
            
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    self.config_dir.parent / "medieval_deck.log",
                    encoding='utf-8'
                )
            ]
        )
        
    def save_configs(self) -> None:
        """Save all configurations to files."""
        self._save_ai_config()
        self._save_game_config()
        self._save_ui_config()
        
    def _save_ai_config(self) -> None:
        """Save AI configuration to file."""
        config_path = self.config_dir / "ai_settings.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.ai), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save AI config: {e}")
            
    def _save_game_config(self) -> None:
        """Save game configuration to file."""
        config_path = self.config_dir / "game_settings.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.game), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save game config: {e}")
            
    def _save_ui_config(self) -> None:
        """Save UI configuration to file."""
        config_path = self.config_dir / "ui_settings.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.ui), f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save UI config: {e}")
            
    def get_cards_config_path(self) -> Path:
        """Get path to cards configuration file."""
        return self.config_dir / "cards.json"
        
    def get_prompts_config_path(self) -> Path:
        """Get path to prompts configuration file."""
        return self.config_dir / "prompts.json"
        
    def get_settings_config_path(self) -> Path:
        """Get path to general settings file."""
        return self.config_dir / "settings.json"
        
    @property
    def memory_efficient(self) -> bool:
        """Check if memory efficient mode is enabled."""
        return self.ai.memory_efficient
        
    @property
    def cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
            
    def get_device(self) -> str:
        """Get the device to use for AI generation."""
        if self.cuda_available:
            return "cuda"
        return "cpu"
        
    def update_ai_config(self, **kwargs) -> None:
        """
        Update AI configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.ai, key):
                setattr(self.ai, key, value)
                self.logger.info(f"Updated AI config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown AI config parameter: {key}")
                
    def update_game_config(self, **kwargs) -> None:
        """
        Update game configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.game, key):
                setattr(self.game, key, value)
                self.logger.info(f"Updated game config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown game config parameter: {key}")
                
    def update_ui_config(self, **kwargs) -> None:
        """
        Update UI configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
                self.logger.info(f"Updated UI config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown UI config parameter: {key}")
                
    def reset_to_defaults(self) -> None:
        """Reset all configurations to default values."""
        self.ai = AIConfig()
        self.game = GameConfig()
        self.ui = UIConfig()
        self.logger.info("Configuration reset to defaults")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            "ai": asdict(self.ai),
            "game": asdict(self.game),
            "ui": asdict(self.ui),
            "paths": {
                "config_dir": str(self.config_dir),
                "assets_dir": str(self.assets_dir),
                "generated_dir": str(self.assets_generated_dir),
                "static_dir": str(self.assets_static_dir),
                "cache_dir": str(self.assets_cache_dir)
            },
            "system": {
                "cuda_available": self.cuda_available,
                "device": self.get_device(),
                "memory_efficient": self.memory_efficient
            }
        }
