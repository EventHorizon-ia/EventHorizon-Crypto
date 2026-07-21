contexto_atual = "rse"

CONTEXTO_APPS = {
    "rse": None,
    "units": ["data_app"],
    "pulse": ["pulse_app"],
    "time": ["time_app"]
}


def processar_comando(comando, universo, estado):
    global contexto_atual
    respostas = []
    partes = comando.split()

    apps_permitidos = CONTEXTO_APPS.get(contexto_atual)

    if comando in ("rse", "units", "pulse", "time"):
        
        contexto_atual = comando
        return [f"Context changed to {contexto_atual}"]

    for app in universo.apps:
        nome_app = getattr(app, "nome", None)

        if apps_permitidos is not None and nome_app not in apps_permitidos:
            continue

        if comando == "apps":
            nomes = [app.nome]
            return [
                f"BalanceApp, FlowApp and CryptoApp are available"
            ]

        if comando.startswith("crypto") and app.nome == "crypto_app":
            resposta = app.handle(comando)
            if resposta is not None:
                return resposta
            
    for app in universo.apps:
        resposta = app.handle(comando)
        if resposta is not None:
            return resposta

                # -----------------------
                # COMANDO INVÁLIDO
                # -----------------------
    
    return [f"Command: '{comando}' not recognized in context '{contexto_atual}'"]

    return respostas     

def get_prompt():
    return f"{contexto_atual}> "




