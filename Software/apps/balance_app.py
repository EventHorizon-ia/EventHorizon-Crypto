class BalanceApp:
    nome = "balance_app"

    def __init__(self, universo):
        self.universo = universo
        self.ativo = False
        self.equilibrio_detectado = False
        self.interacoes = 0
        self.solucao_detectada = False
        self.loop_detectado = False

        # Rastreia o desvio antes de cada ação para calcular recompensa
        self._desvio_anterior: float | None = None

        self.config = {
            "units": None,
            "resource": None,
            "goal": None
        }

    def handle(self, comando):

        if comando.startswith("balance units"):
            valor = comando.split(" ", 2)[2]
            self.config["units"] = valor
            return [f"Units set to: {valor}"]

        if comando.startswith("balance resource"):
            valor = comando.split(" ", 2)[2]
            self.config["resource"] = valor
            return [f"Resource set to: {valor}"]

        if comando.startswith("balance goal"):
            valor = comando.split(" ", 2)[2]
            self.config["goal"] = valor
            return [f"Goal set to: {valor}"]

        if comando == "balance config":
            return [
                f"Units: {self.config['units']}",
                f"Resource: {self.config['resource']}",
                f"Goal: {self.config['goal']}"
            ]

        if comando == "balance start":
            if len(self.universo.dados) < 2:
                return ["At least 2 units are required to start balance simulation"]

            self.equilibrio_detectado = False
            self.interacoes = 0
            self.ativo = False
            self.solucao_detectada = False
            self.loop_detectado = False
            self._desvio_anterior = None

            if None in self.config.values():
                return ["Configuration incomplete"]

            import random
            for d in self.universo.dados:
                d["energia"] = random.uniform(1, 10)

            resultado = self.universo.medir_equilibrio()
            if resultado is None:
                return ["Error measuring balance"]

            return [
                "Problem initialized",
                f"Units = {self.config['units']}",
                f"Resource = {self.config['resource']}",
                f"Goal = {self.config['goal']}",
                f"Initial avg: {resultado['media']:.2f}",
                f"Initial dev: {resultado['desvio']:.2f}"
            ]

        if comando == "balance run":
            self.ativo = True
            return ["Balance simulation running"]

        if comando == "balance result":
            energias = [d["energia"] for d in self.universo.dados]
            if not energias:
                return ["No units"]
            media = sum(energias) / len(energias)
            variancia = sum((e - media) ** 2 for e in energias) / len(energias)
            desvio = variancia ** 0.5
            return [
                "Balance Result", "",
                f"Units: {self.config['units']}",
                f"Resource: {self.config['resource']}",
                f"Goal: {self.config['goal']}", "",
                f"Average energy: {media:.2f}",
                f"Deviation: {desvio:.2f}",
                f"Min energy: {min(energias):.2f}",
                f"Max energy: {max(energias):.2f}"
            ]

        if comando == "balance stop":
            self.ativo = False
            return ["Balance simulation stopped"]

        return None

    def update(self):
        if not self.ativo:
            return

        dados = self.universo.dados
        if not dados:
            return

        media = sum(d["energia"] for d in dados) / len(dados)

        excesso = [(d, d["energia"] - media) for d in dados if d["energia"] - media > 0.5]
        deficit = [(d, media - d["energia"]) for d in dados if media - d["energia"] > 0.5]

        # Mede desvio antes das ações para calcular recompensa depois
        resultado_antes = self.universo.medir_equilibrio()
        desvio_antes = resultado_antes["desvio"] if resultado_antes else None

        for origem, sobra in excesso:
            melhor_destino = None
            melhor_score = -float("inf")

            for destino, falta in deficit:
                dx = origem["pos"][0] - destino["pos"][0]
                dy = origem["pos"][1] - destino["pos"][1]
                distancia = (dx ** 2 + dy ** 2) ** 0.5

                # ── Mente decide o score de cada candidato ────────────────
                # Entrada: energia origem, energia destino, distância, falta, desvio global
                entrada = [
                    origem["energia"] / 10.0,
                    destino["energia"] / 10.0,
                    distancia / 1000.0,
                    falta / 10.0,
                    (desvio_antes or 0) / 10.0,
                ]
                score_mente = self.universo.forward(origem, destino["energia"], distancia)

                # Combina mente com heurística clássica (custo = dist / falta)
                custo_classico = distancia / (falta + 0.001)
                score_final = score_mente - custo_classico * 0.01

                if score_final > melhor_score:
                    melhor_score = score_final
                    melhor_destino = destino
                    melhor_falta = falta

            if melhor_destino is None:
                continue

            # ── Mente decide quanto transferir ────────────────────────────
            # tanh retorna -1..1, mapeamos para 0.05..0.35 do excesso
            saida_mente = self.universo.forward(origem, melhor_destino["energia"],
                          ((origem["pos"][0] - melhor_destino["pos"][0]) ** 2 +
                           (origem["pos"][1] - melhor_destino["pos"][1]) ** 2) ** 0.5)

            fator = 0.2 + saida_mente * 0.15   # 0.05 a 0.35
            energia = min(sobra, melhor_falta) * fator

            if energia <= 0:
                continue

            self.universo.enviar_pulso(origem["id"], melhor_destino["id"], energia)
            self.interacoes += 1

        # ── Recompensa: melhora no desvio ─────────────────────────────────
        resultado_depois = self.universo.medir_equilibrio()
        if resultado_depois and desvio_antes is not None:
            melhora = desvio_antes - resultado_depois["desvio"]
            # Recompensa positiva se o desvio caiu, negativa se piorou
            recompensa = melhora * 2.0
            recompensa = max(-1.0, min(1.0, recompensa))

            for d in dados:
                self.universo.aprender(d, recompensa)

        # ── Detecções ─────────────────────────────────────────────────────
        resultado = self.universo.medir_equilibrio()

        if resultado:
            if resultado["desvio"] < 2.0 and not self.equilibrio_detectado:
                self.equilibrio_detectado = True
                self.ativo = False
                self.universo.resultados_terminal.append(
                    f"[BALANCE] Stable | avg={resultado['media']:.2f} "
                    f"dev={resultado['desvio']:.2f} | interactions={self.interacoes}"
                )

        solucao = self.universo.ler_solucao()
        if solucao and not self.solucao_detectada:
            self.solucao_detectada = True
            self.universo.resultados_terminal.append(
                f"[SOLUTION] cluster | size={solucao['tamanho']} "
                f"energy={solucao['energia']:.2f} coherence={solucao['coerencia']:.2f}"
            )

        loops = self.universo.detectar_loops_energia()
        if loops and not self.loop_detectado:
            self.loop_detectado = True
            self.universo.resultados_terminal.append(
                f"[LOOP] energy cycle detected: {loops[0]}"
            )