# src/main.py
"""Ponto de entrada principal da aplicação."""

import sys
import logging
import atexit
import os
from pathlib import Path

# Adicionar diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# IMPORTANTE: QtWebEngineWidgets deve ser importado ANTES de criar QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
from PyQt6.QtWidgets import QApplication, QMessageBox

# Importar gerenciador de sessões ORM
from src.database.session_manager import session_manager


def setup_logging():
    """Configura o sistema de logging completo."""
    
    # Carrega connection string (prioriza variável de ambiente)
    # TODO: A senha não deve estar hardcoded, mesmo que seja de um ambiente de teste.
    # O ideal é que o .env forneça a string completa.
    connection_string = os.environ.get(
        "MONGODB_CONNECTION_STRING",
        "mongodb+srv://mathbank_logger:MathBank2026@mathbankcluster.4lqsue0.mongodb.net/?appName=MathBankCluster"
    )
    database = os.environ.get("MONGODB_DATABASE", "mathbank_logs")
    
    # Configuração do logger raiz
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    root_logger = logging.getLogger()
    # Definir como DEBUG para capturar todos os níveis. Handlers controlarão o que é emitido.
    root_logger.setLevel(logging.DEBUG) 
    
    # Remover handlers existentes para evitar duplicação
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Handler de Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Nível para o console
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # Handler de Arquivo
    try:
        os.makedirs("logs", exist_ok=True)
        # Usar um nome de arquivo diferente para o log local para evitar confusão com o plano
        file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG) # Nível para o arquivo
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Usar o logger padrão aqui, pois o nosso pode não estar pronto
        logging.warning(f"Não foi possível criar arquivo de log: {e}")
    
    # Logging remoto (MongoDB)
    try:
        from src.infrastructure.logging import (
            create_mongo_handler,
            init_audit_logger,
            init_error_reporter,
            init_metrics_collector,
        )
        
        # Handler MongoDB para erros
        mongo_handler = create_mongo_handler(connection_string, database, "errors", logging.ERROR)
        if mongo_handler:
            root_logger.addHandler(mongo_handler)
            logging.info("Logging remoto (erros) configurado.")
        
        # Error Reporter para exceções não tratadas
        init_error_reporter(connection_string, database, "errors", install_global=True)
        logging.info("Error Reporter global instalado.")
        
        # Audit Logger (singleton)
        audit = init_audit_logger(connection_string, database, "audit")
        logging.info("Audit Logger inicializado.")
        
        # Metrics Collector (singleton)
        metrics = init_metrics_collector(connection_string, database, "metrics")
        
        # Registrar início de sessão na auditoria e métricas
        metrics.start_session()
        audit.sessao_iniciada()
        logging.info("Sessão de métricas e auditoria iniciada.")
        
        # Handler de encerramento para registrar o fim da sessão
        def on_exit():
            try:
                if metrics and metrics._session_start:
                    from datetime import datetime, timezone
                    session_end = datetime.now(timezone.utc)
                    duration = (session_end - metrics._session_start).total_seconds()
                    audit.sessao_encerrada(int(duration))
                    metrics.end_session()
                    logging.info("Sessão de métricas e auditoria finalizada e enviada.")
            except Exception as e:
                logging.warning(f"Erro ao finalizar sessão de métricas/auditoria: {e}")
        
        atexit.register(on_exit)
        
    except ImportError:
        logging.warning("Módulos de logging remoto não encontrados. O logging remoto está desabilitado.")
    except Exception as e:
        logging.warning(f"Falha ao configurar logging remoto: {e}")
    
    logging.info("Sistema de logging inicializado.")


# Configura logging ANTES de outros imports
setup_logging()

logger = logging.getLogger(__name__)


def setup_database() -> bool:
    """
    Configura o banco de dados ORM.
    Verifica se o banco existe, se não, cria as tabelas.

    Returns:
        bool: True se banco está pronto, False caso contrário
    """
    try:
        db_path = Path('database/sistema_questoes_v2.db')

        if not db_path.exists():
            logger.info("Banco de dados não encontrado. Criando tabelas ORM...")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            session_manager.create_all_tables()
            logger.info("Banco de dados ORM inicializado com sucesso")
        else:
            logger.info(f"Banco de dados ORM encontrado: {db_path}")

        with session_manager.session_scope() as session:
            from src.models.orm import TipoQuestao
            session.query(TipoQuestao).first()

        logger.info("Conexão com banco de dados ORM validada")
        return True

    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados ORM: {e}", exc_info=True)
        return False


def show_error_dialog(title: str, message: str):
    """
    Exibe diálogo de erro para o usuário.
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
    """
    logger.info("=" * 60)
    logger.info("INICIANDO SISTEMA DE BANCO DE QUESTÕES EDUCACIONAIS")
    logger.info("Versão: 1.0.1 (com Logging Remoto)")
    logger.info("=" * 60)

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Sistema de Banco de Questões")
        app.setApplicationVersion("1.0.1")
        app.setOrganizationName("Sistema Educacional")
        app.setStyle("Fusion")

        if not setup_database():
            show_error_dialog(
                "Erro de Inicialização",
                "Não foi possível inicializar o banco de dados.\n"
                "Verifique os logs em 'logs/app.log' para mais detalhes."
            )
            logger.critical("Falha na inicialização do banco de dados. A aplicação será encerrada.")
            return 1
        
        logger.info("Banco de dados configurado com sucesso.")

        from src.views.pages.main_window import MainWindow
        window = MainWindow()
        window.showMaximized()

        logger.info("Sistema inicializado e janela principal exibida.")
        
        return app.exec()

    except Exception as e:
        # O error reporter global deve capturar isso, mas logamos como crítico também.
        logger.critical(f"Erro fatal não capturado na inicialização: {e}", exc_info=True)
        show_error_dialog(
            "Erro Crítico",
            f"Ocorreu um erro inesperado na inicialização:\n\n{str(e)}\n\n"
            "Verifique os logs para mais detalhes."
        )
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        # Este é o último recurso. O reporter global já deve ter sido acionado.
        logger.critical(f"Erro fatal de alto nível: {e}", exc_info=True)
        sys.exit(1)
