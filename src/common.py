"""
common.py — Funções e constantes compartilhadas
Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma
"""

import json
import socket
import logging
import datetime

# ─── Configurações de rede ───────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 5000

# ─── Tipos de eventos possíveis ──────────────────────────────────────────────
TIPOS_EVENTO = [
    "lote_criado",
    "coleta_realizada",
    "carregamento_iniciado",
    "em_transporte",
    "atualizacao_localizacao",
    "chegada_centro",
    "saida_centro",
    "chegada_usina",
    "atraso_registrado",
    "falha_registrada",
    "entrega_concluida",
]

# ─── Etapas do fluxo logístico ───────────────────────────────────────────────
FLUXO_LOGISTICO = ["campo", "transporte", "centro_consolidacao", "usina"]

# ─── Logger padrão ───────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger


# ─── Serialização / envio com tamanho prefixado ──────────────────────────────
HEADER_SIZE = 8  # bytes que representam o tamanho da mensagem

def send_msg(sock: socket.socket, payload: dict) -> None:
    """Serializa dict → JSON → envia com header de tamanho."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = len(data).to_bytes(HEADER_SIZE, "big")
    sock.sendall(header + data)


def recv_msg(sock: socket.socket) -> dict | None:
    """Recebe mensagem com header de tamanho; retorna None em desconexão."""
    try:
        header = _recv_exact(sock, HEADER_SIZE)
        if not header:
            return None
        length = int.from_bytes(header, "big")
        data = _recv_exact(sock, length)
        if not data:
            return None
        return json.loads(data.decode("utf-8"))
    except (ConnectionResetError, json.JSONDecodeError, OSError):
        return None


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


# ─── Helpers de timestamp ────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")
