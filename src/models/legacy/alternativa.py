"""
Sistema de Banco de Questões Educacionais
Módulo: Model Alternativa
Versão: 1.0.1

DESCRIÇÃO:
    Model responsável pela entidade Alternativa (opções A-E de questões objetivas).
    Cada questão OBJETIVA possui exatamente 5 alternativas (A, B, C, D, E),
    sendo apenas UMA correta.

FUNCIONALIDADES:
    - Criar alternativa
    - Buscar alternativa por ID
    - Listar alternativas de uma questão
    - Atualizar alternativa
    - Deletar alternativa
    - Obter alternativa correta
    - Validar conjunto de alternativas (5 opções, 1 correta)

RELACIONAMENTOS:
    - questao.py: Uma alternativa pertence a UMA questão (N:1)
    - database.py: Utiliza a conexão com o banco de dados

TABELA NO BANCO:
    alternativa (
        id_alternativa INTEGER PRIMARY KEY,
        id_questao INTEGER NOT NULL,
        letra CHAR(1) CHECK(letra IN ('A','B','C','D','E')),
        texto TEXT,
        imagem VARCHAR(255),
        escala_imagem DECIMAL(3,2) DEFAULT 0.7,
        correta BOOLEAN DEFAULT 0,
        UNIQUE(id_questao, letra),
        CHECK (texto IS NOT NULL OR imagem IS NOT NULL)
    )

REGRAS DE NEGÓCIO:
    - Cada questão OBJETIVA deve ter exatamente 5 alternativas (A, B, C, D, E)
    - Apenas UMA alternativa pode ser correta por questão
    - Pelo menos um dos campos (texto ou imagem) deve estar preenchido
    - Trigger no banco garante unicidade de alternativa correta

UTILIZADO POR:
    - QuestaoModel: Ao criar/editar questão objetiva
    - QuestaoController: Validação de alternativas
    - QuestaoForm (view): Campos de alternativas no formulário
    - ExportController: Montagem das alternativas no PDF

EXEMPLO DE USO:
    >>> from src.models.alternativa import AlternativaModel
    >>>
    >>> # Criar alternativas para uma questão
    >>> id_questao = 1
    >>> AlternativaModel.criar(id_questao, 'A', '$x = 1$', correta=False)
    >>> AlternativaModel.criar(id_questao, 'B', '$x = 2$', correta=False)
    >>> AlternativaModel.criar(id_questao, 'C', '$x = 3$', correta=True)
    >>> AlternativaModel.criar(id_questao, 'D', '$x = 4$', correta=False)
    >>> AlternativaModel.criar(id_questao, 'E', '$x = 5$', correta=False)
    >>>
    >>> # Listar alternativas de uma questão
    >>> alternativas = AlternativaModel.listar_por_questao(id_questao)
    >>> for alt in alternativas:
    >>>     print(f"{alt['letra']}) {alt['texto']}")
    >>>
    >>> # Obter gabarito
    >>> correta = AlternativaModel.obter_correta(id_questao)
    >>> print(f"Gabarito: {correta['letra']}")
"""

import logging
from typing import Optional, List, Dict
from src.models.database import db
from src.constants import LETRAS_ALTERNATIVAS, TOTAL_ALTERNATIVAS, ImagemConfig
from src.models.queries import AlternativaQueries

logger = logging.getLogger(__name__)


class AlternativaModel:
    """
    Model para a entidade Alternativa.
    Implementa operações CRUD e validações.
    """

    # ATUALIZADO: Usar constantes centralizadas
    LETRAS_VALIDAS = LETRAS_ALTERNATIVAS
    TOTAL_ALTERNATIVAS = TOTAL_ALTERNATIVAS

    @staticmethod
    def criar(id_questao: int, letra: str, texto: str = None,
              imagem: str = None, escala_imagem: float = ImagemConfig.ESCALA_PADRAO,
              correta: bool = False) -> Optional[int]:
        """
        Cria uma nova alternativa.

        Args:
            id_questao: ID da questão
            letra: Letra da alternativa (A, B, C, D ou E)
            texto: Texto da alternativa (pode conter LaTeX)
            imagem: Caminho relativo da imagem
            escala_imagem: Escala da imagem no LaTeX (default: 0.7)
            correta: Se esta é a alternativa correta

        Returns:
            int: ID da alternativa criada ou None se erro
        """
        try:
            # Validações
            letra = letra.upper()
            if letra not in AlternativaModel.LETRAS_VALIDAS:
                logger.error(f"Letra inválida: {letra}")
                return None

            if not texto and not imagem:
                logger.error("Alternativa deve ter texto ou imagem")
                return None

            # ATUALIZADO: Usar query centralizada
            query = AlternativaQueries.INSERT

            params = (id_questao, letra, texto, imagem, escala_imagem, 1 if correta else 0)

            if db.execute_update(query, params):
                id_alternativa = db.get_last_insert_id()
                logger.info(f"Alternativa {letra} criada com sucesso. ID: {id_alternativa}")
                return id_alternativa
            return None

        except Exception as e:
            logger.error(f"Erro ao criar alternativa: {e}")
            return None

    @staticmethod
    def buscar_por_id(id_alternativa: int) -> Optional[Dict]:
        """
        Busca uma alternativa pelo ID.

        Args:
            id_alternativa: ID da alternativa

        Returns:
            Dict: Dados da alternativa ou None se não encontrada
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = AlternativaQueries.SELECT_BY_ID
            results = db.execute_query(query, (id_alternativa,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar alternativa por ID: {e}")
            return None

    @staticmethod
    def listar_por_questao(id_questao: int) -> List[Dict]:
        """
        Lista todas as alternativas de uma questão, ordenadas por letra.

        Args:
            id_questao: ID da questão

        Returns:
            List[Dict]: Lista de alternativas (ordenadas A, B, C, D, E)
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = AlternativaQueries.SELECT_BY_QUESTAO
            results = db.execute_query(query, (id_questao,))

            if results:
                return [dict(row) for row in results]
            return []

        except Exception as e:
            logger.error(f"Erro ao listar alternativas: {e}")
            return []

    @staticmethod
    def obter_correta(id_questao: int) -> Optional[Dict]:
        """
        Obtém a alternativa correta de uma questão.

        Args:
            id_questao: ID da questão

        Returns:
            Dict: Alternativa correta ou None se não encontrada
        """
        try:
            # ATUALIZADO: Usar query centralizada
            query = AlternativaQueries.SELECT_CORRETA
            results = db.execute_query(query, (id_questao,))

            if results and len(results) > 0:
                return dict(results[0])
            return None

        except Exception as e:
            logger.error(f"Erro ao obter alternativa correta: {e}")
            return None

    @staticmethod
    def atualizar(id_alternativa: int, texto: str = None, imagem: str = None,
                  escala_imagem: float = None, correta: bool = None) -> bool:
        """
        Atualiza uma alternativa existente.

        Args:
            id_alternativa: ID da alternativa
            texto: Novo texto (opcional)
            imagem: Nova imagem (opcional)
            escala_imagem: Nova escala (opcional)
            correta: Novo status de correta (opcional)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            campos = []
            valores = []

            if texto is not None:
                campos.append("texto = ?")
                valores.append(texto)

            if imagem is not None:
                campos.append("imagem = ?")
                valores.append(imagem)

            if escala_imagem is not None:
                campos.append("escala_imagem = ?")
                valores.append(escala_imagem)

            if correta is not None:
                campos.append("correta = ?")
                valores.append(1 if correta else 0)

            if not campos:
                logger.warning("Nenhum campo para atualizar")
                return False

            valores.append(id_alternativa)
            query = f"UPDATE alternativa SET {', '.join(campos)} WHERE id_alternativa = ?"

            return db.execute_update(query, tuple(valores))

        except Exception as e:
            logger.error(f"Erro ao atualizar alternativa: {e}")
            return False

    @staticmethod
    def deletar(id_alternativa: int) -> bool:
        """
        Deleta uma alternativa permanentemente.

        Args:
            id_alternativa: ID da alternativa

        Returns:
            bool: True se deletada com sucesso
        """
        try:
            query = "DELETE FROM alternativa WHERE id_alternativa = ?"
            return db.execute_update(query, (id_alternativa,))

        except Exception as e:
            logger.error(f"Erro ao deletar alternativa: {e}")
            return False

    @staticmethod
    def deletar_por_questao(id_questao: int) -> bool:
        """
        Deleta todas as alternativas de uma questão.
        Útil ao editar uma questão objetiva.

        Args:
            id_questao: ID da questão

        Returns:
            bool: True se deletadas com sucesso
        """
        try:
            query = "DELETE FROM alternativa WHERE id_questao = ?"
            return db.execute_update(query, (id_questao,))

        except Exception as e:
            logger.error(f"Erro ao deletar alternativas da questão: {e}")
            return False

    @staticmethod
    def validar_alternativas(id_questao: int) -> Dict[str, any]:
        """
        Valida se uma questão possui alternativas válidas:
        - Exatamente 5 alternativas (A, B, C, D, E)
        - Exatamente 1 alternativa correta
        - Todas as letras únicas

        Args:
            id_questao: ID da questão

        Returns:
            Dict: {'valido': bool, 'erros': List[str], 'avisos': List[str]}
        """
        try:
            alternativas = AlternativaModel.listar_por_questao(id_questao)

            erros = []
            avisos = []

            # Verificar quantidade
            if len(alternativas) != AlternativaModel.TOTAL_ALTERNATIVAS:
                erros.append(f"Questão deve ter {AlternativaModel.TOTAL_ALTERNATIVAS} alternativas. Encontradas: {len(alternativas)}")

            # Verificar letras
            letras = [alt['letra'] for alt in alternativas]
            letras_esperadas = set(AlternativaModel.LETRAS_VALIDAS)
            letras_presentes = set(letras)

            faltando = letras_esperadas - letras_presentes
            if faltando:
                erros.append(f"Alternativas faltando: {', '.join(sorted(faltando))}")

            duplicadas = [letra for letra in letras if letras.count(letra) > 1]
            if duplicadas:
                erros.append(f"Letras duplicadas: {', '.join(set(duplicadas))}")

            # Verificar alternativa correta
            corretas = [alt for alt in alternativas if alt['correta']]
            if len(corretas) == 0:
                erros.append("Nenhuma alternativa marcada como correta")
            elif len(corretas) > 1:
                erros.append(f"Múltiplas alternativas corretas: {', '.join([c['letra'] for c in corretas])}")

            # Verificar conteúdo
            for alt in alternativas:
                if not alt['texto'] and not alt['imagem']:
                    avisos.append(f"Alternativa {alt['letra']} sem texto nem imagem")

            return {
                'valido': len(erros) == 0,
                'erros': erros,
                'avisos': avisos,
                'total_alternativas': len(alternativas),
                'corretas': len(corretas)
            }

        except Exception as e:
            logger.error(f"Erro ao validar alternativas: {e}")
            return {
                'valido': False,
                'erros': [f"Erro ao validar: {str(e)}"],
                'avisos': []
            }

    @staticmethod
    def criar_conjunto_completo(id_questao: int, alternativas_dados: List[Dict]) -> bool:
        """
        Cria um conjunto completo de 5 alternativas de uma vez.
        Útil ao criar uma questão objetiva.

        Args:
            id_questao: ID da questão
            alternativas_dados: Lista com 5 dicts, cada um com:
                {'letra': 'A', 'texto': '...', 'imagem': '...', 'correta': bool}

        Returns:
            bool: True se todas foram criadas com sucesso
        """
        try:
            if len(alternativas_dados) != AlternativaModel.TOTAL_ALTERNATIVAS:
                logger.error(f"Esperadas {AlternativaModel.TOTAL_ALTERNATIVAS} alternativas, recebidas {len(alternativas_dados)}")
                return False

            # Verificar se já existe uma alternativa correta
            corretas = [alt for alt in alternativas_dados if alt.get('correta', False)]
            if len(corretas) != 1:
                logger.error(f"Deve haver exatamente 1 alternativa correta. Encontradas: {len(corretas)}")
                return False

            # Criar todas as alternativas
            sucesso = True
            for dados in alternativas_dados:
                id_alt = AlternativaModel.criar(
                    id_questao=id_questao,
                    letra=dados.get('letra'),
                    texto=dados.get('texto'),
                    imagem=dados.get('imagem'),
                    escala_imagem=dados.get('escala_imagem', 0.7),
                    correta=dados.get('correta', False)
                )
                if not id_alt:
                    sucesso = False
                    break

            if sucesso:
                logger.info(f"Conjunto completo de alternativas criado para questão {id_questao}")
            return sucesso

        except Exception as e:
            logger.error(f"Erro ao criar conjunto de alternativas: {e}")
            return False


if __name__ == "__main__":
    """Testes do modelo"""
    print("=" * 60)
    print("TESTE DO MODEL ALTERNATIVA")
    print("=" * 60)

    print("\n1. Constantes:")
    print(f"   - Letras válidas: {AlternativaModel.LETRAS_VALIDAS}")
    print(f"   - Total por questão: {AlternativaModel.TOTAL_ALTERNATIVAS}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
