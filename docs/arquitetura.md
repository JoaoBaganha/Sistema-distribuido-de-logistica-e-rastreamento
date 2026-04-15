# Arquitetura Distribuída — Sistema de Logística da Palma

## Visão Geral

Arquitetura **cliente-servidor multi-tier** com suporte a múltiplos agentes simultâneos.

```
┌─────────────────────────────────────────────────────────┐
│                     NÍVEL 1 — AGENTES                   │
│                                                         │
│  [campo_norte]  [transportadora_1]  [usina_belem]       │
│      (agent.py)      (agent.py)        (agent.py)       │
│         │                │                │             │
│         └────────────────┴────────────────┘             │
│                          │ TCP (sockets)                 │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                NÍVEL 2 — SERVIDOR CENTRAL                │
│                       (server.py)                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Dispatcher  │  │  Processador │  │  Persistência  │  │
│  │  (threading) │  │  de Eventos  │  │  (lotes.json)  │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│     Estado atual     Histórico         Métricas          │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               NÍVEL 3 — CONSOLE OPERADOR                 │
│                       (client.py)                        │
│  Consultas: estado, histórico, listagem, métricas        │
└──────────────────────────────────────────────────────────┘
```

## Protocolo de Comunicação

- **Transporte**: TCP (confiabilidade garantida — crítico para rastreamento)
- **Serialização**: JSON com encoding UTF-8
- **Framing**: Header de 8 bytes (big-endian) com tamanho do payload
- **Formato de mensagem de evento**:

```json
{
  "tipo_mensagem": "evento",
  "id_lote": "L001",
  "tipo_evento": "coleta_realizada",
  "origem_agente": "campo_norte",
  "timestamp": "2026-04-14T10:00:00",
  "detalhes": { "peso_kg": 1200 }
}
```

## Por que TCP e não UDP?

| Critério               | TCP ✓                        | UDP ✗                        |
|------------------------|------------------------------|------------------------------|
| Entrega garantida      | Sim                          | Não                          |
| Ordem das mensagens    | Garantida                    | Não garantida                |
| Rastreamento logístico | Essencial (sem perda)        | Inaceitável perder eventos   |
| Complexidade           | Gerenciado pelo SO           | Retransmissão manual         |

## Mecanismos de Sistemas Distribuídos Implementados

| Mecanismo                   | Onde                          |
|-----------------------------|-------------------------------|
| Concorrência (threading)    | server.py — 1 thread/conexão  |
| Fila de reenvio             | agent.py — retry automático   |
| Persistência de estado      | server.py — lotes.json        |
| Detecção de anomalia/alerta | server.py — tipos de evento   |
| Consultas de estado         | client.py + server.py         |
| Métricas de desempenho      | server.py + teste_carga.py    |
| Tolerância a falha de nó    | agent.py — fila + MAX_RETRIES |

## Fluxo Logístico

```
campo → transporte → centro_consolidacao → usina
```

Eventos possíveis em cada etapa:

- **Campo**: lote_criado, coleta_realizada, carregamento_iniciado
- **Transporte**: em_transporte, atualizacao_localizacao, atraso_registrado, falha_registrada
- **Centro**: chegada_centro, saida_centro
- **Usina**: chegada_usina, entrega_concluida

## Tolerância a Falhas

- Agente sem servidor: eventos enfileirados localmente → reenvio automático a cada 5s
- Nó que para de enviar: servidor mantém último estado conhecido + timestamp
- Servidor reiniciado: estado restaurado do arquivo `logs/lotes.json`

## Limitações

- Sem autenticação de agentes
- Servidor único (sem réplica de servidor)
- Armazenamento em arquivo JSON (sem banco relacional)
