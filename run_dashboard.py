import threading
import time
import webbrowser
import uvicorn
import subprocess
import socket

from Software.core.universe_instance import universo, lock_universo
from Software.core.leis import evoluir_universo
from Software.core.state import estado
from Software.api import app

# ⭐ FUNÇÃO PARA PEGAR O IP LOCAL DA MÁQUINA
def get_local_ip():
    try:
        # Conecta a um IP externo para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

LOCAL_IP = get_local_ip()
print(f"🌐 Seu IP local: {LOCAL_IP}")
print(f"📱 No celular, acesse: http://{LOCAL_IP}:3000")

terminal_linhas = []
contador = 0
frontend_process = None

# verifica se porta está em uso
def porta_em_uso(porta):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0

# LOOP DO UNIVERSO
def loop_simulacao():
    print("THREAD SIMULAÇÃO INICIADA")
    global contador

    while True:
        with lock_universo:
            if not estado["pausado"]:
                evoluir_universo(universo, estado, terminal_linhas)

        contador += 1

        # ⭐ Salva leve (JSON) a cada 100 ticks (~10 segundos)
        if contador % 100 == 0:
            universo.salvar_leve()

        # ⭐ Salva modelos PyTorch a cada 1000 ticks (~100 segundos)
        if contador % 1000 == 0:
            universo.mentes.salvar()

        time.sleep(0.1)
        
# FRONTEND (Next.js na porta 3000 - HOST 0.0.0.0)
def start_frontend():
    global frontend_process
    if porta_em_uso(3000):
        print("Frontend já está rodando na porta 3000")
        return
    print("Iniciando frontend Next.js...")
    # ⭐ IMPORTANTE: `-- -H 0.0.0.0` permite acesso externo
    frontend_process = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "-H", "0.0.0.0"],  
        cwd="Dashboard"
    )

# API
def start_api():
    print("Iniciando API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

    
def esperar_servico(porta, nome):
    print(f"Aguardando {nome}...")
    while not porta_em_uso(porta):
        time.sleep(0.5)
    print(f"{nome} pronto!")

# INICIALIZAÇÃO
threading.Thread(target=loop_simulacao, daemon=True).start()
threading.Thread(target=start_frontend, daemon=True).start()
threading.Thread(target=start_api, daemon=True).start()

esperar_servico(8000, "API")

# ⭐ Restauração atrasada das moedas
def start_crypto_restauracao():
    time.sleep(5)
    crypto = next((a for a in universo.apps if a.nome == "crypto_app"), None)
    if crypto:
        crypto.iniciar_restauracao_async()

threading.Thread(target=start_crypto_restauracao, daemon=True).start()

esperar_servico(3000, "Frontend Next.js")

# ⭐ MOSTRA O IP CORRETO PARA ACESSAR DO CELULAR
print("\n" + "="*50)
print(f"📱 Para acessar do seu CELULAR:")

print(f"   1. Conecte o celular na mesma rede WiFi")
print(f"   2. Abra o navegador e acesse: http://{LOCAL_IP}:3000")
print(f"   3. A API está em: http://{LOCAL_IP}:8000")
print("="*50 + "\n")

webbrowser.open(f"http://{LOCAL_IP}:3000")

while True:
    time.sleep(1)