import pygame

from Software.core.universe_instance import universo
from Software.core.telas import desenhar_tela_atual
from Software.core.terminal import processar_comando
from Software.core.terminal import get_prompt
from Software.core.config import CAMINHO_UNIVERSO, WIDTH, HEIGHT, cores_tipos
from Software.core.leis import evoluir_universo
from Software.core.eventos import processar_eventos
from Software.core.telas import desenhar_tela_atual
from Software.core.user_config import carregar_config, salvar_config
from Software.core.state import estado


from Software.apps.system_app import SystemApp
from Software.apps.data_app import DataApp
from Software.apps.pulse_app import PulseApp
from Software.apps.time_app import TimeApp
from Software.apps.balance_app import BalanceApp
from Software.apps.flow_app import FlowApp
from Software.apps.crypto_app import CryptoApp


# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================

pygame.init()
pygame.mixer.init()

sons = {
    "click": pygame.mixer.Sound("assets/sounds/pause.wav"),
    "erro": pygame.mixer.Sound("assets/sounds/error.wav"),
    "criar_dado": pygame.mixer.Sound("assets/sounds/criar_dado.wav"),
    "whoosh": pygame.mixer.Sound("assets/sounds/whoosh.wav")
}


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Experimental Simulation OS ")
icone = pygame.image.load("assets/icone.png")
pygame.display.set_icon(icone)

clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 20)
font_terminal = pygame.font.SysFont("consolas", 14)

# =========================================================
# LAYOUT
# =========================================================

universe_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)

terminal_linhas = []
historico_comandos = []


contexto_atual = "rse> "


CURSOR_DELAY = 500 # milissegundos
CURSOR_BLINK = 500






universo.apps.append(SystemApp(universo, estado))
universo.apps.append(DataApp(universo))
universo.apps.append(PulseApp(universo))
universo.apps.append(TimeApp(estado))
universo.apps.append(BalanceApp(universo))
universo.apps.append(FlowApp(universo))
universo.apps.append(CryptoApp(universo))

config_usuario = carregar_config()

estado_ui = {
    "tela_atual": "menu",
    "current_text": "",
    "cursor_visivel": True,
    "ultimo_input": pygame.time.get_ticks(),
    "scroll_offset": 0,
    "indice_historico": -1,
    "contador_salvamento": 0,
    "clique_mouse": False,
    "cursor_visivel": True,
    "efeitos": True,
    "fx_particulas_fundo": True,
    "fx_scanlines": True,
    "fx_glow": True,
    "fx_fade": True,
    "fx_pulsos": True,
    "preset_atual": "HIGH",
    "primeira_execucao": config_usuario.get("primeira_execucao", True),
    "boot_index": 0,
    "boot_timer": pygame.time.get_ticks(),
    "tutorial_step": 0,
    "status_sistema": "IDLE",
    "status_timer": 0,
    "log_sistema": [],
    "log_timer": 0,
    "log_index": 0
}

# =========================================================
# LOOP PRINCIPAL
# =========================================================
def main():
    while True:
        processar_eventos(
            estado_ui,
            universo,
            estado,
            terminal_linhas,
            historico_comandos,
            sons,
            WIDTH,
            HEIGHT,
            font_terminal,
            get_prompt,
            processar_comando,
            CURSOR_DELAY,
            CURSOR_BLINK
        )

       
        # -----------------------
        # DESENHO
        # -----------------------

        desenhar_tela_atual(
            screen,
            estado_ui,
            universo,
            estado,
            terminal_linhas,
            historico_comandos,
            sons,
            font,
            font_terminal,
            WIDTH,
            HEIGHT,
            cores_tipos,
            evoluir_universo,
            get_prompt
        )

        

        estado_ui["clique_mouse"] = False

        estado_ui["contador_salvamento"] += 1
        if estado_ui["contador_salvamento"] % 120 == 0:
            universo.salvar()


        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
     main()