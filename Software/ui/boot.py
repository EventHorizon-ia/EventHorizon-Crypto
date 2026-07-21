import pygame
from Software.core.user_config import salvar_config

def desenhar_boot(screen, font_terminal, estado_ui, WIDTH, HEIGHT):

    passos = [
        "EXPERIMENTAL OPERATING SYSTEM - RSE",
        "------------------------------------",
        "INITIALIZING CORE MODULES...",
        "LOADING universe.json ............... [OK]",
        "CALIBRATING RELATIVISTIC CONSTANTS .. [OK]",
        "SYNCHRONIZING UNIT DNA STRUCTURES ... [OK]",
        "ESTABLISHING ENTROPY PROTOCOLS ....... [OK]",
        "VERIFYING CORE STATE REGISTERS ...... [OK]",
        "STABILIZING ENERGY FLOX DYNAMICS .... [OK]",
        "SYSTEM READY — LAUNCHING VISUAL INTERFACE..."
    ]

    # =========================
    # 1. FUNDO
    # =========================
    screen.fill((5, 5, 15))

    # =========================
    # 2. GRID (igual ao original)
    # =========================
    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, (15, 15, 25), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (15, 15, 25), (0, y), (WIDTH, y))

    # =========================
    # 3. TEXTO PROGRESSIVO
    # =========================
    y_offset = 100

    for i in range(min(estado_ui["boot_index"], len(passos))):

        # linha atual (a última) fica branca
        if i == estado_ui["boot_index"] - 1:
            cor = (255, 255, 255)
        else:
            cor = (0, 255, 200)

        txt = font_terminal.render(f"> {passos[i]}", True, cor)
        screen.blit(txt, (100, y_offset))
        y_offset += 25

    # =========================
    # 4. SCANLINES
    # =========================
    if estado_ui["fx_scanlines"]:
        for y in range(0, HEIGHT, 4):
            pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y))

    # =========================
    # 5. CONTROLE DE TEMPO (não bloqueante)
    # =========================
    agora = pygame.time.get_ticks()

    # atraso dinâmico (igual ao original)
    if estado_ui["boot_index"] < len(passos):
        linha = passos[estado_ui["boot_index"]]

        if "[OK]" in linha:
            delay = 120  # rápido
        else:
            delay = 300  # mais lento

        if agora - estado_ui["boot_timer"] > delay:
            estado_ui["boot_timer"] = agora
            estado_ui["boot_index"] += 1

    # =========================
    # 6. FINALIZAÇÃO
    # =========================
    if estado_ui["boot_index"] >= len(passos):

        if estado_ui["primeira_execucao"]:
            estado_ui["tela_atual"] = "tutorial"
            estado_ui["primeira_execucao"] = False
            salvar_config({"primeira_execucao": False})
        else:
            estado_ui["tela_atual"] = "visual"

        # reset para próxima vez
        estado_ui["boot_index"] = 0
        estado_ui["boot_timer"] = pygame.time.get_ticks()