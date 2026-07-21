# mind.py - VERSÃO CORRIGIDA (sem bloqueio no startup)

import json
import os
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor

MODO_IA = os.getenv("MODO_IA", "pytorch")

if MODO_IA == "pytorch":
    CAMINHO_MENTE = "data/minds.json"
    from Software.core.mind_pytorch import MenteTorch as MenteAgente
    print("🤖 PyTorch ACTIVATED - Rede Neural Profunda")
else:
    CAMINHO_MENTE = "data/minds_linear.json"
    from Software.core.mind_linear import MenteAgenteLinear as MenteAgente
    print("📊 Modo Linear - IA Clássica")


class BancoMentes:
    """
    Gerencia todas as mentes persistentes.

    Mudanças em relação à versão anterior
    ──────────────────────────────────────
    • carregar()  → lê apenas o minds.json (metadados leves).
                    NÃO faz torch.load no startup.
    • obter()     → cria a MenteTorch em background se ainda não existir.
                    Retorna None enquanto carrega (caller usa fallback).
    • salvar()    → dispara torch.save em background, nunca bloqueia o loop.
    """

    def __init__(self, caminho: str = None):
        self.caminho = caminho or CAMINHO_MENTE
        self.mentes: dict[int, MenteAgente] = {}

        # mentes que ainda estão sendo carregadas em background
        self._carregando: set[int] = set()
        self._lock = threading.Lock()

        self.ultimo_id_global = 0

        # executor compartilhado: 2 workers evitam saturar o disco
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mente_io")

        self.carregar()

    # ─────────────────────────────────────────────────────────────────────
    # CARREGAR — só metadados, sem torch.load
    # ─────────────────────────────────────────────────────────────────────

    def carregar(self):
        """
        Lê o minds.json e restaura apenas estatísticas leves (acertos,
        erros, geração, pesos lineares).  O torch.load() de cada mente
        PyTorch acontece de forma lazy em background quando obter() é
        chamado pela primeira vez.
        """
        if not os.path.exists(self.caminho):
            return

        try:
            with open(self.caminho, "r") as f:
                dados = json.load(f)

            self.ultimo_id_global = dados.get("ultimo_id_global", 0)

            with self._lock:
                self.mentes = {}
                for id_str, m_data in dados.get("mentes", {}).items():
                    id_ = int(id_str)
                    mente = MenteAgente(id_)           # só aloca a rede em RAM

                    # Estatísticas leves — sempre presentes no JSON
                    raw_acertos = m_data.get("n_acertos", 0)
                    raw_erros   = m_data.get("n_erros",   0)

                    # PyTorch usa lista por horizonte; linear usa int
                    if isinstance(raw_acertos, list):
                        mente.n_acertos = raw_acertos
                        mente.n_erros   = raw_erros
                    else:
                        mente.n_acertos = raw_acertos
                        mente.n_erros   = raw_erros

                    mente.geracao = m_data.get("geracao", 0)

                    # Pesos lineares (só existem no modo linear)
                    if "pesos" in m_data:
                        mente.pesos = m_data["pesos"]
                        mente.bias  = m_data.get("bias", 0)

                    self.mentes[id_] = mente

        except Exception as e:
            print(f"[Mente] Erro ao carregar mentes: {e}")
            with self._lock:
                self.mentes = {}

    # ─────────────────────────────────────────────────────────────────────
    # OBTER — lazy + background torch.load
    # ─────────────────────────────────────────────────────────────────────

    def obter(self, id_agente: int) -> MenteAgente | None:
        """
        Retorna a mente se já estiver pronta.
        Se ainda não existe OU ainda está carregando → dispara init em
        background e retorna None (caller usa fallback clássico).
        """
        with self._lock:
            mente = self.mentes.get(id_agente)
            em_carregamento = id_agente in self._carregando

        if mente is not None:
            # Já existe em RAM — verifica se o .pt foi carregado
            if getattr(mente, '_pt_carregado', False):
                return mente          # pronta para uso
            # Ainda não fez torch.load — agenda se ainda não agendou
            with self._lock:
                if id_agente not in self._carregando:
                    self._carregando.add(id_agente)
                    self._executor.submit(self._carregar_pt_background, id_agente, mente)
            return None               # fallback por enquanto

        if em_carregamento:
            return None               # já está na fila, aguarda

        # Mente nova (nunca vista) — cria e agenda carga
        nova_mente = MenteAgente(id_agente)
        with self._lock:
            self.mentes[id_agente] = nova_mente
            self._carregando.add(id_agente)
        self._executor.submit(self._carregar_pt_background, id_agente, nova_mente)
        return None

    def obter_ou_criar_sincrono(self, id_agente: int) -> MenteAgente:
        """
        Versão síncrona para quando você PRECISA da mente agora
        (ex: relatório, stats, debugging). Evitar no loop principal.
        """
        with self._lock:
            mente = self.mentes.get(id_agente)

        if mente is None:
            mente = MenteAgente(id_agente)
            with self._lock:
                self.mentes[id_agente] = mente

        if not getattr(mente, '_pt_carregado', False) and hasattr(mente, 'carregar'):
            try:
                mente.carregar()
                mente._pt_carregado = True
            except Exception as e:
                print(f"[Mente] Erro ao carregar sincrono {id_agente}: {e}")
                mente._pt_carregado = False

        return mente

    def _carregar_pt_background(self, id_agente: int, mente: MenteAgente):
        """Executa torch.load em thread separada — nunca bloqueia o loop."""
        try:
            if hasattr(mente, 'carregar'):
                ok = mente.carregar()
                mente._pt_carregado = True
                status = "✅" if ok else "⚠️ (arquivo não encontrado)"
            else:
                mente._pt_carregado = True
                status = "✅ (linear)"
            print(f"[Mente] {status} Mente {id_agente} pronta em background")
        except Exception as e:
            mente._pt_carregado = False
            print(f"[Mente] ❌ Erro ao carregar mente {id_agente}: {e}")
        finally:
            with self._lock:
                self._carregando.discard(id_agente)

    # ─────────────────────────────────────────────────────────────────────
    # SALVAR — nunca bloqueia o loop
    # ─────────────────────────────────────────────────────────────────────

    def salvar(self, salvar_modelos: bool = True):
        """
        Salva metadados no minds.json imediatamente (rápido).
        Se salvar_modelos=True, envia cada torch.save para background.
        """
        self._salvar_json()
        if salvar_modelos:
            self._executor.submit(self._salvar_modelos_background)

    def _salvar_json(self):
        """Salva só o JSON de metadados — muito rápido, pode ser síncrono."""
        os.makedirs("data", exist_ok=True)
        temp = self.caminho + ".tmp"

        with self._lock:
            snapshot = dict(self.mentes)

        mentes_dict = {}
        for id_, m in snapshot.items():
            if hasattr(m, 'para_dict'):
                mentes_dict[str(id_)] = m.para_dict()
            else:
                mentes_dict[str(id_)] = {
                    "id_agente":  m.id_agente,
                    "n_acertos":  m.n_acertos,
                    "n_erros":    m.n_erros,
                    "geracao":    m.geracao,
                    "tipo":       "pytorch"
                }

        try:
            with open(temp, "w") as f:
                json.dump({
                    "ultimo_id_global": self.ultimo_id_global,
                    "mentes": mentes_dict
                }, f, indent=2)
            os.replace(temp, self.caminho)
        except Exception as e:
            print(f"[Mente] Erro ao salvar JSON: {e}")

    def _salvar_modelos_background(self):
        """torch.save de cada mente em background — não bloqueia nada."""
        with self._lock:
            snapshot = dict(self.mentes)

        salvos = 0
        for id_, m in snapshot.items():
            if hasattr(m, 'salvar') and getattr(m, '_pt_carregado', False):
                try:
                    m.salvar()
                    salvos += 1
                except Exception as e:
                    print(f"[Mente] Erro ao salvar modelo {id_}: {e}")

        print(f"[Mente] 💾 {salvos} modelos PyTorch salvos em background")

    # ─────────────────────────────────────────────────────────────────────
    # UTILITÁRIOS
    # ─────────────────────────────────────────────────────────────────────

    def notificar_morte(self, id_agente: int):
        with self._lock:
            m = self.mentes.get(id_agente)
        if m:
            m.geracao += 1

    def resetar_mente(self, id_agente: int):
        nova = MenteAgente(id_agente)
        with self._lock:
            self.mentes[id_agente] = nova

    def resetar_todas(self):
        with self._lock:
            self.mentes = {}
        self._salvar_json()

    def stats(self) -> dict:
        with self._lock:
            snapshot = dict(self.mentes)
        if not snapshot:
            return {"total": 0}
        accs = [m.accuracy for m in snapshot.values()]
        return {
            "total":        len(snapshot),
            "prontas":      sum(1 for m in snapshot.values() if getattr(m, '_pt_carregado', False)),
            "carregando":   len(self._carregando),
            "accuracy_avg": round(sum(accs) / len(accs), 3),
            "accuracy_max": round(max(accs), 3),
            "accuracy_min": round(min(accs), 3),
            "geracoes_max": max(m.geracao for m in snapshot.values()),
        }

    def gerar_novo_id(self):
        self.ultimo_id_global += 1
        self._salvar_json()
        return self.ultimo_id_global

    def limpar_mentes_orfas(self, ids_ativos):
        ids_ativos_set = set(ids_ativos)
        with self._lock:
            orfas = [id_ for id_ in self.mentes if id_ not in ids_ativos_set]
            for id_ in orfas:
                del self.mentes[id_]
        if orfas:
            print(f"[Mente] {len(orfas)} mentes órfãs removidas")
            self._salvar_json()
        return len(orfas)

    def get_max_id(self):
        with self._lock:
            return max(self.mentes.keys()) if self.mentes else 0
        
    def sincronizar_de_externo(self, id_agente: int, mente_externa: MenteAgente):
        """
        Copia os acertos/erros/geracao de uma mente externa (ex: CryptoApp)
        para a mente interna do BancoMentes, para que o minds.json reflita
        os valores reais.
        """
        with self._lock:
            mente_interna = self.mentes.get(id_agente)
            if mente_interna is None:
                self.mentes[id_agente] = mente_externa  # usa a própria
                return

        # Copia os campos que importam para o JSON
        mente_interna.n_acertos = mente_externa.n_acertos
        mente_interna.n_erros   = mente_externa.n_erros
        mente_interna.geracao   = mente_externa.geracao