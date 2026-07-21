import math
import pygame
import random

def interpretar_energia(e):
    if e > 7:
        return "HIGH"
    elif e > 3:
        return "MEDIUM"
    else:
        return "CRITICAL"

def interpretar_tempo(fator):
    if fator < 0.6:
        return "SLOW"
    elif fator < 0.9:
        return "NORMAL"
    else:
        return "FAST"

def interpretar_bits(bits):
    return {
        "coop": "ACTIVE" if bits[0] else "INHIBITED",
        "acao": "OK" if bits[1] else "LIMITED",
        "seg": "STABLE" if bits[2] else "RISK"
    }

def calcular_cor(dado):
    energia_norm = min(1.0, dado["energia"] / 20.0)
    r = int((0.5 + 0.5 * dado["estado"][0]) * 255 * energia_norm)
    g = int((0.5 + 0.5 * dado["estado"][1]) * 255 * energia_norm)
    b = int((0.5 + 0.5 * dado["estado"][2]) * 255 * energia_norm)
    return (
        max(0, min(255, r)),
        max(0, min(255, g)),
        max(0, min(255, b))
    )

def fator_glow_preset(estado_ui):
    if estado_ui["preset_atual"] == "LOW":
        return 0.2
    if estado_ui["preset_atual"] == "MEDIUM":
        return 0.5
    if estado_ui["preset_atual"] == "HIGH":
        return 1.0              
    
def desenhar_fundo_profissional(screen, WIDTH, HEIGHT, estado_ui):
    # Fundo escuro base
    base_color = (5, 5, 10)
    screen.fill(base_color)  # só se quiser garantir início do frame

    # Grade muito sutil
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (15, 15, 20), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (15, 15, 20), (0, y), (WIDTH, y))
    
def desenhar_dado_pixelado(screen, dado, cores_tipos, estado, estado_ui, WIDTH, HEIGHT):
    cx, cy = int(dado["pos"][0]), int(dado["pos"][1])

    energia = max(0.0, min(dado["energia"], 10))
    energia_norm = energia / 10.0

    r0, g0, b0 = calcular_cor(dado)

    escala = 1.6 + energia_norm * 1.2

    # ================= NÚCLEO SÓLIDO =================
    t = dado.get("dado_t", 0)

    if estado["pausado"]:
        pulso = 1.0
        raio_base = 4.2 * escala
        raio_nucleo = int(raio_base * pulso)
    else:

        pulso = 1.0 + 0.12 * math.sin(t)
        raio_base = 4.2 * escala
        raio_nucleo = int(raio_base * pulso)

    branco = min(255, int(225 + 30 * energia_norm))
    cor_nucleo = (branco, branco, branco)

# núcleo sólido
    pygame.draw.circle(
        screen,
        cor_nucleo,
        (cx, cy),
        raio_nucleo
    )

# -------- GLOW EM CAMADAS --------
    glow_factor = fator_glow_preset(estado_ui)
    for i in range(1, 6):
        glow_raio = int(raio_nucleo + i * 2.5)
        alpha = int((40 / i) * glow_factor)

        glow_surf = pygame.Surface(
            (glow_raio * 2, glow_raio * 2),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow_surf,
            (*cor_nucleo, alpha),
            (glow_raio, glow_raio),
            glow_raio
        )

        screen.blit(
            glow_surf,
            (cx - glow_raio, cy - glow_raio)
        )

    # ================= ANÉIS DE PARTÍCULAS =================
    if estado_ui["preset_atual"] in ("MEDIUM", "HIGH"):
        for dx, dy, brilho in dado["pixels"]:
            dist = math.sqrt(dx * dx + dy * dy)
            

            raio_anel = 8.0 * escala

            if dist > raio_anel:
                continue

            fator = (1 - dist / raio_anel) * brilho
            fator *= (0.6 + 0.6 * energia_norm)

            neon = 1.4 + energia_norm * 0.8

            cor = (
                min(255, int((r0 * energia_norm + 220) * fator * neon)),
                min(255, int((g0 * energia_norm + 220) * fator * neon)),
                min(255, int((b0 * energia_norm + 220) * fator * neon))
            )

            x = int(cx + dx * escala)
            y = int(cy + dy * escala)

            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                screen.set_at((x, y), cor)

def desenhar_pulsos(universo, screen, estado, estado_ui):

    tempo = pygame.time.get_ticks() * 0.004

    for pulso in universo.pulsos:
        ox, oy = pulso["pos_origem"]
        dx, dy = pulso["pos_destino"]

        vx = dx - ox
        vy = dy - oy
        dist = math.hypot(vx, vy)
        if dist == 0:
            continue

        ux = vx / dist
        uy = vy / dist

        # perpendicular (espessura)
        px = -uy
        py = ux

        energia = pulso["energia"]

        # =========================
        # 1️⃣ FEIXE (cor do dado)
        # =========================
        if estado_ui["preset_atual"] == "LOW":
            largura = 1   
            brilho_base = 0.4
            escala_largura = 0.4
        elif estado_ui["preset_atual"] == "MEDIUM":
            largura = 2   
            brilho_base = 0.7
            escala_largura = 0.7
        elif estado_ui["preset_atual"] == "HIGH":
            largura = 3  
            brilho_base = 1.0
            escala_largura = 1.0

        passos = int(dist / 2)

        for i in range(passos):
            f = i / passos
            x = ox + vx * f
            y = oy + vy * f

            ruido = math.sin(tempo + i * 0.15) * 0.6

            for w in range(-largura, largura + 1):
                intensidade = 1 - abs(w) / max(1, largura)
                brilho = energia * intensidade * brilho_base
                intensidade *= escala_largura

                fx = x + px * w + px * ruido
                fy = y + py * w + py * ruido

                cor = (
                    int(0),   
                    int(0),   
                    0
                )

                pygame.draw.rect(
                    screen,
                    cor,
                    (int(fx), int(fy), 2, 2)
                )

        # =========================
        # 2️⃣ NÚCLEO DO FEIXE
        # =========================
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (ox, oy),
            (dx, dy),
            2
        )

        # =========================
        # 3️⃣ QUANTA (bolinha branca pulsante)
        # =========================
        t = pulso["progresso"]

        bx = ox + vx * t
        by = oy + vy * t
        if estado["pausado"]:
            pulso_vida = 0.0
            raio = 3
        else:
            pulso_vida = (math.sin(tempo * 2) + 1) / 2
            raio = 3 + pulso_vida * 3

        # glow
        for r in range(int(raio * 3), int(raio), -1):
            alpha = int(120 * (1 - r / (raio * 3)))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(
                surf,
                (255, 255, 255, alpha),
                (r, r),
                r
            )
            screen.blit(surf, (bx - r, by - r))

        # núcleo branco
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (int(bx), int(by)),
            int(raio)
        )

def desenhar_particulas_fundo(WIDTH, HEIGHT, screen, estado_ui, ):
    for i in range(50):
        x = random.randint(0, WIDTH-1)
        y = random.randint(0, HEIGHT-1)
        brilho = random.randint(10, 30)
        screen.set_at((x, y), (brilho, brilho, brilho))

def desenhar_hud(screen, universo, font, WIDTH, HEIGHT):
    total_dados = len(universo.dados)
    total_pulsos = len(universo.pulsos)
    if total_dados > 0:
        energia_media = sum(d["energia"] for d in universo.dados) / total_dados
    else:
        energia_media = 0

    estado = "STABLE" if energia_media > 4 else "CRITICAL" if energia_media > 1 else "COLLAPSE"
    linhas = [
        "RSE SYSTEM v0.2",
        f"UNITS: {total_dados}",
        f"PULSES: {total_pulsos}",
        f"ENERGY AVG: {energia_media:.2f} ({estado})",
        f"STATE: {estado}"
    ]

    y = HEIGHT - 100
    for linha in linhas:
        txt = font.render(linha, True, (0, 255, 200))
        screen.blit(txt, (WIDTH - 225, y))
        y += 18

def desenhar_log_visual(screen, terminal_linhas, font, WIDTH, HEIGHT):
    y = HEIGHT - 100
    ultimas = terminal_linhas[-5:]
    for linha in ultimas:
        txt = font.render(linha, True, (0, 255, 0))
        screen.blit(txt, (10, y))
        y += 16

def desenhar_status_avancado(screen, estado_ui, font, WIDTH, HEIGHT):

    x = WIDTH / 2 - 190
    y = HEIGHT - 120

    bg = pygame.Surface((380, 100), pygame.SRCALPHA)
    bg.fill((0, 20, 20, 180))
    screen.blit(bg, (x, y))

    max_index = min(estado_ui["log_index"], len(estado_ui["log_sistema"]) - 1)
    for i in range(max_index + 1):
        txt = font.render(
            estado_ui["log_sistema"][i],
            True,
            (0, 255, 200)
        )
        screen.blit(txt, (x + 10, y + 10 + i * 20))

def analisar_sistema(universo, estado_ui):

    mensagens = []

    # -------------------------
    # 1. DETECTAR DESEQUILÍBRIO
    # -------------------------
    if len(universo.dados) > 1:
        energias = [d["energia"] for d in universo.dados]
        media = sum(energias) / len(energias)

        variacao = max(energias) - min(energias)

        if variacao > 5:
            mensagens.append("> Detected energy imbalance")

    # -------------------------
    # 2. CLUSTERS (simples)
    # -------------------------
    clusters = 0
    for d1 in universo.dados:
        vizinhos = 0
        for d2 in universo.dados:
            if d1 == d2:
                continue
            dist = ((d1["pos"][0]-d2["pos"][0])**2 + (d1["pos"][1]-d2["pos"][1])**2) * 0.5
            if dist < 80:
                vizinhos += 1
        if vizinhos >= 2:
            clusters += 1

    if clusters > 0:
        mensagens.append(f"> Detected cluster activity ({clusters})")

    # -------------------------
    # 3. PULSOS
    # -------------------------
    if len(universo.pulsos) > 5:
        mensagens.append("> High pulse traffic")

    # -------------------------
    # 4. ESTABILIZAÇÃO
    # -------------------------
    if len(mensagens) == 0:
        mensagens.append("> System stable")

    if len(universo.dados) == 0:
        mensagens = ["> All units exhausted - system collapse"]

    return mensagens

def desenhar_baloezinho_dado(screen, dado, pos_mouse, font, estado_ui, WIDTH, HEIGHT):
    # Informação relevante
    energia = dado["energia"]
    id = dado["id"]
    estado = dado.get("estado", [0, 0, 0])
    tempo_proprio = dado.get("tempo_proprio", 0)
    fator_tempo = dado.get("fator_tempo", 1.0)
    
    # Interpretar energia e fator de tempo
    estado_energia = interpretar_energia(energia)
    ritmo = interpretar_tempo(fator_tempo)
    
    texto = [
        f"UNIT #{id}",
        f"Energy: {energia:.2f} / 10 ({estado_energia})",
        f"Proper time: {tempo_proprio:.2f}",
        f"Temporal rhythm: {ritmo}",
        f"State: [fase: {estado[0]:.2f}, tensao: {estado[1]:.2f}, coerencia: {estado[2]:.2f}]"
    ]
    
    # --- Calcula tamanho do balão ---
    largura = max(font.size(l)[0] for l in texto) + 10
    altura = len(texto) * font.get_linesize() + 6
    x, y = pos_mouse
    x += 15 if x + largura + 15 < WIDTH else -largura - 15
    y += 15 if y + altura + 15 < HEIGHT else -altura - 15
    
    # --- Desenha o fundo do balão ---
    pygame.draw.rect(screen, (20, 20, 20), (x, y, largura, altura))
    pygame.draw.rect(screen, (200, 200, 200), (x, y, largura, altura), 1)
    
    # --- Desenha cada linha de texto ---
    for i, linha in enumerate(texto):
        txt_surf = font.render(linha, True, (0, 255, 200))
        screen.blit(txt_surf, (x + 5, y + 3 + i * font.get_linesize()))


def desenhar_tela_visual(screen, universo, estado, estado_ui, font_terminal, WIDTH, HEIGHT, cores_tipos, evoluir_universo, terminal_linhas):
    desenhar_fundo_profissional(screen, WIDTH, HEIGHT, estado_ui)

    if estado_ui["fx_particulas_fundo"]:
        desenhar_particulas_fundo(WIDTH, HEIGHT, screen, estado_ui)
    

    # ----------------------------------
    # EVOLUIR UNIVERSO
    # ----------------------------------
    evoluir_universo(universo, estado, terminal_linhas)
    desenhar_pulsos(universo, screen, estado, estado_ui)

    agora = pygame.time.get_ticks()

    if agora - estado_ui["log_timer"] > 3000:

        estado_ui["log_timer"] = agora

        novas_msgs = analisar_sistema(universo, estado_ui)

        estado_ui["log_sistema"] = novas_msgs
        estado_ui["log_index"] = 0

    
    if estado_ui["log_sistema"]:
        if agora - estado_ui["log_timer"] > 1000:
            if estado_ui["log_index"] < len(estado_ui["log_sistema"]) - 1:
                estado_ui["log_index"] += 1




    # ----------------------------------
    # DESENHAR DADOS
    # ----------------------------------
    
    for dado in universo.dados:
        desenhar_dado_pixelado(screen, dado, cores_tipos, estado, estado_ui, WIDTH, HEIGHT)

    # Encontrar o dado mais próximo do mouse
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dado_selecionado = None
    menor_dist = float('inf')

    for dado in universo.dados:
        dx, dy = dado["pos"]
        dist = math.hypot(mouse_x - dx, mouse_y - dy)
        raio = 8 + (dado["energia"] / 10) * 8  # área ativa
        if dist <= raio and dist < menor_dist:
            menor_dist = dist
            dado_selecionado = dado

    # Desenhar o balão apenas para o dado selecionado
    if dado_selecionado:
        desenhar_baloezinho_dado(screen, dado_selecionado, (mouse_x, mouse_y), font_terminal, estado_ui, WIDTH, HEIGHT)
        
    
    # ----------------------------------
    # FADE SUAVE (mantém pixels antigos mas vai escurecendo)
    # ----------------------------------
    if estado_ui["fx_fade"]:
        fade_surf = pygame.Surface((WIDTH, HEIGHT))
        if estado_ui["preset_atual"] == "LOW":
            fade_surf.set_alpha(90)
        if estado_ui["preset_atual"] == "MEDIUM":
            fade_surf.set_alpha(50)
        if estado_ui["preset_atual"] == "HIGH":
            fade_surf.set_alpha(30)

        fade_surf.fill((0, 0, 0))  # cor do fade (preto)
        screen.blit(fade_surf, (0, 0))    

    desenhar_hud(screen, universo, font_terminal, WIDTH, HEIGHT)
    desenhar_log_visual(screen, terminal_linhas, font_terminal, WIDTH, HEIGHT)
    desenhar_status_avancado(screen, estado_ui, font_terminal, WIDTH, HEIGHT)
    