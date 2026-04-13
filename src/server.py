"""
Servidor central para o sistema de rastreamento de lotes de palma.

Responsabilidades:
- Escutar conexões TCP na porta padrão
- Receber eventos de agentes
- Interpretar e validar eventos JSON
- Armazenar eventos em histórico
- Manter estado atual de lotes
- Exibir logs de operação
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
    validar_evento,
    formatar_log
)


class ServidorCentral:
    """
    Servidor central que recebe e processa eventos de agentes.
    """

    def __init__(self, host=DEFAULT_HOST, porta=DEFAULT_PORT):
        """
        Inicializa o servidor com host e porta.

        Args:
            host: Endereço IP para escutar (padrão: 127.0.0.1)
            porta: Porta TCP (padrão: 5000)
        """
        self.host = host
        self.porta = porta
        self.socket = None

        # Estruturas de memória para armazenar estado
        self.historico_eventos = []
        self.estado_lotes = {}

    def iniciar(self):
        """
        Cria o socket, faz bind e coloca em modo listening.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.porta))
            self.socket.listen(1)

            print(formatar_log("INFO", f"Servidor iniciado em {self.host}:{self.porta}"))
            print(formatar_log("INFO", "Aguardando conexões..."))

        except Exception as e:
            print(formatar_log("ERROR", f"Erro ao iniciar servidor: {str(e)}"))
            raise

    def aguardar_conexoes(self):
        """
        Loop principal que aguarda conexões de agentes.
        Processa um agente por vez (versão inicial simplificada).
        """
        try:
            while True:
                print(formatar_log("INFO", "Aguardando conexão de agente..."))
                conexao, endereco = self.socket.accept()

                print(formatar_log("INFO", f"Conexão recebida de {endereco}"))
                self.processar_cliente(conexao, endereco)

        except KeyboardInterrupt:
            print(formatar_log("INFO", "Servidor finalizado pelo usuário"))
        except Exception as e:
            print(formatar_log("ERROR", f"Erro no loop principal: {str(e)}"))
        finally:
            self.finalizar()

    def processar_cliente(self, conexao, endereco):
        """
        Processa dados recebidos de um cliente.

        Args:
            conexao: Socket da conexão com o cliente
            endereco: Tupla (host, porta) do cliente
        """
        try:
            # Recebe dados do cliente
            dados = conexao.recv(BUFFER_SIZE).decode("utf-8")

            if not dados:
                print(formatar_log("WARNING", f"Cliente {endereco} enviou dados vazios"))
                return

            print(formatar_log("INFO", f"Dados recebidos: {dados}"))

            # Valida o evento recebido
            sucesso, evento, erro = validar_evento(dados)

            if not sucesso:
                print(formatar_log("ERROR", f"Erro ao validar evento: {erro}"))
                conexao.close()
                return

            # Processa o evento válido
            self.registrar_evento(evento)
            self.atualizar_estado_lote(evento)

            # Envia confirmação ao cliente
            resposta = '{"status": "recebido", "id_lote": "' + evento["id_lote"] + '"}'
            conexao.sendall(resposta.encode("utf-8"))

            print(formatar_log("INFO", f"Evento processado para lote {evento['id_lote']}"))

        except Exception as e:
            print(formatar_log("ERROR", f"Erro ao processar cliente: {str(e)}"))
        finally:
            conexao.close()

    def registrar_evento(self, evento):
        """
        Registra um evento no histórico em memória.

        Args:
            evento: Dicionário com dados do evento
        """
        self.historico_eventos.append(evento)
        print(
            formatar_log(
                "DEBUG",
                f"Evento registrado. Total de eventos: {len(self.historico_eventos)}"
            )
        )

    def atualizar_estado_lote(self, evento):
        """
        Atualiza o estado atual de um lote baseado no evento recebido.

        Args:
            evento: Dicionário com dados do evento
        """
        id_lote = evento["id_lote"]

        # Mapeia tipo_evento para status_atual
        mapeamento_status = {
            "criacao_lote": "criado",
            "coleta_realizada": "coletado",
            "carregamento_veiculo": "em_transporte",
            "saida_transporte": "em_transporte",
            "atualizacao_localizacao": "em_transporte",
            "chegada_centro": "no_centro",
            "saida_usina": "em_processamento",
            "atraso": "atrasado",
            "falha_logistica": "falho",
            "entrega_concluida": "entregue"
        }

        novo_status = mapeamento_status.get(
            evento["tipo_evento"],
            "desconhecido"
        )

        # Atualiza ou cria a entrada do lote
        self.estado_lotes[id_lote] = {
            "status_atual": novo_status,
            "ultimo_timestamp": evento["timestamp"],
            "origem_agente": evento["origem_agente"]
        }

        print(
            formatar_log(
                "INFO",
                f"Lote {id_lote} atualizado: {novo_status}"
            )
        )

    def exibir_historico(self, id_lote=None):
        """
        Exibe o histórico de eventos, opcionalmente filtrado por lote.

        Args:
            id_lote: Se fornecido, exibe apenas eventos desse lote
        """
        print("\n" + "="*60)
        print("HISTÓRICO DE EVENTOS")
        print("="*60)

        eventos_a_exibir = self.historico_eventos

        if id_lote:
            eventos_a_exibir = [e for e in self.historico_eventos if e["id_lote"] == id_lote]

        if not eventos_a_exibir:
            print("Nenhum evento encontrado.")
        else:
            for idx, evento in enumerate(eventos_a_exibir, 1):
                print(f"\n[{idx}] Lote: {evento['id_lote']}")
                print(f"    Tipo: {evento['tipo_evento']}")
                print(f"    Agente: {evento['origem_agente']}")
                print(f"    Timestamp: {evento['timestamp']}")
                if evento.get("detalhes"):
                    print(f"    Detalhes: {evento['detalhes']}")

        print("="*60 + "\n")

    def exibir_estado_lotes(self):
        """
        Exibe o estado atual de todos os lotes.
        """
        print("\n" + "="*60)
        print("ESTADO ATUAL DOS LOTES")
        print("="*60)

        if not self.estado_lotes:
            print("Nenhum lote registrado.")
        else:
            for id_lote, estado in self.estado_lotes.items():
                print(f"\nLote: {id_lote}")
                print(f"  Status: {estado['status_atual']}")
                print(f"  Último timestamp: {estado['ultimo_timestamp']}")
                print(f"  Origem do último evento: {estado['origem_agente']}")

        print("="*60 + "\n")

    def finalizar(self):
        """
        Encerra o servidor and fecha o socket.
        """
        if self.socket:
            self.socket.close()
        print(formatar_log("INFO", "Servidor encerrado"))


def main():
    """
    Função principal para executar o servidor.
    """
    servidor = ServidorCentral(DEFAULT_HOST, DEFAULT_PORT)

    try:
        servidor.iniciar()
        servidor.aguardar_conexoes()
    except Exception as e:
        print(formatar_log("ERROR", f"Erro fatal: {str(e)}"))
        sys.exit(1)


if __name__ == "__main__":
    main()
