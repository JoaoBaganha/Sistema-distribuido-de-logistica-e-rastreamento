"""
Agente cliente para o sistema de rastreamento de lotes de palma.

Responsabilidades:
- Conectar ao servidor central via TCP
- Montar eventos em formato JSON
- Enviar eventos para o servidor
- Receber confirmação
"""

import socket
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar common
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    BUFFER_SIZE,
    criar_evento,
    formatar_log
)


class Agente:
    """
    Agente cliente que se conecta ao servidor e envia eventos.
    """

    def __init__(self, nome_agente, host=DEFAULT_HOST, porta=DEFAULT_PORT):
        """
        Inicializa o agente com seu nome e dados de conexão.

        Args:
            nome_agente: Nome identificador do agente (ex: "campo_norte")
            host: Endereço do servidor (padrão: 127.0.0.1)
            porta: Porta do servidor (padrão: 5000)
        """
        self.nome_agente = nome_agente
        self.host = host
        self.porta = porta

    def conectar_e_enviar_evento(self, id_lote, tipo_evento, detalhes=None):
        """
        Conecta ao servidor e envia um evento.

        Args:
            id_lote: Identificador do lote
            tipo_evento: Tipo do evento a ser enviado
            detalhes: Dicionário com informações adicionais (opcional)

        Returns:
            bool: True se sucesso, False caso contrário
        """
        socket_cliente = None

        try:
            # Cria o evento em formato JSON
            evento_json = criar_evento(
                id_lote=id_lote,
                tipo_evento=tipo_evento,
                origem_agente=self.nome_agente,
                detalhes=detalhes
            )

            print(formatar_log("INFO", f"Agente {self.nome_agente} inicializando..."))
            print(formatar_log("DEBUG", f"Evento preparado: {evento_json}"))

            # Cria socket TCP
            socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Conecta ao servidor
            print(
                formatar_log(
                    "INFO",
                    f"Conectando ao servidor {self.host}:{self.porta}..."
                )
            )
            socket_cliente.connect((self.host, self.porta))
            print(formatar_log("INFO", "Conectado ao servidor!"))

            # Envia o evento
            socket_cliente.sendall(evento_json.encode("utf-8"))
            print(formatar_log("INFO", "Evento enviado com sucesso!"))

            # Recebe confirmação do servidor
            confirmacao = socket_cliente.recv(BUFFER_SIZE).decode("utf-8")
            print(formatar_log("INFO", f"Confirmação do servidor: {confirmacao}"))

            return True

        except ConnectionRefusedError:
            print(
                formatar_log(
                    "ERROR",
                    f"Erro: Não conseguiu conectar ao servidor em "
                    f"{self.host}:{self.porta}. "
                    f"Verifique se o servidor está rodando."
                )
            )
            return False
        except Exception as e:
            print(formatar_log("ERROR", f"Erro ao enviar evento: {str(e)}"))
            return False
        finally:
            if socket_cliente:
                socket_cliente.close()
                print(formatar_log("DEBUG", "Socket fechado"))


def main():
    """
    Função principal para executar um agente de exemplo.
    """
    # Cria um agente de campo
    agente = Agente(nome_agente="campo_norte")

    print("="*60)
    print("AGENTE DE RASTREAMENTO - SISTEMA DE PALMA")
    print("="*60 + "\n")

    # Envia primeiro evento: criação do lote
    print(">>> Enviando evento: Criação de lote")
    sucesso = agente.conectar_e_enviar_evento(
        id_lote="L001",
        tipo_evento="criacao_lote",
        detalhes={"peso_kg": 5000, "origem": "campo"}
    )

    if sucesso:
        print(formatar_log("INFO", "Evento de criação processado com sucesso!\n"))

        # Envia segundo evento: coleta realizada
        print(">>> Enviando evento: Coleta realizada")
        sucesso = agente.conectar_e_enviar_evento(
            id_lote="L001",
            tipo_evento="coleta_realizada",
            detalhes={"peso_kg": 1200}
        )

        if sucesso:
            print(formatar_log("INFO", "Evento de coleta processado com sucesso!\n"))
    else:
        print(formatar_log("ERROR", "Falha ao enviar eventos"))
        sys.exit(1)

    print("="*60)
    print("Todos os eventos foram enviados com sucesso!")
    print("="*60)


if __name__ == "__main__":
    main()
