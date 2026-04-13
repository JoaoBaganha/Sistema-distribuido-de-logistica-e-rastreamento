# Especificação Inicial — Sistema Distribuído de Logística e Rastreamento da Cadeia da Palma

## 1. Objetivo

Desenvolver um sistema distribuído inicial para simular o rastreamento logístico de lotes da cadeia da palma.

O sistema deve permitir que múltiplos agentes distribuídos enviem eventos de localização ou status para um servidor central, que mantém o estado atual e o histórico de cada lote.

Esta versão inicial deve ser simples, pequena e incremental, servindo como base para evoluções futuras.

---

## 2. Escopo da versão inicial

A primeira versão não precisa implementar toda a complexidade do projeto final.

O foco inicial será:

* estabelecer comunicação em rede entre processos usando sockets;
* representar um agente enviando um evento para um servidor;
* registrar o evento recebido;
* manter um estado mínimo de um lote;
* estruturar o projeto para posterior expansão.

Não é prioridade nesta etapa:

* interface gráfica;
* banco de dados;
* autenticação;
* múltiplos protocolos ao mesmo tempo;
* consistência avançada;
* tolerância a falhas completa.

---

## 3. Contexto funcional

O domínio escolhido é a cadeia fictícia da palma.

Fluxo logístico simplificado:

**campo → transporte → centro de consolidação → usina**

O sistema irá rastrear lotes de palma ao longo desse fluxo.

Cada lote poderá gerar eventos como:

* criação do lote;
* coleta realizada;
* carregamento no veículo;
* saída para transporte;
* atualização de localização;
* chegada ao centro;
* saída para usina;
* atraso;
* falha logística;
* entrega concluída.

---

## 4. Arquitetura inicial

A arquitetura inicial será do tipo **cliente-servidor**.

### Componentes

#### 4.1. Agente

Processo cliente responsável por simular um nó distribuído do sistema.

Exemplos de agentes futuros:

* agente de campo;
* agente de transporte;
* agente de centro de consolidação.

Na versão inicial, basta um único agente.

Responsabilidades:

* montar um evento em JSON;
* abrir conexão TCP com o servidor;
* enviar o evento;
* encerrar a conexão.

#### 4.2. Servidor central

Processo principal responsável por receber eventos e atualizar o estado do sistema.

Responsabilidades:

* abrir socket TCP e escutar conexões;
* receber eventos enviados pelos agentes;
* interpretar JSON recebido;
* registrar o evento em memória;
* atualizar estado atual do lote;
* exibir logs simples no terminal.

---

## 5. Tecnologia inicial recomendada

* **Linguagem:** Python 3
* **Comunicação:** sockets TCP
* **Formato de mensagem:** JSON
* **Concorrência inicial:** simples; evoluir depois para `threading` ou `asyncio`

### Justificativa

Python permite evolução rápida e reduz complexidade inicial.
TCP é a escolha mais simples para a primeira versão porque garante entrega confiável e ordenada, o que facilita o desenvolvimento e a defesa técnica da solução.
JSON é adequado por ser simples, legível e fácil de serializar/deserializar.

---

## 6. Estrutura inicial do repositório

```text
projeto-palma-distribuido/
├── README.md
├── requirements.txt
├── src/
│   ├── server.py
│   ├── agent.py
│   └── common.py
└── docs/
    └── arquitetura-inicial.md
```

### Descrição dos arquivos

* `README.md`: visão geral do projeto.
* `requirements.txt`: dependências, se necessário.
* `src/server.py`: servidor TCP principal.
* `src/agent.py`: agente cliente que envia eventos.
* `src/common.py`: constantes e funções utilitárias compartilhadas.
* `docs/arquitetura-inicial.md`: notas sobre arquitetura e decisões.

---

## 7. Modelo inicial de dados

### 7.1. Lote

Representa a unidade rastreada no sistema.

Campos mínimos:

* `id_lote`
* `origem`
* `destino`
* `status_atual`
* `ultimo_timestamp`

### 7.2. Evento

Representa uma ocorrência recebida pelo sistema.

Campos mínimos:

* `id_lote`
* `tipo_evento`
* `origem_agente`
* `timestamp`
* `detalhes`

### 7.3. Exemplo de evento

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

---

## 8. Requisitos funcionais da versão inicial

### RF-01

O agente deve conseguir se conectar ao servidor via TCP.

### RF-02

O agente deve conseguir enviar um evento em formato JSON.

### RF-03

O servidor deve receber e interpretar o JSON enviado.

### RF-04

O servidor deve registrar o evento em memória.

### RF-05

O servidor deve atualizar o estado atual do lote com base no último evento recebido.

### RF-06

O servidor deve permitir, ao menos internamente, consulta ao histórico recebido e ao estado atual do lote.

---

## 9. Requisitos não funcionais da versão inicial

### RNF-01

O sistema deve ser simples de executar localmente.

### RNF-02

O código deve ser organizado para permitir evolução incremental.

### RNF-03

As mensagens trocadas pela rede devem ser legíveis e padronizadas.

### RNF-04

O servidor deve registrar logs mínimos para depuração.

---

## 10. Fluxo técnico mínimo esperado

### Passo 1

Executar `server.py` para abrir a porta e aguardar conexões.

### Passo 2

Executar `agent.py` para montar e enviar um evento.

### Passo 3

O servidor recebe a mensagem, converte de JSON para estrutura interna e imprime confirmação.

### Passo 4

O servidor salva o evento em uma lista em memória.

### Passo 5

O servidor atualiza o estado atual do lote.

---

## 11. Estado inicial em memória

Na primeira versão, o servidor pode manter estruturas simples em memória.

Exemplo conceitual:

* `historico_eventos`: lista de eventos recebidos
* `estado_lotes`: dicionário indexado por `id_lote`

Exemplo:

```python
historico_eventos = []
estado_lotes = {
    "L001": {
        "status_atual": "coleta_realizada",
        "ultimo_timestamp": "2026-04-13T10:00:00"
    }
}
```

---

## 12. Limitações assumidas nesta fase

Nesta etapa inicial, é aceitável assumir que:

* há apenas um servidor central;
* há apenas um agente ativo por vez;
* o armazenamento é apenas em memória;
* não há criptografia;
* não há replicação real ainda;
* não há tratamento sofisticado para mensagens duplicadas ou fora de ordem.

Esses pontos poderão ser evoluídos nas próximas iterações.

---

## 13. Próximas evoluções previstas

Depois que a primeira troca de mensagens funcionar, as próximas evoluções naturais são:

1. múltiplos agentes simultâneos;
2. múltiplos tipos de evento;
3. histórico por lote;
4. consultas explícitas ao estado atual;
5. persistência em arquivo ou banco de dados;
6. fila local para reenvio em caso de falha;
7. réplica de eventos ou estado;
8. mecanismo simples de consistência com sequência de eventos;
9. testes de carga com aumento de agentes e eventos.

---

## 14. Critério de pronto da versão inicial

A versão inicial será considerada pronta quando:

* o servidor estiver executando e ouvindo conexões;
* o agente conseguir se conectar ao servidor;
* um evento JSON for enviado com sucesso;
* o servidor conseguir exibir o evento recebido;
* o servidor registrar o evento em memória;
* o estado atual do lote for atualizado corretamente.

---

## 15. Prompt de implementação para Claude

Implementar a primeira versão de um sistema distribuído em Python para rastreamento logístico da cadeia fictícia da palma.

Requisitos desta implementação:

* usar Python 3;
* usar sockets TCP;
* criar os arquivos `src/server.py`, `src/agent.py` e `src/common.py`;
* o servidor deve escutar uma porta TCP e aceitar uma conexão por vez;
* o agente deve se conectar ao servidor e enviar um evento JSON;
* o servidor deve fazer o parse do JSON, imprimir o conteúdo recebido, armazenar o evento em memória e atualizar o estado atual do lote;
* usar código simples, organizado e comentado;
* evitar frameworks;
* priorizar clareza e funcionamento básico;
* incluir instruções de execução no final.

---

## 16. Observação final

O objetivo desta especificação não é fechar a solução completa, mas criar uma base técnica mínima e correta para iniciar o projeto sem excesso de complexidade.
