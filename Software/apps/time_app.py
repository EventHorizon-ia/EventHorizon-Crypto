class TimeApp: 
    nome = "time_app"
    def __init__ (self, estado):
        self.estado = estado
    
    def handle(self, comando):
        partes = comando.split()

        if len(partes) == 2 and partes[0] == "time" and partes[1] == "status":
            
            return [f"Scale Time: {self.estado['escala_usuario']}"]
            

        if len(partes) == 2 and partes[0] == "tempo:":
            try:
                valor = float(partes[1])
                self.estado["escala_usuario"] = max(0.1, min(valor, 20.0))
                return [f"Escala de tempo ajustada para {self.estado['escala_usuario']}"]
            except:
                
                return ["Valor inválido para tempo"]
        
        return None
            