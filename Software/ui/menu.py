import pygame

def desenhar_menu(screen, WIDTH, HEIGHT, universo, font, font_terminal):
    # 1. Fundo Base
    screen.fill((5, 5, 10)) # Azul muito escuro (quase preto)

    # 2. Desenhar Grade de Fundo (Grid)
    for x in range(0, WIDTH, 40):
        pygame.draw.line(screen, (15, 15, 25), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 40):
        pygame.draw.line(screen, (15, 15, 25), (0, y), (WIDTH, y))

    # 3. Textos Decorativos de "Sistema" (Cantos)
    meta_font = pygame.font.SysFont("consolas", 12)
    sys_status = meta_font.render("SYSTEM STATUS: READY", True, (0, 150, 150))
    version_id = meta_font.render("KERNEL_BUILD: v0.2.1-STABLE", True, (0, 150, 150))
    screen.blit(sys_status, (20, 20))
    screen.blit(version_id, (WIDTH - version_id.get_width() - 20, 20))

    # 4. Título com Brilho (Glow)
    titulo_texto = "Relativistic Computational Framework"
    # Sombra/Glow do título
    sombra = font.render(titulo_texto, True, (0, 80, 80))
    screen.blit(sombra, (WIDTH // 2 - sombra.get_width() // 2 + 2, 122))
    # Título principal
    principal = font.render(titulo_texto, True, (0, 255, 255))
    screen.blit(principal, (WIDTH // 2 - principal.get_width() // 2, 120))

    # 5. Lógica de Hover para Botões
    mouse_pos = pygame.mouse.get_pos()
    
    # --- Botão INICIAR ---
    btn_iniciar = pygame.Rect(WIDTH // 2 - 120, 300, 240, 50)
    cor_init = (0, 255, 255) if btn_iniciar.collidepoint(mouse_pos) else (0, 150, 150)
    
    # Fundo do botão (opacidade baixa)
    bg_init = pygame.Surface((btn_iniciar.width, btn_iniciar.height), pygame.SRCALPHA)
    bg_init.fill((*cor_init, 40))
    screen.blit(bg_init, (btn_iniciar.x, btn_iniciar.y))
    
    # Moldura e Cantos (Greebles)
    pygame.draw.rect(screen, cor_init, btn_iniciar, 1)
    # Cantos reforçados
    pygame.draw.line(screen, (255, 255, 255), (btn_iniciar.x, btn_iniciar.y), (btn_iniciar.x + 10, btn_iniciar.y), 2)
    pygame.draw.line(screen, (255, 255, 255), (btn_iniciar.x, btn_iniciar.y), (btn_iniciar.x, btn_iniciar.y + 10), 2)
 
    txt_iniciar = font_terminal.render(" > LAUNCH ENVIROMENT", True, cor_init)
    screen.blit(txt_iniciar, (WIDTH // 2 - txt_iniciar.get_width() // 2, 315))

    # --- Botão SAIR ---
    btn_sair = pygame.Rect(WIDTH // 2 - 120, 380, 240, 50)
    cor_sair = (255, 50, 50) if btn_sair.collidepoint(mouse_pos) else (150, 0, 0)
    
    pygame.draw.rect(screen, cor_sair, btn_sair, 1)
    txt_sair = font_terminal.render(" > TERMINATE SESSION", True, cor_sair)
    screen.blit(txt_sair, (WIDTH // 2 - txt_sair.get_width() // 2, 395))

    # --- Botão Configurações ---
    btn_config = pygame.Rect(WIDTH // 2 - 120, 460, 240, 50)
    cor_config = (200, 200, 200) if btn_config.collidepoint(mouse_pos) else (100, 100, 100)
    pygame.draw.rect(screen, cor_config, btn_config, 1)
    txt_config = font_terminal.render("SYSTEM SETTINGS", True, cor_config)
    screen.blit(txt_config, (WIDTH // 2 - txt_config.get_width() // 2, 475))

    # 6. Scanlines (Efeito de Monitor Antigo)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(screen, (0, 0, 0), (0, y), (WIDTH, y))

    dados_telemetria = universo.obter_telemetria()
    y_offset = 50
    for chave, valor in dados_telemetria.items():
            texto = f"{chave.upper()}: {valor}"
            txt_surf = meta_font.render(f"| {texto}", True, (0, 150, 150))
            screen.blit(txt_surf, (20, y_offset))
            y_offset += 18

    return btn_iniciar, btn_sair, btn_config
