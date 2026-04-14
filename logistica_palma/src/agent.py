"""
agent.py — Agente distribuído com fila de reenvio
Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

Cada agente representa um nó logístico (campo, transportadora, centro, usina).
Possui fila local: eventos não entregues são reenviados automaticamente.
"""

import socket
import time
import random
import threading
import queue
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from common import HOST, PORT, send_msg, recv_msg, get_logger, now_iso

# ─── Configuração ────────────────────────────────────────────────────────────
RETRY_INTERVAL   = 5    # segundos entre tentativas de reenvio
MAX_RETRIES      = 5    # máximo de tentativas por evento
TIMEOUT_CONEXAO  = 4    # segundos de timeout no socket

# ─── Agente ──────────────────────────────────────────────────────────────────

class Agente:
    def __init__(self, nome: str, tipo: str):
        self.nome   = nome
        self.tipo   = tipo  # campo | transportadora | centro | usina
        self.logger = get_logger(f"AGENTE:{nome}")
        self.fila_pendente: queue.Queue = queue.Queue()
        self._stop = threading.Event()

        # Inicia thread de reenvio em background
        t = threading.Thread(target=self._worker_reenvio, daemon=True)
        t.start()

    # ── Envio de um evento ao servidor ───────────────────────────────────────
    def enviar_evento(self, id_lote: str, tipo_evento: str, detalhes: dict = None) -> dict | None:
        payload = {
            "tipo_mensagem": "evento",
            "id_lote":       id_lote,
            "tipo_evento":   tipo_evento,
            "origem_agente": self.nome,
            "timestamp":     now_iso(),
            "detalhes":      detalhes or {},
        }
        resposta = self._tentar_envio(payload)
        if resposta is None:
            self.logger.warning(f"Servidor indisponível — evento enfileirado: {tipo_evento}")
            self.fila_pendente.put({"payload": payload, "tentativas": 0})
        return resposta

    # ── Consulta ao servidor ─────────────────────────────────────────────────
    def consultar_estado(self, id_lote: str) -> dict | None:
        return self._tentar_envio({
            "tipo_mensagem": "consulta",
            "tipo_consulta": "estado",
            "id_lote": id_lote,
        })

    def consultar_historico(self, id_lote: str) -> dict | None:
        return self._tentar_envio({
            "tipo_mensagem": "consulta",
            "tipo_consulta": "historico",
            "id_lote": id_lote,
        })

    def listar_lotes(self) -> dict | None:
        return self._tentar_envio({
            "tipo_mensagem": "consulta",
            "tipo_consulta": "listar",
        })

    # ── Envio com abertura/fechamento de socket por mensagem ─────────────────
    def _tentar_envio(self, payload: dict) -> dict | None:
        try:
            with socket.create_connection((HOST, PORT), timeout=TIMEOUT_CONEXAO) as sock:
                send_msg(sock, payload)
                resposta = recv_msg(sock)
                return resposta
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self.logger.debug(f"Falha de conexão: {e}")
            return None

    # ── Worker de reenvio (roda em background) ────────────────────────────────
    def _worker_reenvio(self):
        while not self._stop.is_set():
            time.sleep(RETRY_INTERVAL)
            itens = []
            while not self.fila_pendente.empty():
                try:
                    itens.append(self.fila_pendente.get_nowait())
                except queue.Empty:
                    break

            for item in itens:
                item["tentativas"] += 1
                self.logger.info(
                    f"Tentativa de reenvio {item['tentativas']}/{MAX_RETRIES} "
                    f"— lote {item['payload'].get('id_lote')}"
                )
                resposta = self._tentar_envio(item["payload"])
                if resposta is None:
                    if item["tentativas"] < MAX_RETRIES:
                        self.fila_pendente.put(item)
                    else:
                        self.logger.error(
                            f"Evento descartado após {MAX_RETRIES} tentativas: "
                            f"{item['payload'].get('tipo_evento')}"
                        )
                else:
                    self.logger.info(f"Reenvio bem-sucedido: {item['payload'].get('tipo_evento')}")

    def parar(self):
        self._stop.set()


# ─── Simulação de fluxo completo ─────────────────────────────────────────────

def simular_fluxo_campo(agente: Agente, id_lote: str):
    """Simula o fluxo de um lote de palma saindo do campo."""
    logger = agente.logger

    print("\n" + "="*60)
    print(f"  AGENTE: {agente.nome} ({agente.tipo})  |  LOTE: {id_lote}")
    print("="*60)

    etapas = [
        ("lote_criado",           {"descricao": "Lote registrado no sistema"}),
        ("coleta_realizada",      {"peso_kg": random.randint(800, 2000)}),
        ("carregamento_iniciado", {"veiculo": f"CAM-{random.randint(10,99)}"}),
        ("em_transporte",         {"velocidade_kmh": random.randint(40, 80)}),
        ("atualizacao_localizacao", {"lat": -1.45 + random.uniform(-0.1, 0.1),
                                     "lon": -48.5 + random.uniform(-0.1, 0.1)}),
    ]

    # Simulação de atraso aleatório (10% de chance)
    if random.random() < 0.10:
        etapas.append(("atraso_registrado", {"motivo": "Estrada interditada"}))

    for tipo_evento, detalhes in etapas:
        print(f"\n>>> Enviando evento: {tipo_evento}")
        resp = agente.enviar_evento(id_lote, tipo_evento, detalhes)
        if resp:
            status = resp.get("status")
            alertas = resp.get("alertas", [])
            print(f"    Resposta: {status}", end="")
            if alertas:
                print(f"  ALERTA: {alertas[0]['tipo']}", end="")
            print()
        else:
            print("    Servidor indisponível — enfileirado para reenvio")
        time.sleep(0.5)


def simular_fluxo_usina(agente: Agente, id_lote: str):
    """Simula o recebimento na usina."""
    print("\n" + "="*60)
    print(f"  AGENTE: {agente.nome} ({agente.tipo})  |  LOTE: {id_lote}")
    print("="*60)

    etapas = [
        ("chegada_centro",    {"local": "Centro de Consolidação Norte"}),
        ("saida_centro",      {"conferido_por": "Op. Joao"}),
        ("chegada_usina",     {"linha_producao": random.randint(1, 4)}),
        ("entrega_concluida", {"nota_fiscal": f"NF-{random.randint(1000,9999)}"}),
    ]

    for tipo_evento, detalhes in etapas:
        print(f"\n>>> Enviando evento: {tipo_evento}")
        resp = agente.enviar_evento(id_lote, tipo_evento, detalhes)
        if resp:
            print(f"    Resposta: {resp.get('status')}")
        else:
            print("    Servidor indisponível — enfileirado para reenvio")
        time.sleep(0.5)


# ─── Entrypoint ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agente de Logística — Cadeia da Palma")
    parser.add_argument("--nome",  default="campo_norte",
                        help="Nome do agente (ex: campo_norte, usina_belem)")
    parser.add_argument("--tipo",  default="campo",
                        choices=["campo", "transportadora", "centro", "usina"],
                        help="Tipo do nó logístico")
    parser.add_argument("--lote",  default="L001",
                        help="ID do lote a rastrear (ex: L001, L002)")
    parser.add_argument("--modo",  default="campo",
                        choices=["campo", "usina"],
                        help="Modo de simulação")
    args = parser.parse_args()

    agente = Agente(nome=args.nome, tipo=args.tipo)

    try:
        if args.modo == "campo":
            simular_fluxo_campo(agente, args.lote)
        else:
            simular_fluxo_usina(agente, args.lote)

        # Aguarda reenvios pendentes
        time.sleep(2)
        pendentes = agente.fila_pendente.qsize()
        if pendentes > 0:
            print(f"\n Aguardando reenvio de {pendentes} evento(s) pendente(s)...")
            time.sleep(RETRY_INTERVAL + 2)

    except KeyboardInterrupt:
        print("\n\nAgente encerrado.")
    finally:
        agente.parar()


if __name__ == "__main__":
    main()
