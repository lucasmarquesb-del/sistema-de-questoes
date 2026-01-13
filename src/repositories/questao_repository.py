"""
Repository para operações com Questões
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.orm import Questao, Tag, FonteQuestao, AnoReferencia, Dificuldade, TipoQuestao, CodigoGenerator
from .base_repository import BaseRepository


class QuestaoRepository(BaseRepository[Questao]):
    """Repository para Questões"""

    def __init__(self, session: Session):
        super().__init__(Questao, session)

    def buscar_por_codigo(self, codigo: str) -> Optional[Questao]:
        """
        Busca questão por código legível

        Args:
            codigo: Código da questão (ex: Q-2026-0001)

        Returns:
            Questão ou None
        """
        return self.session.query(Questao).filter_by(
            codigo=codigo,
            ativo=True
        ).first()

    def buscar_por_titulo(self, titulo: str) -> List[Questao]:
        """
        Busca questões por título (LIKE)

        Args:
            titulo: Texto para buscar no título

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).filter(
            Questao.titulo.ilike(f"%{titulo}%"),
            Questao.ativo == True
        ).all()

    def buscar_por_enunciado(self, texto: str) -> List[Questao]:
        """
        Busca questões por texto no enunciado

        Args:
            texto: Texto para buscar

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).filter(
            Questao.enunciado.ilike(f"%{texto}%"),
            Questao.ativo == True
        ).all()

    def buscar_por_fonte(self, sigla_fonte: str) -> List[Questao]:
        """
        Busca questões por fonte

        Args:
            sigla_fonte: Sigla da fonte (ex: ENEM, FUVEST)

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).join(FonteQuestao).filter(
            FonteQuestao.sigla == sigla_fonte,
            Questao.ativo == True
        ).all()

    def buscar_por_ano(self, ano: int) -> List[Questao]:
        """
        Busca questões por ano

        Args:
            ano: Ano da questão

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).join(AnoReferencia).filter(
            AnoReferencia.ano == ano,
            Questao.ativo == True
        ).all()

    def buscar_por_tag(self, nome_tag: str) -> List[Questao]:
        """
        Busca questões por tag

        Args:
            nome_tag: Nome da tag

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).join(Questao.tags).filter(
            Tag.nome == nome_tag,
            Questao.ativo == True
        ).all()

    def buscar_por_tags(self, nomes_tags: List[str]) -> List[Questao]:
        """
        Busca questões que possuem TODAS as tags especificadas

        Args:
            nomes_tags: Lista de nomes de tags

        Returns:
            Lista de questões
        """
        query = self.session.query(Questao).filter(Questao.ativo == True)

        for nome_tag in nomes_tags:
            query = query.join(Questao.tags).filter(Tag.nome == nome_tag)

        return query.all()

    def buscar_por_dificuldade(self, codigo_dificuldade: str) -> List[Questao]:
        """
        Busca questões por dificuldade

        Args:
            codigo_dificuldade: Código da dificuldade (FACIL, MEDIO, DIFICIL)

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).join(Dificuldade).filter(
            Dificuldade.codigo == codigo_dificuldade,
            Questao.ativo == True
        ).all()

    def buscar_por_tipo(self, codigo_tipo: str) -> List[Questao]:
        """
        Busca questões por tipo

        Args:
            codigo_tipo: Código do tipo (OBJETIVA, DISCURSIVA)

        Returns:
            Lista de questões
        """
        return self.session.query(Questao).join(TipoQuestao).filter(
            TipoQuestao.codigo == codigo_tipo,
            Questao.ativo == True
        ).all()

    def buscar_com_filtros(self, filtros: Dict[str, Any]) -> List[Questao]:
        """
        Busca questões com múltiplos filtros combinados

        Args:
            filtros: Dicionário com os filtros
                - fonte: sigla da fonte
                - ano: ano inteiro
                - tags: lista de nomes de tags
                - dificuldade: código da dificuldade
                - tipo: código do tipo de questão
                - titulo: texto para buscar no título
                - enunciado: texto para buscar no enunciado

        Returns:
            Lista de questões que atendem aos critérios
        """
        query = self.session.query(Questao).filter(Questao.ativo == True)

        # Filtro por fonte
        if filtros.get('fonte'):
            query = query.join(FonteQuestao).filter(
                FonteQuestao.sigla == filtros['fonte']
            )

        # Filtro por ano
        if filtros.get('ano'):
            query = query.join(AnoReferencia).filter(
                AnoReferencia.ano == filtros['ano']
            )

        # Filtro por dificuldade
        if filtros.get('dificuldade'):
            query = query.join(Dificuldade).filter(
                Dificuldade.codigo == filtros['dificuldade']
            )

        # Filtro por tipo
        if filtros.get('tipo'):
            query = query.join(TipoQuestao).filter(
                TipoQuestao.codigo == filtros['tipo']
            )

        # Filtro por tags (AND - questão deve ter todas as tags)
        if filtros.get('tags'):
            for nome_tag in filtros['tags']:
                query = query.join(Questao.tags).filter(Tag.nome == nome_tag)

        # Filtro por título
        if filtros.get('titulo'):
            query = query.filter(Questao.titulo.ilike(f"%{filtros['titulo']}%"))

        # Filtro por enunciado
        if filtros.get('enunciado'):
            query = query.filter(Questao.enunciado.ilike(f"%{filtros['enunciado']}%"))

        return query.all()

    def criar_questao_completa(
        self,
        codigo_tipo: str,
        enunciado: str,
        titulo: Optional[str] = None,
        sigla_fonte: Optional[str] = None,
        ano: Optional[int] = None,
        codigo_dificuldade: Optional[str] = None,
        observacoes: Optional[str] = None,
        uuid_imagem_enunciado: Optional[str] = None,
        escala_imagem_enunciado: Optional[float] = 1.0
    ) -> Questao:
        """
        Cria uma questão completa com todas as relações

        Args:
            codigo_tipo: OBJETIVA ou DISCURSIVA
            enunciado: Enunciado da questão
            titulo: Título opcional
            sigla_fonte: Sigla da fonte
            ano: Ano de referência
            codigo_dificuldade: FACIL, MEDIO ou DIFICIL
            observacoes: Observações
            uuid_imagem_enunciado: UUID da imagem
            escala_imagem_enunciado: Escala da imagem

        Returns:
            Questão criada
        """
        # Gerar código legível
        codigo = CodigoGenerator.gerar_codigo_questao(self.session, ano)

        # Buscar UUIDs das relações
        tipo = self.session.query(TipoQuestao).filter_by(codigo=codigo_tipo).first()
        uuid_tipo = tipo.uuid if tipo else None

        uuid_fonte = None
        if sigla_fonte:
            fonte = self.session.query(FonteQuestao).filter_by(sigla=sigla_fonte).first()
            uuid_fonte = fonte.uuid if fonte else None

        uuid_ano = None
        if ano:
            ano_ref = AnoReferencia.criar_ou_obter(self.session, ano)
            uuid_ano = ano_ref.uuid

        uuid_dificuldade = None
        if codigo_dificuldade:
            dif = self.session.query(Dificuldade).filter_by(codigo=codigo_dificuldade).first()
            uuid_dificuldade = dif.uuid if dif else None

        # Criar questão
        questao = Questao(
            codigo=codigo,
            titulo=titulo,
            enunciado=enunciado,
            uuid_tipo_questao=uuid_tipo,
            uuid_fonte=uuid_fonte,
            uuid_ano_referencia=uuid_ano,
            uuid_dificuldade=uuid_dificuldade,
            uuid_imagem_enunciado=uuid_imagem_enunciado,
            escala_imagem_enunciado=escala_imagem_enunciado,
            observacoes=observacoes
        )

        self.session.add(questao)
        self.session.flush()
        return questao

    def adicionar_tag(self, codigo_questao: str, nome_tag: str) -> bool:
        """
        Adiciona uma tag à questão

        Args:
            codigo_questao: Código da questão
            nome_tag: Nome da tag

        Returns:
            True se adicionado, False caso contrário
        """
        questao = self.buscar_por_codigo(codigo_questao)
        tag = self.session.query(Tag).filter_by(nome=nome_tag, ativo=True).first()

        if questao and tag:
            questao.adicionar_tag(self.session, tag)
            return True
        return False

    def remover_tag(self, codigo_questao: str, nome_tag: str) -> bool:
        """
        Remove uma tag da questão

        Args:
            codigo_questao: Código da questão
            nome_tag: Nome da tag

        Returns:
            True se removido, False caso contrário
        """
        questao = self.buscar_por_codigo(codigo_questao)
        tag = self.session.query(Tag).filter_by(nome=nome_tag).first()

        if questao and tag:
            questao.remover_tag(self.session, tag)
            return True
        return False

    def listar_tags(self, codigo_questao: str) -> List[Tag]:
        """
        Lista tags de uma questão

        Args:
            codigo_questao: Código da questão

        Returns:
            Lista de tags
        """
        questao = self.buscar_por_codigo(codigo_questao)
        if questao:
            return [tag for tag in questao.tags if tag.ativo]
        return []

    def obter_alternativa_correta(self, codigo_questao: str):
        """
        Obtém a alternativa correta de uma questão objetiva

        Args:
            codigo_questao: Código da questão

        Returns:
            Alternativa correta ou None
        """
        questao = self.buscar_por_codigo(codigo_questao)
        if questao:
            return questao.obter_alternativa_correta()
        return None

    def listar_por_ano(self, ano: int, ordenar_por: str = 'codigo') -> List[Questao]:
        """
        Lista questões de um ano específico

        Args:
            ano: Ano
            ordenar_por: Campo para ordenação

        Returns:
            Lista de questões ordenadas
        """
        query = self.session.query(Questao).join(AnoReferencia).filter(
            AnoReferencia.ano == ano,
            Questao.ativo == True
        )

        if ordenar_por == 'codigo':
            query = query.order_by(Questao.codigo)
        elif ordenar_por == 'titulo':
            query = query.order_by(Questao.titulo)
        elif ordenar_por == 'data_criacao':
            query = query.order_by(Questao.data_criacao.desc())

        return query.all()

    def estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre as questões

        Returns:
            Dicionário com estatísticas
        """
        total = self.contar()

        stats = {
            'total': total,
            'por_tipo': {},
            'por_dificuldade': {},
            'por_fonte': {},
            'por_ano': {}
        }

        # Por tipo
        tipos = self.session.query(TipoQuestao).all()
        for tipo in tipos:
            count = self.session.query(Questao).filter_by(
                uuid_tipo_questao=tipo.uuid,
                ativo=True
            ).count()
            stats['por_tipo'][tipo.codigo] = count

        # Por dificuldade
        dificuldades = self.session.query(Dificuldade).all()
        for dif in dificuldades:
            count = self.session.query(Questao).filter_by(
                uuid_dificuldade=dif.uuid,
                ativo=True
            ).count()
            stats['por_dificuldade'][dif.codigo] = count

        # Por fonte
        fontes = self.session.query(FonteQuestao).all()
        for fonte in fontes:
            count = self.session.query(Questao).filter_by(
                uuid_fonte=fonte.uuid,
                ativo=True
            ).count()
            stats['por_fonte'][fonte.sigla] = count

        # Por ano
        anos = self.session.query(AnoReferencia).all()
        for ano in anos:
            count = self.session.query(Questao).filter_by(
                uuid_ano_referencia=ano.uuid,
                ativo=True
            ).count()
            stats['por_ano'][ano.ano] = count

        return stats
