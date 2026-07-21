import pygame
import random

def desenhar_toggle(screen, x, y, texto, ativo, font_terminal):
    cor = (0, 255, 200) if ativo else (120, 120, 120)
    rect = pygame.Rect(x, y, 280, 40)

    pygame.draw.rect(screen, cor, rect, 1)

    label = font_terminal.render(
        f"{texto}: {'ON' if ativo else 'OFF'}",
        True,
        cor
    )
    screen.blit(label, (x + 10, y + 10))
    return rect


def desenhar_menu_configuracoes(screen, WIDTH, HEIGHT, font, font_terminal, estado_ui):
    screen.fill((5, 5, 10))

    for _ in range(300):
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        brilho = random.randint(10, 30)
        screen.set_at((x, y), (brilho, brilho, brilho))

    # GRID DE FUNDO
    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, (15, 15, 25), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (15, 15, 25), (0, y), (WIDTH, y))

    # TÍTULO
    titulo = font.render("SYSTEM CONFIGURATION", True, (255, 255, 255))
    screen.blit(titulo, (WIDTH // 2 - titulo.get_width() // 2, 40))

    # ===== EFEITOS =====
    btn_particulas = desenhar_toggle(
        screen,
        WIDTH // 2 - 160,
        130,
        "BACKGROUND PARTICLES",
        estado_ui["fx_particulas_fundo"],
        font_terminal
    )

    btn_scanlines = desenhar_toggle(
        screen,
        WIDTH // 2 - 160,
        180,
        "SCANLINES",
        estado_ui["fx_scanlines"],
        font_terminal
    )

    # ===== PRESETS =====
    txt_presets = font_terminal.render("GRAPHICS PRESETS", True, (180, 180, 200))
    screen.blit(txt_presets, (WIDTH // 2 - txt_presets.get_width() // 2, 250))

    btn_low = pygame.Rect(WIDTH // 2 - 180, 290, 120, 40)
    btn_med = pygame.Rect(WIDTH // 2 - 60, 290, 120, 40)
    btn_high = pygame.Rect(WIDTH // 2 + 60, 290, 120, 40)

    for btn, label in [
        (btn_low, "LOW"),
        (btn_med, "MEDIUM"),
        (btn_high, "HIGH")
        ]:
        ativo = (estado_ui["preset_atual"] == label)

        if ativo:
            cor = (0, 255, 200)
            espessura = 2
            brilho = True
        else:
            cor = (0, 120, 140)
            espessura = 1
            brilho = False

        pygame.draw.rect(screen, cor, btn, espessura)

        txt = font_terminal.render(label, True, cor)
        screen.blit(
            txt,
            (btn.x + btn.width // 2 - txt.get_width() // 2,
            btn.y + 10)
        )

        # brilho sutil no preset ativo
        if brilho:
            glow = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
            glow.fill((0, 255, 200, 30))
            screen.blit(glow, btn.topleft)

    # ===== VOLTAR =====
    btn_voltar = pygame.Rect(100, HEIGHT - 80, 220, 40)
    pygame.draw.rect(screen, (0, 255, 255), btn_voltar, 1)

    txt_voltar = font_terminal.render("BACK TO MENU", True, (0, 255, 255))
    screen.blit(txt_voltar, (btn_voltar.x + 20, btn_voltar.y + 10))

    return {
        "particulas": btn_particulas,
        "scanlines": btn_scanlines,
        "preset_low": btn_low,
        "preset_med": btn_med,
        "preset_high": btn_high,
        "voltar": btn_voltar
    }