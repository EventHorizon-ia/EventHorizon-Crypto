import pygame
import sys

from Software.ui.menu import desenhar_menu
from Software.ui.configuracoes import desenhar_menu_configuracoes
from Software.ui.visual import desenhar_tela_visual
from Software.ui.terminal_ui import desenhar_tela_terminal
from Software.ui.boot import desenhar_boot
from Software.ui.presets import aplicar_preset

from Software.core.tutorial import desenhar_tutorial


def desenhar_tela_atual(
    screen,
    estado_ui,
    universo,
    estado,
    terminal_linhas,
    historico_comandos,
    sons,
    font,
    font_terminal,
    WIDTH,
    HEIGHT,
    cores_tipos,
    evoluir_universo,
    get_prompt
):

    mouse_pos = pygame.mouse.get_pos()

    # ================= MENU =================
    if estado_ui["tela_atual"] == "menu":

        btn_iniciar, btn_sair, btn_config = desenhar_menu(
            screen, WIDTH, HEIGHT, universo, font, font_terminal
        )

        if estado_ui["clique_mouse"]:
            if btn_iniciar.collidepoint(mouse_pos):
                sons["click"].play()
                estado_ui["tela_atual"] = "boot"
                estado_ui["boot_index"] = 0
                estado_ui["boot_timer"] = pygame.time.get_ticks()
                sons["whoosh"].play()

            elif btn_sair.collidepoint(mouse_pos):
                universo.finalizar()
                pygame.quit()
                sys.exit()

            elif btn_config.collidepoint(mouse_pos):
                estado_ui["tela_atual"] = "configuracoes"
                sons["click"].play()

    # ================= CONFIG =================
    elif estado_ui["tela_atual"] == "configuracoes":

        botoes = desenhar_menu_configuracoes(
            screen, WIDTH, HEIGHT, font, font_terminal, estado_ui
        )

        if estado_ui["clique_mouse"]:
            if botoes["particulas"].collidepoint(mouse_pos):
                sons["click"].play()
                estado_ui["fx_particulas_fundo"] = not estado_ui["fx_particulas_fundo"]

            elif botoes["scanlines"].collidepoint(mouse_pos):
                sons["click"].play()
                estado_ui["fx_scanlines"] = not estado_ui["fx_scanlines"]

            elif botoes["preset_low"].collidepoint(mouse_pos):
                sons["click"].play()
                aplicar_preset("LOW", estado_ui)

            elif botoes["preset_med"].collidepoint(mouse_pos):
                sons["click"].play()
                aplicar_preset("MEDIUM", estado_ui)

            elif botoes["preset_high"].collidepoint(mouse_pos):
                sons["click"].play()
                aplicar_preset("HIGH", estado_ui)

            elif botoes["voltar"].collidepoint(mouse_pos):
                sons["click"].play()
                estado_ui["tela_atual"] = "menu"

    # ================= VISUAL =================
    elif estado_ui["tela_atual"] == "visual":
        desenhar_tela_visual(
            screen,
            universo,
            estado,
            estado_ui,
            font_terminal,
            WIDTH,
            HEIGHT,
            cores_tipos,
            evoluir_universo,
            terminal_linhas
        )

    
    # ================= BOOT =================
    elif estado_ui["tela_atual"] == "boot":
        desenhar_boot(screen, font_terminal, estado_ui, WIDTH, HEIGHT)

    # ================= TERMINAL =================
    elif estado_ui["tela_atual"] == "terminal":
        desenhar_tela_terminal(
            screen,
            terminal_linhas,
            font_terminal,
            estado_ui,
            WIDTH,
            HEIGHT,
            get_prompt
        )

    # ================= TUTORIAL =================
    elif estado_ui["tela_atual"] == "tutorial":
        desenhar_tutorial(screen, WIDTH, HEIGHT, font, estado_ui)