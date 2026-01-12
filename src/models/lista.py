"""
Sistema de Banco de Questões Educacionais
Módulo: Model Lista
Versão: 1.0.1

DESCRIÇÃO:
    Model responsável pela entidade Lista (agrupamento de questões para provas/listas).
    Uma lista é um conjunto de questões que serão exportadas juntas para PDF.

FUNCIONALIDADES:
    - Criar lista
    - Buscar lista por ID
    - Listar todas as listas
    - Atualizar lista
    - Deletar lista
    - Adicionar/remover questões
    - Listar questões de uma lista
    - Duplicar lista
    - Contar questões

RELACIONAMENTOS:
    - questao.py: Uma lista contém VÁRIAS questões (N:N via lista_questao)
    - database.py: Utiliza a conexão com o banco de dados

TABELAS NO BANCO:
    lista (
        id_lista INTEGER PRIMARY KEY,
        titulo VARCHAR(200) NOT NULL,
        tipo VARCHAR(50),
        cabecalho TEXT,
        instrucoes TEXT,
        data_criacao DATETIME
    )

    lista_questao (
        id_lista INTEGER,
        id_questao INTEGER,
        data_adicao DATETIME,
        PRIMARY KEY (id_lista, id_questao)
    )

UTILIZADO POR:
    - ListaController: Lógica de gerenciamento de listas
    - ListaForm (view): Formulário de criação/edição
    - ExportController: Exportação para PDF/LaTeX
    - MainWindow (view): Visualização de listas

EXEMPLO DE USO:
    >>> from src.models.lista import ListaModel
    >>>
    >>> # Criar lista
    >>> dados = {
    >>>     'titulo': 'Prova Bimestral',
    >>>     'tipo': 'prova',
    >>>     'cabecalho': 'Escola ABC\\nProfessor: João',
    >>>     'instrucoes': 'Responda as questões a caneta'
    >>> }
    >>> id_lista = ListaModel.criar(**dados)
    >>>
    >>> # Adicionar questões
    >>> ListaModel.adicionar_questao(id_lista, id_questao_1)
    >>> ListaModel.adicionar_questao(id_lista, id_questao_2)
    >>>
    >>> # Listar questões
    >>> questoes = ListaModel.listar_questoes(id_lista)
    >>> print(f"Total: {len(questoes)} questões")
"""

import logging
from typing import Optional, List, Dict
from src.models.database import db

logger = logging.getLogger(__name__)


class ListaModel:
    """
    Model para a entidade Lista.
    Implementa operações CRUD e gerenciamento de questões.
    """

    @staticmethod
    def criar(titulo: str, tipo: str = None, cabecalho: str = None,
              instrucoes: str = None) -> Optional[int]:
        """
        Cria uma nova lista.

        Args:
            titulo: Título da lista (obrigatório)
            tipo: Tipo da lista (ex: 'prova', 'lista', 'simulado')
            cabecalho: Texto do cabeçalho personalizado
            instrucoes: Instruções gerais

        Returns:
            int: ID da lista criada ou None se erro
        """
        try:
            if not titulo or not titulo.strip():
                logger.error("Título não pode ser vazio")
                return None

            query = """
                INSERT INTO lista (titulo, tipo, cabecalho, instrucoes)
                VALUES (?, ?, ?, ?)
            """

            params = (titulo, tipo, cabecalho, instrucoes)

            if db.execute_update(query, params):
                id_lista = db.get_last_insert_id()
                logger.info(f"Lista criada com sucesso. ID: {id_lista}")
                return id_lista
            return None

        except Exception as e:
            logger.error(f"Erro ao criar lista: {e}")
            return None

    @staticmethod
    def buscar_por_id(id_lista: int) -> Optional[Dict]:
        """
        Busca uma lista pelo ID.

        Args:
            id_lista: ID da lista

        Returns:
            Dict: Dados da lista ou None se não encontrada
        """
        try:
            query = """
                SELECT
                    l.*,
                    COUNT(lq.id_questao) as total_questoes
                FROM lista l
                LEFT JOIN lista_questao lq ON l.id_lista = lq.id_lista
                WHERE l.id_lista = ?
                GROUP BY l.id_lista
            """
            results = db.execute_query(query, (id_lista,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar lista por ID: {e}")
            return None

    @staticmethod
    def listar_todas(ordenar_por: str = "data_criacao DESC") -> List[Dict]:
        """
        Lista todas as listas.

        Args:
            ordenar_por: Campo para ordenação

        Returns:
            List[Dict]: Lista de listas com contagem de questões
        """
        try:
            query = f"""
                SELECT
                    l.*,
                    COUNT(lq.id_questao) as total_questoes
                FROM lista l
                LEFT JOIN lista_questao lq ON l.id_lista = lq.id_lista
                GROUP BY l.id_lista
                ORDER BY {ordenar_por}
            """
            results = db.execute_query(query)

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar listas: {e}")
            return []

    @staticmethod
    def atualizar(id_lista: int, titulo: str = None, tipo: str = None,
                  cabecalho: str = None, instrucoes: str = None) -> bool:
        """
        Atualiza uma lista existente.

        Args:
            id_lista: ID da lista
            titulo: Novo título (opcional)
            tipo: Novo tipo (opcional)
            cabecalho: Novo cabeçalho (opcional)
            instrucoes: Novas instruções (opcional)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            campos = []
            valores = []

            if titulo is not None:
                campos.append("titulo = ?")
                valores.append(titulo)

            if tipo is not None:
                campos.append("tipo = ?")
                valores.append(tipo)

            if cabecalho is not None:
                campos.append("cabecalho = ?")
                valores.append(cabecalho)

            if instrucoes is not None:
                campos.append("instrucoes = ?")
                valores.append(instrucoes)

            if not campos:
                logger.warning("Nenhum campo para atualizar")
                return False

            valores.append(id_lista)
            query = f"UPDATE lista SET {', '.join(campos)} WHERE id_lista = ?"

            return db.execute_update(query, tuple(valores))

        except Exception as e:
            logger.error(f"Erro ao atualizar lista: {e}")
            return False

    @staticmethod
    def deletar(id_lista: int) -> bool:
        """
        Deleta uma lista permanentemente.
        CASCADE irá deletar automaticamente os vínculos em lista_questao.

        Args:
            id_lista: ID da lista

        Returns:
            bool: True se deletada com sucesso
        """
        try:
            query = "DELETE FROM lista WHERE id_lista = ?"
            result = db.execute_update(query, (id_lista,))

            if result:
                logger.info(f"Lista {id_lista} deletada com sucesso")
            return result

        except Exception as e:
            logger.error(f"Erro ao deletar lista: {e}")
            return False

    @staticmethod
    def adicionar_questao(id_lista: int, id_questao: int) -> bool:
        """
        Adiciona uma questão a uma lista.

        Args:
            id_lista: ID da lista
            id_questao: ID da questão

        Returns:
            bool: True se adicionada com sucesso
        """
        try:
            query = """
                INSERT OR IGNORE INTO lista_questao (id_lista, id_questao)
                VALUES (?, ?)
            """
            result = db.execute_update(query, (id_lista, id_questao))

            if result:
                logger.info(f"Questão {id_questao} adicionada à lista {id_lista}")
            return result

        except Exception as e:
            logger.error(f"Erro ao adicionar questão à lista: {e}")
            return False

    @staticmethod
    def remover_questao(id_lista: int, id_questao: int) -> bool:
        """
        Remove uma questão de uma lista.

        Args:
            id_lista: ID da lista
            id_questao: ID da questão

        Returns:
            bool: True se removida com sucesso
        """
        try:
            query = "DELETE FROM lista_questao WHERE id_lista = ? AND id_questao = ?"
            result = db.execute_update(query, (id_lista, id_questao))

            if result:
                logger.info(f"Questão {id_questao} removida da lista {id_lista}")
            return result

        except Exception as e:
            logger.error(f"Erro ao remover questão da lista: {e}")
            return False

    @staticmethod
    def limpar_questoes(id_lista: int) -> bool:
        """
        Remove todas as questões de uma lista.

        Args:
            id_lista: ID da lista

        Returns:
            bool: True se limpada com sucesso
        """
        try:
            query = "DELETE FROM lista_questao WHERE id_lista = ?"
            return db.execute_update(query, (id_lista,))

        except Exception as e:
            logger.error(f"Erro ao limpar questões da lista: {e}")
            return False

    @staticmethod
    def listar_questoes(id_lista: int, incluir_inativas: bool = False,
                       ordem: str = None) -> List[Dict]:
        """
        Lista todas as questões de uma lista.

        Args:
            id_lista: ID da lista
            incluir_inativas: Se True, inclui questões inativas
            ordem: Ordenação personalizada (None = ordem de adição)

        Returns:
            List[Dict]: Lista de questões com seus dados completos
        """
        try:
            filtro_ativo = "" if incluir_inativas else "AND q.ativo = 1"
            ordenacao = ordem if ordem else "lq.data_adicao"

            query = f"""
                SELECT
                    q.*,
                    d.nome as dificuldade_nome,
                    lq.data_adicao
                FROM questao q
                JOIN lista_questao lq ON q.id_questao = lq.id_questao
                LEFT JOIN dificuldade d ON q.id_dificuldade = d.id_dificuldade
                WHERE lq.id_lista = ? {filtro_ativo}
                ORDER BY {ordenacao}
            """
            results = db.execute_query(query, (id_lista,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar questões da lista: {e}")
            return []

    @staticmethod
    def contar_questoes(id_lista: int, incluir_inativas: bool = False) -> int:
        """
        Conta o total de questões em uma lista.

        Args:
            id_lista: ID da lista
            incluir_inativas: Se True, conta também questões inativas

        Returns:
            int: Total de questões
        """
        try:
            filtro_ativo = "" if incluir_inativas else "AND q.ativo = 1"

            query = f"""
                SELECT COUNT(*) as total
                FROM lista_questao lq
                JOIN questao q ON lq.id_questao = q.id_questao
                WHERE lq.id_lista = ? {filtro_ativo}
            """
            result = db.execute_query(query, (id_lista,))

            if result:
                return result[0]['total']
            return 0

        except Exception as e:
            logger.error(f"Erro ao contar questões: {e}")
            return 0

    @staticmethod
    def duplicar(id_lista: int, novo_titulo: str = None) -> Optional[int]:
        """
        Duplica uma lista com todas as suas questões.

        Args:
            id_lista: ID da lista a ser duplicada
            novo_titulo: Título da nova lista (se None, adiciona "Cópia de")

        Returns:
            int: ID da nova lista ou None se erro
        """
        try:
            # Buscar lista original
            lista_original = ListaModel.buscar_por_id(id_lista)
            if not lista_original:
                logger.error(f"Lista {id_lista} não encontrada")
                return None

            # Definir título da cópia
            if not novo_titulo:
                novo_titulo = f"Cópia de {lista_original['titulo']}"

            # Criar nova lista
            id_nova_lista = ListaModel.criar(
                titulo=novo_titulo,
                tipo=lista_original['tipo'],
                cabecalho=lista_original['cabecalho'],
                instrucoes=lista_original['instrucoes']
            )

            if not id_nova_lista:
                return None

            # Copiar questões
            questoes = ListaModel.listar_questoes(id_lista)
            for questao in questoes:
                ListaModel.adicionar_questao(id_nova_lista, questao['id_questao'])

            logger.info(f"Lista {id_lista} duplicada com sucesso. Nova ID: {id_nova_lista}")
            return id_nova_lista

        except Exception as e:
            logger.error(f"Erro ao duplicar lista: {e}")
            return None

    @staticmethod
    def verificar_questao_existe(id_lista: int, id_questao: int) -> bool:
        """
        Verifica se uma questão já está em uma lista.

        Args:
            id_lista: ID da lista
            id_questao: ID da questão

        Returns:
            bool: True se questão já está na lista
        """
        try:
            query = """
                SELECT COUNT(*) as total
                FROM lista_questao
                WHERE id_lista = ? AND id_questao = ?
            """
            result = db.execute_query(query, (id_lista, id_questao))

            if result:
                return result[0]['total'] > 0
            return False

        except Exception as e:
            logger.error(f"Erro ao verificar questão na lista: {e}")
            return False

    @staticmethod
    def estatisticas(id_lista: int) -> Dict:
        """
        Retorna estatísticas sobre uma lista.

        Returns:
            Dict: Estatísticas (total, por tipo, por dificuldade, etc.)
        """
        try:
            questoes = ListaModel.listar_questoes(id_lista, incluir_inativas=True)

            stats = {
                'total': len(questoes),
                'ativas': len([q for q in questoes if q['ativo']]),
                'inativas': len([q for q in questoes if not q['ativo']]),
                'objetivas': len([q for q in questoes if q['tipo'] == 'OBJETIVA']),
                'discursivas': len([q for q in questoes if q['tipo'] == 'DISCURSIVA']),
                'por_dificuldade': {},
                'por_ano': {},
                'por_fonte': {}
            }

            # Agrupar por dificuldade
            for q in questoes:
                if q.get('dificuldade_nome'):
                    diff = q['dificuldade_nome']
                    stats['por_dificuldade'][diff] = stats['por_dificuldade'].get(diff, 0) + 1

            # Agrupar por ano
            for q in questoes:
                ano = q['ano']
                stats['por_ano'][ano] = stats['por_ano'].get(ano, 0) + 1

            # Agrupar por fonte
            for q in questoes:
                fonte = q['fonte']
                stats['por_fonte'][fonte] = stats['por_fonte'].get(fonte, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}


if __name__ == "__main__":
    """Testes do modelo"""
    print("=" * 60)
    print("TESTE DO MODEL LISTA")
    print("=" * 60)

    # Listar todas
    print("\n1. Listando todas as listas:")
    listas = ListaModel.listar_todas()
    if listas:
        for l in listas[:5]:  # Mostrar apenas primeiras 5
            print(f"   - {l['titulo']} ({l['total_questoes']} questões)")
    else:
        print("   - Nenhuma lista cadastrada")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
