# config_ia.py - Centraliza configurações da IA

import os

# ⭐ ESCOLHA O MODO: "linear" ou "pytorch"
# Comece com "linear" e depois mude para "pytorch"
MODO_IA = os.getenv("MODO_IA", "linear")  # padrão linear

# Configurações PyTorch
PYTORCH_N_ENTRADAS = 12
PYTORCH_LEARNING_RATE = 0.005
PYTORCH_SALVAR_AUTO = True