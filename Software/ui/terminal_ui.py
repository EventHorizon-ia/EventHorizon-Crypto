import pygame
import random
def desenhar_terminal(surface, linhas, font, largura_max, estado_ui, HEIGHT):
    y = 40
    linhas_quebradas = []
    
    # Quebra cada linha se ultrapassar a largura máxima
    for linha in linhas:
        linha = str(linha)
        palavras = linha.split(" ")
        atual = ""
        for palavra in palavras:
            teste = atual + (" " if atual else "") + palavra
            if font.size(teste)[0] > largura_max:
                linhas_quebradas.append(atual)
                atual = palavra
            else:
                atual = teste
        linhas_quebradas.append(atual)
    
    linhas_visiveis = (HEIGHT - 80) // font.get_linesize()

    total = len(linhas_quebradas)
    start = max(0, total - linhas_visiveis - estado_ui["scroll_offset"])
    end = max(0, total - estado_ui["scroll_offset"])

    for l in linhas_quebradas[start:end]:
        texto = font.render(l, True, (0, 255, 0))
        surface.blit(texto, (10, y))
        y += font.get_linesize()
    return y

def desenhar_tela_terminal(screen, terminal_linhas, font_terminal, estado_ui, WIDTH, HEIGHT, get_prompt):
    screen.fill((10, 10, 10))
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y))

    for _ in range(100):
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        brilho = random.randint(0, 30)
        screen.set_at((x, y), (0, brilho, 0))

    y_input = desenhar_terminal(
        screen,
        terminal_linhas,
        font_terminal,
        WIDTH - 20,
        estado_ui,
        HEIGHT
    )

    if estado_ui["cursor_visivel"] == True:
        cursor = "|"
    else:
        cursor = ""

    prompt_text = f"{get_prompt()}{estado_ui['current_text']}{cursor}"
    text_surface = font_terminal.render(prompt_text, True, (0, 255, 0))
    screen.blit(text_surface, (10, y_input))
