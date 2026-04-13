# Arquitetura Inicial — Sistema de Rastreamento de Palma

## Visão Geral da Arquitetura

O sistema segue um padrão **cliente-servidor** simples e confiável. A primeira versão foi projetada para ser minimalista, funcional e extensível.

```
┌─────────────┐                    ┌──────────────┐
│   Agente    │                    │   Servidor   │
│  (Cliente)  │                    │   Central    │
│             │                    │              │
│ Coleta e    │  ──TCP JSON──>     │ Recebe e     │
│ monta       │                    │ valida       │
│ eventos     │  <───JSON───────   │              │
│             │  (confirmação)     │ Atualiza     │
└─────────────┘                    │ estado       │
                                   └──────────────┘
```

## Componentes Principais

### 1. Servidor Central (`src/server.py`)

**Responsabilidades:**
- Inicializar socket TCP e escutar conexões na porta 5000
- Aceitar conexões de agentes
- Receber dados JSON e validar estrutura
- Armazenar eventos em histórico
- Atualizar estado atual de lotes
- Exibir logs de operação
- Encerrar graciosamente

**Estrutura de Dados:**

```python
# Histórico: lista de eventos recebidos
historico_eventos = [
    {
        "id_lote": "L001",
        "tipo_evento": "criacao_lote",
        "origem_agente": "campo_norte",
        "timestamp": "2026-04-13T10:00:00",
        "detalhes": {...}
    },
    ...
]

# Estado: dicionário indexado por id_lote
estado_lotes = {
    "L001": {
        "status_atual": "criado",
        "ultimo_timestamp": "2026-04-13T10:00:00",
        "origem_agente": "campo_norte"
    },
    ...
}
```

**Fluxo de Operação:**

1. `iniciar()`: Cria socket, faz bind e coloca em listen
2. `aguardar_conexoes()`: Loop infinito que aceita conexões
3. `processar_cliente()`: Para cada conexão:
   - Recebe dados do socket
   - Valida JSON
   - Chama `registrar_evento()`
   - Chama `atualizar_estado_lote()`
   - Envia confirmação
   - Fecha conexão
4. `finalizar()`: Encerra socket ao sair

**Mapeamento de Eventos para Status:**

| Tipo de Evento | Status Resultante |
|---|---|
| `criacao_lote` | criado |
| `coleta_realizada` | coletado |
| `carregamento_veiculo` | em_transporte |
| `saida_transporte` | em_transporte |
| `atualizacao_localizacao` | em_transporte |
| `chegada_centro` | no_centro |
| `saida_usina` | em_processamento |
| `atraso` | atrasado |
| `falha_logistica` | falho |
| `entrega_concluida` | entregue |

### 2. Agente (`src/agent.py`)

**Responsabilidades:**
- Conectar ao servidor via TCP
- Montar eventos em formato JSON
- Enviar eventos
- Receber confirmação
- Encerrar conexão

**Fluxo de Operação:**

1. Instancia `Agente(nome, host, porta)`
2. Chama `conectar_e_enviar_evento()` para cada evento
3. No método:
   - Cria JSON do evento
   - Abre socket TCP
   - Conecta ao servidor
   - Envia evento
   - Recebe confirmação
   - Fecha socket

**Exemplo de Uso:**

```python
agente = Agente("campo_norte")
agente.conectar_e_enviar_evento(
    id_lote="L001",
    tipo_evento="coleta_realizada",
    detalhes={"peso_kg": 1200}
)
```

### 3. Módulo Comum (`src/common.py`)

**Funções Utilitárias:**

- `criar_evento()`: Monta um evento em JSON
- `validar_evento()`: Valida estrutura de um evento recebido
- `formatar_log()`: Formata mensagens com timestamp

**Constantes:**

- `DEFAULT_HOST`: "127.0.0.1"
- `DEFAULT_PORT`: 5000
- `BUFFER_SIZE`: 1024 bytes
- `VALID_EVENT_TYPES`: Lista de tipos de evento válidos
- `VALID_STATUSES`: Lista de estados possíveis

## Protocolo de Comunicação

### Formato de Evento (Agente → Servidor)

```json
{
  "id_lote": "L001",
  "tipo_evento": "coleta_realizada",
  "origem_agente": "campo_norte",
  "timestamp": "2026-04-13T10:00:00",
  "detalhes": {
    "peso_kg": 1200
  }
}
```

### Confirmação de Recebimento (Servidor → Agente)

```json
{
  "status": "recebido",
  "id_lote": "L001"
}
```

### Validação

O servidor valida:
1. JSON bem formado
2. Presença de todos os campos obrigatórios
3. Tipo de evento válido

Em caso de erro, o evento é rejeitado e uma mensagem é exibida.

## Fluxo Técnico Completo

```
Servidor                          Agente
    │                               │
    │ Inicia listening              │
    │ (5000)                        │
    │                               │
    │                  Cria evento  │
    │                  conecta      │
    │ <────── SYN TCP ─────────     │
    │ SYN/ACK TCP ──────>           │
    │ <─────── ACK TCP ──────       │
    │ (conexão estabelecida)        │
    │                               │
    │ <────── EVENTO JSON ─────     │
    │ (recebe e valida)             │
    │ │ Registra evento             │
    │ │ Atualiza estado             │
    │ CONFIRMAÇÃO ──────> (recebe)  │
    │ FIN/ACK ──────>               │
    │ <─────── FIN/ACK ─────        │
    │ (conexão fechada)             │
    │                               │
```

## Decisões de Design

### 1. Python com Sockets Puros

**Razão:** Simplicidade, legibilidade e sem complexidade adicional de frameworks.

### 2. TCP em vez de UDP

**Razão:** Garantia de entrega confiável e ordenação, essencial para rastreamento logístico.

### 3. JSON em vez de Binário

**Razão:** Legibilidade, facilidade de debug e compatibilidade.

### 4. Um Agente por Vez (Inicialmente)

**Razão:** Simplificar a primeira versão. Threading será adicionado depois.

### 5. Armazenamento em Memória

**Razão:** Reduzir complexidade inicial. Persistência virá em próximas versões.

### 6. Validação Básica

**Razão:** Evitar dados malformados sem sobre-engenharia.

## Escalabilidade Futura

A arquitetura foi projetada para evolução:

1. **Threading:** Adicionar `threading.Thread` no servidor para processar múltiplos clientes
2. **Persistência:** Integrar SQLite ou PostgreSQL para histórico permanente
3. **Replicação:** Adicionar sincronização entre múltiplos servidores
4. **Fila:** Implementar fila de reenvio nos agentes
5. **Consultas:** API REST para consultar estado
6. **Monitoramento:** Métricas e alertas

## Tratamento de Erros

### Servidor

- Erro ao iniciar socket: imprime log e encerra
- Erro ao processar cliente: imprime log, continua listening
- Desconexão inesperada: fecha socket e continua

### Agente

- Servidor offline: erro de conexão, retorna False
- JSON inválido: erro de encoding, retorna False
- Socket fechado: fecha e retorna status

## Logs

O sistema usa níveis de log simples:

```
[YYYY-MM-DD HH:MM:SS] NIVEL      mensagem
[2026-04-13 10:00:00] INFO       Servidor iniciado...
[2026-04-13 10:00:01] DEBUG      Evento preparado: {...}
[2026-04-13 10:00:01] ERROR      Erro ao conectar
[2026-04-13 10:00:02] WARNING    Cliente enviou dados vazios
```

## Como Estender

### 1. Adicionar Novo Tipo de Evento

1. Adicione em `common.py` → `VALID_EVENT_TYPES`
2. Adicione mapeamento em `server.py` → `mapeamento_status`
3. Use nos agentes

### 2. Adicionar Novo Agente

```python
from src.common import criar_evento
from src.agent import Agente

agente = Agente("novo_agente")
agente.conectar_e_enviar_evento(
    id_lote="L002",
    tipo_evento="tipo_evento",
    detalhes={...}
)
```

### 3. Adicionar Threading

```python
import threading

for conexao, endereco in conexoes:
    thread = threading.Thread(
        target=self.processar_cliente,
        args=(conexao, endereco)
    )
    thread.start()
```

### 4. Adicionar Persistência

```python
import sqlite3

conn = sqlite3.connect("rastreamento.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE eventos (
        id INTEGER PRIMARY KEY,
        id_lote TEXT,
        tipo_evento TEXT,
        ...
    )
""")
```

## Conclusão

Esta arquitetura inicial estabelece uma base sólida, simples e testável para evoluir incrementalmente o sistema de rastreamento de palma. O código é intencionalmente simples para permitir aprendizado e expansão futura.
