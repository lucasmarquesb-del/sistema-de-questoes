"""
Adapters - Compatibilidade entre Controllers ORM e Views Legacy

Este módulo fornece adapters que mantêm a mesma interface das factory functions
antigas (criar_questao_controller, criar_lista_controller, etc) mas usam os
novos controllers ORM por trás.

Isso permite que as views continuem funcionando sem grandes modificações enquanto
usam a nova arquitetura ORM.
"""
from types import SimpleNamespace
from src.controllers import (
    QuestaoControllerORM,
    ListaControllerORM,
    TagControllerORM,
    AlternativaControllerORM
)


def _dict_to_obj(data):
    """Converte dict para objeto com atributos (recursivo)"""
    if data is None:
        return None
    if isinstance(data, dict):
        obj = SimpleNamespace()
        for key, value in data.items():
            setattr(obj, key, _dict_to_obj(value))
        return obj
    if isinstance(data, list):
        return [_dict_to_obj(item) for item in data]
    return data


class QuestaoControllerAdapter:
    """Adapter que simula o antigo QuestaoController mas usa ORM"""

    def criar_questao(self, dto):
        """Cria questão a partir de DTO"""
        dados = {
            'tipo': dto.tipo,
            'enunciado': dto.enunciado,
            'titulo': dto.titulo,
            'fonte': dto.fonte,
            'ano': dto.ano,
            'dificuldade': self._map_dificuldade(dto.id_dificuldade),
            'observacoes': dto.observacoes,
            'tags': dto.tags if hasattr(dto, 'tags') else [],
            'alternativas': [
                {
                    'letra': alt.letra,
                    'texto': alt.texto,
                    'uuid_imagem': getattr(alt, 'uuid_imagem', None),
                    'escala_imagem': getattr(alt, 'escala_imagem', 1.0)
                }
                for alt in (dto.alternativas if hasattr(dto, 'alternativas') else [])
            ]
        }

        # Adicionar resposta
        if hasattr(dto, 'resposta_objetiva') and dto.resposta_objetiva:
            dados['resposta_objetiva'] = {
                'uuid_alternativa_correta': dto.resposta_objetiva.uuid_alternativa_correta,
                'resolucao': getattr(dto.resposta_objetiva, 'resolucao', None),
                'justificativa': getattr(dto.resposta_objetiva, 'justificativa', None)
            }
        elif hasattr(dto, 'resposta_discursiva') and dto.resposta_discursiva:
            dados['resposta_discursiva'] = {
                'gabarito': dto.resposta_discursiva.gabarito,
                'resolucao': getattr(dto.resposta_discursiva, 'resolucao', None),
                'justificativa': getattr(dto.resposta_discursiva, 'justificativa', None)
            }

        return QuestaoControllerORM.criar_questao_completa(dados)

    def buscar_por_id(self, questao_id):
        """Busca questão por ID (agora por código)"""
        # Se for um ID inteiro, converter para código
        if isinstance(questao_id, int):
            codigo = f"Q-2024-{questao_id:04d}"
        else:
            codigo = questao_id
        return QuestaoControllerORM.buscar_questao(codigo)

    def obter_questao_completa(self, questao_id):
        """Obtém questão com todos os dados"""
        result = self.buscar_por_id(questao_id)
        return _dict_to_obj(result)

    def buscar_questoes(self, filtros=None):
        """Busca questões com filtros"""
        return QuestaoControllerORM.listar_questoes(filtros)

    def atualizar_questao(self, questao_id, dto):
        """Atualiza questão"""
        if isinstance(questao_id, int):
            codigo = f"Q-2024-{questao_id:04d}"
        else:
            codigo = questao_id

        dados = {
            'titulo': dto.titulo,
            'enunciado': dto.enunciado,
            'tipo': dto.tipo,
            'ano': dto.ano,
            'fonte': dto.fonte,
            'dificuldade': self._map_dificuldade(dto.id_dificuldade),
            'observacoes': dto.observacoes
        }
        return QuestaoControllerORM.atualizar_questao(codigo, **dados)

    def atualizar_questao_completa(self, dto):
        """Atualiza questão completa a partir de DTO"""
        questao_id = dto.id_questao
        if isinstance(questao_id, int):
            codigo = f"Q-2024-{questao_id:04d}"
        else:
            codigo = questao_id

        dados = {
            'titulo': dto.titulo,
            'enunciado': dto.enunciado,
            'tipo': dto.tipo,
            'ano': dto.ano,
            'fonte': dto.fonte,
            'dificuldade': self._map_dificuldade(dto.id_dificuldade),
            'observacoes': getattr(dto, 'observacoes', None),
            'tags': getattr(dto, 'tags', []),
            'alternativas': [
                {
                    'letra': alt.get('letra') if isinstance(alt, dict) else alt.letra,
                    'texto': alt.get('texto') if isinstance(alt, dict) else alt.texto,
                    'correta': alt.get('correta') if isinstance(alt, dict) else getattr(alt, 'correta', False)
                }
                for alt in (dto.alternativas if hasattr(dto, 'alternativas') else [])
            ]
        }
        return QuestaoControllerORM.atualizar_questao(codigo, **dados)

    def criar_questao_completa(self, dto):
        """Alias para criar_questao"""
        return self.criar_questao(dto)

    def deletar_questao(self, questao_id):
        """Deleta questão (soft delete / inativar)"""
        if isinstance(questao_id, int):
            codigo = f"Q-2024-{questao_id:04d}"
        else:
            codigo = questao_id
        return QuestaoControllerORM.deletar_questao(codigo)

    def reativar_questao(self, questao_id):
        """Reativa uma questão inativa"""
        if isinstance(questao_id, int):
            codigo = f"Q-2024-{questao_id:04d}"
        else:
            codigo = questao_id
        return QuestaoControllerORM.reativar_questao(codigo)

    def _map_dificuldade(self, id_dificuldade):
        """Mapeia ID de dificuldade para código"""
        mapa = {
            1: 'FACIL',
            2: 'MEDIO',
            3: 'DIFICIL',
            4: None
        }
        return mapa.get(id_dificuldade)


class ListaControllerAdapter:
    """Adapter que simula o antigo ListaController mas usa ORM"""

    def criar_lista(self, dto):
        """Cria lista a partir de DTO"""
        return ListaControllerORM.criar_lista(
            titulo=dto.titulo,
            tipo=dto.tipo,
            cabecalho=getattr(dto, 'cabecalho', None),
            instrucoes=getattr(dto, 'instrucoes', None),
            codigos_questoes=getattr(dto, 'codigos_questoes', None)
        )

    def buscar_por_id(self, lista_id):
        """Busca lista por ID (agora por código)"""
        if isinstance(lista_id, int):
            codigo = f"LST-2026-{lista_id:04d}"
        else:
            codigo = lista_id
        return ListaControllerORM.buscar_lista(codigo)

    def obter_lista_completa(self, lista_id):
        """Obtém lista com todos os dados incluindo questões"""
        result = self.buscar_por_id(lista_id)
        return _dict_to_obj(result)

    def listar_todas(self):
        """Lista todas as listas"""
        return ListaControllerORM.listar_listas()

    def listar_todas_listas(self):
        """Alias para listar_todas - compatibilidade"""
        return self.listar_todas()

    def adicionar_questao(self, lista_id, questao_id):
        """Adiciona questão à lista"""
        if isinstance(lista_id, int):
            codigo_lista = f"LST-2026-{lista_id:04d}"
        else:
            codigo_lista = lista_id

        if isinstance(questao_id, int):
            codigo_questao = f"Q-2024-{questao_id:04d}"
        else:
            codigo_questao = questao_id

        return ListaControllerORM.adicionar_questao(codigo_lista, codigo_questao)

    def remover_questao(self, lista_id, questao_id):
        """Remove questão da lista"""
        if isinstance(lista_id, int):
            codigo_lista = f"LST-2026-{lista_id:04d}"
        else:
            codigo_lista = lista_id

        if isinstance(questao_id, int):
            codigo_questao = f"Q-2024-{questao_id:04d}"
        else:
            codigo_questao = questao_id

        return ListaControllerORM.remover_questao(codigo_lista, codigo_questao)

    def atualizar_lista(self, dto):
        """Atualiza lista a partir de DTO"""
        lista_id = getattr(dto, 'id_lista', None) or getattr(dto, 'codigo', None)
        if isinstance(lista_id, int):
            codigo = f"LST-2026-{lista_id:04d}"
        else:
            codigo = lista_id

        return ListaControllerORM.atualizar_lista(
            codigo=codigo,
            titulo=getattr(dto, 'titulo', None),
            tipo=getattr(dto, 'tipo', None),
            cabecalho=getattr(dto, 'cabecalho', None),
            instrucoes=getattr(dto, 'instrucoes', None)
        )

    def deletar_lista(self, lista_id):
        """Deleta lista (soft delete)"""
        if isinstance(lista_id, int):
            codigo = f"LST-2026-{lista_id:04d}"
        else:
            codigo = lista_id
        return ListaControllerORM.deletar_lista(codigo)


class TagControllerAdapter:
    """Adapter que simula o antigo TagController mas usa ORM"""

    def obter_arvore_tags_completa(self):
        """Retorna árvore hierárquica de tags"""
        return TagControllerORM.obter_arvore_hierarquica()

    def obter_arvore_conteudos(self):
        """Retorna árvore hierárquica apenas de tags de conteúdos (exclui banca e etapa)"""
        return TagControllerORM.obter_arvore_conteudos()

    def listar_series(self):
        """Lista tags de série/nível de escolaridade"""
        return TagControllerORM.listar_series()

    def listar_todas(self):
        """Lista todas as tags"""
        return TagControllerORM.listar_todas()

    def buscar_por_nome(self, nome):
        """Busca tag por nome"""
        return TagControllerORM.buscar_por_nome(nome)

    def buscar_por_id(self, tag_id):
        """Busca tag por ID (agora retorna por numeração aproximada)"""
        # Para compatibilidade, retornar a primeira tag
        tags = TagControllerORM.listar_todas()
        if tags and len(tags) > tag_id - 1:
            return tags[tag_id - 1]
        return None


# Factory functions para manter compatibilidade com código existente
def criar_questao_controller():
    """Factory para criar QuestaoController (adapter)"""
    return QuestaoControllerAdapter()


def criar_lista_controller():
    """Factory para criar ListaController (adapter)"""
    return ListaControllerAdapter()


def criar_tag_controller():
    """Factory para criar TagController (adapter)"""
    return TagControllerAdapter()


def criar_export_controller():
    """Factory para criar ExportController"""
    from src.controllers.export_controller import ExportController
    return ExportController()


def listar_fontes_questao():
    """Lista todas as fontes de questão (bancas/vestibulares) ativas"""
    from database import session_manager
    from models.orm import FonteQuestao

    session = session_manager.create_session()
    try:
        fontes = session.query(FonteQuestao).filter_by(ativo=True).order_by(FonteQuestao.sigla).all()
        return [{'uuid': f.uuid, 'sigla': f.sigla, 'nome_completo': f.nome_completo} for f in fontes]
    finally:
        session.close()
