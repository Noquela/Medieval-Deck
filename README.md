# Medieval Deck 🏰⚔️

An AI-powered medieval fantasy card game with dynamically generated backgrounds using Stable Diffusion XL.

## 🎮 Features

- **AI-Generated Art**: High-quality medieval backgrounds created with Stable Diffusion XL
- **Strategic Gameplay**: Deck-building card game with creatures, spells, and artifacts  
- **Medieval Theme**: Knights, dragons, wizards, and mystical lands
- **Modern Engine**: Built with Pygame and optimized for RTX 5070 GPU
- **Modular Design**: Clean, maintainable Python architecture

## 🚀 Quick Start

### Prerequisites

- Python 3.13.5+
- NVIDIA GPU with CUDA support (recommended: RTX 5070)
- 16GB+ RAM
- 10GB+ free disk space

### Installation

1. **Clone and Setup**
   ```bash
   cd "c:\Users\Bruno\Documents\Medieval Deck"
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Game**
   ```bash
   python src\main.py
   ```

### First Time Setup

The game will automatically:
- Download SDXL models (~13GB)
- Generate initial card backgrounds
- Setup configuration files

## 🎯 Game Modes

- **🆚 Player vs Player**: Local multiplayer battles
- **🎨 Asset Generation**: Create AI backgrounds for custom cards
- **⚙️ Deck Builder**: Design and test custom decks

## 📋 Command Line Options

```bash
# Basic usage
python src\main.py

# Generate all AI backgrounds
python src\main.py --generate-assets

# Debug mode with detailed logging  
python src\main.py --debug

# Disable AI generation (use placeholders)
python src\main.py --no-ai

# Custom window size
python src\main.py --window-size 1920x1080

# System information
python src\main.py --system-info
```

## 🏗️ Project Structure

```
Medieval Deck/
├── src/                          # Source code
│   ├── main.py                   # Game launcher
│   ├── models/                   # AI and data models
│   │   ├── sdxl_pipeline.py      # SDXL generation pipeline
│   │   └── card_models.py        # Game data structures
│   ├── generators/               # AI asset generation
│   │   ├── asset_generator.py    # Background generator
│   │   └── prompt_optimizer.py   # 77-token CLIP optimization
│   ├── game/                     # Core game logic
│   │   ├── engine.py             # Game engine
│   │   ├── cards.py              # Card management
│   │   ├── deck.py               # Deck system
│   │   └── ui.py                 # Pygame interface
│   └── utils/                    # Utilities
│       ├── config.py             # Configuration management
│       └── helpers.py            # Helper functions
├── assets/                       # Game assets
│   ├── generated/                # AI-generated backgrounds
│   ├── static/                   # Static images/sounds
│   └── cache/                    # Model cache
├── config/                       # Configuration files
│   ├── cards.json                # Card definitions
│   ├── prompts.json              # AI prompt library
│   └── settings.json             # Game settings
└── requirements.txt              # Python dependencies
```

## 🤖 AI Generation

### Optimized for Quality
- **Model**: Stable Diffusion XL + Refiner
- **Resolution**: 1024x1024 high-quality backgrounds
- **Parameters**: CFG 8.5, 80 steps for optimal quality
- **Memory**: Optimized for RTX 5070 with 16GB VRAM

### Prompt Engineering
- **77-Token Optimization**: CLIP tokenizer limit handling
- **Priority System**: Critical → High → Medium → Low token selection
- **Medieval Themes**: Castles, knights, dragons, magic
- **Quality Enhancement**: Masterpiece, detailed, professional

### Example Prompts
```
# Creature Card
"ancient fire dragon, dark mountain lair, masterpiece, dramatic lighting, medieval fantasy"

# Spell Card  
"magical energy, spell circle, mystical runes, high quality, atmospheric"

# Land Card
"medieval castle, towering walls, royal banners, epic atmosphere, golden hour"
```

## ⚙️ Configuration

### AI Settings (`config/settings.json`)
```json
{
  "ai": {
    "model_id": "stabilityai/stable-diffusion-xl-base-1.0",
    "num_inference_steps": 80,
    "guidance_scale": 8.5,
    "memory_efficient": true
  }
}
```

### Game Settings
```json
{
  "game": {
    "starting_health": 30,
    "max_mana": 10,
    "deck_size_min": 40
  }
}
```

## 🎴 Card System

### Card Types
- **🛡️ Creatures**: Attack and defend with stats and abilities
- **✨ Spells**: Instant effects and ongoing enchantments  
- **⚔️ Artifacts**: Equipment and magical items
- **🏞️ Lands**: Mana sources and special locations

### Rarity Levels
- **Common**: Basic cards with simple effects
- **Uncommon**: Enhanced stats and minor abilities
- **Rare**: Powerful effects and unique mechanics
- **Legendary**: Game-changing cards with epic backgrounds

## 🎨 Creating Custom Cards

1. **Edit Cards Configuration**
   ```bash
   notepad config\cards.json
   ```

2. **Add New Card**
   ```json
   {
     "id": "my_dragon",
     "name": "Custom Dragon", 
     "type": "creature",
     "cost": 7,
     "attack": 6,
     "defense": 6,
     "background_prompt": "majestic blue dragon, ice crystals, frozen castle"
   }
   ```

3. **Generate Background**
   ```bash
   python src\main.py --generate-assets
   ```

## 🐛 Troubleshooting

### GPU Issues
```bash
# Check CUDA availability
python src\main.py --system-info

# Run without GPU
python src\main.py --no-ai
```

### Memory Issues
- Reduce `cuda_memory_fraction` in settings
- Enable `memory_efficient` mode
- Close other GPU applications

### Model Download Issues
- Check internet connection
- Ensure 10GB+ free space
- Restart if download interrupts

## 🔧 Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Format code
black src/

# Lint code  
flake8 src/
```

### Adding New Features
1. Follow modular architecture
2. Use type hints and docstrings
3. Add configuration options
4. Update documentation

## 📈 Performance Tips

### For RTX 5070
- Use `memory_efficient=True`
- Set `cuda_memory_fraction=0.8`
- Enable model CPU offloading
- Use FP16 precision

### General Optimization
- Cache generated backgrounds
- Limit concurrent AI generation
- Use progressive model loading
- Monitor VRAM usage

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Stability AI** for Stable Diffusion XL
- **Hugging Face** for diffusers library
- **Pygame** community for game engine
- **Medieval artists** for inspiration

---

⚔️ **Ready to build your medieval empire?** Start playing now!

```bash
python src\main.py
```
