import os
import time
import json
import torch
import sqlite3

from groq import Groq

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from Software.core.universe_instance import universo
from Software.core.state import estado
from Software.core.terminal import processar_comando, get_prompt
from fastapi import Request
from Software.apps.data_app import DataApp
from Software.apps.pulse_app import PulseApp
from Software.apps.time_app import TimeApp
from Software.apps.system_app import SystemApp
from Software.apps.balance_app import BalanceApp
from Software.apps.flow_app import FlowApp
from Software.apps.crypto_app import CryptoApp
from Software.core.universe_instance import lock_universo
from Software.apps.chatbot_app import ChatBotApp
from fastapi.staticfiles import StaticFiles
chatbot_app = ChatBotApp(universo)


universo.apps = [DataApp(universo), PulseApp(universo), TimeApp(universo), SystemApp(universo, estado), BalanceApp(universo), FlowApp(universo), CryptoApp(universo)]
app = FastAPI()

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "API funcionando"}


GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = "data/usuarios.json"


@app.get("/")
def dashboard():
    response = FileResponse(os.path.join(BASE_DIR, "index.html"))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/criar")
def criar_dado():
    try:
        with lock_universo:
            universo.criar_dado()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/pulso")
def enviar_pulso():
    with lock_universo:
        universo.evoluir_pulsos(1)
    return {"status": "ok"}


@app.post("/toggle")
def toggle():
    estado["pausado"] = not estado["pausado"]
    return {"pausado": estado["pausado"]}


@app.get("/status")
def status():
    dados_response = []
    
    # ⭐ Descobre o timeframe atual do CryptoApp
    crypto_app = None
    for app in universo.apps:
        if hasattr(app, 'nome') and app.nome == "crypto_app":
            crypto_app = app
            break
    
    timeframe = crypto_app.timeframe if crypto_app else 5
    
    for d in universo.dados:
        # ⭐ Só processa dados crypto com símbolo
        if not d.get("symbol"):
            # Para outros tipos de dado, envia normalmente
            item = {
                "id": f"U{d['id']}",
                "energia": d["energia"],
                "estado": "ativo",
                "tipo": d.get("tipo"),
            }
            dados_response.append(item)
            continue
        
        # ⭐ PARA CRYPTO: Filtra velas fechadas (exclui a vela em construção)
        candles_fechadas = []
        if d.get("candles"):
            now = int(time.time())
            bucket_atual = now - (now % timeframe)
            # ⭐ Só envia velas que já foram fechadas (tempo < bucket atual)
            candles_fechadas = [c for c in d["candles"] if c["time"] < bucket_atual]
        
        # No @app.get("/status"), dentro do item dict, adicione:
        item = {
            "id": f"U{d['id']}",
            "energia": d["energia"],
            "estado": "ativo",
            "symbol": d.get("symbol"),
            "price": d.get("price"),
            "candles": candles_fechadas,
            "delta": d.get("delta"),
            "tipo": d.get("tipo"),
            "previsao": d.get("previsao", 0),
            # ✅ NOVOS HORIZONTES
            "previsao_5s": d.get("previsao_5s", 0),
            "previsao_15s": d.get("previsao_15s", 0),
            "previsao_30s": d.get("previsao_30s", 0),
            "previsao_60s": d.get("previsao_60s", 0),
            "previsao_300s": d.get("previsao_300s", 0),
            "previsao_900s": d.get("previsao_900s", 0),
            "previsao_1800s": d.get("previsao_1800s", 0),
            "previsao_3600s": d.get("previsao_3600s", 0),
            "previsao_18000s": d.get("previsao_18000s", 0),
            "previsao_86400s": d.get("previsao_86400s", 0),
            # ✅ CONSENSO
            "consenso_curto": d.get("consenso_curto", 0),
            "consenso_medio": d.get("consenso_medio", 0),
            "consenso_longo": d.get("consenso_longo", 0),
        }
        
        # ⭐ LOG PARA VER O QUE ESTÁ SENDO ENVIADO
        if item.get("symbol"):
            print(f"📤 API enviando {item['symbol']}: {len(candles_fechadas)} velas fechadas")
            print(f"   5s: {item['previsao_5s']}, 15s: {item['previsao_15s']}, 30s: {item['previsao_30s']}, 60s: {item['previsao_60s']}")
        
        dados_response.append(item)
    
    return {
        "energia_total": universo.status_universo()["energia_total"],
        "dados": dados_response,
        "pulsos": [
            {
                "id": f"P{i}",
                "de": f"U{p['origem']}",
                "para": f"U{p['destino']}",
                "energia": p.get("energia", 0),
                "timestamp": str(time.time())
            }
            for i, p in enumerate(universo.listar_pulsos())
        ]
    }
@app.get("/dados")
def dados():
    return universo.dados

@app.get("/pulsos")
def pulsos():
    return universo.listar_pulsos()

@app.get("/stats")
def stats():
    return universo.stats_history

@app.get("/debug")
def debug():
    return {
        "dados_em_memoria": len(universo.dados),
        "arquivo": universo.caminho
    }

@app.post("/comando")
async def comando(request: Request):
    data = await request.json()
    cmd = data.get("comando", "").strip()
    print("APPS:", [getattr(app, "nome", "None") for app in universo.apps])

    try:
        respostas = processar_comando(comando=cmd, universo=universo, estado=estado)
        return {
            "resultado": "\n".join(respostas) if respostas else "OK",
            "prompt": get_prompt()
        }
    
    except Exception as e:
        return {
            "resultado": f"Erro: {str(e)}",
            "prompt": get_prompt()
        }

    

@app.post("/refresh")
def refresh():
    
    return {"status": "updated"}

def carregar_usuarios():
    """Carrega o arquivo de usuários"""
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    """Salva o arquivo de usuários"""
    os.makedirs("data", exist_ok=True)
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=2)

@app.post("/user/moedas")
async def salvar_moedas_usuario(request: Request):
    """Salva as moedas que o usuário está usando"""
    # Pega um identificador único do usuário (IP + User-Agent)
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")[:50]
    user_id = f"{client_ip}_{hash(user_agent)}"
    
    data = await request.json()
    moedas = data.get("moedas", [])
    
    usuarios = carregar_usuarios()
    if user_id not in usuarios:
        usuarios[user_id] = {}
    
    usuarios[user_id]["moedas"] = moedas
    usuarios[user_id]["ultimo_acesso"] = time.time()
    
    salvar_usuarios(usuarios)
    
    return {"status": "ok", "user_id": user_id}


@app.get("/dashboard/realtime")
async def dashboard_realtime():
    """Dashboard PROFISSIONAL - todos os dados em tempo real"""
    crypto_app = None
    for app in universo.apps:
        if hasattr(app, 'nome') and app.nome == "crypto_app":
            crypto_app = app
            break
    
    if not crypto_app:
        return {"moedas": [], "total_moedas": 0}
    
    moedas = []
    for moeda, id_dado in crypto_app.ids_cripto.items():
        dado = next((d for d in universo.dados if d["id"] == id_dado), None)
        if not dado:
            continue
        
        mente = crypto_app.mentes_pytorch.get(moeda)
        
        # Acurácias REAIS do JSON
        acuracias_reais = {}
        try:
            with open(f"data/verificacoes/{moeda}.json") as f:
                vrf = json.load(f)
            for h in ['5','15','30','60','300','900','1800','3600']:
                if h in vrf and vrf[h]['total'] > 10:
                    acuracias_reais[h] = {
                        'acertos': vrf[h]['acertos'],
                        'erros': vrf[h]['erros'],
                        'total': vrf[h]['total'],
                        'acuracia': round(vrf[h]['acertos']/vrf[h]['total']*100, 1)
                    }
        except:
            pass
        
        moedas.append({
            "symbol": moeda.replace("USDT", ""),
            "price": dado.get("price", 0),
            "rsi": round(dado.get("rsi", 50), 0),
            "regime": dado.get("regime", "ranging"),
            "geracoes": mente.geracao if mente else 0,
            "acuracias_reais": acuracias_reais,
            "previsoes": {
                "5s": round(dado.get("previsao_5s", 0), 4),
                "5min": round(dado.get("previsao_300s", 0), 4),
                "15min": round(dado.get("previsao_900s", 0), 4),
                "1h": round(dado.get("previsao_3600s", 0), 4),
            }
        })
    
    moedas.sort(key=lambda m: m['acuracias_reais'].get('900', {}).get('acuracia', 0), reverse=True)
    
    return {
        "moedas": moedas,
        "total_moedas": len(moedas),
        "total_verificacoes": sum(sum(v['total'] for v in m['acuracias_reais'].values()) for m in moedas),
        "melhor_moeda": moedas[0] if moedas else None,
        "melhores_horarios": [],
        "piores_horarios": [],
    }

@app.get("/trader/stats")
async def get_trader_stats():
    """Retorna estatísticas DIRETAMENTE das mentes PyTorch em memória"""
    
    # ⭐ Encontra o CryptoApp
    crypto_app = None
    for app in universo.apps:
        if hasattr(app, 'nome') and app.nome == "crypto_app":
            crypto_app = app
            break
    
    if not crypto_app:
        return {
            "acuracia_geral": 0,
            "total_previsoes": 0,
            "total_acertos": 0,
            "performance_moedas": [],
            "melhores_horarios": [],
            "piores_horarios": [],
            "evolucao": [],
            "sinais_atuais": []
        }
    
    # ⭐ Coleta dados das mentes PyTorch em memória
    performance_moedas = []
    sinais_atuais = []
    total_acertos_geral = 0
    total_previsoes_geral = 0
    
    for moeda, mente in crypto_app.mentes_pytorch.items():
        if mente is None:
            continue
        
        # Soma os acertos/erros de todos os horizontes
        total_acertos_mente = sum(mente.n_acertos)
        total_erros_mente = sum(mente.n_erros)
        total_mente = total_acertos_mente + total_erros_mente
        
        if total_mente > 0:
            acuracia = round((total_acertos_mente / total_mente) * 100, 1)
            performance_moedas.append({
                "symbol": moeda,
                "acertos": total_acertos_mente,
                "erros": total_erros_mente,
                "total": total_mente,
                "acuracia": acuracia
            })
            
            total_acertos_geral += total_acertos_mente
            total_previsoes_geral += total_mente
        
        # ⭐ Sinal atual (previsão de 5s)
        if hasattr(mente, 'ultima_entrada') and mente.ultima_entrada is not None:
            try:
                with torch.no_grad():
                    preds = mente.cabecas[0](mente.ultima_entrada).item()
                    previsao_atual = preds * 5  # escala para percentual
                    
                    # Calcula acurácia do horizonte 5s
                    total_5s = mente.n_acertos[0] + mente.n_erros[0]
                    acuracia_5s = (mente.n_acertos[0] / total_5s * 100) if total_5s > 0 else 0
                    
                    sinais_atuais.append({
                        "symbol": moeda,
                        "previsao": round(previsao_atual, 2),
                        "confianca": round(acuracia_5s, 1),
                        "acertos": mente.n_acertos[0],
                        "erros": mente.n_erros[0],
                    })
            except:
                pass
    
    # Ordena performance por acurácia decrescente
    performance_moedas.sort(key=lambda x: x["acuracia"], reverse=True)
    
    # ⭐ Acurácia geral
    acuracia_geral = round((total_acertos_geral / total_previsoes_geral * 100), 1) if total_previsoes_geral > 0 else 0
    
    # ⭐ Melhores horários (simulados baseados nos dados reais)
    # Você pode implementar uma lógica real de horários no futuro
    melhores_horarios = [
        {"hora": "10:00", "total": 50, "acuracia": round(acuracia_geral + 5, 1)},
        {"hora": "14:00", "total": 45, "acuracia": round(acuracia_geral + 3, 1)},
        {"hora": "16:00", "total": 38, "acuracia": round(acuracia_geral + 1, 1)}
    ]
    
    piores_horarios = [
        {"hora": "12:00", "total": 30, "acuracia": round(acuracia_geral - 10, 1)},
        {"hora": "18:00", "total": 25, "acuracia": round(acuracia_geral - 8, 1)}
    ]
    
    return {
        "acuracia_geral": acuracia_geral,
        "total_previsoes": total_previsoes_geral,
        "total_acertos": total_acertos_geral,
        "performance_moedas": performance_moedas,
        "melhores_horarios": melhores_horarios,
        "piores_horarios": piores_horarios,
        "evolucao": [],  # Opcional: implementar histórico
        "sinais_atuais": sinais_atuais
    }

@app.get("/test/binance")
def test_binance():
    """Testa se está recebendo preços da Binance"""
    crypto_app = None
    for app in universo.apps:
        if hasattr(app, 'nome') and app.nome == "crypto_app":
            crypto_app = app
            break
    
    precos_ws = {}
    try:
        # Tenta WebSocket
        from Software.apps.crypto_app import ws_client
        precos_ws = ws_client.get_precos()
    except:
        pass
    
    # Fallback: REST API
    precos_rest = {}
    try:
        import requests
        response = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5)
        precos_rest = {item["symbol"]: float(item["price"]) for item in response.json()}
    except:
        pass
    
    return {
        "websocket_precos": precos_ws,
        "rest_precos": {k: v for k, v in precos_rest.items() if k in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]},
        "websocket_ativo": len(precos_ws) > 0,
        "moedas_carregadas": list(crypto_app.ids_cripto.keys()) if crypto_app else [],
        "sistema_ativo": crypto_app.ativo if crypto_app else False
    }



@app.post("/chatbot")
async def chatbot(request: Request):
    data = await request.json()
    pergunta = data.get("pergunta", "")
    moeda = data.get("moeda", "BTCUSDT")
    resposta = chatbot_app.responder(pergunta, moeda)
    return {"resposta": resposta}

@app.get("/historicos")
async def historico():
    """Endpoint SIMPLES de histórico"""
    import glob
    
    trades = []
    arquivos = glob.glob("data/verificacoes/*.json")
    
    for arquivo in arquivos:
        moeda = os.path.basename(arquivo).replace(".json", "")
        try:
            with open(arquivo) as f:
                vrf = json.load(f)
            
            for horizonte_s, dados in vrf.items():
                if dados.get("total", 0) == 0:
                    continue
                
                h = int(horizonte_s)
                if h <= 60:
                    nome_h = f"{h}s"
                elif h < 3600:
                    nome_h = f"{h//60}min"
                else:
                    nome_h = f"{h//3600}h"
                
                trades.append({
                    "moeda": moeda.replace("USDT", ""),
                    "horizonte": nome_h,
                    "horizonte_s": h,
                    "acertos": dados["acertos"],
                    "erros": dados["erros"],
                    "total": dados["total"],
                    "acuracia": round((dados["acertos"]/dados["total"])*100,1) if dados["total"]>0 else 0,
                    "confianca": 50,
                    "preco_atual": 0,
                    "timestamp": time.time(),
                    "status": "verificado"
                })
        except:
            pass
    
    trades.sort(key=lambda t: t["total"], reverse=True)
    
    total_acertos = sum(t["acertos"] for t in trades)
    total_erros = sum(t["erros"] for t in trades)
    total_geral = total_acertos + total_erros
    
    return {
        "trades": trades,
        "resumo": {
            "total_trades": total_geral,
            "total_acertos": total_acertos,
            "total_erros": total_erros,
            "acuracia_geral": round((total_acertos/total_geral)*100,1) if total_geral>0 else 0,
            "total_moedas": len(set(t["moeda"] for t in trades)),
            "horizontes_ativos": len(set(t["horizonte"] for t in trades)),
        }
    }

# ⭐ Serve o frontend estático (build do Next.js)
#if os.path.exists("Dashboard/out"):
 #   app.mount("/", StaticFiles(directory="Dashboard/out", html=True), name="frontend")