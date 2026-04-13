# Sistema Distribuído de Logística e Rastreamento — Cadeia da Palma

## Visão Geral

Este é um sistema distribuído inicial para simular o rastreamento logístico de lotes da cadeia da palma. O sistema permite que múltiplos agentes distribuídos enviem eventos de localização ou status para um servidor central, que mantém o estado atual e o histórico de cada lote.

O projeto foi estruturado de forma incremental e extensível, servindo como base para evoluções futuras.

## Características da Versão Inicial

- **Comunicação em rede**: Usa sockets TCP para comunicação cliente-servidor confiável
- **Formato de mensagem**: JSON para estruturação e legibilidade
- **Armazenamento simples**: Em memória, com estruturas básicas de histórico e estado
- **Logs mínimos**: Exibição no terminal para depuração
- **Código organizado**: Estrutura preparada para expansão futura

## Fluxo Logístico

O sistema rastreia lotes de palma ao longo deste fluxo:

```
campo → transporte → centro de consolidação → usina
```

Cada lote pode gerar eventos como:
- Criação, coleta, carregamento, transporte, atualização de localização, chegada, saída, atraso, falha e entrega

## Requisitos

- Python 3.7 ou superior
- Não há dependências externas nesta versão inicial

## Estrutura do Projeto

```
projeto-palma-distribuido/
├── README.md                  # Este arquivo
├── requirements.txt           # Dependências Python
├── src/
│   ├── server.py             # Servidor TCP central
│   ├── agent.py              # Agente cliente (exemplo)
│   └── common.py             # Funções e constantes compartilhadas
└── docs/
    └── arquitetura-inicial.md # Documentação técnica
```

## Instalação e Execução

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

(Na versão inicial, não há dependências externas)

### 2. Executar o Servidor

Em um terminal:

```bash
python src/server.py
```

Saída esperada:
```
[2026-04-13 10:00:00] INFO     Servidor iniciado em 127.0.0.1:5000
[2026-04-13 10:00:00] INFO     Aguardando conexões...
```

### 3. Executar um Agente (em outro terminal)

```bash
python src/agent.py
```

Saída esperada:
```
============================================================
AGENTE DE RASTREAMENTO - SISTEMA DE PALMA
============================================================

>>> Enviando evento: Criação de lote
[2026-04-13 10:00:01] INFO     Agente campo_norte inicializando...
[2026-04-13 10:00:01] DEBUG    Evento preparado: {"id_lote": "L001", ...}
[2026-04-13 10:00:01] INFO     Conectando ao servidor 127.0.0.1:5000...
[2026-04-13 10:00:01] INFO     Conectado ao servidor!
[2026-04-13 10:00:01] INFO     Evento enviado com sucesso!
[2026-04-13 10:00:01] INFO     Confirmação do servidor: {"status": "recebido", ...}
[2026-04-13 10:00:01] INFO     Evento de criação processado com sucesso!

>>> Enviando evento: Coleta realizada
...
```

No servidor, você verá:
```
[2026-04-13 10:00:01] INFO     Aguardando conexão de agente...
[2026-04-13 10:00:01] INFO     Conexão recebida de ('127.0.0.1', 54321)
[2026-04-13 10:00:01] INFO     Dados recebidos: {"id_lote": "L001", ...}
[2026-04-13 10:00:01] INFO     Lote L001 atualizado: criado
[2026-04-13 10:00:01] INFO     Evento processado para lote L001
```

## Modelo de Dados

### Evento

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

### Estado de um Lote (armazenado no servidor)

```python
estado_lotes = {
    "L001": {
        "status_atual": "coleta_realizada",
        "ultimo_timestamp": "2026-04-13T10:00:00",
        "origem_agente": "campo_norte"
    }
}
```

## Próximas Evoluções

As seguintes melhorias estão planejadas:

1. Suporte para múltiplos agentes simultâneos (threading)
2. Persistência em arquivo ou banco de dados
3. Fila local nos agentes para reenvio em caso de falha
4. Mecanismo de consultas explícitas ao estado
5. Réplica de eventos ou sincronização entre servidores
6. Testes de carga e performance
7. Interface web simples para visualização
8. Protocolo de comunicação mais robusto

## Limitações da Versão Inicial

- Um agente por vez
- Armazenamento apenas em memória
- Sem criptografia
- Sem mecanismo de reenvio automático
- Sem tratamento para mensagens fora de ordem

## Arquitetura Técnica

Veja [`docs/arquitetura-inicial.md`](docs/arquitetura-inicial.md) para detalhes técnicos da arquitetura, decisões de design e fluxo de implementação.

## Contribuições

Este é um projeto acadêmico de demonstração de sistemas distribuídos.

## Licença

Este projeto é fornecido como é para fins educacionais.
