import threading

from Software.core.engine import Universo
from Software.core.config import CAMINHO_UNIVERSO

universo = Universo(caminho=CAMINHO_UNIVERSO)

lock_universo = threading.Lock()