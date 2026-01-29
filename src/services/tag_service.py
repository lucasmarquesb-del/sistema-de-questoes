"""
Service para gerenciar Tags - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.repositories import TagRepository


class TagService:
    """Service para operações de negócio com tags"""

    def __init__(self, session: Session):
        self.session = session
        self.tag_repo = TagRepository(session)

    def listar_todas(self) -> List[Dict[str, Any]]:
        """
        Lista todas as tags ativas

        Returns:
            Lista de dicts com dados das tags
        """
        tags = self.tag_repo.listar_todos()
        return [
            {
                'id': hash(tag.uuid) % 2147483647,  # Converter uuid para int positivo
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'caminho_completo': tag.obter_caminho_completo()
            }
            for tag in tags
        ]

    def listar_raizes(self) -> List[Dict[str, Any]]:
        """
        Lista tags raiz (sem pai)

        Returns:
            Lista de tags raiz
        """
        tags = self.tag_repo.listar_raizes()
        return [
            {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel
            }
            for tag in tags
        ]

    def listar_filhas(self, numeracao_pai: str) -> List[Dict[str, Any]]:
        """
        Lista tags filhas de uma tag pai

        Args:
            numeracao_pai: Numeração da tag pai

        Returns:
            Lista de tags filhas
        """
        tags = self.tag_repo.listar_filhas(numeracao_pai)
        return [
            {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel
            }
            for tag in tags
        ]

    def buscar_por_nome(self, nome: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por nome

        Args:
            nome: Nome da tag

        Returns:
            Dict com dados da tag ou None
        """
        tag = self.tag_repo.buscar_por_nome(nome)
        if not tag:
            return None

        return {
            'id': hash(tag.uuid) % 2147483647,
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel,
            'caminho_completo': tag.obter_caminho_completo()
        }

    def buscar_por_numeracao(self, numeracao: str) -> Optional[Dict[str, Any]]:
        """
        Busca tag por numeração

        Args:
            numeracao: Numeração da tag (ex: 2.1.3)

        Returns:
            Dict com dados da tag ou None
        """
        tag = self.tag_repo.buscar_por_numeracao(numeracao)
        if not tag:
            return None

        return {
            'id': hash(tag.uuid) % 2147483647,
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel,
            'caminho_completo': tag.obter_caminho_completo()
        }

    def obter_arvore_hierarquica(self, filtrar_por_nome: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna estrutura hierárquica completa das tags

        Args:
            filtrar_por_nome: Se fornecido, retorna apenas a árvore da tag raiz com esse nome

        Returns:
            Lista de dicts representando a árvore
        """
        def construir_arvore(tag):
            return {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'filhas': [construir_arvore(filha) for filha in tag.tags_filhas if filha.ativo]
            }

        raizes = self.tag_repo.listar_raizes()

        # Filtrar por nome da tag raiz se especificado
        if filtrar_por_nome:
            raizes = [tag for tag in raizes if tag.nome.upper() == filtrar_por_nome.upper()]

        return [construir_arvore(tag) for tag in raizes]

    def obter_arvore_conteudos(self) -> List[Dict[str, Any]]:
        """
        Retorna apenas a árvore de tags de conteúdos (exclui vestibular e série)

        As tags de conteúdo têm numeração começando com número (1, 2, 3...)
        Tags de vestibular começam com "V" (V1, V2...)
        Tags de série/nível começam com "N" (N1, N2...)

        Returns:
            Lista de dicts representando a árvore de conteúdos
        """
        def construir_arvore(tag):
            return {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao,
                'nivel': tag.nivel,
                'filhas': [construir_arvore(filha) for filha in tag.tags_filhas if filha.ativo]
            }

        raizes = self.tag_repo.listar_raizes()

        # Filtrar apenas tags de conteúdo (numeração começa com número, não V ou N)
        raizes_filtradas = [
            tag for tag in raizes
            if tag.numeracao and tag.numeracao[0].isdigit()
        ]

        return [construir_arvore(tag) for tag in raizes_filtradas]

    def listar_series(self) -> List[Dict[str, Any]]:
        """
        Lista tags de série/nível de escolaridade (numeração começa com N)

        Returns:
            Lista de dicts com dados das tags de série
        """
        raizes = self.tag_repo.listar_raizes()

        # Filtrar apenas tags de série (numeração começa com N)
        series = [
            tag for tag in raizes
            if tag.numeracao and tag.numeracao.startswith('N')
        ]

        return [
            {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao
            }
            for tag in series
        ]

    def listar_vestibulares(self) -> List[Dict[str, Any]]:
        """
        Lista tags de vestibular/banca (numeração começa com V)

        Returns:
            Lista de dicts com dados das tags de vestibular
        """
        raizes = self.tag_repo.listar_raizes()

        # Filtrar apenas tags de vestibular (numeração começa com V)
        vestibulares = [
            tag for tag in raizes
            if tag.numeracao and tag.numeracao.startswith('V')
        ]

        return [
            {
                'id': hash(tag.uuid) % 2147483647,
                'uuid': tag.uuid,
                'nome': tag.nome,
                'numeracao': tag.numeracao
            }
            for tag in vestibulares
        ]

    def _obter_prefixo_disciplina(self, uuid_disciplina: str) -> Optional[str]:
        """
        Obtém o prefixo de numeração da disciplina (baseado na ordem).

        Args:
            uuid_disciplina: UUID da disciplina

        Returns:
            String com o prefixo (ex: "1" para Matemática) ou None
        """
        from src.models.orm.disciplina import Disciplina
        disciplina = self.session.query(Disciplina).filter_by(uuid=uuid_disciplina, ativo=True).first()
        if disciplina:
            return str(disciplina.ordem)
        return None

    def _obter_proxima_numeracao_raiz_disciplina(self, uuid_disciplina: str, prefixo_disciplina: str) -> int:
        """
        Obtém a próxima numeração para tag raiz dentro de uma disciplina.

        Args:
            uuid_disciplina: UUID da disciplina
            prefixo_disciplina: Prefixo da disciplina (ex: "1")

        Returns:
            Próximo número disponível
        """
        from src.models.orm.tag import Tag
        # Buscar tags raiz da disciplina (nivel=1 e sem pai)
        tags_raiz = self.session.query(Tag).filter(
            Tag.uuid_disciplina == uuid_disciplina,
            Tag.uuid_tag_pai == None,
            Tag.numeracao.like(f"{prefixo_disciplina}.%")
        ).all()

        if not tags_raiz:
            return 1

        # Extrair números das tags raiz
        numeros = []
        for tag in tags_raiz:
            partes = tag.numeracao.split('.')
            if len(partes) >= 2:
                try:
                    numeros.append(int(partes[1]))
                except ValueError:
                    pass

        return max(numeros) + 1 if numeros else 1

    def criar_tag(self, nome: str, uuid_tag_pai: Optional[str] = None, tipo: str = 'CONTEUDO', uuid_disciplina: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova tag

        Args:
            nome: Nome da tag (será convertido para maiúsculas)
            uuid_tag_pai: UUID da tag pai (opcional, None para tag raiz)
            tipo: Tipo da tag raiz - 'CONTEUDO', 'VESTIBULAR' ou 'SERIE' (ignorado se tiver pai)
            uuid_disciplina: UUID da disciplina (obrigatorio para tags de conteudo)

        Returns:
            Dict com dados da tag criada ou None se erro
        """
        # Converter nome para maiúsculas
        nome = nome.strip().upper()

        if not nome:
            raise ValueError("O nome da tag não pode estar vazio")

        # Verificar se já existe tag com mesmo nome (case insensitive já que convertemos para upper)
        existente = self.tag_repo.buscar_por_nome(nome)
        if existente:
            raise ValueError(f"Já existe uma tag com o nome '{nome}'")

        # Determinar disciplina
        disciplina_uuid = uuid_disciplina

        # Determinar nível e numeração
        if uuid_tag_pai:
            tag_pai = self.tag_repo.buscar_por_uuid(uuid_tag_pai)
            if not tag_pai:
                raise ValueError("Tag pai não encontrada")

            # Não permitir sub-tags em tags de vestibular (V) ou série (N)
            if tag_pai.numeracao and (tag_pai.numeracao.startswith('V') or tag_pai.numeracao.startswith('N')):
                raise ValueError("Não é permitido criar sub-tags para tags de vestibular ou série")

            nivel = tag_pai.nivel + 1
            # Buscar maior numeração existente (incluindo inativas)
            maior_num = self.tag_repo.obter_maior_numeracao_filha(uuid_tag_pai)
            proxima_ordem = maior_num + 1
            numeracao = f"{tag_pai.numeracao}.{proxima_ordem}"
            ordem = proxima_ordem

            # Herdar disciplina do pai se não fornecida
            if not disciplina_uuid and tag_pai.uuid_disciplina:
                disciplina_uuid = tag_pai.uuid_disciplina
        else:
            # Tag raiz - determinar prefixo baseado no tipo
            nivel = 1

            if tipo == 'VESTIBULAR':
                # Tags de vestibular começam com V
                maior_num = self.tag_repo.obter_maior_numeracao_raiz('V')
                proxima_ordem = maior_num + 1
                numeracao = f"V{proxima_ordem}"
                ordem = 100 + proxima_ordem  # Ordem alta para ficar após conteúdos
            elif tipo == 'SERIE':
                # Tags de série começam com N
                maior_num = self.tag_repo.obter_maior_numeracao_raiz('N')
                proxima_ordem = maior_num + 1
                numeracao = f"N{proxima_ordem}"
                ordem = 200 + proxima_ordem  # Ordem mais alta ainda
            else:
                # Tags de conteúdo - usar prefixo da disciplina
                if disciplina_uuid:
                    prefixo_disc = self._obter_prefixo_disciplina(disciplina_uuid)
                    if prefixo_disc:
                        proxima_ordem = self._obter_proxima_numeracao_raiz_disciplina(disciplina_uuid, prefixo_disc)
                        numeracao = f"{prefixo_disc}.{proxima_ordem}"
                        ordem = proxima_ordem
                    else:
                        # Fallback se não encontrar disciplina
                        maior_num = self.tag_repo.obter_maior_numeracao_raiz('')
                        proxima_ordem = maior_num + 1
                        numeracao = str(proxima_ordem)
                        ordem = proxima_ordem
                else:
                    # Sem disciplina - comportamento antigo
                    maior_num = self.tag_repo.obter_maior_numeracao_raiz('')
                    proxima_ordem = maior_num + 1
                    numeracao = str(proxima_ordem)
                    ordem = proxima_ordem

        # Criar tag
        tag = self.tag_repo.criar(
            nome=nome,
            numeracao=numeracao,
            nivel=nivel,
            uuid_tag_pai=uuid_tag_pai,
            ordem=ordem,
            uuid_disciplina=disciplina_uuid
        )

        self.session.flush()

        return {
            'id': hash(tag.uuid) % 2147483647,
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel
        }

    def atualizar_tag(self, uuid: str, nome: str) -> Optional[Dict[str, Any]]:
        """
        Atualiza o nome de uma tag

        Args:
            uuid: UUID da tag
            nome: Novo nome

        Returns:
            Dict com dados atualizados ou None
        """
        # Verificar se nome já existe em outra tag
        existente = self.tag_repo.buscar_por_nome(nome)
        if existente and existente.uuid != uuid:
            raise ValueError(f"Já existe uma tag com o nome '{nome}'")

        tag = self.tag_repo.atualizar(uuid, nome=nome)
        if not tag:
            return None

        self.session.flush()

        return {
            'id': hash(tag.uuid) % 2147483647,
            'uuid': tag.uuid,
            'nome': tag.nome,
            'numeracao': tag.numeracao,
            'nivel': tag.nivel
        }

    def deletar_tag(self, uuid: str) -> bool:
        """
        Deleta uma tag (soft delete)

        Args:
            uuid: UUID da tag

        Returns:
            True se deletada, False se não encontrada
        """
        tag = self.tag_repo.buscar_por_uuid(uuid)
        if not tag:
            return False

        # Verificar se tem filhas ativas
        filhas_ativas = [t for t in tag.tags_filhas if t.ativo]
        if filhas_ativas:
            raise ValueError("Não é possível deletar uma tag que possui sub-tags. Delete as sub-tags primeiro.")

        # Verificar se está associada a questões
        if tag.questoes:
            raise ValueError("Não é possível deletar uma tag que está associada a questões.")

        result = self.tag_repo.desativar(uuid)
        self.session.flush()
        return result

    def pode_criar_subtag(self, uuid_tag_pai: str) -> bool:
        """
        Verifica se é permitido criar sub-tags para uma tag

        Args:
            uuid_tag_pai: UUID da tag pai

        Returns:
            True se permitido, False caso contrário
        """
        tag_pai = self.tag_repo.buscar_por_uuid(uuid_tag_pai)
        if not tag_pai:
            return False

        # Não permitir sub-tags em tags de vestibular (V) ou série (N)
        if tag_pai.numeracao and (tag_pai.numeracao.startswith('V') or tag_pai.numeracao.startswith('N')):
            return False

        return True

    def inativar_tag(self, uuid: str) -> bool:
        """
        Inativa uma tag (soft delete)

        Args:
            uuid: UUID da tag

        Returns:
            True se inativada, False se não encontrada
        """
        tag = self.tag_repo.buscar_por_uuid(uuid)
        if not tag:
            return False

        # Verificar se tem filhas ativas
        filhas_ativas = [t for t in tag.tags_filhas if t.ativo]
        if filhas_ativas:
            raise ValueError("Não é possível inativar uma tag que possui sub-tags ativas. Inative as sub-tags primeiro.")

        result = self.tag_repo.desativar(uuid)
        self.session.flush()
        return result

    def reativar_tag(self, uuid: str) -> bool:
        """
        Reativa uma tag inativa

        Args:
            uuid: UUID da tag

        Returns:
            True se reativada, False se não encontrada
        """
        # Buscar tag inativa
        tag = self.session.query(self.tag_repo.model_class).filter_by(uuid=uuid, ativo=False).first()
        if not tag:
            return False

        # Verificar se a tag pai está ativa (se tiver pai)
        if tag.uuid_tag_pai:
            tag_pai = self.tag_repo.buscar_por_uuid(tag.uuid_tag_pai)
            if not tag_pai:
                raise ValueError("Não é possível reativar: a tag pai está inativa. Reative a tag pai primeiro.")

        tag.ativo = True
        self.session.flush()
        return True

    def obter_arvore_tags_inativas(self) -> List[Any]:
        """
        Obtém árvore de tags inativas (formato flat, não hierárquico)

        Returns:
            Lista de TagResponseDTO com tags inativas
        """
        from src.application.dtos.tag_dto import TagResponseDTO

        # Buscar todas as tags inativas
        tags_inativas = self.session.query(self.tag_repo.model_class).filter_by(ativo=False).order_by(
            self.tag_repo.model_class.numeracao
        ).all()

        resultado = []
        for tag in tags_inativas:
            dto = TagResponseDTO(
                id=hash(tag.uuid) % 2147483647,
                uuid=tag.uuid,
                nome=tag.nome,
                numeracao=tag.numeracao,
                nivel=tag.nivel,
                filhos=[]
            )
            resultado.append(dto)

        return resultado
