"""
Módulo comum com constantes e funções utilitárias compartilhadas
entre servidor e agentes do sistema de rastreamento de palma.
"""

import json
from datetime import datetime

# Configuração de rede
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
BUFFER_SIZE = 1024

# Tipos de evento válidos
VALID_EVENT_TYPES = [
    "criacao_lote",
    "coleta_realizada",
    "carregamento_veiculo",
    "saida_transporte",
    "atualizacao_localizacao",
    "chegada_centro",
    "saida_usina",
    "atraso",
    "falha_logistica",
    "entrega_concluida"
]

# Estados possíveis de um lote
VALID_STATUSES = [
    "criado",
    "coletado",
    "em_transporte",
    "no_centro",
    "em_processamento",
    "entregue",
    "atrasado",
    "falho"
]


def criar_evento(id_lote, tipo_evento, origem_agente, detalhes=None):
    """
    Cria um evento estruturado em formato JSON.

    Args:
        id_lote: Identificador único do lote
        tipo_evento: Tipo do evento (deve estar em VALID_EVENT_TYPES)
        origem_agente: Identificação do agente que originou o evento
        detalhes: Dicionário com informações adicionais (opcional)

    Returns:
        String JSON do evento estruturado
    """
    if detalhes is None:
        detalhes = {}

    evento = {
        "id_lote": id_lote,
        "tipo_evento": tipo_evento,
        "origem_agente": origem_agente,
        "timestamp": datetime.now().isoformat(),
        "detalhes": detalhes
    }

    return json.dumps(evento, ensure_ascii=False)


def validar_evento(evento_json):
    """
    Valida a estrutura de um evento JSON recebido.

    Args:
        evento_json: String JSON com o evento

    Returns:
        Tupla (sucesso: bool, evento_dict: dict, erro: str)
    """
    try:
        evento = json.loads(evento_json)
    except json.JSONDecodeError as e:
        return False, None, f"JSON inválido: {str(e)}"

    # Validação de campos obrigatórios
    campos_obrigatorios = ["id_lote", "tipo_evento", "origem_agente", "timestamp"]
    for campo in campos_obrigatorios:
        if campo not in evento:
            return False, None, f"Campo obrigatório ausente: {campo}"

    # Validação de tipo_evento
    if evento["tipo_evento"] not in VALID_EVENT_TYPES:
        return False, None, f"Tipo de evento inválido: {evento['tipo_evento']}"

    return True, evento, None


def formatar_log(nivel, mensagem):
    """
    Formata uma mensagem de log com timestamp e nível.

    Args:
        nivel: Nível do log (INFO, WARNING, ERROR, etc)
        mensagem: Conteúdo da mensagem

    Returns:
        String formatada para exibição
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {nivel:8} {mensagem}"
