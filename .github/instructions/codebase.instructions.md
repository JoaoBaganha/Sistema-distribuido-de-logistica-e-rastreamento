---
description: Distributed Logistics and Tracking System for Palm Supply Chain - Codebase Guidelines and Architecture Documentation
applyTo: "sistema.*|server|agent|common" # Automatically loaded for files matching these patterns
---

# Codebase Instructions: Sistema Distribuído de Logística e Rastreamento

## 1. Project Overview

**Project Name:** Sistema Distribuído de Logística e Rastreamento da Cadeia da Palma  
**Language:** Python 3.7+  
**Architecture:** Client-Server (Distributed Agent-Based)  
**Domain:** Supply Chain Management — Palm (Palma) Agribusiness  
**Status:** Version 1.0 (Initial Implementation)

### Purpose

This distributed system simulates real-time tracking of palm batches through a supply chain network. It demonstrates inter-process communication via TCP sockets using JSON message format, designed to be extensible for future enhancements such as multi-agent support, persistent storage, and advanced state management.

### Supply Chain Flow

```
campo (field) → transporte (transport) → centro de consolidação (consolidation center) → usina (processing plant)
```

Each stage can emit events that update batch status in real-time.

---

## 2. Architecture & Design Patterns

### 2.1 Client-Server Model

The system uses a **synchronous client-server** architecture:

- **Clients (Agentes):** Represent distributed nodes that send tracking events
- **Server (Servidor Central):** Central hub that receives, validates, and aggregates events
- **Communication:** TCP sockets with JSON payloads (synchronous request-response)

```
┌──────────────────────────────────────────────────────────┐
│                    Servidor Central                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Sistema de Histórico de Eventos                   │  │
│  │  - Registra cada evento recebido                   │  │
│  │  - Mantém sequência temporal                       │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Estado de Lotes (Cache em Memória)                │  │
│  │  - Status atual de cada lote (L001, L002, etc)     │  │
│  │  - Último timestamp conhecido                      │  │
│  │  - Agente responsável                              │  │
│  └────────────────────────────────────────────────────┘  │
│                        ↑ ↓                                │
│                 TCP Port 5000                            │
│                        ↑ ↓                                │
└──────────────────────────────────────────────────────────┘
     ↑              ↑              ↑
  Agente        Agente         Agente
 (campo)     (transporte)    (centro)
```

### 2.2 Key Design Decisions

| Decision | Rationale | Future Evolution |
|----------|-----------|------------------|
| **Single connection per event** | Simplicity in v1; stateless | Connection pooling or persistent connections |
| **In-memory storage** | Fast, minimal overhead | PostgreSQL/MongoDB for persistence |
| **Synchronous only** | Simpler protocol | Async with message queues (RabbitMQ/Kafka) |
| **No authentication** | Prototype phase | OAuth2 or token-based auth |
| **Sequential client processing** | Avoid complexity | Thread pool for concurrent handling |

---

## 3. File Structure & Responsibilities

### 3.1 Project Layout

```
sistema-distribuido-de-logistica-e-rastreamento/
├── README.md                           # User-facing project overview
├── instructions.md                     # Functional requirements (domain level)
├── requirements.txt                    # Python dependencies (currently empty)
├── docs/
│   └── arquitetura-inicial.md          # Technical architecture deep-dive
├── .github/
│   └── instructions/
│       └── codebase.instructions.md    # This file — coding guidelines
└── src/
    ├── server.py                       # Central server implementation
    ├── agent.py                        # Client agent implementation
    └── common.py                       # Shared utilities & constants
```

### 3.2 Module Responsibilities

#### **src/server.py** — Central Server

**Class:** `ServidorCentral`

**Responsibilities:**
- Initialize TCP socket, bind to host:port, and enter listening state
- Accept incoming connections from agents (currently sequential)
- Receive and validate JSON event payloads
- Store events in memory (append-only history)
- Update batch state based on event type
- Send acknowledgment responses
- Maintain two data structures:
  - `historico_eventos[]`: Complete event log (audit trail)
  - `estado_lotes{}`: Current state cache (key: id_lote, value: status info)

**Key Methods:**
- `__init__(host, porta)` — Initialization
- `iniciar()` — Bind socket and enter listening state
- `aguardar_conexoes()` — Main loop; accepts one client at a time
- `processar_cliente(conexao, endereco)` — Handle single connection
- `registrar_evento(evento)` — Append to history
- `atualizar_estado_lote(evento)` — Update state cache using event-to-status mapping
- `exibir_historico(id_lote=None)` — Debug utility

**Entry Point:**
```python
if __name__ == "__main__":
    servidor = ServidorCentral()
    servidor.iniciar()
    servidor.aguardar_conexoes()
```

#### **src/agent.py** — Client Agent

**Class:** `Agente`

**Responsibilities:**
- Identify itself with a unique name (e.g., "campo_norte")
- Construct JSON events using `criar_evento()`
- Connect to server via TCP, send event, receive confirmation
- Handle connection errors gracefully
- Clean up socket resources

**Key Methods:**
- `__init__(nome_agente, host, porta)` — Initialization
- `conectar_e_enviar_evento(id_lote, tipo_evento, detalhes)` — Full client lifecycle

**Entry Point:**
```python
if __name__ == "__main__":
    agente = Agente(nome_agente="campo_norte")
    agente.conectar_e_enviar_evento(
        id_lote="L001",
        tipo_evento="criacao_lote",
        detalhes={"peso_kg": 5000}
    )
```

#### **src/common.py** — Shared Utilities

**Constants:**
- `DEFAULT_HOST = "127.0.0.1"` — Localhost (change for remote deployment)
- `DEFAULT_PORT = 5000` — Well-known TCP port for this service
- `BUFFER_SIZE = 1024` — Maximum bytes per socket recv()
- `VALID_EVENT_TYPES` — Whitelist of acceptable event types (10 types)
- `VALID_STATUSES` — Whitelist of batch states (8 states)

**Functions:**
- `criar_evento(id_lote, tipo_evento, origem_agente, detalhes=None)` → JSON string
- `validar_evento(evento_json)` → (bool success, dict evento, str error)
- `formatar_log(nivel, mensagem)` → formatted string with timestamp

**Design Pattern:** Centralized validation and logging reduce duplication and ensure consistency.

---

## 4. Code Organization Guidelines

### 4.1 Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Variáveis | `snake_case` | `id_lote`, `historico_eventos` |
| Constantes | `UPPER_SNAKE_CASE` | `DEFAULT_PORT`, `BUFFER_SIZE` |
| Classes | `PascalCase` | `ServidorCentral`, `Agente` |
| Métodos/Funções | `snake_case` | `iniciar()`, `processar_cliente()` |
| Private members | `_prefixed_name` | `_socket_interno` |

### 4.2 Documentation Standards

- **Module docstring:** Purpose, responsibilities, key components
- **Class docstring:** Role and lifecycle
- **Method docstring:** Args, Returns, Raises sections using Google style
- **Error handling:** All exceptions logged with context

**Example:**
```python
def validar_evento(evento_json):
    """
    Valida a estrutura de um evento JSON recebido.

    Args:
        evento_json: String JSON com o evento

    Returns:
        Tupla (sucesso: bool, evento_dict: dict, erro: str)
        - sucesso: True se validação passou
        - evento_dict: Dicionário parseado ou None se erro
        - erro: Descrição do erro ou None se sucesso
    """
```

### 4.3 Coding Style

- **Python Version:** 3.7+ (use f-strings, avoid old % formatting)
- **Line Length:** No strict limit; prefer readability
- **Imports:** Standard library first, then local modules
- **Error Handling:** Try-except with logging, graceful degradation
- **Resource Cleanup:** Always use try-finally for sockets

---

## 5. Event System & Data Models

### 5.1 Event Structure

Every event follows this JSON schema:

```json
{
  "id_lote": "L001",
  "tipo_evento": "criacao_lote",
  "origem_agente": "campo_norte",
  "timestamp": "2026-04-13T10:00:00.123456",
  "detalhes": {
    "peso_kg": 5000,
    "origem": "campo"
  }
}
```

**Invariants:**
- `id_lote` and `tipo_evento` are mandatory
- `timestamp` is auto-generated; never trusted from external source
- `detalhes` is always present (empty dict if no additional data)

### 5.2 Event Type Reference

| Event Type | Trigger | Resulting Status | Typical Detalhes |
|---|---|---|---|
| `criacao_lote` | Batch created | `criado` | `{"peso_kg": int, "origem": str}` |
| `coleta_realizada` | Harvested/collected | `coletado` | `{"peso_kg": int}` |
| `carregamento_veiculo` | Loaded onto vehicle | `em_transporte` | `{"veiculo_id": str}` |
| `saida_transporte` | Left origin point | `em_transporte` | `{"destino": str}` |
| `atualizacao_localizacao` | Location update | `em_transporte` | `{"lat": float, "lng": float}` |
| `chegada_centro` | Arrived at center | `no_centro` | `{"centro_id": str}` |
| `saida_usina` | Left for processing | `em_processamento` | `{"usina_id": str}` |
| `atraso` | Delayed | `atrasado` | `{"motivo": str, "horas": int}` |
| `falha_logistica` | Failure occurred | `falho` | `{"motivo": str}` |
| `entrega_concluida` | Delivered | `entregue` | `{"destino_final": str}` |

### 5.3 Batch State Model

Server maintains `estado_lotes[id_lote]`:

```python
estado_lotes = {
    "L001": {
        "status_atual": "em_transporte",
        "ultimo_timestamp": "2026-04-13T10:00:15",
        "origem_agente": "campo_norte"
    }
}
```

**State Transition Rules:**
- States are **overwritten** on each event (not append-only)
- Most recent event type determines status
- No explicit state machine validation (v1 simplicity)

---

## 6. Development Guidelines

### 6.1 Adding New Event Types

**Steps:**

1. Add event type string to `VALID_EVENT_TYPES` in `common.py`
2. (Optional) Add corresponding status to `VALID_STATUSES` if needed
3. Update `atualizar_estado_lote()` mapeamento_status dict in `server.py`
4. Document in Event Type Reference (Section 5.2)

**Example:**
```python
# In common.py
VALID_EVENT_TYPES = [
    "criacao_lote",
    # ... existing types ...
    "atualizacao_qualidade",  # NEW
]

# In server.py, atualizar_estado_lote()
mapeamento_status = {
    # ... existing mappings ...
    "atualizacao_qualidade": "em_inspecao",  # NEW mapping
}
```

### 6.2 Extending for Multiple Concurrent Agents

**Limitation in v1:** Server processes one agent at a time.

**To support concurrent connections:**

1. Import `threading`
2. Change `listen(1)` to `listen(10)` for backlog
3. In `aguardar_conexoes()`, spawn thread for each connection
4. Add thread-safe locks to `historico_eventos` and `estado_lotes`
5. Test with multiple concurrent agents

### 6.3 Persistence (Future Version)

**Current:** In-memory only; data lost when server stops.

**To add database persistence:**

1. Create `src/persistence.py` with database repository
2. Add `cargar_historico()` and `guardar_evento()` methods
3. Integrate with server initialization and event processing

### 6.4 Testing the System

**Manual test flow:**

```bash
# Terminal 1: Start server
python src/server.py

# Terminal 2-N: Run agents
python src/agent.py

# Expected: Agent connects, sends event, receives confirmation, closes
```

**Validation checklist:**
- ✅ Server starts without errors
- ✅ Agent connects on first try
- ✅ Multiple events from same agent are processed
- ✅ Multiple agents can send (sequential in v1)
- ✅ Event validation rejects invalid JSON
- ✅ Event validation rejects unknown event types
- ✅ Ctrl+C gracefully shuts down

---

## 7. Communication Protocol

### 7.1 Request Flow (Agent → Server)

1. Agent creates socket
2. Agent connects to server (host, port)
3. Agent sends JSON event as single string (UTF-8 encoded)
4. Server receives and parses
5. Server validates against schema and event types
6. Server updates history and state
7. Server sends confirmation: `{"status": "recebido", "id_lote": "L001"}`
8. Agent receives confirmation and displays
9. Both close socket

### 7.2 Error Handling

| Error Scenario | Agent Behavior | Server Behavior |
|---|---|---|
| Connection refused | Print error, exit | (server not running) |
| Invalid JSON | Server rejects, closes | Log error, continue listening |
| Unknown event type | Server rejects, closes | Log validation error |
| Empty data | Server logs warning | (agent sent nothing) |

---

## 8. Performance & Scalability Notes

### Current Limitations (v1)

- **Throughput:** ~1 event per second (sequential processing)
- **Latency:** ~10-50ms per event (network + parsing + state update)
- **Memory:** Unbounded growth of `historico_eventos` (no cleanup)
- **Availability:** No failover; single point of failure

### Scaling Roadmap

| Concern | v1 Status | v2+ Solution |
|---|---|---|
| **Concurrency** | Sequential | Thread pool or async/await |
| **Storage** | In-memory | PostgreSQL + event sourcing |
| **Redundancy** | None | Multi-master replication |
| **Monitoring** | Printf logs | ELK Stack or Prometheus |
| **API** | TCP sockets | gRPC or REST/HTTP |

---

## 9. Common Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| "Address already in use" on server start | Previous instance still holding port | Wait 1-2 min or restart terminal |
| "Connection refused" on agent run | Server not started | Start server first in separate terminal |
| "JSON decode error" in server | Agent sent malformed JSON | Check `criar_evento()` output; verify encoding |
| Events not appearing in history | Network issue or silent error | Check server logs for ERROR entries |
| Slow response times | Network latency or server overloaded | Monitor with timestamps; profile code |

---

## 10. Revision History

| Date | Version | Author | Changes |
|---|---|---|---|
| 2026-04-13 | 1.0 | Initial Implementation | TCP socket comm; JSON events; in-memory state |

---

**Last updated:** 13 de abril de 2026  
**Next review:** Before implementing v2 features (concurrency, persistence)