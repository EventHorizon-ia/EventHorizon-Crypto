import json
import os

CAMINHO_CONFIG = "user_config.json"

def carregar_config():
    if not os.path.exists(CAMINHO_CONFIG):
        return {"primeira_execucao": True}

    try:
        with open(CAMINHO_CONFIG, "r") as f:
            return json.load(f)
    except:
        return {"primeira_execucao": True}


def salvar_config(config):
    with open(CAMINHO_CONFIG, "w") as f:
        json.dump(config, f, indent=4)