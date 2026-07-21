class SystemApp:
    nome = "system_app"
    def __init__(self, universo, estado):
        self.universo = universo
        self.estado = estado

    def handle(self, comando):
        respostas = []
        partes = comando.split()

        if comando == "help":
            respostas.append("system commands:")
            respostas.append("clear")
            respostas.append("pause")
            respostas.append("status")
            respostas.append("send pulse X Y")
            respostas.append("c [optional X Y]")
            respostas.append("list pulses")
            respostas.append("list units")
            respostas.append("use unit X")
            respostas.append("duplicate unit X")
            respostas.append("stats units")
            respostas.append("inspect unit X")
            respostas.append("stats universe")
            respostas.append("apps")
            respostas.append("list dead units")
            respostas.append("total energy")
            respostas.append("duplicate unit X")
            respostas.append("time: X")
            respostas.append("reset universe")

            respostas.append("")
            respostas.append("BALANCE APP:")
            respostas.append("balance units (...)")
            respostas.append("balance resource (...)")
            respostas.append("balance goal (...)")
            respostas.append("balance config")
            respostas.append("balance start")
            respostas.append("balance run")
            respostas.append("balance stop")
            respostas.append("")
            respostas.append("FLOW APP:")
            respostas.append("flow source X")
            respostas.append("flow target X")
            respostas.append("flow range (123456789)")
            respostas.append("flow start")
            respostas.append("flow run")
            respostas.append("flow result")
            respostas.append("flow stop")
            respostas.append("")
            respostas.append("CRYPTO APP:")
            respostas.append("crypto start")
            respostas.append("crypto spawn btcusdt ethusdt")
            respostas.append("crypto signal")
            respostas.append("crypto stop")
            return respostas

        if comando == "pause":
            self.estado["pausado"] = not self.estado["pausado"]
            
            return ["Universe paused" if self.estado["pausado"] else "Universe resumed"]

        if comando == "status":                
            return [self.universo.status_universo()]

        if comando == "clear":
            return ["__CLEAR__"]
        
        elif comando == "reset universe":
            self.universo.reset_universo(manter_aprendizado=True)
            respostas.append("universe reset: all units removed and data cleared")
            return respostas

        return None  # comando não é desse app
