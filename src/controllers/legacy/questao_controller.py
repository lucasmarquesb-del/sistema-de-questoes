"""
Sistema de Banco de Questões Educacionais
Módulo: Controller Questão (Legacy)
Versão: 1.0.1

⚠️ NOTA: Este é o controller LEGADO. As views atualmente usam
questao_controller_refactored.py que implementa arquitetura DDD.

Este arquivo é mantido para:
- Referência e migração gradual
- Funções utilitárias ainda não migradas
- Backwards compatibility

NOVA ARQUITETURA: Ver questao_controller_refactored.py

DESCRIÇÃO:
    Controller responsável pela lógica de negócio relacionada a Questões.
    Faz a mediação entre as Views (interface) e os Models (dados).

FUNCIONALIDADES:
    - Validar dados de questão antes de salvar
    - Orquestrar criação completa de questão (questão + alternativas + tags)
    - Buscar questões com filtros complexos
    - Gerenciar alternativas de questões objetivas
    - Exportar dados de questão para diferentes formatos
    - Validar integridade de questões

RELACIONAMENTOS:
    - questao.py (model): Acesso aos dados de questões
    - alternativa.py (model): Gerenciamento de alternativas
    - tag.py (model): Vinculação de tags
    - dificuldade.py (model): Validação de dificuldade
    - QuestaoForm (view): Recebe dados do formulário
    - SearchPanel (view): Fornece resultados de busca

REGRAS DE NEGÓCIO IMPLEMENTADAS:
    - Questão OBJETIVA deve ter exatamente 5 alternativas (A-E)
    - Apenas 1 alternativa pode ser correta
    - Questão deve ter no mínimo 1 tag
    - Campos obrigatórios: enunciado, tipo, ano, fonte
    - Validação de imagens (formato, tamanho)
    - Soft delete (inativar ao invés de deletar)
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil
from datetime import datetime

from src.models.questao import QuestaoModel
from src.models.alternativa import AlternativaModel
from src.models.tag import TagModel
from src.models.dificuldade import DificuldadeModel
from src.constants import (
    TipoQuestao, DificuldadeID, Validacao,
    ImagemConfig, ErroMensagens, TOTAL_ALTERNATIVAS
)
from src.utils.exceptions import (
    ValidationError, EnunciadoVazioError, TipoInvalidoError,
    AnoInvalidoError, AlternativasInvalidasError, AlternativaCorretaInvalidaError,
    ImagemInvalidaError, Result
)

logger = logging.getLogger(__name__)


class QuestaoController:
    """
    Controller para gerenciar lógica de negócio de questões.
    """

    @staticmethod
    def validar_dados_questao(dados: Dict) -> Dict[str, Any]:
        """
        Valida todos os dados de uma questão antes de salvar.

        Args:
            dados: Dict com dados da questão

        Returns:
            Dict: {'valido': bool, 'erros': List[str], 'avisos': List[str]}
        """
        erros = []
        avisos = []

        try:
            # Validar enunciado (obrigatório)
            if not dados.get('enunciado') or not dados.get('enunciado').strip():
                erros.append(ErroMensagens.ENUNCIADO_VAZIO)

            # Validar tipo (obrigatório)
            tipo = dados.get('tipo', '').upper()
            if tipo not in [TipoQuestao.OBJETIVA, TipoQuestao.DISCURSIVA]:
                erros.append(ErroMensagens.TIPO_INVALIDO)

            # Validar ano (obrigatório e razoável)
            ano = dados.get('ano')
            if not ano:
                erros.append("O ano é obrigatório")
            elif not isinstance(ano, int) or ano < Validacao.ANO_MINIMO or ano > Validacao.ANO_MAXIMO:
                erros.append(ErroMensagens.ANO_INVALIDO)

            # Validar fonte (obrigatório)
            if not dados.get('fonte') or not dados.get('fonte').strip():
                erros.append(ErroMensagens.FONTE_VAZIA)

            # Validar dificuldade (opcional, mas se fornecida deve ser válida)
            id_dificuldade = dados.get('id_dificuldade')
            dificuldades_validas = [
                DificuldadeID.FACIL,
                DificuldadeID.MEDIO,
                DificuldadeID.DIFICIL,
                DificuldadeID.SEM_DIFICULDADE
            ]
            if id_dificuldade and id_dificuldade not in dificuldades_validas:
                erros.append(ErroMensagens.DIFICULDADE_INVALIDA)

            # Validar alternativas se OBJETIVA
            if tipo == TipoQuestao.OBJETIVA:
                alternativas = dados.get('alternativas', [])

                if len(alternativas) == 0:
                    erros.append("Questão objetiva deve ter alternativas")
                elif len(alternativas) < TOTAL_ALTERNATIVAS:
                    erros.append(ErroMensagens.FALTAM_ALTERNATIVAS)

                # Verificar se há exatamente uma correta
                corretas = [alt for alt in alternativas if alt.get('correta', False)]
                if len(corretas) == 0:
                    erros.append(ErroMensagens.FALTA_CORRETA)
                elif len(corretas) > 1:
                    erros.append(ErroMensagens.MULTIPLAS_CORRETAS)

                # Verificar se alternativas têm conteúdo
                for alt in alternativas:
                    if not alt.get('texto') and not alt.get('imagem'):
                        avisos.append(f"Alternativa {alt.get('letra')} sem texto nem imagem")

            # Validar tags (recomendado ter pelo menos 1)
            tags = dados.get('tags', [])
            if len(tags) < Validacao.MIN_TAGS_POR_QUESTAO:
                avisos.append(ErroMensagens.SEM_TAGS)

            # Validar imagem do enunciado (se fornecida)
            imagem_enunciado = dados.get('imagem_enunciado')
            if imagem_enunciado:
                if not Path(imagem_enunciado).exists():
                    erros.append(ErroMensagens.IMAGEM_NAO_ENCONTRADA)
                else:
                    # Validar extensão
                    ext = Path(imagem_enunciado).suffix.lower()
                    if ext not in ImagemConfig.EXTENSOES_VALIDAS:
                        erros.append(ErroMensagens.FORMATO_INVALIDO)

            # Validar título (se fornecido)
            titulo = dados.get('titulo')
            if titulo and len(titulo) > Validacao.TITULO_MAX_LENGTH:
                avisos.append(f"Título muito longo (máximo {Validacao.TITULO_MAX_LENGTH} caracteres)")

            return {
                'valido': len(erros) == 0,
                'erros': erros,
                'avisos': avisos
            }

        except Exception as e:
            logger.error(f"Erro ao validar dados da questão: {e}")
            return {
                'valido': False,
                'erros': [f"Erro na validação: {str(e)}"],
                'avisos': []
            }

    @staticmethod
    def criar_questao_completa(dados: Dict) -> Optional[int]:
        """
        Cria uma questão completa com alternativas e tags.

        Args:
            dados: Dict com todos os dados da questão

        Returns:
            int: ID da questão criada ou None se erro
        """
        try:
            # 1. Validar dados
            validacao = QuestaoController.validar_dados_questao(dados)
            if not validacao['valido']:
                logger.error(f"Validação falhou: {validacao['erros']}")
                return None

            logger.info("Criando questão completa...")

            # 2. Processar imagem do enunciado (copiar para pasta correta)
            imagem_destino = None
            if dados.get('imagem_enunciado'):
                imagem_destino = QuestaoController._processar_imagem(
                    dados['imagem_enunciado'],
                    'enunciado'
                )

            # 3. Criar questão
            id_questao = QuestaoModel.criar(
                titulo=dados.get('titulo'),
                enunciado=dados['enunciado'],
                tipo=dados['tipo'].upper(),
                ano=dados['ano'],
                fonte=dados['fonte'],
                id_dificuldade=dados.get('id_dificuldade'),
                imagem_enunciado=imagem_destino,
                escala_imagem_enunciado=dados.get('escala_imagem_enunciado', 0.7),
                resolucao=dados.get('resolucao'),
                gabarito_discursiva=dados.get('gabarito_discursiva'),
                observacoes=dados.get('observacoes')
            )

            if not id_questao:
                logger.error("Falha ao criar questão no banco")
                return None

            logger.info(f"Questão criada com ID: {id_questao}")

            # 4. Se OBJETIVA, criar alternativas
            if dados['tipo'].upper() == QuestaoModel.TIPO_OBJETIVA:
                alternativas = dados.get('alternativas', [])
                if alternativas:
                    sucesso = AlternativaModel.criar_conjunto_completo(
                        id_questao,
                        alternativas
                    )
                    if not sucesso:
                        logger.warning(f"Problema ao criar alternativas para questão {id_questao}")

            # 5. Vincular tags
            tags = dados.get('tags', [])
            for id_tag in tags:
                QuestaoModel.vincular_tag(id_questao, id_tag)

            logger.info(f"Questão completa criada com sucesso. ID: {id_questao}")
            return id_questao

        except Exception as e:
            logger.error(f"Erro ao criar questão completa: {e}")
            return None

    @staticmethod
    def atualizar_questao_completa(id_questao: int, dados: Dict) -> bool:
        """
        Atualiza uma questão completa incluindo alternativas e tags.

        Args:
            id_questao: ID da questão
            dados: Dict com dados atualizados

        Returns:
            bool: True se atualizada com sucesso
        """
        try:
            # 1. Validar dados
            validacao = QuestaoController.validar_dados_questao(dados)
            if not validacao['valido']:
                logger.error(f"Validação falhou: {validacao['erros']}")
                return False

            logger.info(f"Atualizando questão {id_questao}...")

            # 2. Processar imagem (se alterada)
            imagem_destino = dados.get('imagem_enunciado')
            if imagem_destino and Path(imagem_destino).exists():
                imagem_destino = QuestaoController._processar_imagem(
                    imagem_destino,
                    'enunciado',
                    id_questao
                )

            # 3. Atualizar questão
            sucesso = QuestaoModel.atualizar(
                id_questao,
                titulo=dados.get('titulo'),
                enunciado=dados['enunciado'],
                tipo=dados['tipo'].upper(),
                ano=dados['ano'],
                fonte=dados['fonte'],
                id_dificuldade=dados.get('id_dificuldade'),
                imagem_enunciado=imagem_destino,
                escala_imagem_enunciado=dados.get('escala_imagem_enunciado', 0.7),
                resolucao=dados.get('resolucao'),
                gabarito_discursiva=dados.get('gabarito_discursiva'),
                observacoes=dados.get('observacoes')
            )

            if not sucesso:
                logger.error("Falha ao atualizar questão no banco")
                return False

            # 4. Se OBJETIVA, recriar alternativas
            if dados['tipo'].upper() == QuestaoModel.TIPO_OBJETIVA:
                # Deletar alternativas antigas
                AlternativaModel.deletar_por_questao(id_questao)

                # Criar novas
                alternativas = dados.get('alternativas', [])
                if alternativas:
                    AlternativaModel.criar_conjunto_completo(id_questao, alternativas)
            else:
                # Se mudou para DISCURSIVA, remover alternativas
                AlternativaModel.deletar_por_questao(id_questao)

            # 5. Atualizar tags (remover todas e adicionar novamente)
            # Buscar tags atuais
            tags_atuais = QuestaoModel.listar_tags(id_questao)
            for tag in tags_atuais:
                QuestaoModel.desvincular_tag(id_questao, tag['id_tag'])

            # Adicionar novas tags
            tags_novas = dados.get('tags', [])
            for id_tag in tags_novas:
                QuestaoModel.vincular_tag(id_questao, id_tag)

            logger.info(f"Questão {id_questao} atualizada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar questão: {e}")
            return False

    @staticmethod
    def buscar_questoes(filtros: Dict = None) -> List[Dict]:
        """
        Busca questões aplicando filtros.
        Enriquece os dados com alternativas e tags.

        Args:
            filtros: Dict com filtros opcionais:
                - titulo: str
                - tipo: str (OBJETIVA/DISCURSIVA)
                - ano: int
                - ano_de: int
                - ano_ate: int
                - fonte: str
                - id_dificuldade: int
                - tags: List[int]
                - busca_texto: str (busca no enunciado)

        Returns:
            List[Dict]: Lista de questões
        """
        try:
            if filtros is None:
                filtros = {}

            logger.info(f"Buscando questões com filtros: {filtros}")

            # Preparar filtros para o model
            model_filtros = {}

            if 'titulo' in filtros:
                model_filtros['titulo'] = filtros['titulo']

            if 'tipo' in filtros and filtros['tipo'] not in ['Todas', 'TODAS', '']:
                model_filtros['tipo'] = filtros['tipo'].upper()

            if 'ano' in filtros:
                model_filtros['ano'] = filtros['ano']

            if 'fonte' in filtros and filtros['fonte']:
                model_filtros['fonte'] = filtros['fonte']

            if 'id_dificuldade' in filtros:
                model_filtros['id_dificuldade'] = filtros['id_dificuldade']

            if 'tags' in filtros and len(filtros['tags']) > 0:
                model_filtros['tags'] = filtros['tags']

            # Buscar questões
            questoes = QuestaoModel.buscar_por_filtros(**model_filtros)

            # Enriquecer com alternativas (se objetiva) e tags
            for questao in questoes:
                if questao['tipo'] == QuestaoModel.TIPO_OBJETIVA:
                    questao['alternativas'] = AlternativaModel.listar_por_questao(
                        questao['id_questao']
                    )
                else:
                    questao['alternativas'] = []

                questao['tags'] = QuestaoModel.listar_tags(questao['id_questao'])

            # Aplicar filtros adicionais não suportados pelo model
            if 'ano_de' in filtros:
                questoes = [q for q in questoes if q['ano'] >= filtros['ano_de']]

            if 'ano_ate' in filtros:
                questoes = [q for q in questoes if q['ano'] <= filtros['ano_ate']]

            if 'busca_texto' in filtros and filtros['busca_texto']:
                texto = filtros['busca_texto'].lower()
                questoes = [q for q in questoes
                           if texto in q.get('enunciado', '').lower() or
                              texto in q.get('titulo', '').lower()]

            logger.info(f"Encontradas {len(questoes)} questões")
            return questoes

        except Exception as e:
            logger.error(f"Erro ao buscar questões: {e}")
            return []

    @staticmethod
    def obter_questao_completa(id_questao: int) -> Optional[Dict]:
        """
        Obtém uma questão completa com todas as informações.

        Args:
            id_questao: ID da questão

        Returns:
            Dict: Questão completa ou None se não encontrada
        """
        try:
            questao = QuestaoModel.buscar_por_id(id_questao)
            if not questao:
                return None

            # Adicionar alternativas
            if questao['tipo'] == QuestaoModel.TIPO_OBJETIVA:
                questao['alternativas'] = AlternativaModel.listar_por_questao(id_questao)
            else:
                questao['alternativas'] = []

            # Adicionar tags
            questao['tags'] = QuestaoModel.listar_tags(id_questao)

            return questao

        except Exception as e:
            logger.error(f"Erro ao obter questão completa: {e}")
            return None

    @staticmethod
    def inativar_questao(id_questao: int) -> bool:
        """
        Inativa uma questão (soft delete).

        Args:
            id_questao: ID da questão

        Returns:
            bool: True se inativada com sucesso
        """
        try:
            return QuestaoModel.inativar(id_questao)
        except Exception as e:
            logger.error(f"Erro ao inativar questão: {e}")
            return False

    @staticmethod
    def reativar_questao(id_questao: int) -> bool:
        """
        Reativa uma questão inativa.

        Args:
            id_questao: ID da questão

        Returns:
            bool: True se reativada com sucesso
        """
        try:
            return QuestaoModel.reativar(id_questao)
        except Exception as e:
            logger.error(f"Erro ao reativar questão: {e}")
            return False

    @staticmethod
    def inativar_questao_v2(id_questao: int) -> Result:
        """
        Versão 2.0: Inativa questão usando Result pattern.

        Args:
            id_questao: ID da questão

        Returns:
            Result com sucesso ou falha

        EXEMPLO DE USO:
            result = QuestaoController.inativar_questao_v2(123)
            if result:
                print("Questão inativada")
            else:
                print(f"Erro: {result.error}")
        """
        try:
            questao = QuestaoModel.buscar_por_id(id_questao)
            if not questao:
                return Result.fail(
                    error="Questão não encontrada",
                    details={'id_questao': id_questao}
                )

            if not questao.get('ativo', True):
                return Result.fail(
                    error="Questão já está inativa",
                    details={'id_questao': id_questao}
                )

            sucesso = QuestaoModel.inativar(id_questao)
            if sucesso:
                logger.info(f"Questão {id_questao} inativada")
                return Result.ok(data={'id_questao': id_questao})
            else:
                return Result.fail(
                    error="Falha ao inativar questão",
                    details={'id_questao': id_questao}
                )

        except Exception as e:
            logger.error(f"Erro ao inativar questão: {e}")
            return Result.fail(
                error=f"Erro inesperado: {str(e)}",
                details={'id_questao': id_questao, 'exception_type': type(e).__name__}
            )

    @staticmethod
    def reativar_questao_v2(id_questao: int) -> Result:
        """
        Versão 2.0: Reativa questão usando Result pattern.

        Args:
            id_questao: ID da questão

        Returns:
            Result com sucesso ou falha

        EXEMPLO DE USO:
            result = QuestaoController.reativar_questao_v2(123)
            if result:
                print("Questão reativada")
            else:
                print(f"Erro: {result.error}")
        """
        try:
            questao = QuestaoModel.buscar_por_id(id_questao)
            if not questao:
                return Result.fail(
                    error="Questão não encontrada",
                    details={'id_questao': id_questao}
                )

            if questao.get('ativo', False):
                return Result.fail(
                    error="Questão já está ativa",
                    details={'id_questao': id_questao}
                )

            sucesso = QuestaoModel.reativar(id_questao)
            if sucesso:
                logger.info(f"Questão {id_questao} reativada")
                return Result.ok(data={'id_questao': id_questao})
            else:
                return Result.fail(
                    error="Falha ao reativar questão",
                    details={'id_questao': id_questao}
                )

        except Exception as e:
            logger.error(f"Erro ao reativar questão: {e}")
            return Result.fail(
                error=f"Erro inesperado: {str(e)}",
                details={'id_questao': id_questao, 'exception_type': type(e).__name__}
            )

    @staticmethod
    def _processar_imagem(caminho_origem: str, tipo: str, id_questao: int = None) -> Optional[str]:
        """
        Processa uma imagem copiando para pasta de imagens do sistema.

        Args:
            caminho_origem: Caminho completo da imagem original
            tipo: Tipo (enunciado, alternativa, etc)
            id_questao: ID da questão (opcional)

        Returns:
            str: Caminho relativo da imagem copiada ou None se erro
        """
        try:
            origem = Path(caminho_origem)
            if not origem.exists():
                logger.error(f"Imagem não encontrada: {caminho_origem}")
                return None

            # Criar diretório de imagens se não existir
            # Estrutura: imagens/questoes/
            from src.models.database import db
            project_root = db.get_project_root()
            img_dir = project_root / 'imagens' / 'questoes'
            img_dir.mkdir(parents=True, exist_ok=True)

            # Nome do arquivo: questao_{id}_{tipo}_{timestamp}.ext
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            id_str = f"questao_{id_questao}_" if id_questao else ""
            nome_arquivo = f"{id_str}{tipo}_{timestamp}{origem.suffix}"

            destino = img_dir / nome_arquivo

            # Copiar arquivo
            shutil.copy2(origem, destino)

            # Retornar caminho relativo
            caminho_relativo = f"imagens/questoes/{nome_arquivo}"
            logger.info(f"Imagem processada: {caminho_relativo}")

            return caminho_relativo

        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return None

    @staticmethod
    def obter_estatisticas() -> Dict:
        """
        Obtém estatísticas gerais sobre questões.

        Returns:
            Dict: Estatísticas
        """
        try:
            total = QuestaoModel.contar_total(apenas_ativas=True)
            todas = QuestaoModel.listar_todas(apenas_ativas=True)

            objetivas = len([q for q in todas if q['tipo'] == QuestaoModel.TIPO_OBJETIVA])
            discursivas = len([q for q in todas if q['tipo'] == QuestaoModel.TIPO_DISCURSIVA])

            # Contadores por dificuldade
            faceis = len([q for q in todas if q.get('id_dificuldade') == 1])
            medias = len([q for q in todas if q.get('id_dificuldade') == 2])
            dificeis = len([q for q in todas if q.get('id_dificuldade') == 3])

            return {
                'total': total,
                'objetivas': objetivas,
                'discursivas': discursivas,
                'faceis': faceis,
                'medias': medias,
                'dificeis': dificeis
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total': 0,
                'objetivas': 0,
                'discursivas': 0,
                'faceis': 0,
                'medias': 0,
                'dificeis': 0
            }

    # ============================================
    # MÉTODOS NOVOS COM EXCEÇÕES E RESULT PATTERN
    # ============================================

    @staticmethod
    def buscar_questao_segura(id_questao: int) -> Result:
        """
        Busca questão usando Result pattern (sem lançar exceções).

        EXEMPLO DE USO:
            result = QuestaoController.buscar_questao_segura(123)
            if result:
                questao = result.data
                print(f"Questão encontrada: {questao['titulo']}")
            else:
                print(f"Erro: {result.error}")

        Args:
            id_questao: ID da questão

        Returns:
            Result: Result.ok(data=questao) ou Result.fail(error=mensagem)
        """
        try:
            questao = QuestaoModel.buscar_por_id(id_questao)

            if not questao:
                return Result.fail(
                    "Questão não encontrada",
                    details={'id_questao': id_questao}
                )

            return Result.ok(data=questao)

        except Exception as e:
            logger.error(f"Erro ao buscar questão {id_questao}: {e}")
            return Result.fail(
                f"Erro ao buscar questão: {str(e)}",
                details={'id_questao': id_questao}
            )

    @staticmethod
    def criar_questao_completa_v2(dados: Dict) -> Result:
        """
        Versão 2.0: Cria questão usando Result pattern.

        Esta versão NÃO lança exceções, retorna Result.
        Ideal para uso em APIs ou quando você quer tratar erros sem try/except.

        Args:
            dados: Dados da questão com alternativas e tags

        Returns:
            Result com id_questao em caso de sucesso

        EXEMPLO DE USO:
            result = QuestaoController.criar_questao_completa_v2(dados)
            if result:
                print(f"Questão criada: {result.data}")
            else:
                print(f"Erro: {result.error}")
                for campo, erro in result.details.items():
                    print(f"  - {campo}: {erro}")
        """
        try:
            # 1. Validar dados básicos
            validacao = QuestaoController.validar_dados_questao(dados)
            if not validacao['valido']:
                return Result.fail(
                    error="Dados de validação inválidos",
                    details={
                        'erros': validacao['erros'],
                        'avisos': validacao.get('avisos', [])
                    }
                )

            logger.info("Criando questão completa (v2)...")

            # 2. Processar imagem do enunciado
            imagem_destino = None
            if dados.get('imagem_enunciado'):
                try:
                    imagem_destino = QuestaoController._processar_imagem(
                        dados['imagem_enunciado'],
                        'enunciado'
                    )
                except Exception as e:
                    return Result.fail(
                        error="Falha ao processar imagem",
                        details={'motivo': str(e)}
                    )

            # 3. Criar questão
            id_questao = QuestaoModel.criar(
                titulo=dados.get('titulo'),
                enunciado=dados['enunciado'],
                tipo=dados['tipo'].upper(),
                ano=dados['ano'],
                fonte=dados['fonte'],
                id_dificuldade=dados.get('id_dificuldade'),
                imagem_enunciado=imagem_destino,
                escala_imagem_enunciado=dados.get('escala_imagem_enunciado', ImagemConfig.ESCALA_PADRAO),
                resolucao=dados.get('resolucao'),
                gabarito_discursiva=dados.get('gabarito_discursiva'),
                observacoes=dados.get('observacoes')
            )

            if not id_questao:
                return Result.fail(error="Falha ao criar questão no banco de dados")

            logger.info(f"Questão criada com ID: {id_questao}")

            # 4. Se OBJETIVA, criar alternativas
            if dados['tipo'].upper() == TipoQuestao.OBJETIVA:
                alternativas = dados.get('alternativas', [])
                if alternativas:
                    sucesso = AlternativaModel.criar_conjunto_completo(
                        id_questao,
                        alternativas
                    )
                    if not sucesso:
                        logger.warning(f"Problema ao criar alternativas para questão {id_questao}")
                        return Result.fail(
                            error="Questão criada mas alternativas falharam",
                            details={'id_questao': id_questao}
                        )

            # 5. Vincular tags
            tags = dados.get('tags', [])
            for id_tag in tags:
                QuestaoModel.vincular_tag(id_questao, id_tag)

            logger.info(f"Questão completa criada com sucesso. ID: {id_questao}")
            return Result.ok(data={'id_questao': id_questao})

        except Exception as e:
            logger.error(f"Erro inesperado ao criar questão: {e}")
            return Result.fail(
                error=f"Erro inesperado: {str(e)}",
                details={'exception_type': type(e).__name__}
            )

    @staticmethod
    def criar_questao_completa_v3(dados: Dict) -> int:
        """
        Versão 3.0: Cria questão lançando exceções específicas.

        Esta versão LANÇA EXCEÇÕES tipadas.
        Ideal quando você quer capturar tipos específicos de erro.

        Args:
            dados: Dados da questão com alternativas e tags

        Returns:
            int: ID da questão criada

        Raises:
            EnunciadoVazioError: Enunciado não fornecido
            TipoInvalidoError: Tipo não é OBJETIVA ou DISCURSIVA
            AnoInvalidoError: Ano fora do range válido
            AlternativasInvalidasError: Alternativas inválidas
            ImagemInvalidaError: Problema com imagem
            DatabaseError: Erro ao salvar no banco

        EXEMPLO DE USO:
            try:
                id_questao = QuestaoController.criar_questao_completa_v3(dados)
                print(f"Questão criada: {id_questao}")
            except EnunciadoVazioError as e:
                print("Erro: O enunciado é obrigatório")
            except TipoInvalidoError as e:
                print(f"Tipo inválido: {e.tipo_fornecido}")
            except AlternativasInvalidasError as e:
                print(f"Alternativas inválidas: {e.message}")
            except Exception as e:
                print(f"Erro geral: {e}")
        """
        # 1. Validar e lançar exceções específicas
        QuestaoController.validar_dados_com_excecoes(dados)

        logger.info("Criando questão completa (v3 - com exceções)...")

        # 2. Processar imagem do enunciado
        imagem_destino = None
        if dados.get('imagem_enunciado'):
            try:
                imagem_destino = QuestaoController._processar_imagem(
                    dados['imagem_enunciado'],
                    'enunciado'
                )
            except Exception as e:
                raise ImagemInvalidaError(str(dados['imagem_enunciado']), motivo=str(e))

        # 3. Criar questão
        id_questao = QuestaoModel.criar(
            titulo=dados.get('titulo'),
            enunciado=dados['enunciado'],
            tipo=dados['tipo'].upper(),
            ano=dados['ano'],
            fonte=dados['fonte'],
            id_dificuldade=dados.get('id_dificuldade'),
            imagem_enunciado=imagem_destino,
            escala_imagem_enunciado=dados.get('escala_imagem_enunciado', ImagemConfig.ESCALA_PADRAO),
            resolucao=dados.get('resolucao'),
            gabarito_discursiva=dados.get('gabarito_discursiva'),
            observacoes=dados.get('observacoes')
        )

        if not id_questao:
            from src.utils.exceptions import DatabaseError
            raise DatabaseError("Falha ao criar questão no banco de dados")

        logger.info(f"Questão criada com ID: {id_questao}")

        # 4. Se OBJETIVA, criar alternativas
        if dados['tipo'].upper() == TipoQuestao.OBJETIVA:
            alternativas = dados.get('alternativas', [])
            if alternativas:
                sucesso = AlternativaModel.criar_conjunto_completo(
                    id_questao,
                    alternativas
                )
                if not sucesso:
                    raise AlternativasInvalidasError(
                        "Falha ao criar conjunto de alternativas",
                        detalhes={'id_questao': id_questao}
                    )

        # 5. Vincular tags
        tags = dados.get('tags', [])
        for id_tag in tags:
            QuestaoModel.vincular_tag(id_questao, id_tag)

        logger.info(f"Questão completa criada com sucesso. ID: {id_questao}")
        return id_questao

    @staticmethod
    def atualizar_questao_completa_v2(id_questao: int, dados: Dict) -> Result:
        """
        Versão 2.0: Atualiza questão usando Result pattern.

        Esta versão NÃO lança exceções, retorna Result.

        Args:
            id_questao: ID da questão a atualizar
            dados: Novos dados da questão

        Returns:
            Result com sucesso ou falha

        EXEMPLO DE USO:
            result = QuestaoController.atualizar_questao_completa_v2(123, dados)
            if result:
                print("Questão atualizada com sucesso")
            else:
                print(f"Erro: {result.error}")
        """
        try:
            # 1. Verificar se questão existe
            questao_existente = QuestaoModel.buscar_por_id(id_questao)
            if not questao_existente:
                return Result.fail(
                    error="Questão não encontrada",
                    details={'id_questao': id_questao}
                )

            # 2. Validar novos dados
            validacao = QuestaoController.validar_dados_questao(dados)
            if not validacao['valido']:
                return Result.fail(
                    error="Dados de validação inválidos",
                    details={
                        'erros': validacao['erros'],
                        'avisos': validacao.get('avisos', [])
                    }
                )

            logger.info(f"Atualizando questão {id_questao} (v2)...")

            # 3. Processar imagem se fornecida
            imagem_destino = None
            if dados.get('imagem_enunciado'):
                try:
                    imagem_destino = QuestaoController._processar_imagem(
                        dados['imagem_enunciado'],
                        'enunciado'
                    )
                except Exception as e:
                    return Result.fail(
                        error="Falha ao processar imagem",
                        details={'motivo': str(e)}
                    )

            # 4. Atualizar questão
            sucesso = QuestaoModel.atualizar(
                id_questao=id_questao,
                titulo=dados.get('titulo'),
                enunciado=dados.get('enunciado'),
                tipo=dados.get('tipo'),
                ano=dados.get('ano'),
                fonte=dados.get('fonte'),
                id_dificuldade=dados.get('id_dificuldade'),
                imagem_enunciado=imagem_destino,
                escala_imagem_enunciado=dados.get('escala_imagem_enunciado'),
                resolucao=dados.get('resolucao'),
                gabarito_discursiva=dados.get('gabarito_discursiva'),
                observacoes=dados.get('observacoes')
            )

            if not sucesso:
                return Result.fail(error="Falha ao atualizar questão no banco")

            # 5. Se OBJETIVA, atualizar alternativas
            if dados.get('tipo', '').upper() == TipoQuestao.OBJETIVA:
                # Deletar alternativas antigas
                AlternativaModel.deletar_por_questao(id_questao)

                # Criar novas
                alternativas = dados.get('alternativas', [])
                if alternativas:
                    sucesso_alt = AlternativaModel.criar_conjunto_completo(
                        id_questao,
                        alternativas
                    )
                    if not sucesso_alt:
                        return Result.fail(
                            error="Questão atualizada mas alternativas falharam",
                            details={'id_questao': id_questao}
                        )

            # 6. Atualizar tags
            if 'tags' in dados:
                # Desvincular todas as tags antigas
                QuestaoModel.desvincular_todas_tags(id_questao)

                # Vincular novas
                for id_tag in dados['tags']:
                    QuestaoModel.vincular_tag(id_questao, id_tag)

            logger.info(f"Questão {id_questao} atualizada com sucesso")
            return Result.ok(data={'id_questao': id_questao})

        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar questão: {e}")
            return Result.fail(
                error=f"Erro inesperado: {str(e)}",
                details={'exception_type': type(e).__name__}
            )

    @staticmethod
    def validar_dados_com_excecoes(dados: Dict) -> None:
        """
        Valida dados da questão lançando exceções específicas.

        EXEMPLO DE USO:
            try:
                QuestaoController.validar_dados_com_excecoes(dados)
                # Se chegou aqui, dados são válidos
            except EnunciadoVazioError:
                print("Enunciado vazio!")
            except AlternativasInvalidasError as e:
                print(f"Alternativas inválidas: {e.message}")
            except ValidationError as e:
                print(f"Erro de validação: {e.message}")

        Args:
            dados: Dict com dados da questão

        Raises:
            EnunciadoVazioError: Se enunciado vazio
            TipoInvalidoError: Se tipo inválido
            AnoInvalidoError: Se ano fora do intervalo válido
            AlternativasInvalidasError: Se número de alternativas incorreto
            AlternativaCorretaInvalidaError: Se problema com alternativa correta
            ImagemInvalidaError: Se imagem inválida
        """
        # Validar enunciado
        if not dados.get('enunciado') or not dados.get('enunciado').strip():
            raise EnunciadoVazioError()

        # Validar tipo
        tipo = dados.get('tipo', '').upper()
        if tipo not in [TipoQuestao.OBJETIVA, TipoQuestao.DISCURSIVA]:
            raise TipoInvalidoError(tipo)

        # Validar ano
        ano = dados.get('ano')
        if not ano:
            raise ValidationError("O ano é obrigatório")

        if not isinstance(ano, int) or ano < Validacao.ANO_MINIMO or ano > Validacao.ANO_MAXIMO:
            raise AnoInvalidoError(ano, Validacao.ANO_MINIMO, Validacao.ANO_MAXIMO)

        # Validar fonte
        if not dados.get('fonte') or not dados.get('fonte').strip():
            raise ValidationError(ErroMensagens.FONTE_VAZIA)

        # Validar alternativas se OBJETIVA
        if tipo == TipoQuestao.OBJETIVA:
            alternativas = dados.get('alternativas', [])

            if len(alternativas) < TOTAL_ALTERNATIVAS:
                raise AlternativasInvalidasError(len(alternativas), TOTAL_ALTERNATIVAS)

            # Verificar alternativa correta
            corretas = [alt for alt in alternativas if alt.get('correta', False)]
            if len(corretas) != 1:
                raise AlternativaCorretaInvalidaError(len(corretas))

        # Validar imagem do enunciado
        imagem_enunciado = dados.get('imagem_enunciado')
        if imagem_enunciado:
            if not Path(imagem_enunciado).exists():
                raise ImagemInvalidaError(imagem_enunciado, "Arquivo não encontrado")

            ext = Path(imagem_enunciado).suffix.lower()
            if ext not in ImagemConfig.EXTENSOES_VALIDAS:
                raise ImagemInvalidaError(imagem_enunciado, f"Formato inválido: {ext}")


logger.info("QuestaoController carregado")
