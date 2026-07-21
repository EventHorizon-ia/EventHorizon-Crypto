# scripts/comparar_treino.py
import requests
import json
import time
import sys

API = "http://localhost:8000"

def enviar_comando(cmd):
    r = requests.post(f"{API}/comando", json={"comando": cmd})
    return r.json()

print("📸 Tirando snapshot ANTES...")
print(enviar_comando("crypto snapshot antes"))

print("\n⏳ Deixe rodando por alguns minutos...")
print("Pressione ENTER quando quiser tirar o snapshot DEPOIS")
input()

print("\n📸 Tirando snapshot DEPOIS...")
print(enviar_comando("crypto snapshot depois"))

# Lista snapshots
import os
arquivos = sorted(os.listdir("data/snapshots"))
print(f"\n📁 Snapshots salvos: {len(arquivos)}")
for a in arquivos:
    print(f"   {a}")