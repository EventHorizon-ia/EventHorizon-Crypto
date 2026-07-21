PRESETS_GRAFICOS = {
    "LOW": {
        "fx_particulas_fundo": False,
        "fx_scanlines": False,
        "fx_fade": False,
        "fx_pulsos": False,
        "fx_glow": False,
    },
    "MEDIUM": {
        "fx_particulas_fundo": True,
        "fx_scanlines": False,
        "fx_fade": True,
        "fx_pulsos": True,
        "fx_glow": False,
    },
    "HIGH": {
        "fx_particulas_fundo": True,
        "fx_scanlines": True,
        "fx_fade": True,
        "fx_pulsos": True,
        "fx_glow": True,
    }
}

def aplicar_preset(nome_preset, estado_ui):
    preset = PRESETS_GRAFICOS[nome_preset]

    for efeito, valor in preset.items():
        estado_ui[efeito] = valor

    estado_ui["preset_atual"] = nome_preset



