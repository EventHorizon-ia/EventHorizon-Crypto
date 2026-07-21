
import uuid
class DataApp:
    nome = "data_app"
    def __init__(self, universo):
        self.universo = universo

    def handle(self, comando):
        partes = comando.split()
        respostas = []

        # criar dado
        if comando.startswith("c"):
            config = {}
            x, y = None, None

            for parte in partes[1:]:
                if "=" in parte:
                    chave, valor = parte.split("=")

                    try:
                        valor = float(valor)
                    except:
                        pass

                    config[chave] = valor

            # posição separada
            if "x" in config and "y" in config:
                x = config.pop("x")
                y = config.pop("y")

            pos = (x, y) if x is not None and y is not None else None

           
            dado = self.universo.criar_dado(pos=pos, config=config)

            return [f"Unit {dado['id']} created with config {config}"]
        
        # usar dado X
        if len(partes) == 3 and partes[0] == "use" and partes[1] == "unit":
            try:
                id_dado = int(partes[2])
            except:
                return ["invalid id"]

            dado = next((d for d in self.universo.dados if d["id"] == id_dado), None)

            if dado is None:
                return [f"unit {id_dado} does not exist"]

            dado["energia"] -= 1
            respostas.append(f"unit {id_dado} used | energy = {dado['energia']}")

            if dado["energia"] <= 0:
                self.universo.dados.remove(dado)
                self.universo.dados_mortos.append(dado)
                respostas.append(f"unit {id_dado} exhausted and removed")

            return respostas

        # duplicar dado X
        if len(partes) == 3 and partes[0] == "duplicate" and partes[1] == "unit":
            try:
                id_dado = int(partes[2])
            except:
              
                return ["invalid id"]

            original = next((d for d in self.universo.dados if d["id"] == id_dado), None)
            if original is None:
              
                return [f"unit {id_dado} not found"]

            novo = self.universo.criar_dado()
            novo["tipo"] = original["tipo"]
            novo["energia"] = original["energia"]
           
            return [f"unit {id_dado} duplicated as id={novo['id']}"]

        # energia total
        if comando == "total energy":
            return [f"Total energy of units: {self.universo.energia_dados()}",
                    f"Total energy of pulses: {self.universo.energia_pulsos()}",
                    f"Total universe energy: {self.universo.energia_total()}"]
        
        if comando == "list units":
            if not self.universo.dados:
                return ["No active units in the universe"]
            
            total = len(self.universo.dados)
            respostas.append(f"Active units: {total}")
            respostas.append("") 
            respostas.append("ID            STATE           ENERGY      TIME   BITS")
            respostas.append("--    --------------------   --------     -----   ----")
            
            for d in self.universo.dados:
                bits = "".join(str(b) for b in d["bits"])
                estado_str = ", ".join(f"{x:.2f}" for x in d.get("estado", [0, 0, 0]))

                linha = (
                    f"{d['id']:<3}  "
                    f"{estado_str:<13}  "
                    f"{d['energia']:<9.1f}  "
                    f"{d['tempo_proprio']:<7.1f}  "

                    f"{bits}"
                )
                respostas.append(linha)

            return respostas
                    
        if comando == "list dead units":
            if not self.universo.dados_mortos:
                return ["No dead units in the universe"]
            
            respostas.append("Dead units:")
            for d in self.universo.dados_mortos:
                respostas.append(f"id: {d['id']} | ")
                                 
            return respostas
        
        if len(partes) == 3 and partes[0] == "inspect" and partes[1] == "unit":
            try:
                id_dado = int(partes[2])
            except:
                
                return ["Invalid ID"]

            dado = next(
                (d for d in self.universo.dados if d["id"] == id_dado),
                None
            )

            if not dado:
               
                return ["Unit not found"]

            return [
                f"  Unit {dado['id']}",
                f" ├ State: {dado['estado']}",
                f" ├ Energy: {dado['energia']:.2f}",
                f" ├ Proper time: {dado['tempo_proprio']:.2f}",
                f" ├ Time factor: {dado['fator_tempo']}",
                f" ├ Memory: {len(dado['memoria'])} events",
                f" └ Bits: {dado['bits']}",
                f"   Value: {dado['valor']}"
            ]

        if comando == "stats units":
            total = len(self.universo.dados)

            if total == 0:
                return ["No active units in the universe"]

            energia_total = self.universo.energia_dados()
            energia_transito = self.universo.energia_pulsos()
            energia_media = energia_total / total

            maior = max(self.universo.dados, key=lambda d: d["energia"])
            menor = min(self.universo.dados, key=lambda d: d["energia"])

            return [
                "GLOBAL STATE OF UNITS",
                "----------------------",
                f"Total of units......: {total}",
                f"Stored energy.......: {energia_total:.2f}",
                f"Transit energy.......: {energia_transito:.2f}",
                f"Average energy.......: {energia_media:.2f}",
                f"Highest energy.......: Unit {maior['id']} ({maior['energia']:.2f})",
                f"Lowest energy.......: Unit {menor['id']} ({menor['energia']:.2f})"
            ]
        
        if comando == "stats universe":
            if not self.universo.stats_history:
                return ["No statistics collected yet"]

            stats = self.universo.stats_history[-1]  # pega o último registro
            respostas = [
                "=== UNIVERSE STATS ===",
                f"Simulation time: {stats['simulation_time']:.2f}",
                f"Total units: {stats['num_dados']}",
                f"Total pulses: {stats['num_pulsos']}",
                f"Total energy: {stats['energia_total']:.2f}",
                f"Average proper time: {stats['media_tau']:.2f}",
                f"Proper time deviation: {stats['desvio_tau']:.2f}"
            ]
            return respostas

            
        

            return [f"Expression sent: {comando} | Result will arrive at unit {destino['id']}"]
        if len(partes) == 3 and partes[0] == "memory" and partes[1] == "unit":
            try:
                id_dado = int(partes[2])
            except:
            
                return ["Invalid ID"]

            # Procura dado entre vivos e mortos
            dado = next(
                (d for d in self.universo.dados + self.universo.dados_mortos
                 if d["id"] == id_dado),
                None
            )

            if dado is None:
                return [f"Unit {id_dado} not found"]

            memoria = dado.get("memoria", [])

            if not memoria:
                return [f"Unit {id_dado} has empty memory"]

            respostas.append(f"Memory of unit {id_dado}:")
            for evento in memoria:
                if evento.get("acao") == "enviou pulso":
                    respostas.append(
                        f"Pulse {evento.get('pulso_id')} | Energy: {evento.get('energia')}"
                    )

            return respostas
        
                # expressão matemática vira pulso físico
        try:
            permitido = "0123456789+-*/().% "
            if all(c in permitido for c in comando):

                if len(self.universo.dados) < 2:
                    return ["Need at least 2 units"]

                origem = self.universo.dados[0]
                destino = self.universo.dados[1]

                sucesso = self.universo.enviar_pulso(
                    origem["id"],
                    destino["id"],
                    energia=0.2
                )

                if sucesso:
                    # pega último pulso criado
                    pulso = self.universo.pulsos[-1]
                    pulso["expressao"] = comando
                    return [f"Expression sent as pulse from {origem['id']} to {destino['id']}"]

                
                           
                            

        except:
            pass

        if self.universo.resultados_terminal:
            resultados = self.universo.resultados_terminal.copy()
            self.universo.resultados_terminal.clear()
            return resultados
                    


        return None  # não é deste app
