class FlowApp:
    nome = "flow_app"

    def __init__(self, universo):
        self.universo = universo

        self.source = None
        self.target = None
        self.ativo = False
        self.raio_pulso = 220

        self.visitados = set()
        self.pais = {}
        self.abertos = []
        self.ativos = set()
        self.proximos = set()
        self.fila = []
        self.energia_anteriores = {}
        self.custo = {}

        # Para calcular recompensa ao final
        self._hops_solucao: int | None = None
        self._hops_minimo_conhecido: int | None = None

    def handle(self, comando):

        if comando.startswith("flow source"):
            self.source = int(comando.split()[2])
            return [f"Source set to {self.source}"]

        if comando.startswith("flow target"):
            self.target = int(comando.split()[2])
            return [f"Target set to {self.target}"]

        if comando.startswith("flow range"):
            try:
                self.raio_pulso = float(comando.split()[2])
                return [f"Pulse range set to {self.raio_pulso}"]
            except (ValueError, IndexError):
                return ["Invalid range value"]

        if comando == "flow start":
            if self.source is None or self.target is None:
                return ["Source or target not defined"]

            self.energia_anteriores = {d["id"]: d["energia"] for d in self.universo.dados}
            self.custo = {self.source: 0}
            self.visitados = {self.source}
            self.ativos = {self.source}
            self.proximos = set()
            self.pais = {}
            self.abertos = [self.source]
            self.fila = [(self.source, 0)]
            self._hops_solucao = None

            return ["Flow problem initialized"]

        if comando == "flow run":
            if self.source is None or self.target is None:
                return ["Source or target not defined"]
            self.ativo = True
            return ["Flow simulation running"]

        if comando == "flow result":
            caminho = []
            atual = self.target
            while atual in self.pais:
                caminho.append(atual)
                atual = self.pais[atual]
            caminho.append(self.source)
            caminho.reverse()

            hops = len(caminho) - 1
            distancia_total = 0
            for i in range(len(caminho) - 1):
                d1 = next((d for d in self.universo.dados if d["id"] == caminho[i]), None)
                d2 = next((d for d in self.universo.dados if d["id"] == caminho[i + 1]), None)
                if d1 is None or d2 is None:
                    continue
                dx = d1["pos"][0] - d2["pos"][0]
                dy = d1["pos"][1] - d2["pos"][1]
                distancia_total += (dx ** 2 + dy ** 2) ** 0.5

            return [
                "FLOW RESULT", "",
                f"path: {' -> '.join(map(str, caminho))}",
                f"hops: {hops}",
                f"distance: {round(distancia_total, 2)}"
            ]

        if comando == "flow stop":
            self.ativo = False
            return ["Flow simulation stopped"]

        return None

    def _escolher_proximo(self, atual_id, candidatos, target):
        """
        A mente decide qual candidato escolher no próximo hop.
        Combina o score da mente com a heurística A*.
        """
        if not candidatos:
            return None

        atual = next((d for d in self.universo.dados if d["id"] == atual_id), None)
        if atual is None:
            return None

        melhor = None
        melhor_score = -float("inf")

        for outro in candidatos:
            dx = atual["pos"][0] - outro["pos"][0]
            dy = atual["pos"][1] - outro["pos"][1]
            distancia = (dx ** 2 + dy ** 2) ** 0.5

            dist_target = self.distancia_ate_target(outro["id"], target)
            custo_novo  = self.custo.get(atual_id, float("inf")) + distancia

            # ── Score da mente ────────────────────────────────────────────
            # Entrada: energia do atual, energia do candidato, distância,
            # distância ao target normalizada
            score_mente = self.universo.forward(
                atual,
                outro["energia"],
                distancia
            )

            # Heurística A* normalizada (menor = melhor, então invertemos)
            score_astar = -(custo_novo + dist_target) / 1000.0

            # Combina: 50% mente, 50% A*
            score_final = score_mente * 0.5 + score_astar * 0.5

            if score_final > melhor_score:
                melhor_score = score_final
                melhor = outro
                melhor_custo = custo_novo
                melhor_dist_target = dist_target

        if melhor:
            self.custo[melhor["id"]] = melhor_custo

        return melhor

    def _recompensar_caminho(self, hops_atual):
        """
        Recompensa a mente com base na qualidade do caminho encontrado.
        Menor número de hops = recompensa maior.
        """
        if self._hops_minimo_conhecido is None:
            self._hops_minimo_conhecido = hops_atual
            recompensa = 0.5   # primeiro caminho sempre recebe recompensa moderada
        elif hops_atual < self._hops_minimo_conhecido:
            recompensa = 1.0   # melhorou o recorde
            self._hops_minimo_conhecido = hops_atual
        elif hops_atual == self._hops_minimo_conhecido:
            recompensa = 0.3   # igualou
        else:
            recompensa = -0.5  # piorou

        # Aplica recompensa a todos os agentes do caminho
        atual = self.target
        while atual in self.pais:
            dado = next((d for d in self.universo.dados if d["id"] == atual), None)
            if dado:
                self.universo.aprender(dado, recompensa)
            atual = self.pais[atual]

    def update(self):
        if not self.ativo:
            return

        dados = self.universo.dados
        target = next((d for d in dados if d["id"] == self.target), None)

        # ===== PASSO 1: primeiro hop do source =====
        if not self.pais:
            origem = next((d for d in dados if d["id"] == self.source), None)
            if origem is None or target is None:
                return

            dist_atual = self.distancia_ate_target(self.source, target)

            candidatos = [
                outro for outro in dados
                if outro["id"] != self.source
                and ((origem["pos"][0] - outro["pos"][0]) ** 2 +
                     (origem["pos"][1] - outro["pos"][1]) ** 2) ** 0.5 <= self.raio_pulso
                and self.distancia_ate_target(outro["id"], target) < dist_atual
            ]

            melhor = self._escolher_proximo(self.source, candidatos, target)

            if melhor:
                self.universo.enviar_pulso(self.source, melhor["id"], 0.1)
                self.pais[melhor["id"]] = self.source

            return

        # ===== PASSO 2: detectar quem recebeu energia =====
        novos_ativos = []
        for d in dados:
            energia_anterior = self.energia_anteriores.get(d["id"], d["energia"])
            if d["energia"] > energia_anterior + 0.05 and d["id"] not in self.visitados:
                novos_ativos.append(d["id"])
                self.visitados.add(d["id"])

        for d in dados:
            self.energia_anteriores[d["id"]] = d["energia"]

        # ===== PASSO 3: propagação com mente ====
        for atual_id in novos_ativos:
            atual = next((x for x in dados if x["id"] == atual_id), None)
            if atual is None:
                continue

            dist_atual = self.distancia_ate_target(atual_id, target)

            candidatos = [
                outro for outro in dados
                if outro["id"] not in self.visitados
                and ((atual["pos"][0] - outro["pos"][0]) ** 2 +
                     (atual["pos"][1] - outro["pos"][1]) ** 2) ** 0.5 <= self.raio_pulso
                and self.distancia_ate_target(outro["id"], target) < dist_atual
            ]

            melhor = self._escolher_proximo(atual_id, candidatos, target)

            if melhor:
                self.universo.enviar_pulso(atual_id, melhor["id"], 0.1)
                self.pais[melhor["id"]] = atual_id

                if melhor["id"] == self.target:
                    self.ativo = False

                    # Calcula hops do caminho encontrado
                    hops = 0
                    node = self.target
                    while node in self.pais:
                        hops += 1
                        node = self.pais[node]

                    self._hops_solucao = hops
                    self._recompensar_caminho(hops)

                    self.universo.resultados_terminal.append(
                        f"[FLOW] path found | hops={hops}"
                    )
                    return

    def distancia_ate_target(self, id_dado, target):
        if target is None:
            return float("inf")
        dado = next((d for d in self.universo.dados if d["id"] == id_dado), None)
        if dado is None:
            return float("inf")
        dx = dado["pos"][0] - target["pos"][0]
        dy = dado["pos"][1] - target["pos"][1]
        return (dx ** 2 + dy ** 2) ** 0.5