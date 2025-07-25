<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Medieval Deck - Copilot Instructions

This is a Medieval-themed card game project with AI-generated backgrounds using Stable Diffusion XL.

## Project Structure
- `src/models/` - SDXL pipeline and card data models
- `src/generators/` - AI asset generation with prompt optimization
- `src/game/` - Pygame-based game engine and card management
- `src/utils/` - Configuration and utility functions
- `assets/` - Generated and static game assets
- `config/` - JSON configuration files

## Key Technologies
- **AI Generation**: Stable Diffusion XL (SDXL) with diffusers library
- **Game Engine**: Pygame for card game interface
- **GPU**: RTX 5070 with CUDA acceleration and memory optimization
- **Python**: 3.13.5 with type hints and modern features

## Development Guidelines
1. **AI Generation**: Use 77-token CLIP optimization for prompts, CFG=8.5, 80 steps
2. **Memory Management**: Implement CUDA memory cleanup after generation
3. **Error Handling**: Robust fallbacks for AI generation failures
4. **Performance**: Cache generated assets and optimize model loading
5. **Code Style**: Follow PEP8, use type hints, and modular architecture

## Prompt Optimization
- Medieval themes: castles, forests, dungeons, taverns
- Quality tokens: "masterpiece", "high quality", "detailed"
- Style tokens: "medieval fantasy", "gothic architecture"
- Lighting: "dramatic lighting", "atmospheric"

## CUDA Settings
- Model precision: float16 for memory efficiency
- Memory fraction: 0.8 for 16GB VRAM
- Progressive loading for large SDXL models
