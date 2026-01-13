"""
Adapter para manter compatibilidade entre código antigo e novo ORM
Permite migração gradual sem quebrar código existente
"""
from typing import List, Dict, Any, Optional
from database.session_manager import session_manager
from repositories import (
    QuestaoRepository,
    AlternativaRepository,
    RespostaQuestaoRepository,
    TagRepository,
    DificuldadeRepository,
    FonteQuestaoRepository,
    AnoReferenciaRepository,
    TipoQuestaoRepository
)


class QuestaoAdapter:
    """
    Adapter que expõe interface antiga mas usa repositories novos internamente
    Permite migração gradual do código
    """

    def __init__(self):
        """Inicializa adapter"""
        self.session = None
        self.questao_repo = None
        self.alternativa_repo = None
        self.resposta_repo = None
        self.tag_repo = None

    def _ensure_session(self):
        """Garante que há uma sessão ativa"""
        if self.session is None:
            self.session = session_manager.create_session()
            self.questao_repo = QuestaoRepository(self.session)
            self.alternativa_repo = AlternativaRepository(self.session)
            self.resposta_repo = RespostaQuestaoRepository(self.session)
            self.tag_repo = TagRepository(self.session)

    def criar_questao(
        self,
        tipo: str,
        enunciado: str,
        titulo: str = None,
        fonte: str = None,
        ano: int = None,
        dificuldade: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria questão (interface antiga)

        Returns:
            Dict com dados da questão criada
        """
        self._ensure_session()

        # Mapear dificuldade antiga → nova
        dificuldade_map = {
            'FÁCIL': 'FACIL',
            'MÉDIO': 'MEDIO',
            'DIFÍCIL': 'DIFICIL'
        }
        codigo_dificuldade = dificuldade_map.get(dificuldade, dificuldade)

        questao = self.questao_repo.criar_questao_completa(
            codigo_tipo=tipo,
            enunciado=enunciado,
            titulo=titulo,
            sigla_fonte=fonte,
            ano=ano,
            codigo_dificuldade=codigo_dificuldade,
            observacoes=kwargs.get('observacoes'),
            uuid_imagem_enunciado=kwargs.get('imagem_enunciado'),
            escala_imagem_enunciado=kwargs.get('escala_imagem_enunciado', 1.0)
        )

        self.session.commit()

        return {
            'id_questao': questao.codigo,  # Retorna código ao invés de ID numérico
            'uuid': questao.uuid,
            'codigo': questao.codigo,
            'titulo': questao.titulo,
            'tipo': tipo,
            'enunciado': questao.enunciado
        }

    def buscar_questao(self, id_questao: Any) -> Optional[Dict[str, Any]]:
        """
        Busca questão por ID antigo ou código novo

        Args:
            id_questao: ID numérico antigo ou código (Q-XXXX-YYYY)

        Returns:
            Dict com dados da questão ou None
        """
        self._ensure_session()

        # Se for string começando com Q-, é código novo
        if isinstance(id_questao, str) and id_questao.startswith('Q-'):
            questao = self.questao_repo.buscar_por_codigo(id_questao)
        else:
            # Tenta buscar por código assumindo formato antigo
            questao = self.questao_repo.buscar_por_codigo(str(id_questao))

        if not questao:
            return None

        return {
            'id_questao': questao.codigo,
            'uuid': questao.uuid,
            'codigo': questao.codigo,
            'titulo': questao.titulo,
            'tipo': questao.tipo.codigo if questao.tipo else None,
            'enunciado': questao.enunciado,
            'ano': questao.ano.ano if questao.ano else None,
            'fonte': questao.fonte.sigla if questao.fonte else None,
            'dificuldade': questao.dificuldade.codigo if questao.dificuldade else None,
            'observacoes': questao.observacoes,
            'ativo': questao.ativo,
            'data_criacao': questao.data_criacao
        }

    def listar_questoes(self, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Lista questões com filtros opcionais

        Args:
            filtros: Dict com filtros (fonte, ano, tags, etc.)

        Returns:
            Lista de dicts com dados das questões
        """
        self._ensure_session()

        if filtros:
            questoes = self.questao_repo.buscar_com_filtros(filtros)
        else:
            questoes = self.questao_repo.listar_todos()

        return [
            {
                'id_questao': q.codigo,
                'uuid': q.uuid,
                'codigo': q.codigo,
                'titulo': q.titulo,
                'tipo': q.tipo.codigo if q.tipo else None,
                'ano': q.ano.ano if q.ano else None,
                'fonte': q.fonte.sigla if q.fonte else None
            }
            for q in questoes
        ]

    def adicionar_alternativa(
        self,
        id_questao: Any,
        letra: str,
        texto: str,
        correta: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Adiciona alternativa a uma questão

        Args:
            id_questao: ID ou código da questão
            letra: Letra da alternativa (A-E)
            texto: Texto da alternativa
            correta: Se é a alternativa correta

        Returns:
            Dict com dados da alternativa
        """
        self._ensure_session()

        # Buscar questão
        if isinstance(id_questao, str) and id_questao.startswith('Q-'):
            questao = self.questao_repo.buscar_por_codigo(id_questao)
        else:
            questao = self.questao_repo.buscar_por_codigo(str(id_questao))

        if not questao:
            raise ValueError(f"Questão não encontrada: {id_questao}")

        # Calcular ordem pela letra
        letra_ordem = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
        ordem = letra_ordem.get(letra, 1)

        # Criar alternativa
        alternativa = self.alternativa_repo.criar(
            uuid_questao=questao.uuid,
            letra=letra,
            ordem=ordem,
            texto=texto,
            uuid_imagem=kwargs.get('imagem'),
            escala_imagem=kwargs.get('escala_imagem', 1.0)
        )

        # Se for correta, criar/atualizar resposta
        if correta:
            self.resposta_repo.criar_resposta_objetiva(
                codigo_questao=questao.codigo,
                uuid_alternativa_correta=alternativa.uuid,
                resolucao=kwargs.get('resolucao')
            )

        self.session.commit()

        return {
            'id_alternativa': alternativa.uuid,
            'uuid': alternativa.uuid,
            'letra': alternativa.letra,
            'texto': alternativa.texto
        }

    def adicionar_tag(self, id_questao: Any, nome_tag: str) -> bool:
        """Adiciona tag a uma questão"""
        self._ensure_session()

        codigo = id_questao if isinstance(id_questao, str) and id_questao.startswith('Q-') else str(id_questao)
        sucesso = self.questao_repo.adicionar_tag(codigo, nome_tag)

        if sucesso:
            self.session.commit()

        return sucesso

    def commit(self):
        """Faz commit da sessão"""
        if self.session:
            self.session.commit()

    def rollback(self):
        """Faz rollback da sessão"""
        if self.session:
            self.session.rollback()

    def close(self):
        """Fecha a sessão"""
        if self.session:
            self.session.close()
            self.session = None


# Instância global para uso como singleton
questao_adapter = QuestaoAdapter()
