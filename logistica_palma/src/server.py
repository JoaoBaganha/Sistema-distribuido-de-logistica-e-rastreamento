"""
server.py — Servidor TCP Central (multi-threaded)
Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

Responsabilidades:
  • Aceita múltiplos agentes simultaneamente (1 thread por conexão)
  • Armazena estado atual e histórico completo de cada lote
  • Persiste dados em JSON (logs/lotes.json) para sobreviver a reinicializações
  • Responde a consultas de estado e histórico
  • Detecta e registra atrasos e falhas
  • Coleta métricas de desempenho (tempo de resposta, vazão)
"""

import socket
import threading
import json
import time
import os
import sys

# Garante que src/ está no path
sys.path.insert(0, os.path.dirname(__file__))
from common import HOST, PORT, send_msg, recv_msg, get_logger, now_iso

logger = get_logger("SERVIDOR")

# ─── Estado global (protegido por lock) ─────────────────────────────────────
lock = threading.Lock()

estado_lotes: dict = {}   # { id_lote: { status_atual, ultimo_timestamp, ... } }
historico: dict   = {}    # { id_lote: [ evento, ... ] }
metricas: dict    = {     # contadores globais
    "total_eventos": 0,
    "total_alertas": 0,
    "tempo_total_ms": 0.0,
    "conexoes_ativas": 0,
}

ARQUIVO_PERSISTENCIA = os.path.join(os.path.dirname(__file__), "..", "logs", "lotes.json")

# ─── Persistência ────────────────────────────────────────────────────────────

def salvar_estado() -> None:
    """Persiste estado + histórico em disco."""
    os.makedirs(os.path.dirname(ARQUIVO_PERSISTENCIA), exist_ok=True)
    with open(ARQUIVO_PERSISTENCIA, "w", encoding="utf-8") as f:
        json.dump({"estado_lotes": estado_lotes, "historico": historico}, f,
                  ensure_ascii=False, indent=2)


def carregar_estado() -> None:
    """Carrega estado + histórico do disco (se existir)."""
    global estado_lotes, historico
    if os.path.exists(ARQUIVO_PERSISTENCIA):
        try:
            with open(ARQUIVO_PERSISTENCIA, "r", encoding="utf-8") as f:
                dados = json.load(f)
            estado_lotes = dados.get("estado_lotes", {})
            historico    = dados.get("historico", {})
            logger.info(f"Estado restaurado: {len(estado_lotes)} lotes carregados.")
        except Exception as e:
            logger.warning(f"Falha ao carregar estado persistido: {e}")

# ─── Processamento de mensagens ──────────────────────────────────────────────

def processar_evento(msg: dict) -> dict:
    """Atualiza estado e histórico; retorna resposta ao agente."""
    t0 = time.perf_counter()

    id_lote      = msg.get("id_lote")
    tipo_evento  = msg.get("tipo_evento")
    agente       = msg.get("origem_agente", "desconhecido")
    timestamp    = msg.get("timestamp", now_iso())
    detalhes     = msg.get("detalhes", {})

    if not id_lote or not tipo_evento:
        return {"status": "erro", "mensagem": "Campos obrigatórios ausentes."}

    with lock:
        # Inicializa lote se novo
        if id_lote not in estado_lotes:
            estado_lotes[id_lote] = {
                "status_atual": tipo_evento,
                "ultimo_timestamp": timestamp,
                "origem_agente": agente,
                "alertas": [],
            }
            historico[id_lote] = []

        # Detecta situações de alerta
        alertas = []
        if tipo_evento in ("atraso_registrado", "falha_registrada"):
            alerta = {
                "tipo": tipo_evento,
                "timestamp": timestamp,
                "agente": agente,
                "detalhes": detalhes,
            }
            estado_lotes[id_lote]["alertas"].append(alerta)
            alertas.append(alerta)
            metricas["total_alertas"] += 1
            logger.warning(f"ALERTA no lote {id_lote}: {tipo_evento} | agente={agente}")

        # Atualiza estado atual
        estado_lotes[id_lote]["status_atual"]      = tipo_evento
        estado_lotes[id_lote]["ultimo_timestamp"]  = timestamp
        estado_lotes[id_lote]["origem_agente"]     = agente

        # Registra no histórico
        historico[id_lote].append({
            "tipo_evento": tipo_evento,
            "timestamp":   timestamp,
            "agente":      agente,
            "detalhes":    detalhes,
        })

        metricas["total_eventos"] += 1
        elapsed_ms = (time.perf_counter() - t0) * 1000
        metricas["tempo_total_ms"] += elapsed_ms

        salvar_estado()

    logger.info(f"Lote {id_lote} → {tipo_evento} | agente={agente} | {elapsed_ms:.2f}ms")

    return {
        "status": "recebido",
        "id_lote": id_lote,
        "tipo_evento": tipo_evento,
        "timestamp_servidor": now_iso(),
        "alertas": alertas,
    }


def processar_consulta(msg: dict) -> dict:
    """Responde consultas de estado atual ou histórico."""
    tipo    = msg.get("tipo_consulta")   # "estado" | "historico" | "metricas" | "listar"
    id_lote = msg.get("id_lote")

    with lock:
        if tipo == "listar":
            return {
                "status": "ok",
                "lotes": list(estado_lotes.keys()),
                "total": len(estado_lotes),
            }

        if tipo == "metricas":
            total = metricas["total_eventos"]
            media = (metricas["tempo_total_ms"] / total) if total > 0 else 0
            return {
                "status": "ok",
                "total_eventos": total,
                "total_alertas": metricas["total_alertas"],
                "media_tempo_resposta_ms": round(media, 3),
                "conexoes_ativas": metricas["conexoes_ativas"],
            }

        if not id_lote:
            return {"status": "erro", "mensagem": "id_lote obrigatório."}

        if id_lote not in estado_lotes:
            return {"status": "erro", "mensagem": f"Lote {id_lote} não encontrado."}

        if tipo == "estado":
            return {"status": "ok", "id_lote": id_lote,
                    "estado": estado_lotes[id_lote]}

        if tipo == "historico":
            return {"status": "ok", "id_lote": id_lote,
                    "historico": historico.get(id_lote, [])}

    return {"status": "erro", "mensagem": "Tipo de consulta desconhecido."}

# ─── Handler de conexão (roda em thread separada) ────────────────────────────

def handle_client(conn: socket.socket, addr: tuple) -> None:
    logger.info(f"Conexão recebida de {addr}")
    with lock:
        metricas["conexoes_ativas"] += 1

    try:
        while True:
            msg = recv_msg(conn)
            if msg is None:
                break  # cliente desconectou

            tipo_msg = msg.get("tipo_mensagem", "evento")

            if tipo_msg == "evento":
                resposta = processar_evento(msg)
            elif tipo_msg == "consulta":
                resposta = processar_consulta(msg)
            elif tipo_msg == "ping":
                resposta = {"status": "pong", "timestamp": now_iso()}
            else:
                resposta = {"status": "erro", "mensagem": "Tipo de mensagem desconhecido."}

            send_msg(conn, resposta)

    except Exception as e:
        logger.error(f"Erro na conexão {addr}: {e}")
    finally:
        conn.close()
        with lock:
            metricas["conexoes_ativas"] -= 1
        logger.info(f"Conexão encerrada: {addr}")

# ─── Loop principal ──────────────────────────────────────────────────────────

def main():
    carregar_estado()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((HOST, PORT))
        logger.info(f"✓ Socket vinculado a {HOST}:{PORT}")
    except OSError as e:
        logger.error(f"✗ Falha ao vincular socket: {e}")
        logger.error(f"  Verifique se a porta {PORT} está em uso ou permissões insuficientes.")
        return
    
    try:
        server_sock.listen(10)
        logger.info(f"✓ Servidor escutando com fila de até 10 conexões")
    except OSError as e:
        logger.error(f"✗ Falha ao colocar em escuta: {e}")
        return

    logger.info(f"Servidor iniciado em {HOST}:{PORT}")
    logger.info("Aguardando conexões... (Ctrl+C para encerrar)")

    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
            logger.debug(f"Thread iniciada para {addr} | threads ativas: {threading.active_count()-1}")
    except KeyboardInterrupt:
        logger.info("Servidor encerrado pelo usuário.")
    finally:
        server_sock.close()
        logger.info("Socket fechado.")


if __name__ == "__main__":
    main()
