import time
import traceback

def evoluir_universo(universo, estado, terminal_linhas):

    escala_base = estado["escala_tempo"] * estado["escala_usuario"]
    escala = 0 if estado["pausado"] else escala_base

    universo.simulation_time += escala

    # ===== 1️⃣ Evoluir pulsos =====
    universo.evoluir_pulsos(escala)
    universo.estabilizar_loops()
    
    # ===== 2️⃣ Atualização física dos dados =====
    for dado in universo.dados[:]:

        if "cooldown" not in dado:
            dado["cooldown"] = 0.0

        if dado["cooldown"] > 0:
            dado["cooldown"] -= escala
            continue

        universo.aplicar_consumo(dado, escala)
        universo.aplicar_relatividade(dado, escala)
        universo.atualizar_estado(dado, escala)
        universo.atualizar_bits(dado)
        

        dado["dado_t"] += 0.05

        if dado["energia"] <= 0:
            universo.matar_dado(dado)


    for app in universo.apps:

        try:
            if hasattr(app, "update"):
                app.update()

        except Exception as e:

            erro = traceback.format_exc()

            universo.resultados_terminal.append(
                f"[APP ERROR] {app.nome}"
            )

            universo.resultados_terminal.append(erro)

            app.ativo = False

    # ===== 3️⃣ Agora sim mede o universo =====
    universo.atualizar_consciencia_global()

    # ===== 4️⃣ Decisões acontecem com estado atualizado =====
    for dado in universo.dados[:]:
        universo.decidir_interacoes(dado)

    # ===== 5️⃣ Processa mortes =====
    universo.processar_mortes()

    # ===== Terminal =====
    if universo.resultados_terminal:
        terminal_linhas.extend(universo.resultados_terminal)
        universo.resultados_terminal.clear()

    # ===== Estatísticas =====
    agora = time.time()
    if agora - universo._last_stats_time >= universo.stats_interval:
        universo.collect_stats()
        universo._last_stats_time = agora


