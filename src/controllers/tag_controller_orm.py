"""
TagController - Nova versão usando ORM + Service Layer
Substitui tag_controller.py (legacy)
"""
from typing import Dict, List, Optional, Any
from src.services import services
from src.application.dtos.tag_dto import TagResponseDTO


class TagControllerORM:
    """
    Controller para operações de tags usando ORM e Service Layer

    IMPORTANTE: Este controller usa a Service Facade com UUIDs e estrutura hierárquica
    """

    @staticmethod
    def listar_todas() -> List[Dict[str, Any]]:
        """
        Lista todas as tags ativas

        Returns:
            Lista de dicts com dados das tags (uuid, nome, numeracao, nivel, caminho_completo)
        """
        try:
            return services.tag.listar_todas()
        except Exception as e:
            print(f"Erro ao listar tags: {e}")
            return []

    @staticmethod
    def listar_raizes() -> List[Dict[str, Any]]:
        """
        Lista apenas tags raiz (sem pai)

        Returns:
            Lista de tags raiz
        """
        try:
            return services.tag.listar_raizes()
        except Exception as e:
            print(f"Erro ao listar tags raiz: {e}")
            return []

    @staticmethod
    def listar_filhas(numeracao_pai: str) -> List[Dict[str, Any]]:
        """
        Lista tags filhas de uma tag pai

        Args:
            numeracao_pai: Numeração da tag pai (ex: '2.1')

        Returns:
            Lista de tags filhas
        """
        try:
            return services.tag.listar_filhas(numeracao_pai)
        except Exception as e:
            print(f"Erro ao listar tags filhas: {e}")
            return []

    @staticmethod
    def buscar_por_nome(nome: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por nome

        Args:
            nome: Nome da tag

        Returns:
            Dict com dados da tag ou None
        """
        try:
            return services.tag.buscar_por_nome(nome)
        except Exception as e:
            print(f"Erro ao buscar tag por nome: {e}")
            return None

    @staticmethod
    def buscar_por_numeracao(numeracao: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por numeração

        Args:
            numeracao: Numeração da tag (ex: '2.1.3')

        Returns:
            Dict com dados da tag ou None
        """
        try:
            return services.tag.buscar_por_numeracao(numeracao)
        except Exception as e:
            print(f"Erro ao buscar tag por numeração: {e}")
            return None

    @staticmethod
    def obter_arvore_hierarquica() -> List[TagResponseDTO]:
        """
        Retorna estrutura hierárquica completa das tags

        Returns:
            Lista de TagResponseDTOs representando a árvore de tags
        """
        try:
            tree_dicts = services.tag.obter_arvore_hierarquica()

            def convert_to_dto_recursive(node_dict):
                dto = TagResponseDTO.from_dict(node_dict)
                if 'filhas' in node_dict and node_dict['filhas']:
                    dto.filhos = [convert_to_dto_recursive(child) for child in node_dict['filhas']]
                return dto

            return [convert_to_dto_recursive(root_dict) for root_dict in tree_dicts]

        except Exception as e:
            print(f"Erro ao obter árvore hierárquica: {e}")
            return []

    @staticmethod
    def obter_arvore_conteudos() -> List[TagResponseDTO]:
        """
        Retorna apenas a árvore de tags de conteúdos (exclui banca/vestibular e etapa)

        Returns:
            Lista de TagResponseDTOs representando a árvore de conteúdos
        """
        try:
            tree_dicts = services.tag.obter_arvore_conteudos()

            def convert_to_dto_recursive(node_dict):
                dto = TagResponseDTO.from_dict(node_dict)
                if 'filhas' in node_dict and node_dict['filhas']:
                    dto.filhos = [convert_to_dto_recursive(child) for child in node_dict['filhas']]
                return dto

            return [convert_to_dto_recursive(root_dict) for root_dict in tree_dicts]

        except Exception as e:
            print(f"Erro ao obter árvore de conteúdos: {e}")
            return []

    @staticmethod
    def listar_series() -> List[Dict[str, Any]]:
        """
        Lista tags de série/nível de escolaridade

        Returns:
            Lista de dicts com dados das séries
        """
        try:
            return services.tag.listar_series()
        except Exception as e:
            print(f"Erro ao listar séries: {e}")
            return []

    @staticmethod
    def listar_vestibulares() -> List[Dict[str, Any]]:
        """
        Lista tags de vestibular/banca

        Returns:
            Lista de dicts com dados dos vestibulares
        """
        try:
            return services.tag.listar_vestibulares()
        except Exception as e:
            print(f"Erro ao listar vestibulares: {e}")
            return []

    @staticmethod
    def criar_tag(nome: str, uuid_tag_pai: str = None, tipo: str = 'CONTEUDO', uuid_disciplina: str = None) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova tag

        Args:
            nome: Nome da tag
            uuid_tag_pai: UUID da tag pai (opcional)
            tipo: Tipo da tag raiz - 'CONTEUDO', 'VESTIBULAR' ou 'SERIE'
            uuid_disciplina: UUID da disciplina (obrigatorio para tags de conteudo)

        Returns:
            Dict com dados da tag criada
        """
        try:
            result = services.tag.criar_tag(nome, uuid_tag_pai, tipo, uuid_disciplina)
            services.commit()
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            services.rollback()
            print(f"Erro ao criar tag: {e}")
            raise e

    @staticmethod
    def atualizar_tag(uuid: str, nome: str) -> Optional[Dict[str, Any]]:
        """
        Atualiza o nome de uma tag

        Args:
            uuid: UUID da tag
            nome: Novo nome

        Returns:
            Dict com dados atualizados
        """
        try:
            result = services.tag.atualizar_tag(uuid, nome)
            services.commit()
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            services.rollback()
            print(f"Erro ao atualizar tag: {e}")
            raise e

    @staticmethod
    def deletar_tag(uuid: str) -> bool:
        """
        Deleta uma tag (soft delete)

        Args:
            uuid: UUID da tag

        Returns:
            True se deletada
        """
        try:
            result = services.tag.deletar_tag(uuid)
            services.commit()
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            services.rollback()
            print(f"Erro ao deletar tag: {e}")
            raise e

    @staticmethod
    def pode_criar_subtag(uuid_tag_pai: str) -> bool:
        """
        Verifica se é permitido criar sub-tags para uma tag

        Args:
            uuid_tag_pai: UUID da tag pai

        Returns:
            True se permitido
        """
        try:
            return services.tag.pode_criar_subtag(uuid_tag_pai)
        except Exception as e:
            print(f"Erro ao verificar permissão de sub-tag: {e}")
            return False

    @staticmethod
    def inativar_tag(uuid: str) -> bool:
        """
        Inativa uma tag (soft delete)

        Args:
            uuid: UUID da tag

        Returns:
            True se inativada
        """
        try:
            result = services.tag.inativar_tag(uuid)
            services.commit()
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            services.rollback()
            print(f"Erro ao inativar tag: {e}")
            raise e

    @staticmethod
    def reativar_tag(uuid: str) -> bool:
        """
        Reativa uma tag inativa

        Args:
            uuid: UUID da tag

        Returns:
            True se reativada
        """
        try:
            result = services.tag.reativar_tag(uuid)
            services.commit()
            return result
        except ValueError as e:
            raise e
        except Exception as e:
            services.rollback()
            print(f"Erro ao reativar tag: {e}")
            raise e

    @staticmethod
    def obter_arvore_tags_inativas() -> List[Any]:
        """
        Obtém árvore hierárquica de tags inativas

        Returns:
            Lista de TagResponseDTO com hierarquia de tags inativas
        """
        try:
            return services.tag.obter_arvore_tags_inativas()
        except Exception as e:
            print(f"Erro ao obter árvore de tags inativas: {e}")
            return []

    @staticmethod
    def listar_disciplinas() -> List[Dict[str, Any]]:
        """
        Lista todas as disciplinas ativas

        Returns:
            Lista de dicts com dados das disciplinas (uuid, codigo, nome, cor)
        """
        from src.database import session_manager
        from src.repositories.disciplina_repository import DisciplinaRepository

        session = session_manager.create_session()
        try:
            repo = DisciplinaRepository(session)
            return repo.listar_para_select_com_cor()
        except Exception as e:
            print(f"Erro ao listar disciplinas: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def listar_tags_por_disciplina(uuid_disciplina: str) -> List[Dict[str, Any]]:
        """
        Lista tags de conteúdo de uma disciplina específica

        Args:
            uuid_disciplina: UUID da disciplina

        Returns:
            Lista de dicts com dados das tags (uuid, nome, numeracao, caminho_completo)
        """
        from src.database import session_manager
        from src.repositories.tag_repository import TagRepository
        from src.models.orm.disciplina import Disciplina

        session = session_manager.create_session()
        try:
            repo = TagRepository(session)
            tags = repo.listar_por_disciplina(uuid_disciplina)

            # Obter prefixo da disciplina para remover da exibição
            disciplina = session.query(Disciplina).filter_by(uuid=uuid_disciplina).first()
            prefixo_disc = str(disciplina.ordem) + "." if disciplina else ""

            resultado = []
            for tag in tags:
                # Remover prefixo da disciplina da numeração para exibição
                numeracao_exibicao = tag.numeracao
                if prefixo_disc and numeracao_exibicao.startswith(prefixo_disc):
                    numeracao_exibicao = numeracao_exibicao[len(prefixo_disc):]

                # Construir caminho completo sem prefixo da disciplina
                caminho = tag.obter_caminho_completo() if hasattr(tag, 'obter_caminho_completo') else tag.nome
                # Remover prefixo da disciplina do caminho também
                if prefixo_disc:
                    partes = caminho.split(' > ')
                    partes_ajustadas = []
                    for parte in partes:
                        # Remover numeração com prefixo de disciplina
                        if parte.startswith(prefixo_disc):
                            # Encontrar onde termina a numeração (primeiro espaço ou fim)
                            idx_espaco = parte.find(' ')
                            if idx_espaco > 0:
                                num_parte = parte[:idx_espaco]
                                resto = parte[idx_espaco:]
                                num_sem_prefixo = num_parte[len(prefixo_disc):] if num_parte.startswith(prefixo_disc) else num_parte
                                parte = num_sem_prefixo + resto
                        partes_ajustadas.append(parte)
                    caminho = ' > '.join(partes_ajustadas)

                resultado.append({
                    'uuid': tag.uuid,
                    'nome': tag.nome,
                    'numeracao': numeracao_exibicao,
                    'numeracao_completa': tag.numeracao,  # Manter numeração original para uso interno
                    'nivel': tag.nivel,
                    'caminho_completo': f"{numeracao_exibicao} - {tag.nome}"
                })
            return resultado
        except Exception as e:
            print(f"Erro ao listar tags por disciplina: {e}")
            return []
        finally:
            session.close()
