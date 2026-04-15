# Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

## Estrutura do Projeto

```
logistica_palma/
├── README.md
├── requirements.txt
├── src/
│   ├── common.py          # Funções compartilhadas (protocolo, logger)
│   ├── server.py          # Servidor TCP central (multi-threaded)
│   ├── agent.py           # Agente distribuído (com fila de reenvio)
│   ├── client.py          # Console interativo de consultas
│   └── teste_carga.py     # Testes experimentais de desempenho
├── docs/
│   └── arquitetura.md     # Documentação técnica completa
└── logs/
    └── lotes.json         # Gerado automaticamente (persistência)
```

## Como Executar no VS Code

### Pré-requisito
- Python 3.7 ou superior instalado
- Sem dependências externas (apenas stdlib)

---

### Passo 1 — Abrir o projeto

Abra a pasta `logistica_palma` no VS Code:
```
Arquivo → Abrir Pasta → selecione logistica_palma/
```

---

### Passo 2 — Abrir terminais (você precisará de pelo menos 3)

No VS Code: `Terminal → Novo Terminal` (repita para cada terminal necessário).

---

### Passo 3 — Iniciar o servidor (Terminal 1)

```bash
python src/server.py
```

Saída esperada:
```
[2026-04-14 10:00:00] INFO     Servidor iniciado em 127.0.0.1:5000
[2026-04-14 10:00:00] INFO     Aguardando conexões... (Ctrl+C para encerrar)
```

---

### Passo 4 — Executar agentes (Terminal 2, 3, ...)

Agente do campo (lote L001):
```bash
python src/agent.py --nome campo_norte --tipo campo --lote L001 --modo campo
```

Agente da usina (lote L001, depois do campo ter enviado):
```bash
python src/agent.py --nome usina_belem --tipo usina --lote L001 --modo usina
```

Agente de outro campo (lote diferente, simultâneo):
```bash
python src/agent.py --nome campo_sul --tipo campo --lote L002 --modo campo
```

---

### Passo 5 — Consultar o sistema (Terminal 4)

```bash
python src/client.py
```

Menu interativo:
```
1. Listar todos os lotes
2. Ver estado atual de um lote
3. Ver histórico completo de um lote
4. Ver métricas de desempenho do servidor
0. Sair
```

---

### Passo 6 — Testes experimentais (Terminal 5)

Com o servidor rodando:
```bash
python src/teste_carga.py
```

Executa 3 cenários automaticamente e exibe: tempo mínimo, máximo, médio, desvio padrão e vazão.

---

## Testando Tolerância a Falhas

### Simulando servidor offline
1. Inicie o servidor normalmente
2. Inicie um agente
3. **Durante a execução do agente**, pressione Ctrl+C no servidor
4. O agente exibirá: *"Servidor indisponível — enfileirado para reenvio"*
5. Reinicie o servidor: `python src/server.py`
6. Em até 5 segundos, o agente reenvia automaticamente

### Verificando persistência
1. Execute agentes normalmente
2. Encerre o servidor (Ctrl+C)
3. Reinicie o servidor
4. Use `client.py` → os lotes ainda estão lá (carregados de `logs/lotes.json`)

---

## Parâmetros do Agente

| Parâmetro | Valores               | Descrição                     |
|-----------|-----------------------|-------------------------------|
| --nome    | qualquer string       | Identificador do agente       |
| --tipo    | campo/transportadora/centro/usina | Tipo do nó      |
| --lote    | L001, L002, ...       | ID do lote rastreado          |
| --modo    | campo / usina         | Sequência de eventos a enviar |
