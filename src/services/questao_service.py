"""
Service para gerenciar Questões - usa apenas ORM
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.repositories import (
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

    def _gerar_titulo_automatico(
        self,
        tags: Optional[List[str]],
        ano: Optional[int]
    ) -> Optional[str]:
        """
        Gera título automático no formato: FONTE - CONTEÚDO - ANO

        Args:
            tags: Lista de UUIDs de tags
            ano: Ano de referência

        Returns:
            Título gerado ou None se não houver dados suficientes
        """
        if not tags:
            return None

        fonte_nome = None
        conteudo_nome = None

        for tag_uuid in tags:
            if not isinstance(tag_uuid, str):
                continue

            tag = self.tag_repo.buscar_por_uuid(tag_uuid)
            if not tag or not tag.numeracao:
                continue

            # Tag de fonte/vestibular (numeracao começa com 'V')
            if tag.numeracao.startswith('V') and not fonte_nome:
                fonte_nome = tag.nome.upper()

            # Tag de conteúdo (numeracao começa com dígito)
            elif tag.numeracao[0].isdigit() and not conteudo_nome:
                conteudo_nome = tag.nome.upper()

            # Se já encontrou ambos, pode parar
            if fonte_nome and conteudo_nome:
                break

        # Montar título com as partes disponíveis
        partes = []
        if fonte_nome:
            partes.append(fonte_nome)
        if conteudo_nome:
            partes.append(conteudo_nome)
        if ano:
            partes.append(str(ano))

        return ' - '.join(partes) if partes else None

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
        # Gerar título automático se não fornecido
        titulo_final = titulo
        if not titulo or not titulo.strip():
            titulo_final = self._gerar_titulo_automatico(tags, ano)

        # Criar questão
        questao = self.questao_repo.criar_questao_completa(
            codigo_tipo=tipo,
            enunciado=enunciado,
            titulo=titulo_final,
            sigla_fonte=fonte,
            ano=ano,
            codigo_dificuldade=dificuldade,
            observacoes=observacoes
        )

        # Adicionar tags (suporta UUID ou nome)
        if tags:
            for tag_ref in tags:
                # Tentar buscar por UUID primeiro, depois por nome
                tag = self.tag_repo.buscar_por_uuid(tag_ref) if isinstance(tag_ref, str) and len(tag_ref) > 20 else None
                if not tag:
                    tag = self.tag_repo.buscar_por_nome(tag_ref)
                if tag:
                    questao.adicionar_tag(self.session, tag)

        # Adicionar alternativas (apenas para objetivas)
        alternativas_criadas = []
        alternativa_correta_uuid = None
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
                # Identificar alternativa correta
                if alt_data.get('correta'):
                    alternativa_correta_uuid = alternativa.uuid

        # Criar resposta objetiva
        if tipo == 'OBJETIVA' and alternativa_correta_uuid:
            self.resposta_repo.criar_resposta_objetiva(
                codigo_questao=questao.codigo,
                uuid_alternativa_correta=alternativa_correta_uuid,
                resolucao=resposta_objetiva.get('resolucao') if resposta_objetiva else None,
                justificativa=resposta_objetiva.get('justificativa') if resposta_objetiva else None
            )
        elif resposta_objetiva and tipo == 'OBJETIVA':
            # Fallback: usar resposta_objetiva passada diretamente
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
            'tags': [{'uuid': tag.uuid, 'nome': tag.nome, 'numeracao': tag.numeracao} for tag in questao.tags if tag.ativo],
            'niveis_escolares': [{'uuid': nivel.uuid, 'codigo': nivel.codigo, 'nome': nivel.nome} for nivel in questao.niveis_escolares if nivel.ativo],
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
                'id': hash(q.uuid) % 2147483647,  # Converter uuid para int positivo
                'codigo': q.codigo,
                'uuid': q.uuid,
                'titulo': q.titulo,
                'enunciado': q.enunciado,
                'tipo': q.tipo.codigo if q.tipo else None,
                'ano': q.ano.ano if q.ano else None,
                'fonte': q.fonte.sigla if q.fonte else None,
                'dificuldade': q.dificuldade.codigo if q.dificuldade else None,
                'tags': [tag.nome for tag in q.tags if tag.ativo],
                'ativo': q.ativo
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
        import logging
        logger = logging.getLogger(__name__)

        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            logger.warning(f"Questão {codigo} não encontrada")
            return None

        # Tratar tags separadamente (requerem objetos Tag, não IDs)
        tags_ids = kwargs.pop('tags', None)

        # Tratar alternativas separadamente
        alternativas_data = kwargs.pop('alternativas', None)

        # Tratar campos de relacionamento separadamente
        tipo_codigo = kwargs.pop('tipo', None)
        fonte_sigla = kwargs.pop('fonte', None)
        ano_valor = kwargs.pop('ano', None)
        dificuldade_codigo = kwargs.pop('dificuldade', None)

        # Tratar título separadamente para gerar automático se necessário
        titulo = kwargs.pop('titulo', None)

        # Atualizar campos simples (enunciado, observacoes)
        campos_simples = ['enunciado', 'observacoes']
        for key, value in kwargs.items():
            if key in campos_simples:
                setattr(questao, key, value)

        # Gerar título automático se não fornecido
        if titulo is None or (isinstance(titulo, str) and not titulo.strip()):
            titulo = self._gerar_titulo_automatico(tags_ids, ano_valor)
        questao.titulo = titulo

        # Atualizar relacionamentos usando UUIDs de foreign keys
        if tipo_codigo:
            from src.models.orm import TipoQuestao
            tipo = self.session.query(TipoQuestao).filter_by(codigo=tipo_codigo, ativo=True).first()
            if tipo:
                questao.uuid_tipo_questao = tipo.uuid

        if fonte_sigla:
            from src.models.orm import FonteQuestao
            fonte = self.session.query(FonteQuestao).filter_by(sigla=fonte_sigla, ativo=True).first()
            if fonte:
                questao.uuid_fonte = fonte.uuid

        if ano_valor:
            from src.models.orm import AnoReferencia
            ano = AnoReferencia.criar_ou_obter(self.session, ano_valor)
            if ano:
                questao.uuid_ano_referencia = ano.uuid

        if dificuldade_codigo:
            from src.models.orm import Dificuldade
            dificuldade = self.session.query(Dificuldade).filter_by(codigo=dificuldade_codigo, ativo=True).first()
            if dificuldade:
                questao.uuid_dificuldade = dificuldade.uuid

        # Atualizar tags se fornecidas (tags_ids são UUIDs de tags)
        if tags_ids is not None and isinstance(tags_ids, list):
            # Limpar tags existentes usando SQL direto
            from src.models.orm import QuestaoTag
            from sqlalchemy import delete, insert
            self.session.execute(delete(QuestaoTag).where(QuestaoTag.c.uuid_questao == questao.uuid))

            # Adicionar novas tags
            for tag_uuid in tags_ids:
                if tag_uuid and isinstance(tag_uuid, str):
                    tag = self.tag_repo.buscar_por_uuid(tag_uuid)
                    if tag:
                        # Inserir relacionamento diretamente na tabela
                        self.session.execute(
                            insert(QuestaoTag).values(
                                uuid_questao=questao.uuid,
                                uuid_tag=tag.uuid
                            )
                        )

        # Atualizar alternativas se fornecidas
        tipo_atual = tipo_codigo if tipo_codigo else (questao.tipo.codigo if questao.tipo else None)
        if alternativas_data is not None and tipo_atual == 'OBJETIVA':
            alternativas_existentes = self.alternativa_repo.buscar_por_questao(codigo)

            # Identificar qual alternativa deve ser a correta
            alternativa_correta_uuid = None

            for alt_data in alternativas_data:
                letra = alt_data.get('letra')
                texto = alt_data.get('texto')
                correta = alt_data.get('correta', False)

                alt_existente = next(
                    (a for a in alternativas_existentes if a.letra == letra),
                    None
                )

                if alt_existente:
                    alt_existente.texto = texto
                    if correta:
                        alternativa_correta_uuid = alt_existente.uuid

            # Atualizar ou criar resposta com a alternativa correta
            if alternativa_correta_uuid:
                resposta = self.resposta_repo.buscar_por_questao(codigo)
                if resposta:
                    resposta.uuid_alternativa_correta = alternativa_correta_uuid
                else:
                    # Criar resposta se não existir
                    self.resposta_repo.criar_resposta_objetiva(
                        codigo_questao=codigo,
                        uuid_alternativa_correta=alternativa_correta_uuid
                    )

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

    def reativar_questao(self, codigo: str) -> bool:
        """
        Reativa uma questão inativa

        Args:
            codigo: Código da questão

        Returns:
            True se reativada, False se não encontrada
        """
        # Buscar incluindo inativos
        questao = self.questao_repo.buscar_por_codigo(codigo, incluir_inativos=True)
        if questao:
            questao.ativo = True
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

    # =========================================================================
    # Métodos para gerenciamento de variantes (questões semelhantes)
    # =========================================================================

    def criar_variante(
        self,
        codigo_original: str,
        enunciado: str,
        alternativas: Optional[List[Dict[str, Any]]] = None,
        resolucao: Optional[str] = None,
        observacoes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Cria uma variante de uma questão existente.
        A variante herda: tipo, fonte, ano, dificuldade, série/nível, disciplina, tags.
        Permite modificar: enunciado, alternativas, resolução, observações.

        Args:
            codigo_original: Código da questão original
            enunciado: Novo enunciado da variante
            alternativas: Novas alternativas (para objetivas)
            resolucao: Nova resolução
            observacoes: Novas observações

        Returns:
            Dict com dados da variante criada ou None se erro
        """
        import logging
        logger = logging.getLogger(__name__)

        # Buscar questão original
        questao_original = self.questao_repo.buscar_por_codigo(codigo_original)
        if not questao_original:
            logger.warning(f"Questão original {codigo_original} não encontrada")
            return None

        # Verificar se a original já é uma variante (não pode criar variante de variante)
        if self.questao_repo.eh_variante(questao_original.uuid):
            logger.warning(f"Questão {codigo_original} é uma variante. Não é possível criar variante de variante.")
            return None

        # Verificar limite de 3 variantes
        num_variantes = self.questao_repo.contar_variantes(questao_original.uuid)
        if num_variantes >= 3:
            logger.warning(f"Questão {codigo_original} já possui 3 variantes (limite máximo)")
            return None

        # Obter dados herdados da original
        tipo_codigo = questao_original.tipo.codigo if questao_original.tipo else 'OBJETIVA'
        fonte_sigla = questao_original.fonte.sigla if questao_original.fonte else None
        ano = questao_original.ano.ano if questao_original.ano else None
        dificuldade_codigo = questao_original.dificuldade.codigo if questao_original.dificuldade else None
        tags_uuids = [tag.uuid for tag in questao_original.tags if tag.ativo]

        # Gerar título automático com indicação de variante
        titulo_base = questao_original.titulo or ""
        num_variante = num_variantes + 1
        if titulo_base:
            titulo = f"{titulo_base} (Variante {num_variante})"
        else:
            partes = []
            if fonte_sigla:
                partes.append(fonte_sigla)
            if tags_uuids:
                # Pegar primeira tag de conteúdo
                for tag in questao_original.tags:
                    if tag.ativo and tag.numeracao and tag.numeracao[0].isdigit():
                        partes.append(tag.nome.upper())
                        break
            if ano:
                partes.append(str(ano))
            partes.append(f"(Variante {num_variante})")
            titulo = " - ".join(partes) if partes else f"Variante {num_variante}"

        # Criar a variante
        variante = self.questao_repo.criar_questao_completa(
            codigo_tipo=tipo_codigo,
            enunciado=enunciado,
            titulo=titulo,
            sigla_fonte=fonte_sigla,
            ano=ano,
            codigo_dificuldade=dificuldade_codigo,
            observacoes=observacoes
        )

        if not variante:
            logger.error("Falha ao criar questão variante")
            return None

        # Adicionar tags herdadas
        for tag_uuid in tags_uuids:
            tag = self.tag_repo.buscar_por_uuid(tag_uuid)
            if tag:
                variante.adicionar_tag(self.session, tag)

        # Copiar níveis escolares
        for nivel in questao_original.niveis_escolares:
            variante.adicionar_nivel(nivel)

        # Adicionar alternativas (apenas para objetivas)
        alternativas_criadas = []
        alternativa_correta_uuid = None
        if alternativas and tipo_codigo == 'OBJETIVA':
            letra_ordem = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
            for alt_data in alternativas:
                alternativa = self.alternativa_repo.criar(
                    uuid_questao=variante.uuid,
                    letra=alt_data['letra'],
                    ordem=letra_ordem.get(alt_data['letra'], 1),
                    texto=alt_data['texto'],
                    uuid_imagem=alt_data.get('uuid_imagem'),
                    escala_imagem=alt_data.get('escala_imagem', 1.0)
                )
                alternativas_criadas.append(alternativa)
                if alt_data.get('correta'):
                    alternativa_correta_uuid = alternativa.uuid

        # Criar resposta objetiva
        if tipo_codigo == 'OBJETIVA' and alternativa_correta_uuid:
            self.resposta_repo.criar_resposta_objetiva(
                codigo_questao=variante.codigo,
                uuid_alternativa_correta=alternativa_correta_uuid,
                resolucao=resolucao
            )

        # Criar vínculo de versão
        self.questao_repo.criar_vinculo_versao(
            uuid_original=questao_original.uuid,
            uuid_variante=variante.uuid,
            observacao=f"Variante {num_variante} criada"
        )

        self.session.flush()

        return {
            'codigo': variante.codigo,
            'uuid': variante.uuid,
            'titulo': variante.titulo,
            'tipo': tipo_codigo,
            'enunciado': variante.enunciado,
            'codigo_original': codigo_original,
            'numero_variante': num_variante
        }

    def listar_questoes_principais(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista questões que NÃO são variantes, incluindo contagem de variantes.

        Args:
            filtros: Dict com filtros opcionais

        Returns:
            Lista de dicts com dados das questões principais
        """
        questoes = self.questao_repo.listar_questoes_principais(filtros)

        resultado = []
        for q in questoes:
            # Contar variantes desta questão
            num_variantes = self.questao_repo.contar_variantes(q.uuid)

            resultado.append({
                'id': hash(q.uuid) % 2147483647,
                'codigo': q.codigo,
                'uuid': q.uuid,
                'titulo': q.titulo,
                'enunciado': q.enunciado,
                'tipo': q.tipo.codigo if q.tipo else None,
                'ano': q.ano.ano if q.ano else None,
                'fonte': q.fonte.sigla if q.fonte else None,
                'dificuldade': q.dificuldade.codigo if q.dificuldade else None,
                'tags': [tag.nome for tag in q.tags if tag.ativo],
                'ativo': q.ativo,
                'quantidade_variantes': num_variantes
            })

        return resultado

    def obter_variantes(self, codigo: str) -> List[Dict[str, Any]]:
        """
        Obtém lista de variantes de uma questão.

        Args:
            codigo: Código da questão original

        Returns:
            Lista de dicts com dados resumidos das variantes
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return []

        variantes = self.questao_repo.buscar_variantes(questao.uuid)

        return [
            {
                'codigo': v.codigo,
                'uuid': v.uuid,
                'titulo': v.titulo or '',
                'enunciado': (v.enunciado[:100] + '...' if len(v.enunciado or '') > 100 else v.enunciado) or ''
            }
            for v in variantes
        ]

    def obter_original(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a questão original de uma variante.

        Args:
            codigo: Código da questão variante

        Returns:
            Dict com dados da questão original ou None se não for variante
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return None

        original = self.questao_repo.buscar_original(questao.uuid)
        if not original:
            return None

        return {
            'codigo': original.codigo,
            'uuid': original.uuid,
            'titulo': original.titulo
        }

    def eh_variante(self, codigo: str) -> bool:
        """
        Verifica se uma questão é variante de outra.

        Args:
            codigo: Código da questão

        Returns:
            True se for variante, False caso contrário
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return False
        return self.questao_repo.eh_variante(questao.uuid)

    def contar_variantes(self, codigo: str) -> int:
        """
        Conta quantas variantes uma questão possui.

        Args:
            codigo: Código da questão

        Returns:
            Número de variantes
        """
        questao = self.questao_repo.buscar_por_codigo(codigo)
        if not questao:
            return 0
        return self.questao_repo.contar_variantes(questao.uuid)
