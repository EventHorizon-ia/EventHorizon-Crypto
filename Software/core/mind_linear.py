# mind_linear.py - SEU CÓDIGO ORIGINAL DO MenteAgente

import random
import math

class MenteAgenteLinear:
    """Rede neural linear - versão original"""
    
    N_ENTRADAS = 5
    
    def __init__(self, id_agente: int):
        self.id_agente = id_agente
        self.pesos = [random.uniform(-1, 1) for _ in range(self.N_ENTRADAS)]
        self.bias = random.uniform(-0.5, 0.5)
        self.taxa = 0.01
        self.ultima_entrada = None
        self.ultima_acao = 0.0
        self.n_acertos = 0
        self.n_erros = 0
        self.geracao = 0
    
    def forward(self, entrada: list) -> float:
        while len(self.pesos) < len(entrada):
            self.pesos.append(random.uniform(-1, 1))
        
        soma = sum(e * w for e, w in zip(entrada, self.pesos)) + self.bias
        saida = math.tanh(soma)
        
        self.ultima_entrada = entrada
        self.ultima_acao = saida
        return saida
    
    def aprender(self, recompensa: float):
        if self.ultima_entrada is None:
            return
        
        for i in range(len(self.pesos)):
            self.pesos[i] += self.taxa * recompensa * self.ultima_entrada[i]
        
        self.bias += self.taxa * recompensa
        
        if recompensa > 0:
            self.n_acertos += 1
        else:
            self.n_erros += 1
    
    def para_dict(self) -> dict:
        return {
            "id_agente": self.id_agente,
            "pesos": self.pesos,
            "bias": self.bias,
            "taxa": self.taxa,
            "n_acertos": self.n_acertos,
            "n_erros": self.n_erros,
            "geracao": self.geracao,
        }
    
    @staticmethod
    def de_dict(d: dict) -> "MenteAgenteLinear":
        m = MenteAgenteLinear(d["id_agente"])
        m.pesos = d.get("pesos", m.pesos)
        m.bias = d.get("bias", m.bias)
        m.taxa = d.get("taxa", m.taxa)
        m.n_acertos = d.get("n_acertos", 0)
        m.n_erros = d.get("n_erros", 0)
        m.geracao = d.get("geracao", 0)
        return m
    
    @property
    def accuracy(self) -> float:
        total = self.n_acertos + self.n_erros
        return self.n_acertos / total if total > 0 else 0.5