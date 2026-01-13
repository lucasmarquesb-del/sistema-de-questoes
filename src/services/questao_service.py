"""
Service para gerenciar Questões - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from repositories import (
    QuestaoRepository,
    AlternativaRepository,
    RespostaQuestaoRepository,
    TagRepository
)


class QuestaoService:
    """Service para operações de negócio com questões"""

    def __init__(self, session: Session):
        """
        Inicializa service com sessão

        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
        self.questao_repo = QuestaoRepository(session)
        self.alternativa_repo = AlternativaRepository(session)
        self.resposta_repo = RespostaQuestaoRepository(session)
        self.tag_repo = TagRepository(session)

    def criar_questao(
        self,
        tipo: str,
        enunciado: str,
        titulo: Optional[str] = None,
        fonte: Optional[str] = None,
        ano: Optional[int] = None,
        dificuldade: Optional[str] = None,
        observacoes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        alternativas: Optional[List[Dict[str, Any]]] = None,
        resposta_objetiva: Optional[Dict[str, Any]] = None,
        resposta_discursiva: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma questão completa com alternativas e resposta

        Args:
            tipo: OBJETIVA ou DISCURSIVA
            enunciado: Enunciado da questão
            titulo: Título opcional
            fonte: Sigla da fonte (ENEM, FUVEST, etc.)
            ano: Ano de referência
            dificuldade: FACIL, MEDIO ou DIFICIL
            observacoes: Observações
            tags: Lista de nomes de tags
            alternativas: Lista de dicts com dados das alternativas
            resposta_objetiva: Dict com uuid_alternativa_correta e resolucao
            resposta_discursiva: Dict com gabarito_discursivo e resolucao

        Returns:
            Dict com dados da questão criada
        """
        # Criar questão
        questao = self.questao_repo.criar_questao_completa(
            codigo_tipo=tipo,
            enunciado=enunciado,
            titulo=titulo,
            sigla_fonte=fonte,
            ano=ano,
            codigo_dificuldade=dificuldade,
            observacoes=observacoes
        )

        # Adicionar tags
        if tags:
            for nome_tag in tags:
                tag = self.tag_repo.buscar_por_nome(nome_tag)
                if tag:
                    questao.adicionar_tag(self.session, tag)

        # Adicionar alternativas (apenas para objetivas)
        alternativas_criadas = []
        if alternativas and tipo == 'OBJETIVA':
            letra_ordem = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
            for alt_data in alternativas:
                alternativa = self.alternativa_repo.criar(
                    uuid_questao=questao.uuid,
                    letra=alt_data['letra'],
                    ordem=letra_ordem.get(alt_data['letra'], 1),
                    texto=alt_data['texto'],
                    uuid_imagem=alt_data.get('uuid_imagem'),
                    escala_imagem=alt_data.get('escala_imagem', 1.0)
                )
                alternativas_criadas.append(alternativa)

        # Criar resposta
        if resposta_objetiva and tipo == 'OBJETIVA':
            self.resposta_repo.criar_resposta_objetiva(
                codigo_questao=questao.codigo,
                uuid_alternativa_correta=resposta_objetiva['uuid_alternativa_correta'],
                resolucao=resposta_objetiva.get('resolucao'),
                justificativa=resposta_objetiva.get('justificativa')
            )

        if resposta_discursiva and tipo == 'DISCURSIVA':
            self.resposta_repo.criar_resposta_discursiva(
                codigo_questao=questao.codigo,
                gabarito_discursivo=resposta_discursiva['gabarito'],
                resolucao=resposta_discursiva.get('resolucao'),
                justificativa=resposta_discursiva.get('justificativa')
            )

        self.session.flush()

        return {
            'codigo': questao.codigo,
            'uuid': questao.uuid,
            'titulo': questao.titulo,
            'tipo': tipo,
            'enunciado': questao.enunciado,
            'alternativas': [
                {
                    'uuid': alt.uuid,
                    'letra': alt.letra,
                    'texto': alt.texto
                }
                for alt in alternativas_criadas
            ]
        }

    def buscar_questao(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Busca questão por código

        Args:
            codigo: Código da questão (Q-XXXX-YYYY)

        Returns:
            Dict com dados completos da questão
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return None

        # Buscar alternativas
        alternativas = self.alternativa_repo.buscar_por_questao(codigo)

        # Buscar resposta
        resposta = self.resposta_repo.buscar_por_questao(codigo)

        return {
            'codigo': questao.codigo,
            'uuid': questao.uuid,
            'titulo': questao.titulo,
            'tipo': questao.tipo.codigo if questao.tipo else None,
            'enunciado': questao.enunciado,
            'ano': questao.ano.ano if questao.ano else None,
            'fonte': questao.fonte.sigla if questao.fonte else None,
            'dificuldade': questao.dificuldade.codigo if questao.dificuldade else None,
            'observacoes': questao.observacoes,
            'tags': [tag.nome for tag in questao.tags if tag.ativo],
            'alternativas': [
                {
                    'uuid': alt.uuid,
                    'letra': alt.letra,
                    'ordem': alt.ordem,
                    'texto': alt.texto,
                    'correta': (resposta and resposta.uuid_alternativa_correta == alt.uuid) if resposta else False
                }
                for alt in alternativas
            ],
            'resposta': {
                'resolucao': resposta.resolucao if resposta else None,
                'gabarito_discursivo': resposta.gabarito_discursivo if resposta else None
            } if resposta else None
        }

    def listar_questoes(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista questões com filtros opcionais

        Args:
            filtros: Dict com filtros (fonte, ano, tags, dificuldade, tipo, titulo)

        Returns:
            Lista de dicts com dados das questões
        """
        if filtros:
            questoes = self.questao_repo.buscar_com_filtros(filtros)
        else:
            questoes = self.questao_repo.listar_todos()

        return [
            {
                'codigo': q.codigo,
                'uuid': q.uuid,
                'titulo': q.titulo,
                'tipo': q.tipo.codigo if q.tipo else None,
                'ano': q.ano.ano if q.ano else None,
                'fonte': q.fonte.sigla if q.fonte else None,
                'dificuldade': q.dificuldade.codigo if q.dificuldade else None,
                'tags': [tag.nome for tag in q.tags if tag.ativo]
            }
            for q in questoes
        ]

    def atualizar_questao(
        self,
        codigo: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma questão

        Args:
            codigo: Código da questão
            **kwargs: Campos a atualizar

        Returns:
            Dict com dados atualizados
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return None

        # Atualizar campos simples
        for key, value in kwargs.items():
            if hasattr(questao, key) and key not in ['codigo', 'uuid']:
                setattr(questao, key, value)

        self.session.flush()
        return self.buscar_questao(codigo)

    def deletar_questao(self, codigo: str) -> bool:
        """
        Desativa uma questão (soft delete)

        Args:
            codigo: Código da questão

        Returns:
            True se desativada, False se não encontrada
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if questao:
            questao.ativo = False
            self.session.flush()
            return True
        return False

    def adicionar_tag(self, codigo_questao: str, nome_tag: str) -> bool:
        """Adiciona tag à questão"""
        return self.questao_repo.adicionar_tag(codigo_questao, nome_tag)

    def remover_tag(self, codigo_questao: str, nome_tag: str) -> bool:
        """Remove tag da questão"""
        return self.questao_repo.remover_tag(codigo_questao, nome_tag)

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre questões"""
        return self.questao_repo.estatisticas()
