"""
Service: Validation
DESCRIÇÃO: Serviço especializado em validação de dados de questões
RESPONSABILIDADE ÚNICA: Validar dados antes de criar/atualizar questões
BENEFÍCIOS:
    - Centraliza lógica de validação
    - Facilita testes unitários
    - Permite extensão de regras sem modificar controller
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from src.domain.value_objects import TipoQuestao, Dificuldade, LetraAlternativa

logger = logging.getLogger(__name__)


class ValidationResult:
    """Resultado de validação"""

    def __init__(self):
        self.erros: List[str] = []
        self.avisos: List[str] = []

    @property
    def valido(self) -> bool:
        """Retorna se validação passou (sem erros)"""
        return len(self.erros) == 0

    def adicionar_erro(self, mensagem: str):
        """Adiciona um erro"""
        self.erros.append(mensagem)
        logger.warning(f"Erro de validação: {mensagem}")

    def adicionar_aviso(self, mensagem: str):
        """Adiciona um aviso (não impede a operação)"""
        self.avisos.append(mensagem)
        logger.info(f"Aviso de validação: {mensagem}")

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'valido': self.valido,
            'erros': self.erros,
            'avisos': self.avisos
        }


class ValidationService:
    """Serviço de validação de questões"""

    @staticmethod
    def validar_questao_completa(dados: Dict[str, Any]) -> ValidationResult:
        """Valida dados completos de uma questão

        Args:
            dados: Dicionário com dados da questão
                - enunciado (str): Texto do enunciado
                - tipo (str): 'OBJETIVA' ou 'DISCURSIVA'
                - ano (int, opcional): Ano da questão
                - fonte (str, opcional): Fonte da questão
                - id_dificuldade (int): ID da dificuldade (1, 2 ou 3)
                - alternativas (list, opcional): Lista de alternativas (se objetiva)
                - tags (list, opcional): Lista de IDs de tags
                - imagem_enunciado (str, opcional): Caminho da imagem
                - escala_imagem_enunciado (float, opcional): Escala da imagem

        Returns:
            ValidationResult com erros e avisos
        """
        result = ValidationResult()

        # Validações obrigatórias
        ValidationService._validar_enunciado(dados, result)
        ValidationService._validar_tipo(dados, result)
        ValidationService._validar_dificuldade(dados, result)

        # Validações opcionais
        ValidationService._validar_ano(dados, result)
        ValidationService._validar_alternativas(dados, result)
        ValidationService._validar_tags(dados, result)
        ValidationService._validar_imagem(dados, result)

        logger.info(
            f"Validação de questão: "
            f"{'PASSOU' if result.valido else 'FALHOU'} "
            f"({len(result.erros)} erros, {len(result.avisos)} avisos)"
        )

        return result

    @staticmethod
    def _validar_enunciado(dados: Dict[str, Any], result: ValidationResult):
        """Valida enunciado"""
        enunciado = dados.get('enunciado', '').strip()

        if not enunciado:
            result.adicionar_erro("Enunciado é obrigatório")
            return

        if len(enunciado) < 10:
            result.adicionar_aviso(
                f"Enunciado muito curto ({len(enunciado)} caracteres). "
                "Considere adicionar mais contexto."
            )

        if len(enunciado) > 5000:
            result.adicionar_aviso(
                f"Enunciado muito longo ({len(enunciado)} caracteres). "
                "Considere dividir em múltiplas questões."
            )

    @staticmethod
    def _validar_tipo(dados: Dict[str, Any], result: ValidationResult):
        """Valida tipo de questão"""
        tipo_str = dados.get('tipo', '').strip()

        if not tipo_str:
            result.adicionar_erro("Tipo de questão é obrigatório")
            return

        try:
            TipoQuestao.from_string(tipo_str)
        except ValueError as e:
            result.adicionar_erro(str(e))

    @staticmethod
    def _validar_dificuldade(dados: Dict[str, Any], result: ValidationResult):
        """Valida dificuldade"""
        id_dificuldade = dados.get('id_dificuldade')

        if id_dificuldade is None:
            result.adicionar_erro("Dificuldade é obrigatória")
            return

        try:
            Dificuldade.from_id(id_dificuldade)
        except ValueError as e:
            result.adicionar_erro(str(e))

    @staticmethod
    def _validar_ano(dados: Dict[str, Any], result: ValidationResult):
        """Valida ano"""
        ano = dados.get('ano')

        if ano is None:
            return  # Ano é opcional

        if not isinstance(ano, int):
            result.adicionar_erro("Ano deve ser um número inteiro")
            return

        ano_atual = datetime.now().year

        if ano < 1900:
            result.adicionar_erro("Ano não pode ser anterior a 1900")

        if ano > ano_atual + 1:
            result.adicionar_erro(
                f"Ano não pode ser superior a {ano_atual + 1}"
            )

        if ano > ano_atual:
            result.adicionar_aviso(
                f"Ano {ano} está no futuro. Verifique se está correto."
            )

    @staticmethod
    def _validar_alternativas(dados: Dict[str, Any], result: ValidationResult):
        """Valida alternativas (se questão objetiva)"""
        tipo_str = dados.get('tipo', '').strip()

        # Se tipo inválido, validação de tipo já capturou
        try:
            tipo = TipoQuestao.from_string(tipo_str)
        except ValueError:
            return

        alternativas = dados.get('alternativas', [])

        if tipo == TipoQuestao.DISCURSIVA:
            if alternativas:
                result.adicionar_aviso(
                    "Questão discursiva não deve ter alternativas. "
                    "Elas serão ignoradas."
                )
            return

        # Questão objetiva - validar alternativas
        if not alternativas:
            result.adicionar_erro(
                "Questão objetiva deve ter alternativas"
            )
            return

        # Validar quantidade
        total_esperado = LetraAlternativa.total_obrigatorio()
        if len(alternativas) != total_esperado:
            result.adicionar_erro(
                f"Questão objetiva deve ter exatamente {total_esperado} alternativas, "
                f"mas tem {len(alternativas)}"
            )
            return

        # Validar letras únicas
        letras_vistas = set()
        letras_esperadas = {letra.value for letra in LetraAlternativa.todas()}

        for alt in alternativas:
            letra = alt.get('letra', '').strip().upper()

            if not letra:
                result.adicionar_erro("Alternativa sem letra")
                continue

            if letra in letras_vistas:
                result.adicionar_erro(f"Letra {letra} duplicada")

            if letra not in letras_esperadas:
                result.adicionar_erro(
                    f"Letra {letra} inválida. "
                    f"Letras válidas: {', '.join(sorted(letras_esperadas))}"
                )

            letras_vistas.add(letra)

        # Validar textos
        for alt in alternativas:
            letra = alt.get('letra', '?')
            texto = alt.get('texto', '').strip()

            if not texto:
                result.adicionar_erro(
                    f"Alternativa {letra} sem texto"
                )

            if len(texto) < 2:
                result.adicionar_aviso(
                    f"Alternativa {letra} muito curta ({len(texto)} caracteres)"
                )

        # Validar alternativa correta
        corretas = [alt for alt in alternativas if alt.get('correta', False)]

        if len(corretas) == 0:
            result.adicionar_erro(
                "Deve haver pelo menos uma alternativa correta"
            )
        elif len(corretas) > 1:
            letras_corretas = [alt.get('letra', '?') for alt in corretas]
            result.adicionar_erro(
                f"Deve haver apenas uma alternativa correta, "
                f"mas {len(corretas)} estão marcadas: {', '.join(letras_corretas)}"
            )

    @staticmethod
    def _validar_tags(dados: Dict[str, Any], result: ValidationResult):
        """Valida tags"""
        tags = dados.get('tags', [])

        if not tags:
            result.adicionar_aviso(
                "Nenhuma tag selecionada. "
                "Recomenda-se adicionar tags para facilitar a busca."
            )
            return

        if not isinstance(tags, list):
            result.adicionar_erro("Tags devem ser uma lista de IDs")
            return

        # Validar IDs
        for tag_id in tags:
            if not isinstance(tag_id, int) or tag_id <= 0:
                result.adicionar_erro(
                    f"ID de tag inválido: {tag_id}"
                )

        if len(tags) > 10:
            result.adicionar_aviso(
                f"Muitas tags selecionadas ({len(tags)}). "
                "Considere usar apenas as mais relevantes."
            )

    @staticmethod
    def _validar_imagem(dados: Dict[str, Any], result: ValidationResult):
        """Valida dados de imagem"""
        imagem = dados.get('imagem_enunciado')
        escala = dados.get('escala_imagem_enunciado')

        if not imagem:
            return  # Imagem é opcional

        if escala is not None:
            if not isinstance(escala, (int, float)):
                result.adicionar_erro(
                    "Escala de imagem deve ser um número"
                )
            elif not (0 < escala <= 1):
                result.adicionar_erro(
                    "Escala de imagem deve estar entre 0 e 1"
                )

    @staticmethod
    def validar_alternativas_conjunto(
        alternativas: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Valida conjunto de alternativas isoladamente

        Args:
            alternativas: Lista de dicionários com dados de alternativas

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        dados = {
            'tipo': 'OBJETIVA',
            'alternativas': alternativas,
            'enunciado': 'validacao',  # Dummy para não falhar
            'id_dificuldade': 1  # Dummy
        }

        ValidationService._validar_alternativas(dados, result)

        return result
