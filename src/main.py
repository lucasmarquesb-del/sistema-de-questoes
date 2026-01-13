"""
Sistema de Banco de Questões Educacionais
Módulo: Main
Descrição: Ponto de entrada da aplicação
Versão: 1.0.1
Data: Janeiro 2026
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
import logging

# Importar gerenciador de sessões ORM
from src.database.session_manager import session_manager

# Configuração de logging
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'

# Usar force=True para garantir que a configuração seja aplicada (Python 3.8+)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ],
    force=True  # Garante que a configuração seja re-aplicada se já houver uma.
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configurado para salvar em arquivo: {log_file.resolve()}")


def setup_database() -> bool:
    """
    Configura o banco de dados ORM.
    Verifica se o banco existe, se não, cria as tabelas.

    Returns:
        bool: True se banco está pronto, False caso contrário
    """
    try:
        db_path = Path('database/sistema_questoes_v2.db')

        # Se banco não existe, criar tabelas
        if not db_path.exists():
            logger.info("Banco de dados não encontrado. Criando tabelas ORM...")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            session_manager.create_all_tables()
            logger.info("Banco de dados ORM inicializado com sucesso")
        else:
            logger.info(f"Banco de dados ORM encontrado: {db_path}")

        # Verificar se conseguimos conectar
        with session_manager.session_scope() as session:
            # Teste básico de conexão
            from src.models.orm import TipoQuestao
            session.query(TipoQuestao).first()

        logger.info("Conexão com banco de dados ORM validada")
        return True

    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados ORM: {e}")
        return False


def show_error_dialog(title: str, message: str):
    """
    Exibe diálogo de erro para o usuário.

    Args:
        title: Título da janela
        message: Mensagem de erro
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()


def main():
    """
    Função principal da aplicação.
    Inicializa a aplicação Qt e exibe a janela principal.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO SISTEMA DE BANCO DE QUESTÕES EDUCACIONAIS")
    logger.info("Versão: 1.0.1")
    logger.info("=" * 60)

    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Banco de Questões")
    app.setApplicationVersion("1.0.1")
    app.setOrganizationName("Sistema Educacional")

    # Configurar estilo
    app.setStyle("Fusion")  # Estilo moderno cross-platform

    try:
        # Configurar banco de dados
        logger.info("Configurando banco de dados...")
        if not setup_database():
            show_error_dialog(
                "Erro de Inicialização",
                "Não foi possível inicializar o banco de dados.\n"
                "Verifique os logs em 'logs/app.log' para mais detalhes."
            )
            logger.error("Falha na inicialização do banco de dados")
            return 1

        logger.info("Banco de dados configurado com sucesso")

        # Importar e criar janela principal
        from src.views.main_window import MainWindow
        window = MainWindow()
        window.show()

        logger.info("Sistema inicializado com sucesso!")
        logger.info("Entrando no loop de eventos da aplicação")

        # Entrar no loop de eventos
        return app.exec()

    except Exception as e:
        logger.error(f"Erro crítico na aplicação: {e}", exc_info=True)
        show_error_dialog(
            "Erro Crítico",
            f"Ocorreu um erro inesperado:\n\n{str(e)}\n\n"
            "Verifique os logs para mais detalhes."
        )
        return 1

    finally:
        # Nota: O session_manager gerencia conexões automaticamente
        logger.info("Aplicação finalizada")


if __name__ == "__main__":
    """
    Ponto de entrada quando o script é executado diretamente.
    """
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)
