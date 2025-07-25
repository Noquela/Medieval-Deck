#!/usr/bin/env python3
"""
Script mestre para regenerar todos os assets do Medieval Deck.
Executa: backgrounds, sprites e animações em sequência otimizada.
"""
import sys
import time
from pathlib import Path

def run_regeneration_sequence():
    """Executa toda a sequência de regeneração de assets."""
    print("🏰 === MEDIEVAL DECK - REGENERAÇÃO COMPLETA === 🏰")
    print()
    
    scripts = [
        {
            "name": "Backgrounds da Tela de Seleção",
            "script": "scripts/regenerate_selection_backgrounds.py",
            "description": "Regenera backgrounds com qualidade premium, remove bugs visuais"
        },
        {
            "name": "Sprites de Personagens",
            "script": "scripts/regenerate_character_sprites.py", 
            "description": "Regenera sprites com transparência perfeita, remove fundos residuais"
        },
        {
            "name": "Animações 30fps",
            "script": "scripts/generate_character_animations.py",
            "description": "Gera sprite sheets de animação para todos os personagens"
        }
    ]
    
    total_start_time = time.time()
    
    for i, script_info in enumerate(scripts, 1):
        print(f"🎯 [{i}/{len(scripts)}] {script_info['name']}")
        print(f"📝 {script_info['description']}")
        print(f"🔄 Executando: {script_info['script']}")
        print("-" * 60)
        
        start_time = time.time()
        
        # Executar script
        try:
            import subprocess
            import os
            
            # Mudar para diretório do projeto
            os.chdir(Path(__file__).parent.parent)
            
            # Executar script Python
            result = subprocess.run([
                ".venv/Scripts/python.exe", 
                script_info['script']
            ], capture_output=True, text=True, shell=True)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ {script_info['name']} concluído em {duration:.1f}s")
                print("📤 Output:")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            else:
                print(f"❌ {script_info['name']} falhou após {duration:.1f}s")
                print("📤 Error:")
                print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
                
        except Exception as e:
            print(f"❌ Erro ao executar {script_info['script']}: {e}")
            
        print()
        print("=" * 80)
        print()
    
    total_duration = time.time() - total_start_time
    
    print("🎉 === REGENERAÇÃO COMPLETA ===")
    print(f"⏱️  Tempo total: {total_duration:.1f}s ({total_duration/60:.1f} minutos)")
    print()
    print("📋 Resumo dos assets gerados:")
    print("   🖼️  Backgrounds: main_menu, character_selection, deck_selection, settings")
    print("   👤 Sprites: knight, wizard, rogue, archer, goblin, orc, skeleton, dragon")
    print("   🎬 Animações: idle, attack, cast, hurt (30fps, 8 frames cada)")
    print()
    print("🎮 Pronto para testar o jogo com assets regenerados!")
    print("🚀 Execute: .venv/Scripts/python.exe -m src.main")

if __name__ == "__main__":
    try:
        run_regeneration_sequence()
    except KeyboardInterrupt:
        print("\n⛔ Regeneração cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na regeneração: {e}")
        import traceback
        traceback.print_exc()
