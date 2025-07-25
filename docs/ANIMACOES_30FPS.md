# Sistema de Animações 30fps - Medieval Deck

Sistema totalmente automatizado para gerar e reproduzir animações fluidas de personagens usando IA e sprite sheets.

## 🎯 Funcionalidades

- **Geração automática**: Sprite sheets criados via Stable Diffusion XL
- **30 FPS fluido**: Animações suaves sem travamentos
- **Zero trabalho manual**: Copilot gera tudo automaticamente
- **Múltiplas ações**: idle, attack, cast, hurt, death
- **Escalamento inteligente**: Adapta-se a diferentes resoluções
- **Integração completa**: Funciona diretamente no combate

## 🚀 Como Usar

### 1. Gerar Sprite Sheets (Uma vez)

```bash
python scripts/generate_sprite_sheets.py
```

Este script:
- Gera 10-12 frames por ação usando SDXL
- Cria sprite sheets horizontais em `assets/sprite_sheets/`
- Processa knight, goblin, orc, skeleton, mage, dragon

### 2. Demo das Animações

```bash
python demo_animations_30fps.py
```

- Mostra todos os personagens animados
- Use ESPAÇO para trocar ações
- FPS counter em tempo real

### 3. Jogar com Animações

```bash
python src/main.py
```

As animações funcionam automaticamente no combate:
- Jogador (knight) anima idle/attack/cast
- Inimigos animam idle/hurt/death
- Transições fluidas entre ações

## 📁 Estrutura dos Arquivos

```
assets/sprite_sheets/
├── knight_idle_sheet.png      # 8 frames de respiração
├── knight_attack_sheet.png    # 12 frames de ataque
├── goblin_idle_sheet.png      # 8 frames idle
├── goblin_attack_sheet.png    # 12 frames ataque
└── ...

src/gameplay/animation.py      # Sistema de animação
src/utils/sprite_loader.py     # Carregador de sprites
src/generators/sprite_sheet_generator.py  # Gerador IA
```

## 🎨 Como o Sistema Funciona

### 1. Geração com IA

```python
# Prompt automático por frame
"heroic knight, frame 3 of 12, raising sword, transparent background"
"heroic knight, frame 4 of 12, mid-attack swing, transparent background"
```

### 2. Sprite Sheet Horizontal

```
[Frame1][Frame2][Frame3]...[Frame10]
```

### 3. Reprodução 30fps

```python
# Automaticamente no CombatScreen
animation_manager.update(dt)
current_frame = animation_manager.get_current_frame("knight")
screen.blit(current_frame, position)
```

## ⚙️ Configuração Avançada

### Personalizar Personagem

```python
# Em scripts/generate_sprite_sheets.py
characters = {
    "meu_heroi": {
        "prompt": "heroic paladin with golden armor and holy sword",
        "actions": ["idle", "attack", "heal", "death"]
    }
}
```

### Ajustar FPS/Frames

```python
# Em sprite_sheet_generator.py
def generate_sprite_sheet(self, char_id, action, n_frames=16):  # Mais frames
    # ...
    animation = FrameAnimation(frames, fps=60)  # Mais FPS
```

### Trocar Ação no Combate

```python
# Quando jogador ataca
animation_manager.play_animation("knight", "attack", force_restart=True)

# Quando inimigo toma dano
animation_manager.play_animation(f"goblin_{enemy_index}", "hurt", force_restart=True)
```

## 🔧 Troubleshooting

### Sprite Sheets Não Geram
- Verifique se SDXL está funcionando: `python test_minimal.py`
- Confirme que GPU tem VRAM suficiente (8GB+)
- Reduza resolução se necessário: `width=256, height=256`

### Animações Não Aparecem
- Execute primeiro: `python scripts/generate_sprite_sheets.py`
- Verifique arquivos em `assets/sprite_sheets/`
- Logs mostram quais animações carregaram

### Performance Lenta
- Reduza número de frames: `n_frames=6`
- Use resolução menor: `256x256` ao invés de `512x512`
- Cache sprites escalados

## 🎮 Resultado Final

Com esse sistema você tem:

✅ **Personagens 100% animados** - idle, attack, hurt, death
✅ **30 FPS fluido** - sem stuttering ou lag  
✅ **Zero trabalho manual** - IA gera tudo automaticamente
✅ **Estilo consistente** - SDXL mantém arte coesa
✅ **Fácil expansão** - adicione novos personagens facilmente

O resultado visual fica idêntico ao Slay the Spire - personagens com vida própria, ações fluidas e transições naturais entre estados!

## 📋 Próximos Passos

1. Execute `python scripts/generate_sprite_sheets.py`
2. Teste com `python demo_animations_30fps.py`  
3. Jogue o combate animado com `python src/main.py`
4. Customize personagens editando o script de geração
