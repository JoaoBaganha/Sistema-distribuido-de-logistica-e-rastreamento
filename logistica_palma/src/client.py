"""
client.py — Console interativo para consultas ao servidor
Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

Permite ao operador consultar:
  • Estado atual de um lote
  • Histórico completo de eventos
  • Listagem de todos os lotes
  • Métricas de desempenho do servidor
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))
from common import HOST, PORT, send_msg, recv_msg, get_logger
import socket

logger = get_logger("CLIENT")
TIMEOUT = 5


def _enviar(payload: dict) -> dict | None:
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
            send_msg(sock, payload)
            return recv_msg(sock)
    except Exception as e:
        print(f"  Erro de conexão: {e}")
        return None


def listar_lotes():
    resp = _enviar({"tipo_mensagem": "consulta", "tipo_consulta": "listar"})
    if resp and resp.get("status") == "ok":
        lotes = resp.get("lotes", [])
        print(f"\n  Total de lotes: {resp['total']}")
        for l in lotes:
            print(f"    • {l}")
    else:
        print("  Sem resposta ou erro.")


def ver_estado(id_lote: str):
    resp = _enviar({"tipo_mensagem": "consulta", "tipo_consulta": "estado", "id_lote": id_lote})
    if resp and resp.get("status") == "ok":
        estado = resp["estado"]
        print(f"\n  Lote: {id_lote}")
        print(f"    Status atual   : {estado.get('status_atual')}")
        print(f"    Último evento  : {estado.get('ultimo_timestamp')}")
        print(f"    Agente         : {estado.get('origem_agente')}")
        alertas = estado.get("alertas", [])
        if alertas:
            print(f"    Alertas ({len(alertas)}):")
            for a in alertas:
                print(f"       - {a['tipo']} em {a['timestamp']} | {a['detalhes']}")
    else:
        print(f"  Lote {id_lote} não encontrado ou erro.")


def ver_historico(id_lote: str):
    resp = _enviar({"tipo_mensagem": "consulta", "tipo_consulta": "historico", "id_lote": id_lote})
    if resp and resp.get("status") == "ok":
        hist = resp.get("historico", [])
        print(f"\n  Histórico do lote {id_lote} — {len(hist)} evento(s):")
        for i, ev in enumerate(hist, 1):
            print(f"    {i:2}. [{ev['timestamp']}] {ev['tipo_evento']}"
                  f"  (agente: {ev['agente']})")
            if ev.get("detalhes"):
                print(f"         detalhes: {ev['detalhes']}")
    else:
        print(f"  Lote {id_lote} não encontrado ou erro.")


def ver_metricas():
    resp = _enviar({"tipo_mensagem": "consulta", "tipo_consulta": "metricas"})
    if resp and resp.get("status") == "ok":
        print("\n  Métricas do servidor:")
        print(f"    Total de eventos processados : {resp['total_eventos']}")
        print(f"    Total de alertas             : {resp['total_alertas']}")
        print(f"    Tempo médio de resposta      : {resp['media_tempo_resposta_ms']} ms")
        print(f"    Conexões ativas agora        : {resp['conexoes_ativas']}")
    else:
        print("  Sem resposta ou erro.")


def menu():
    print("\n" + "="*55)
    print("  CONSOLE DE MONITORAMENTO — LOGÍSTICA DA PALMA")
    print("="*55)
    print("  1. Listar todos os lotes")
    print("  2. Ver estado atual de um lote")
    print("  3. Ver histórico completo de um lote")
    print("  4. Ver métricas de desempenho do servidor")
    print("  0. Sair")
    print("-"*55)
    return input("  Escolha: ").strip()


def main():
    print("\n  Conectando ao servidor em", HOST, ":", PORT, "...")
    ping = _enviar({"tipo_mensagem": "ping"})
    if ping:
        print("  Servidor disponível:", ping.get("timestamp"))
    else:
        print("  Servidor não disponível. Inicie server.py primeiro.")
        sys.exit(1)

    while True:
        opcao = menu()
        if opcao == "0":
            print("  Saindo.")
            break
        elif opcao == "1":
            listar_lotes()
        elif opcao == "2":
            id_lote = input("  ID do lote (ex: L001): ").strip()
            ver_estado(id_lote)
        elif opcao == "3":
            id_lote = input("  ID do lote (ex: L001): ").strip()
            ver_historico(id_lote)
        elif opcao == "4":
            ver_metricas()
        else:
            print("  Opção inválida.")
        input("\n  [Enter para continuar]")


if __name__ == "__main__":
    main()
