import requests

TELEGRAM_TOKEN = "8898574077:AAFnKzYpum6CWiZgca4zgvAo6hB79qnT-rM"
CANAL_VIP_ID = "-1004322239279"
 
def enviar_teste():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL_VIP_ID,
        "text": "🚨 TESTE DE SINAL\n\n*Par:* BTC/USDT (M5)\n• *Entrada:* $64,250\n• *Alvo:* $64,800\n• *Stop:* $63,950\n\n📊 *Acurácia:* 57.2%\n📈 *Profit Factor:* 1.33",
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")

if __name__ == "__main__":
    enviar_teste()