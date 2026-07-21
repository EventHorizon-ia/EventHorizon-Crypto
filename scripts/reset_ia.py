# scripts/reset_ia.py
import os
import shutil

print("=" * 50)
print("🔄 RESETANDO IA PARA COMEÇAR DO ZERO")
print("=" * 50)

# Backup
backup_dir = "backup_antigo"
os.makedirs(backup_dir, exist_ok=True)

# Copia dados antigos para backup
if os.path.exists("data"):
    shutil.copytree("data", f"{backup_dir}/data_backup", dirs_exist_ok=True)
    print(f"✅ Backup salvo em {backup_dir}")

# Remove dados antigos
arquivos_remover = ["minds.json", "mentes.db", "mentes_pytorch"]
for item in arquivos_remover:
    caminho = f"data/{item}"
    if os.path.exists(caminho):
        if os.path.isdir(caminho):
            shutil.rmtree(caminho)
        else:
            os.remove(caminho)
        print(f"🗑️ Removido: {caminho}")

print("\n✅ IA resetada! Agora rode o sistema do zero.")
print("=" * 50)