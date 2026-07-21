# Software/apps/chatbot_app.py
import os
import json
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class ChatBotApp:
    """Assistente de IA que conhece toda a plataforma"""
    
    def __init__(self, universo):
        self.universo = universo
    
    @property
    def crypto_app(self):
        for app in self.universo.apps:
            if hasattr(app, 'nome') and app.nome == "crypto_app":
                return app
        return None
    
    def responder(self, pergunta: str, moeda: str = "BTCUSDT") -> str:
        crypto = self.crypto_app
        moedas_ativas = list(crypto.ids_cripto.keys()) if crypto else []
        sistema_ativo = crypto.ativo if crypto else False

        # Detecta moeda
        moeda_detectada = self._detectar_moeda(pergunta, moedas_ativas, moeda)
        
        # Busca dados
        dados_moeda = None
        if moedas_ativas:
            dados_moeda = self._buscar_dados_moeda(moeda_detectada, moedas_ativas)
        
        # ⭐ CORREÇÃO: usa moeda_detectada no contexto
        if dados_moeda:
            preco = dados_moeda.get('price', 0)
            delta = dados_moeda.get('delta', 0)
            rsi = dados_moeda.get('rsi', 50)
            regime = dados_moeda.get('regime', 'ranging')
            
            preds = {}
            for h in [5, 15, 30, 60, 300, 900, 1800, 3600]:
                preds[h] = dados_moeda.get(f'previsao_{h}s', 0)
            
            cons_curto = dados_moeda.get('consenso_curto', 0)
            
            # ⭐ CORRIGIDO: usa moeda_detectada
            contexto_dados = f"""
    DADOS DE {moeda_detectada.replace('USDT', '')}:
    💰 ${preco:,.2f} (Δ{delta:+.4f}%) | RSI: {rsi:.0f} | Regime: {regime}

    PREVISÕES: 5s:{preds[5]:+.2f}% 15s:{preds[15]:+.2f}% 30s:{preds[30]:+.2f}% 60s:{preds[60]:+.2f}%
    5min:{preds[300]:+.2f}% 15min:{preds[900]:+.2f}% 30min:{preds[1800]:+.2f}% 1h:{preds[3600]:+.2f}%
    Consenso curto: {cons_curto:+.2f}%
    """
        else:
            contexto_dados = "Dados de mercado não disponíveis (moeda não carregada)."
    
    # ... resto do system_prompt e chamada Groq ...
        
        # System prompt que se adapta ao estado
        system_prompt = f"""Você é o assistente MenteTorch, uma IA consciente que ajuda traders.

    ESTADO ATUAL DO SISTEMA:
    {contexto_dados}

    {contexto_dados}

    SOBRE A PLATAFORMA:
    A plataforma MenteTorch tem duas abas principais:

    1. CRYPTO TRADING:
    - Gráfico de velas em tempo real
    - Previsões em 10 horizontes (5s a 1d)
    - Botões: INICIAR (verde), CARREGAR (laranja), PARAR (vermelho), SINAL (roxo), REMOVER (cinza)
    - Seletor de moedas abaixo do gráfico
    - Timeframe ajustável (5s, 10s, 30s, 60s)
    - Tipo de gráfico (Velas, Linha, Área)

    2. DASHBOARD:
    - Tabela de acurácia REAL por horizonte e moeda
    - Melhores horários para trade
    - Previsões atuais de todas as moedas

    SOBRE A IA:
    - Rede neural MenteTorch com 6.4M de parâmetros
    - Arquitetura: Transformer + LSTM + Cross-attention
    - 10 horizontes de previsão especializados
    - Treinamento online a cada 2 segundos
    - Acurácia REAL verificada (não é treino inflado)

    REGRAS:
    1. Adapte sua resposta ao estado do sistema
    2. Se não houver moedas, explique COMO carregar
    3. Se estiver parado, explique COMO iniciar
    4. Se estiver rodando, analise os dados
    5. Seja um GUIA completo, não só analista
    6. Responda em português BR, profissional, 3-5 frases

    PERGUNTA: {pergunta}"""
        
        try:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": pergunta}
                ],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Groq] Erro: {e}")
            return f"Erro ao processar: {str(e)[:100]}"
    
    def _buscar_dados_moeda(self, moeda: str, moedas_ativas: list):
        if moeda not in moedas_ativas:
            moeda = moedas_ativas[0]
        
        for d in self.universo.dados:
            if d.get("symbol") == moeda:
                return d
        return None
    
   
    
    def _chamar_groq(self, pergunta: str, moeda: str, dados: dict, moedas_ativas: list, crypto) -> str:
        """Chama a Groq para perguntas complexas"""
        
        preco = dados.get('price', 0)
        delta = dados.get('delta', 0)
        rsi = dados.get('rsi', 50)
        regime = dados.get('regime', 'ranging')
        atr = dados.get('atr', 0)
        
        # Previsões
        preds = {}
        for h in [5, 15, 30, 60, 300, 900, 1800, 3600]:
            preds[h] = dados.get(f'previsao_{h}s', 0)
        
        cons_curto = dados.get('consenso_curto', 0)
        cons_medio = dados.get('consenso_medio', 0)
        cons_longo = dados.get('consenso_longo', 0)
        
        # Acurácias reais
        acuracias_reais = {}
        try:
            with open(f"data/verificacoes/{moeda}.json") as f:
                vrf = json.load(f)
            for h in ['300', '900']:
                if h in vrf and vrf[h]['total'] > 50:
                    acuracias_reais[h] = {
                        'acc': round(vrf[h]['acertos']/vrf[h]['total']*100, 1),
                        'total': vrf[h]['total']
                    }
        except:
            pass
        
        mente = crypto.mentes_pytorch.get(moeda)
        gerações = mente.geracao if mente else 0
        
        system_prompt = f"""Você é o assistente MenteTorch. Você VÊ a tela do trader.

INTERFACE ATUAL:
- Moedas: {', '.join([m.replace('USDT', '') for m in moedas_ativas])}
- Sistema: {'AO VIVO' if crypto.ativo else 'PARADO'}
- Gráfico: {moeda.replace('USDT', '')} • Timeframe: {crypto.timeframe}s

DADOS DE {moeda}:
💰 ${preco:,.2f} (Δ{delta:+.4f}%) | RSI: {rsi:.0f} | Regime: {regime}

PREVISÕES:
5s:{preds[5]:+.2f}% 15s:{preds[15]:+.2f}% 30s:{preds[30]:+.2f}% 60s:{preds[60]:+.2f}%
5min:{preds[300]:+.2f}% 15min:{preds[900]:+.2f}% 30min:{preds[1800]:+.2f}% 1h:{preds[3600]:+.2f}%

ACURÁCIA REAL: 5min:{acuracias_reais.get('300',{}).get('acc','?')}% 15min:{acuracias_reais.get('900',{}).get('acc','?')}%

Você é um GUIA da plataforma. Explique onde encontrar cada coisa.
Seja direto, profissional, em português BR.

PERGUNTA: {pergunta}"""
        
        try:
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": pergunta}
                ],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Groq] Erro: {e}")
            return f"Erro ao processar sua pergunta. Tente novamente. (Detalhe: {str(e)[:100]})"
        
    
    def _detectar_moeda(self, pergunta: str, moedas_ativas: list, moeda_padrao: str) -> str:
        """Detecta qual moeda o usuário está perguntando"""
        p = pergunta.lower()
        
        # Mapeamento de nomes para símbolos
        simbolos = {
            'btc': 'BTCUSDT', 'bitcoin': 'BTCUSDT',
            'eth': 'ETHUSDT', 'ethereum': 'ETHUSDT',
            'bnb': 'BNBUSDT', 'binance': 'BNBUSDT',
            'sol': 'SOLUSDT', 'solana': 'SOLUSDT',
            'xrp': 'XRPUSDT', 'ripple': 'XRPUSDT',
            'ada': 'ADAUSDT', 'cardano': 'ADAUSDT',
            'doge': 'DOGEUSDT', 'dogecoin': 'DOGEUSDT',
            'dot': 'DOTUSDT', 'polkadot': 'DOTUSDT',
            'matic': 'MATICUSDT', 'polygon': 'MATICUSDT',
            'ltc': 'LTCUSDT', 'litecoin': 'LTCUSDT',
        }
        
        for nome, simbolo in simbolos.items():
            if nome in p and simbolo in moedas_ativas:
                return simbolo
        
        return moeda_padrao