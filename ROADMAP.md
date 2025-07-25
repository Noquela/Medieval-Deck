# Medieval Deck - Roadmap Detalhado e Refatoração

> Documento completo de 14 páginas com detalhes técnicos, design de gameplay, plano de implementação, arquitetura refatorada e próximos passos específicos.

## 1. Visão Geral do Projeto

Medieval Deck é um **roguelite card game estratégico** com arte gerada por IA (Stable Diffusion XL) integrada via SDXLPipeline. O jogo roda em Pygame no modo ultrawide (3440×1440), com uma estrutura modular e CLI flexível. Os principais módulos incluem engine de turnos, componentes de UI, pipeline de IA e generadores de assets.

## 2. Refatoração da Estrutura do Projeto

Proposta de organização clara para escalabilidade e testes:

### 2.1 Estrutura Core
- `src/core/turn_engine.py`: classe TurnEngine com métodos `start()`, `player_turn()`, `enemy_turn()`, `check_end()`

### 2.2 Gameplay
- `src/gameplay/cards.py`: definição de Card, SpellCard, CreatureCard, e carregamento via JSON
- `src/gameplay/deck.py`: classes Deck, Hand, DrawPile, DiscardPile com métodos `draw()`, `play()`, `discard()`

### 2.3 Inimigos e IA
- `src/enemies/ai.py`: BehaviorTree básico, mapeando cada inimigo a um conjunto de ações

### 2.4 IA e Assets
- `src/ai/asset_generator.py`: geração e cache de imagens IA

### 2.5 Interface
- `src/ui/`: screens (`menu_screen.py`, `selection_screen.py`, `game_screen.py`) e components (`button.py`, `panel.py`)

### 2.6 Utilitários
- `src/utils/`: `logger.py`, `config_loader.py`, helper functions

## 3. Fase 0 – Design de Gameplay

### 3.1 Documento de Game Design (GDD) Resumido
- **Narrativa central**: rebelião contra tirania no reino de Arenthia
- **Objetivo**: liderar expedição com decks personalizados para libertar territórios
- **Mapa de runs**: sequências de encontros organizadas em um grafo; decisões estratégicas

### 3.2 Tipos de Cartas
- **Criaturas**: Tank (Cavaleiro), DPS (Assassino), Suporte (Mago)
- **Magias**: AoE, Buffs, Debuffs
- **Artefatos**: Relíquia (passivo), Consumíveis

## 4. Fase 1 – Engine de Turnos

### 4.1 Classe TurnEngine

```python
class TurnEngine:
    def __init__(self, player, enemies):
        self.player = player
        self.enemies = enemies
    
    def start(self):
        while not self.check_end():
            self.player_turn()
            self.enemy_turns()
    
    def player_turn(self):
        # lógica de input, play_card, update states
        pass
    
    def enemy_turns(self):
        # IA decide ações e aplica efeitos
        pass
    
    def check_end(self):
        return self.player.hp <= 0 or all(e.hp <= 0 for e in self.enemies)
```

## 5. Fase 2 – Mecânicas de Cartas e Deck

### 5.1 Classes de Cartas
- **Card**: id, name, cost, description
- **CreatureCard(Card)**: attack, defense, `on_play(target)`
- **SpellCard(Card)**: `effect_function(player, targets)`

### 5.2 Deck Management
- **Deck.draw()**: move card do draw_pile para hand
- **Hand.play(card, target)**: executa efeito e descarta
- **DiscardPile**: reembaralha quando draw_pile vazio

## 6. Fase 3 – Inimigos e IA

### 6.1 Tipos de Inimigos e Stats
- **Grunt**: hp=10, atk=2, speed=5
- **Elite**: hp=20, atk=5, buff own attack
- **Boss**: múltiplas fases com triggers em thresholds de HP

### 6.2 IA e BehaviorTree
- Estrutura em `enemies/behavior.py` usando nodes Sequence, Selector, Action
- **Ações**: `attack_highest_hp`, `buff_lowest_ally`
- Configuração via JSON em `enemies/config.json`

## 7. Fase 4 – Progressão e Runs

### 7.1 Mapa de Runs
- Representado por grafo em `gameplay/map.py`
- **Node**: Encounter, Shop, Rest
- Player escolhe caminho e recebe buffs

### 7.2 Recompensas
- Ao final de cada run desbloqueia relics
- Sistema de salvamento em `saves/run_{date}.json`

## 8. Fase 5 – UI/UX e Assets IA

### 8.1 Menu Principal
- `menu_bg.png` carregado em `ui/screens/menu_screen.py`
- **Buttons**: component button com states idle, hover, pressed
- Animações de fade e parallax

### 8.2 Seleção de Personagem
- `selection_screen.py`: carrossel de backgrounds e setas
- **sprite class**: PNG transparente posicionado livremente
- Painel de info com abas e barras animadas

## 9. Detalhes Específicos de UI

- **Botões com texture IA**: `button_idle.png`, `button_hover.png`, `button_pressed.png`
- Políticas de cor definidas em `ui/theme.py`
- **Layout responsivo**: cálculo de centering via `screen.get_width()/get_height()`
- **Tweening** implementado em `ui/animations.py` (tween linear, ease-in-out)

## 10. Fase 6 – Testes e CI

### 10.1 Testes Unitários
- `tests/test_turn_engine.py`
- `tests/test_cards.py`
- `tests/test_asset_generator.py`

### 10.2 Pipeline CI
- **GitHub Actions**: Flake8, Black, Pytest, Coverage
- Configuração em `.github/workflows/ci.yml`

## 11. Fase 7 – Recursos Avançados

- **Multiplayer local**: pass-and-play com sessões salvas
- **AI Opponent**: múltiplos perfis de dificuldade
- **Daily Challenges**: cargas variantes com seed fixa
- **Leaderboards**: uso de arquivo CSV ou Google Sheets API

## 12. Refatoração e Qualidade de Código

- Adotar type hints e mypy para verificação de tipos
- Padronizar docstrings no formato Google/Pep257
- Usar pre-commit hooks: black, flake8, isort
- Logging centralizado em `utils/logger.py` com níveis configuráveis

## 13. Timeline Detalhada (12 Semanas)

| Semanas | Foco | Descrição |
|---------|------|-----------|
| **1-2** | Design de Gameplay & Engine de Turnos | Base fundamental do sistema |
| **3-4** | Implementação de Cartas e Deck | Mecânicas core do card game |
| **5-6** | Inimigos, IA e Balanceamento Inicial | Sistema de combate |
| **7-8** | UI/UX Refinado e Assets IA | Interface e arte |
| **9-10** | Testes, CI e Ajustes Finais | Qualidade e estabilidade |
| **11-12** | Recursos Avançados e Polimento | Features extras e refinamento |

## 14. Próximos Passos Imediatos e Responsáveis

### 🎯 Prioridades Imediatas

- **Bruno Ballerini**: Coordenação geral e design de gameplay
- **Time de Dev**: implementação de fases 0-2
- **Time de Arte**: geração de assets IA e QA de sprites
- **Time de QA**: playtests e feedbacks

### 🔗 Repositório
**GitHub**: https://github.com/Noquela/Medieval-Deck

---

## 📋 Status Atual (25/07/2025)

### ✅ Concluído
- [x] Sistema de remoção de fundo com AI (rembg)
- [x] Sprites transparentes profissionais
- [x] Backgrounds HD em 3440x1440 ultrawide
- [x] Integração natural de personagens
- [x] GPU RTX 5070 otimizada
- [x] Pipeline SDXL funcional

### 🔄 Em Desenvolvimento
- [ ] Engine de turnos (Fase 1)
- [ ] Sistema de cartas (Fase 2)
- [ ] IA de inimigos (Fase 3)

### 📅 Próximo Marco
**Fase 1**: Implementação do TurnEngine e estrutura core do gameplay
