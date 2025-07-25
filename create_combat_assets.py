"""
Cria assets temporários de combate para testar a demo.
"""
import shutil
from pathlib import Path

# Copiar assets existentes como temporários para teste
assets_ia = Path("assets/ia")

# Se não existem, criar usando os existentes
mapping = {
    "knight_bg.png": "combat_bg.png",
    "knight_sprite.png": "player_sprite.png",
    "wizard_sprite.png": "goblin_scout_sprite.png",
    "assassin_sprite.png": "orc_berserker_sprite.png"
}

print("🎮 Criando assets temporários para demo de combate...")

for source, target in mapping.items():
    source_path = assets_ia / source
    target_path = assets_ia / target
    
    if source_path.exists() and not target_path.exists():
        shutil.copy2(source_path, target_path)
        print(f"✅ Copiado: {source} → {target}")
    elif target_path.exists():
        print(f"✅ Já existe: {target}")
    else:
        print(f"❌ Faltando: {source}")

# Criar sprites adicionais
additional_sprites = [
    "skeleton_archer_sprite.png",
    "dark_mage_sprite.png"
]

for sprite in additional_sprites:
    sprite_path = assets_ia / sprite
    if not sprite_path.exists():
        # Usar assassin como base
        base_path = assets_ia / "assassin_sprite.png"
        if base_path.exists():
            shutil.copy2(base_path, sprite_path)
            print(f"✅ Criado temporário: {sprite}")

print("\n🎉 Assets temporários criados! Agora você pode testar a demo.")
print("Execute: python demo_combat_ui.py")
