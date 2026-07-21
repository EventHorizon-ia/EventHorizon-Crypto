# engine.py
import json
import os
import random
import time
import uuid
import math
import statistics
import torch
from Software.core.mind import BancoMentes




def consumo_por_tick(dado):
    base    = 0.000002
    dinamico = 0.0000005 * dado["energia"]
    fase, tensao, coerencia = dado["estado"]
    fator_estado = 1 + 0.3 * tensao + 0.2 * (1 - coerencia) + 0.1 * abs(math.sin(fase))
    return (base + dinamico) * fator_estado


def eficiencia(dado):
    consumo = consumo_por_tick(dado)
    if consumo <= 0:
        return float("inf")
    return dado["energia"] / consumo


def perda_universo(dado, outro, energia):
    perda_dado  = consumo_por_tick(dado)
    perda_outro = consumo_por_tick(outro)
    dissipacao_pulso = energia * 0.02
    return perda_dado + perda_outro + dissipacao_pulso


def custo_futuro(dado):
    horizonte = 10 + dado["energia"] * 5
    consumo   = consumo_por_tick(dado)
    return consumo * horizonte


class Universo:
    def __init__(self, caminho="data/universe.json"):
        self.caminho        = caminho
        self.caminho_mortos = "data/dados_mortos.json"
        self.dados          = []
        self.apps           = []
        self.dados_mortos   = []
        self.mortes_pendentes = 0
        self.simulation_time  = 0.0
        self.start_real_time  = time.time()
        self.stats_history    = []
        self.stats_interval   = 1.0
        self._last_stats_time = time.time()
        
        self.pulsos           = []
        self.clusters         = {}
        self.historico_pulsos = []
        self.resultados_terminal = []
        self.memoria_global   = {
            "energia_total":   0.0,
            "energia_anterior": 0.0,
            "delta_energia":   0.0,
            "entropia":        0.0,
        }

        # ── Mente persistente (não reseta com o universo) ─────────────────────
        self.mentes = BancoMentes()
        self.ultimo_id        = self.mentes.gerar_novo_id()
        self.carregar()
        self.carregar_mortos()

    # ── Consciência global ────────────────────────────────────────────────────
    def atualizar_consciencia_global(self):
        energia_atual = self.energia_total()
        self.memoria_global["energia_anterior"] = self.memoria_global["energia_total"]
        self.memoria_global["energia_total"]    = energia_atual
        self.memoria_global["delta_energia"]    = energia_atual - self.memoria_global["energia_anterior"]

        if self.dados:
            media    = energia_atual / len(self.dados)
            variancia = sum((d["energia"] - media) ** 2 for d in self.dados) / len(self.dados)
            self.memoria_global["entropia"] = variancia

    # ── Criar dado (corpo apenas, sem rede) ───────────────────────────────────
   

    def criar_dado(self, tipo="padrão", pos=None, config=None):
        config = config or {}
        self.ultimo_id += 1

        energia_base = 8
        if tipo == "padrão":
            energia = energia_base + random.uniform(-2, 2)
        elif tipo == "energetico":
            energia = energia_base + random.uniform(3, 6)
        elif tipo == "fraco":
            energia = energia_base + random.uniform(-5, -1)
        else:
            energia = energia_base

        fator_tempo = random.uniform(0.8, 1.2)
        fase        = random.uniform(0, 2 * math.pi)
        tensao      = random.uniform(0, 0.1)
        coerencia   = random.uniform(0.4, 0.8)

        energia     = config.get("energy",      energia)
        fator_tempo = config.get("time_factor", fator_tempo)
        fase        = config.get("phase",       fase)
        tensao      = config.get("tension",     tensao)
        coerencia   = config.get("coherence",   coerencia)

        if pos is None:
            cluster_centro = [random.randint(200, 400), random.randint(150, 350)]
            if random.random() < 0.3:
                pos = [
                    cluster_centro[0] + random.randint(-30, 30),
                    cluster_centro[1] + random.randint(-30, 30),
                ]
            else:
                pos = [random.randint(10, 1280), random.randint(10, 720)]
        else:
            pos = [float(pos[0]), float(pos[1])]

        dado = {
            "id":           self.ultimo_id,
            "pos":          pos,
            "energia":      energia,
            "tempo_proprio": 0,
            "fator_tempo":  fator_tempo,
            "memoria":      [],
            "cooldown":     0.0,
            "pixels":       0, # antes era pygame
            "dado_t":       random.uniform(0, 1000),
            "bits":         [1, 1, 1],
            "estado":       [fase, tensao, coerencia],
            "previsao":     0.0,
            # ← "rede" removida daqui — vive em BancoMentes
            "ultima_energia": energia,
            "dna": {
                "agressiveness": config.get("agressiveness", random.uniform(0, 1)),
                "cooperation":   config.get("cooperation",   random.uniform(0, 1)),
                "exploration":   config.get("exploration",   random.uniform(0, 1)),
            },
        }

        # Garante que a mente existe para este ID
        self.mentes.obter(dado["id"])
        self.mentes.salvar()

        self.dados.append(dado)
        self.salvar()
        return dado

    # ── Forward (delega para a Mente) ─────────────────────────────────────────
    def forward_multi(self, dado, energia_outro, distancia):
        """Retorna a lista completa de previsões por horizonte"""
        memoria_score = self.score_memoria(dado)

        entrada = [
            dado["energia"],
            energia_outro,
            distancia / 200,
            self.memoria_global["delta_energia"],
            memoria_score,
        ]

        mente = self.mentes.obter(dado["id"])
        return mente.forward(entrada)  # Retorna lista [5s, 15s, 30s, 60s]

    def forward(self, dado, energia_outro, distancia):
        """Compatibilidade: retorna apenas o primeiro horizonte (5s)"""
        saida_multi = self.forward_multi(dado, energia_outro, distancia)
        return saida_multi[0] if saida_multi else 0.0

    # ── Aprender (delega para a Mente) ────────────────────────────────────────
    def aprender(self, dado, recompensa):
        """Aprendizado do universo (compatível com PyTorch e clássico)"""
        mente = self.mentes.obter(dado["id"])
        
        # ⭐ Verifica se é uma mente PyTorch INSANA
        if hasattr(mente, 'cabecas'):  # Mente INSANA tem o atributo 'cabecas'
            # Converte recompensa para lista de 4 valores
            if isinstance(recompensa, (int, float)):
                recompensas = [recompensa / 5.0] * 4
            elif isinstance(recompensa, torch.Tensor):
                if recompensa.numel() == 0:
                    return
                # Se for tensor, pega o valor escalar
                valor = recompensa.item() if recompensa.numel() == 1 else recompensa.mean().item()
                recompensas = [valor / 5.0] * 4
            else:
                # Se já for lista, usa direto (mas deve ter 4 elementos)
                recompensas = recompensa if len(recompensa) == 4 else [0.0] * 4
            mente.aprender(recompensas)
        else:
            # Mente clássica (não PyTorch)
            mente.aprender(recompensa)

    # ── Persistência ──────────────────────────────────────────────────────────
    def salvar(self):
        os.makedirs("data", exist_ok=True)
        temp_path = self.caminho + ".tmp"
        with open(temp_path, "w") as f:
            json.dump({"ultimo_id": self.ultimo_id, "dados": self.dados}, f, indent=4)
        os.replace(temp_path, self.caminho)

        # Salva mentes junto (mas em arquivo separado)
        self.mentes.salvar()

    def salvar_leve(self):
        """Salva apenas dados do universo (rápido) - SEM modelos .pt"""
        os.makedirs("data", exist_ok=True)
        temp_path = self.caminho + ".tmp"
        with open(temp_path, "w") as f:
            json.dump({"ultimo_id": self.ultimo_id, "dados": self.dados}, f, indent=4)
        os.replace(temp_path, self.caminho)
        # ⭐ NÃO chama self.mentes.salvar()

    

    def carregar(self):
        if os.path.exists(self.caminho):
            try:
                with open(self.caminho, "r") as f:
                    universo_salvo = json.load(f)
                self.dados     = universo_salvo.get("dados", [])
                self.ultimo_id = universo_salvo.get("ultimo_id", 0)

                # Remove campo "rede" de dados antigos (migração)
                for d in self.dados:
                    d.pop("rede", None)
                    if "ultima_entrada" not in d:
                        d["ultima_entrada"] = None
                    if "ultima_acao" not in d:
                        d["ultima_acao"] = 0.0

            except Exception as e:
                print("[ERRO] Falha ao carregar universo:", e)
                os.rename(self.caminho, self.caminho + ".corrompido")
                self.dados     = []
                self.ultimo_id = 0

        # Sincronização SIMPLES: se as mentes têm IDs maiores, atualiza ultimo_id
        if self.mentes.mentes:
            id_max_mente = max(self.mentes.mentes.keys())
            if self.ultimo_id < id_max_mente:
                self.ultimo_id = id_max_mente
                print(f"[Engine] ultimo_id atualizado para {self.ultimo_id} (baseado nas mentes)")
                # Salva para persistir a correção
                self.salvar()

    def salvar_mortos(self):
        os.makedirs("data", exist_ok=True)
        with open(self.caminho_mortos, "w") as f:
            json.dump(self.dados_mortos, f, indent=4)

    def carregar_mortos(self):
        if os.path.exists(self.caminho_mortos):
            with open(self.caminho_mortos, "r") as f:
                self.dados_mortos = json.load(f)

    def finalizar(self):
        self.salvar()
        self.salvar_mortos()

    # ── Pulsos ────────────────────────────────────────────────────────────────
    def enviar_pulso(self, id_origem, id_destino, energia=0.2, resultado_terminal=None):
        origem  = next((d for d in self.dados if d["id"] == id_origem),  None)
        destino = next((d for d in self.dados if d["id"] == id_destino), None)

        if self.existe_pulso(id_origem, id_destino):
            return False
        if origem is None or destino is None:
            return False
        if origem["energia"] < energia:
            return False
        if "memoria" not in origem:
            origem["memoria"] = []

        if resultado_terminal is not None:
            destino_viavel = self.escolher_destino_viavel(origem, 1.5)
            if destino_viavel is None:
                return False
            destino = destino_viavel

        pulso_id = str(uuid.uuid4())
        origem["memoria"].append({
            "acao":     "enviou pulso",
            "destino":  destino["id"],
            "energia":  energia,
            "pulso_id": pulso_id,
        })
        origem["energia"] -= energia

        dx = destino["pos"][0] - origem["pos"][0]
        dy = destino["pos"][1] - origem["pos"][1]
        distancia = (dx * dx + dy * dy) ** 0.5

        pulso = {
            "id":                 pulso_id,
            "origem":             id_origem,
            "destino":            id_destino,
            "energia":            energia,
            "progresso":          0.0,
            "pos_origem":         origem["pos"][:],
            "pos_destino":        destino["pos"][:],
            "pos":                origem["pos"][:],
            "distancia":          max(distancia, 1),
            "velocidade":         1.5,
            "resultado_terminal": resultado_terminal,
            "expressao":          None,
        }
        self.pulsos.append(pulso)
        self.historico_pulsos.append({
            "origem":  id_origem,
            "destino": id_destino,
            "energia": energia,
            "tempo":   self.simulation_time,
        })
        if len(self.historico_pulsos) > 300:
            self.historico_pulsos.pop(0)
        return True

    def evoluir_pulsos(self, escala):
        for pulso in self.pulsos[:]:
            origem  = next((d for d in self.dados if d["id"] == pulso["origem"]),  None)
            destino = next((d for d in self.dados if d["id"] == pulso["destino"]), None)

            if origem is None or destino is None:
                self.pulsos.remove(pulso)
                continue

            velocidade = min(pulso["velocidade"], 2.0)
            if pulso["distancia"] > 0:
                pulso["progresso"] += (velocidade * escala * origem["fator_tempo"]) / pulso["distancia"]

            if pulso["progresso"] >= 1.0:
                if pulso.get("expressao"):
                    try:
                        resultado = eval(pulso["expressao"])
                        self.resultados_terminal.append(f"{pulso['expressao']} = {resultado}")
                    except:
                        self.resultados_terminal.append("Error computing expression")
                elif pulso.get("resultado_terminal"):
                    self.resultados_terminal.append(pulso["resultado_terminal"])

                impacto        = pulso["energia"] - consumo_por_tick(destino)
                impacto_global = impacto + 0.2 * self.memoria_global["delta_energia"]
                # Dentro de evoluir_pulsos, quando chama self.aprender(origem, impacto_global)
                if isinstance(impacto_global, torch.Tensor) and impacto_global.numel() == 0:
                    continue  # ignora aprendizado com tensor vazio
                self.aprender(origem, impacto_global)
                

                destino["energia"] += pulso["energia"]
                destino["estado"][0] += pulso["energia"] * 0.05
                destino["estado"][1] += pulso["energia"]

                impacto        = pulso["energia"] - consumo_por_tick(destino)
                impacto_global = impacto + self.memoria_global["delta_energia"]
                origem = next(d for d in self.dados if d["id"] == pulso["origem"])
                origem["memoria"].append({
                    "tipo":           "feedback",
                    "impacto_local":  impacto,
                    "impacto_global": impacto_global,
                })

                self.pulsos.remove(pulso)
                continue

            ox, oy = pulso["pos_origem"]
            dx, dy = pulso["pos_destino"]
            pulso["distancia"] = ((dx - ox) ** 2 + (dy - oy) ** 2) ** 0.5
            pulso["velocidade"] = 1
            pulso["energia"]   *= 0.999
            t = pulso["progresso"]
            pulso["pos"][0] = ox + (dx - ox) * t
            pulso["pos"][1] = oy + (dy - oy) * t

    def existe_pulso(self, origem, destino):
        return any(p["origem"] == origem and p["destino"] == destino for p in self.pulsos)

    def listar_pulsos(self):
        return [{"origem": p["origem"], "destino": p["destino"], "energia": p["energia"]} for p in self.pulsos]

    # ── Energia ───────────────────────────────────────────────────────────────
    def energia_dados(self):   return sum(d["energia"] for d in self.dados)
    def energia_pulsos(self):  return sum(p["energia"] for p in self.pulsos)
    def energia_total(self):   return self.energia_dados() + self.energia_pulsos()
    def fluxo_total(self):     return sum(abs(p["energia"]) for p in self.pulsos)

    def status_universo(self):
        return {"dados": len(self.dados), "pulsos": len(self.pulsos), "energia_total": self.energia_total()}

    # ── Física ────────────────────────────────────────────────────────────────
    def aplicar_consumo(self, dado, escala):
        consumo = consumo_por_tick(dado)
        dado["energia"] -= consumo * escala * dado["fator_tempo"]
        dado["energia"]  = max(0, dado["energia"])

    def aplicar_relatividade(self, dado, escala):
        fase, tensao, coerencia = dado["estado"]
        dado["fator_tempo"]   = 1 / (1 + 0.1 * dado["energia"] * (1 + 0.5 * (1 - coerencia)) + 0.05 * abs(math.sin(fase)))
        dado["tempo_proprio"] += escala * dado["fator_tempo"]

    def atualizar_estado(self, dado, escala):
        fase, tensao, coerencia = dado["estado"]
        fase     += escala * dado["fator_tempo"]
        tensao   += 0.001 * dado["energia"]
        coerencia *= 0.999
        dado["estado"] = [fase, tensao, coerencia]

    def atualizar_bits(self, dado):
        ritmo = dado["fator_tempo"]
        dado["bits"][0] = 1 if ritmo < 0.5  else 0
        dado["bits"][1] = 1 if 0.5 <= ritmo < 0.8 else 0
        dado["bits"][2] = 1 if ritmo >= 0.8 else 0

    def pode_transferir(self, origem, destino, energia):
        b0, b1, b2 = origem["bits"]
        if b0 == 0: return False
        if b1 == 0: return False
        if b2 == 0 and origem["energia"] - energia < 2.0: return False
        if origem["energia"] - energia <= 0: return False
        return True

    # ── Interações ────────────────────────────────────────────────────────────
    def decidir_interacoes(self, dado):
        dna = dado.get("dna", {})
        if dado["energia"] < 0.5:
            return

        for outro in self.dados:
            if outro is dado:
                continue

            dx = dado["pos"][0] - outro["pos"][0]
            dy = dado["pos"][1] - outro["pos"][1]
            distancia = (dx * dx + dy * dy) ** 0.5
            if distancia > 120:
                continue

            sync = self.sincronizacao(dado, outro)
            if sync < 0.2:
                continue

            aggressiveness = dna.get("aggressiveness", 0.5)
            cooperation    = dna.get("cooperation",    0.5)

            saida         = self.forward(dado, outro["energia"], distancia)
            memoria_score = self.score_memoria(dado)

            saida_final = (
                saida
                + 0.5 * memoria_score
                + 0.4 * aggressiveness
                + 0.3 * cooperation * sync
            )
            if saida_final <= 0:
                continue

            fator_dna = 0.5 + aggressiveness * 0.7 + cooperation * sync
            energia   = min(min(dado["energia"] * fator_dna, saida_final * 0.5), dado["energia"])
            if energia <= 0:
                continue

            self.enviar_pulso(dado["id"], outro["id"], energia)

            for cluster in self.detectar_clusters():
                if sum(d["energia"] for d in cluster) > 30:
                    for d in cluster:
                        d["estado"][1] += 0.01

            break  # um por tick

    # ── Morte ─────────────────────────────────────────────────────────────────
    def matar_dado(self, dado):
        dado["_morrer"] = True

    def processar_mortes(self):
        novos_dados = []
        for dado in self.dados:
            if dado.get("_morrer"):
                self.dados_mortos.append({
                    "id":         dado["id"],
                    "estado":     dado["estado"],
                    "tempo_vida": dado["tempo_proprio"],
                })
                # Notifica a mente que o corpo morreu (incrementa geração)
                self.mentes.notificar_morte(dado["id"])
                dado["pixels"]  = None
                dado["memoria"] = None
            else:
                novos_dados.append(dado)
        self.dados = novos_dados

    # ── Sincronização ─────────────────────────────────────────────────────────
    def sincronizacao(self, d1, d2):
        fase1, _, coerencia1 = d1["estado"]
        fase2, _, coerencia2 = d2["estado"]
        diff = abs(fase1 - fase2)
        if diff > math.pi:
            diff = 2 * math.pi - diff
        alinhamento = 1 - (diff / math.pi)
        estabilidade = (coerencia1 + coerencia2) / 2
        return alinhamento * estabilidade

    # ── Clusters & loops ──────────────────────────────────────────────────────
    def detectar_clusters(self):
        clusters  = []
        visitados = set()
        for d in self.dados:
            if d["id"] in visitados:
                continue
            grupo = [d]
            for outro in self.dados:
                if outro is d:
                    continue
                dx = d["pos"][0] - outro["pos"][0]
                dy = d["pos"][1] - outro["pos"][1]
                if (dx * dx + dy * dy) ** 0.5 < 80:
                    grupo.append(outro)
            if len(grupo) > 3:
                for g in grupo:
                    visitados.add(g["id"])
                clusters.append(grupo)
        return clusters

    def detectar_loops_energia(self):
        loops = []
        for p1 in self.historico_pulsos:
            for p2 in self.historico_pulsos:
                if p1["destino"] == p2["origem"]:
                    for p3 in self.historico_pulsos:
                        if p2["destino"] == p3["origem"] and p3["destino"] == p1["origem"]:
                            loop = (p1["origem"], p2["origem"], p3["origem"])
                            if loop not in loops:
                                loops.append(loop)
        return loops

    def estabilizar_loops(self):
        for loop in self.detectar_loops_energia():
            chave = tuple(sorted(loop))
            self.clusters[chave] = self.clusters.get(chave, 0) + 1
            if self.clusters[chave] > 10:
                for dado in self.dados:
                    if dado["id"] in loop:
                        dado["estado"][2] = min(1.0, dado["estado"][2] + 0.01)

    # ── Equilíbrio & solução ──────────────────────────────────────────────────
    def medir_equilibrio(self):
        if len(self.dados) < 2:
            return None
        energias = [d["energia"] for d in self.dados]
        media  = statistics.mean(energias)
        desvio = statistics.pstdev(energias)
        return {"media": media, "desvio": desvio, "min": min(energias), "max": max(energias)}

    def ler_solucao(self):
        clusters = self.detectar_clusters()
        if not clusters:
            return None
        maior    = max(clusters, key=lambda c: sum(d["energia"] for d in c))
        energia  = sum(d["energia"] for d in maior)
        coerencia = statistics.mean(d["estado"][2] for d in maior)
        return {"tamanho": len(maior), "energia": energia, "coerencia": coerencia}

    # ── Sobrevivência ─────────────────────────────────────────────────────────
    def sobrevivera_ate(self, dado, tempo):
        return dado["energia"] - consumo_por_tick(dado) * tempo > 0

    def tempo_de_viagem(self, origem, destino, velocidade):
        dx = destino["pos"][0] - origem["pos"][0]
        dy = destino["pos"][1] - origem["pos"][1]
        return ((dx ** 2 + dy ** 2) ** 0.5) / max(velocidade, 0.0001)

    def escolher_destino_viavel(self, origem, velocidade):
        candidatos = [
            (self.tempo_de_viagem(origem, d, velocidade), d)
            for d in self.dados
            if d["id"] != origem["id"] and self.sobrevivera_ate(d, self.tempo_de_viagem(origem, d, velocidade))
        ]
        return min(candidatos, key=lambda x: x[0])[1] if candidatos else None

    # ── Memória ───────────────────────────────────────────────────────────────
    def score_memoria(self, dado):
        if not dado.get("memoria"):
            return 0.0
        impactos = [m.get("impacto_local", 0) for m in dado["memoria"] if m.get("tipo") == "feedback"]
        if not impactos:
            return 0.0
        return max(-1.0, min(1.0, sum(impactos) / len(impactos)))

    # ── Delta sobrevivência ───────────────────────────────────────────────────
    def delta_sobrevivencia(self, dado, outro, energia, pos="None"):
        custo_antes = custo_futuro(dado) + custo_futuro(outro)
        if dado["energia"] - energia <= 0:
            return -float("inf")
        custo_depois = (
            custo_futuro({**dado,  "energia": dado["energia"]  - energia}) +
            custo_futuro({**outro, "energia": outro["energia"] + energia})
        )
        return custo_antes - custo_depois - energia * 0.02

    # ── Stats & telemetria ────────────────────────────────────────────────────
    def collect_stats(self):
        if not self.dados:
            return
        tempos = [d["tempo_proprio"] for d in self.dados]
        self.stats_history.append({
            "simulation_time": self.simulation_time,
            "energia_total":   self.energia_total(),
            "num_dados":       len(self.dados),
            "media_tau":       statistics.mean(tempos),
            "desvio_tau":      statistics.pstdev(tempos) if len(tempos) > 1 else 0,
            "num_pulsos":      len(self.pulsos),
        })

    def obter_telemetria(self):
        tamanho_kb = os.path.getsize(self.caminho) / 1024 if os.path.exists(self.caminho) else 0
        return {
            "name":         os.path.basename(self.caminho),
            "size":         f"{tamanho_kb:.2f} KB",
            "living_units": len(self.dados),
            "dead_units":   len(self.dados_mortos),
            "total_energy": self.energia_total(),
            "minds":        self.mentes.stats(),
        }

    def calcular_acao_global(self):
        S = (
            0.05 * self.energia_total()
            + 0.5  * self.memoria_global["entropia"]
            + 0.2  * self.memoria_global["delta_energia"]
            - 0.05 * self.fluxo_total()
        )
        return S

    def calcular_acao_local(self, dado):
        entradas = [
            dado["energia"],
            abs(dado["energia"] - statistics.mean(d["energia"] for d in self.dados)),
            self.memoria_global["delta_energia"],
            self.fluxo_total(),
        ]
        mente = self.mentes.obter(dado["id"])
        while len(mente.pesos) < len(entradas):
            mente.pesos.append(random.uniform(-1, 1))
        return sum(e * w for e, w in zip(entradas, mente.pesos))

    def apps_ativos(self):
        return any(
            app.nome in ["flow_app", "balance_app", "crypto_app"] and getattr(app, "ativo", False)
            for app in self.apps
        )
    
    

    

    def reset_universo(self, manter_aprendizado=True):
        """
        Reseta o universo (dados, pulsos, estatísticas).
        
        Args:
            manter_aprendizado: Se True, as mentes sobrevivem e novos dados
                            receberão IDs sequenciais a partir do último ID usado.
                            Se False, reseta tudo (dados e mentes).
        """
        # Salva estado atual por segurança
        self.salvar()
        
        # Limpa dados do universo (mas NÃO as mentes)
        self.dados = []
        self.pulsos = []
        self.historico_pulsos = []
        self.resultados_terminal = []
        self.mortes_pendentes = 0
        self.simulation_time = 0.0
        self.start_real_time = time.time()
        self.stats_history = []
        self._last_stats_time = time.time()
        
        # Reseta memória global
        self.memoria_global = {
            "energia_total":   0.0,
            "energia_anterior": 0.0,
            "delta_energia":   0.0,
            "entropia":        0.0,
        }
        
        if manter_aprendizado:
            # Mantém as mentes e o contador de ID onde está
            # O ultimo_id já está correto porque as mentes têm IDs maiores
            if self.mentes.mentes:
                id_max_mente = max(self.mentes.mentes.keys())
                if self.ultimo_id < id_max_mente:
                    self.ultimo_id = id_max_mente
                    print(f"[Universo] Reset mantendo mentes. Próximo ID será: {self.ultimo_id + 1}")
            else:
                # Se não tem mentes, mantém o ID atual
                print(f"[Universo] Reset mantendo estado. Próximo ID: {self.ultimo_id + 1}")
        
        # Salva o universo vazio
        self.salvar()


    def remover_dados_por_ids(self, ids_para_remover):
        """Remove dados por IDs - método direto"""
        print(f"[Engine] 🔴 Tentando remover IDs: {ids_para_remover}")
        print(f"[Engine] 📊 Dados antes: {len(self.dados)}")
        
        novos_dados = []
        for dado in self.dados:
            if dado["id"] not in ids_para_remover:
                novos_dados.append(dado)
            else:
                print(f"[Engine] 🗑️ Removendo dado ID {dado['id']} - {dado.get('symbol', 'unknown')}")
        
        self.dados = novos_dados
        self.salvar()
        
        print(f"[Engine] 📊 Dados depois: {len(self.dados)}")
        
        return len(ids_para_remover)