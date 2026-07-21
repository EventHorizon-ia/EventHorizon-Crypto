import pygame
import sys

def processar_eventos(
        estado_ui,
        universo,
        estado,
        terminal_linhas,
        historico_comandos,
        sons,
        WIDTH,
        HEIGHT,
        font_terminal,
        get_prompt,
        processar_comando,
        CURSOR_DELAY,
        CURSOR_BLINK
):
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if estado_ui["tela_atual"] == "tutorial":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    estado_ui["tutorial_step"] += 1
                    sons["click"].play()
                    if estado_ui["tutorial_step"] >= 5:
                        estado_ui["tela_atual"] = "visual"
                        estado_ui["tutorial_step"] = 0
            continue  # 🔥 ESSENCIAL

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            estado_ui["clique_mouse"] = True
    
        if event.type == pygame.QUIT:
            if universo.apps_ativos():
                universo.resultados_terminal.append("[WARNING] Active apps detected.")
                sons["erro"].play()
                continue
            universo.finalizar()
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and estado_ui["tela_atual"] != "menu" and estado_ui["tela_atual"] != "configuracoes":
            if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                estado_ui["tela_atual"] = "visual" if estado_ui["tela_atual"] == "terminal" else "terminal"
                estado_ui["current_text"] = ""


            elif event.key == pygame.K_RETURN and estado_ui["tela_atual"] == "terminal":
                comando = estado_ui["current_text"].strip().lower()
                if comando == "":
                    estado_ui["current_text"] = ""
                    terminal_linhas.append(f"{get_prompt()}{comando}") #novo
                    estado_ui["scroll_offset"] = 0
                    estado_ui["ultimo_input"] = pygame.time.get_ticks()
                    estado_ui["cursor_visivel"] = True
                    continue
            
                terminal_linhas.append(f"{get_prompt()}{comando}") #novo
                estado_ui["scroll_offset"] = 0
                estado_ui["ultimo_input"] = pygame.time.get_ticks()
                estado_ui["cursor_visivel"] = True

                    
                respostas = processar_comando(comando, universo, estado)

                if comando != "":
                    historico_comandos.append(comando)
                    estado_ui["indice_historico"] = len(historico_comandos) - 1

                for r in respostas:
                    if r == "__CLEAR__":
                        terminal_linhas.clear()
                    else:
                        terminal_linhas.append(r)
                        estado_ui["current_text"] = ""

            elif event.key == pygame.K_BACKSPACE and estado_ui["tela_atual"] == "terminal":
                estado_ui["current_text"] = estado_ui["current_text"][:-1]
                estado_ui["ultimo_input"] = pygame.time.get_ticks()
                estado_ui["cursor_visivel"] = True


                
            elif event.key == pygame.K_UP and estado_ui["tela_atual"] == "terminal":
                if historico_comandos:
                    estado_ui["indice_historico"] = max(0, estado_ui["indice_historico"] - 1)
                    estado_ui["current_text"] = historico_comandos[estado_ui["indice_historico"]]

            # SETA PARA BAIXO
            elif event.key == pygame.K_DOWN and estado_ui["tela_atual"] == "terminal":
                if historico_comandos:
                    estado_ui["indice_historico"] = min(len(historico_comandos) - 1, estado_ui["indice_historico"] + 1)
                    estado_ui["current_text"] = historico_comandos[estado_ui["indice_historico"]]

            elif event.key == pygame.K_PAGEUP and estado_ui["tela_atual"] == "terminal":
                linhas_visiveis = (HEIGHT - 80) // font_terminal.get_linesize()
                max_scroll = max(0, len(terminal_linhas) - linhas_visiveis)
                estado_ui["scroll_offset"] = min(estado_ui["scroll_offset"] + 3, max_scroll)

            elif event.key == pygame.K_PAGEDOWN and estado_ui["tela_atual"] == "terminal":
                estado_ui["scroll_offset"] = max(0, estado_ui["scroll_offset"] - 3)

            elif event.key == pygame.K_F1:
                estado_ui["tela_atual"] = "menu"
                if universo.apps_ativos():
                    universo.resultados_terminal.append("[WARNING] Active apps detected.")
                    sons["erro"].play()



                

            elif estado_ui["tela_atual"] == "terminal":
                    
                estado_ui["current_text"] += event.unicode
                estado_ui["ultimo_input"] = pygame.time.get_ticks()
                estado_ui["cursor_visivel"] = True

        if event.type == pygame.MOUSEWHEEL and estado_ui["tela_atual"] == "terminal":
            linhas_visiveis = (HEIGHT - 80) // font_terminal.get_linesize()
            max_scroll = max(0, len(terminal_linhas) - linhas_visiveis)
            estado_ui["scroll_offset"] += event.y * 3
            estado_ui["scroll_offset"] = max(0, min(estado_ui["scroll_offset"], max_scroll))

        #-----------------------
        # CURSOR PISCANDO
        #-----------------------
    agora = pygame.time.get_ticks()

    if agora - estado_ui["ultimo_input"] > CURSOR_DELAY:
        if (agora // CURSOR_BLINK) % 2 == 0:
            estado_ui["cursor_visivel"] = True
        else:
            estado_ui["cursor_visivel"] = False
    else:
        estado_ui["cursor_visivel"] = True