class PulseApp:
    nome = "pulse_app"
    def __init__(self, universo):
        self.universo = universo

    def handle(self, comando):
        respostas = []
        partes = comando.split()

        if comando == "list pulses":
       # respostas = ["__CLEAR__"]
        
            if not self.universo.pulsos:
                respostas.append(f"No active pulses in the universe")
            else:
                for i, pulso in enumerate(self.universo.pulsos, 1):
                    respostas.append(f"Pulse {i} | "
                                    f"Origin: {pulso['origem']} → "
                                    f"Destination: {pulso['destino']} | "
                                    f"Energy: {pulso['energia']:.2f} | "
                                    f"Progress: {int(pulso['progresso'] * 100)}%")
            return respostas
                    
        elif len(partes) == 4 and partes[0] == "send" and partes[1] == "pulse":
            try:
                id1 = int(partes[2])
                id2 = int(partes[3])
                ok = self.universo.enviar_pulso(id1, id2)

                if ok:
                    respostas.append(f"Pulse {id1} → {id2}")
                else:
                    
                    respostas.append(f"Failed to send pulse")
            except:
                respostas.append("Usage: send pulse <origin> <destination>")
        
        return None
                                      

    