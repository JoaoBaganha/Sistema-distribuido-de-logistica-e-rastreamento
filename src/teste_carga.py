"""
teste_carga.py — Testes experimentais de desempenho e escalabilidade
Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

Cenários:
  1. Agentes sequenciais  — 1 agente por vez
  2. Agentes concorrentes — N agentes em paralelo (threads)
  3. Falha de servidor    — agente envia, servidor reinicia
  4. Avaliar vazão e tempo médio de resposta
"""

import threading
import time
import statistics
import socket
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import HOST, PORT, send_msg, recv_msg, now_iso

TIMEOUT = 4

# ─── Envio isolado de 1 evento ───────────────────────────────────────────────

def enviar_evento(id_lote: str, tipo_evento: str, agente: str) -> float | None:
    """Envia 1 evento e retorna o tempo de resposta em ms, ou None em falha."""
    payload = {
        "tipo_mensagem": "evento",
        "id_lote": id_lote,
        "tipo_evento": tipo_evento,
        "origem_agente": agente,
        "timestamp": now_iso(),
        "detalhes": {},
    }
    t0 = time.perf_counter()
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
            send_msg(sock, payload)
            resp = recv_msg(sock)
            elapsed = (time.perf_counter() - t0) * 1000
            return elapsed if resp else None
    except Exception:
        return None


# ─── Cenário 1: Sequencial ───────────────────────────────────────────────────

def cenario_sequencial(n_eventos: int = 20):
    print(f"\n{'='*55}")
    print(f"  CENÁRIO 1: {n_eventos} eventos sequenciais")
    print(f"{'='*55}")
    tempos = []
    falhas = 0
    for i in range(n_eventos):
        t = enviar_evento(f"SEQ{i:03}", "em_transporte", f"agente_seq_{i}")
        if t is not None:
            tempos.append(t)
        else:
            falhas += 1

    _resumo(tempos, falhas, n_eventos)


# ─── Cenário 2: Concorrente ──────────────────────────────────────────────────

def cenario_concorrente(n_agentes: int = 10, eventos_por_agente: int = 5):
    total = n_agentes * eventos_por_agente
    print(f"\n{'='*55}")
    print(f"  CENÁRIO 2: {n_agentes} agentes × {eventos_por_agente} eventos = {total} total")
    print(f"{'='*55}")

    resultados = []
    lock = threading.Lock()

    def worker(agente_id: int):
        for j in range(eventos_por_agente):
            t = enviar_evento(f"CONC{agente_id:02}{j:02}", "em_transporte", f"agente_{agente_id}")
            with lock:
                resultados.append(t)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_agentes)]
    t_inicio = time.perf_counter()
    for th in threads: th.start()
    for th in threads: th.join()
    duracao_total = (time.perf_counter() - t_inicio) * 1000

    tempos = [r for r in resultados if r is not None]
    falhas = resultados.count(None)
    _resumo(tempos, falhas, total)
    vazao = total / (duracao_total / 1000)
    print(f"    Duração total         : {duracao_total:.1f} ms")
    print(f"    Vazão (eventos/s)     : {vazao:.1f}")


# ─── Cenário 3: Consultas concorrentes ───────────────────────────────────────

def cenario_consultas(n_consultas: int = 20):
    print(f"\n{'='*55}")
    print(f"  CENÁRIO 3: {n_consultas} consultas de métricas concorrentes")
    print(f"{'='*55}")

    resultados = []
    lock = threading.Lock()

    def consultar():
        t0 = time.perf_counter()
        try:
            with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
                send_msg(sock, {"tipo_mensagem": "consulta", "tipo_consulta": "metricas"})
                resp = recv_msg(sock)
                elapsed = (time.perf_counter() - t0) * 1000
                with lock:
                    resultados.append(elapsed if resp else None)
        except Exception:
            with lock:
                resultados.append(None)

    threads = [threading.Thread(target=consultar) for _ in range(n_consultas)]
    for th in threads: th.start()
    for th in threads: th.join()

    tempos = [r for r in resultados if r is not None]
    falhas = resultados.count(None)
    _resumo(tempos, falhas, n_consultas)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _resumo(tempos: list, falhas: int, total: int):
    if tempos:
        print(f"    Eventos com sucesso   : {len(tempos)}/{total}")
        print(f"    Falhas                : {falhas}")
        print(f"    Tempo mínimo          : {min(tempos):.2f} ms")
        print(f"    Tempo máximo          : {max(tempos):.2f} ms")
        print(f"    Tempo médio           : {statistics.mean(tempos):.2f} ms")
        print(f"    Desvio padrão         : {statistics.stdev(tempos):.2f} ms" if len(tempos) > 1 else "")
    else:
        print(f"    Nenhum evento entregue (servidor offline?)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n  Verificando servidor...")
    try:
        with socket.create_connection((HOST, PORT), timeout=2) as sock:
            send_msg(sock, {"tipo_mensagem": "ping"})
            resp = recv_msg(sock)
        print("  ✓ Servidor online:", resp.get("timestamp"))
    except Exception:
        print("  ✗ Servidor offline. Inicie server.py antes de rodar os testes.")
        sys.exit(1)

    cenario_sequencial(n_eventos=20)
    cenario_concorrente(n_agentes=10, eventos_por_agente=5)
    cenario_consultas(n_consultas=15)

    print(f"\n{'='*55}")
    print("  Testes concluídos.")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
