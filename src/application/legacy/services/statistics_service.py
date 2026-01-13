"""
Service: Statistics
DESCRIÇÃO: Serviço especializado em geração de estatísticas
RESPONSABILIDADE ÚNICA: Calcular e agregar estatísticas do sistema
BENEFÍCIOS:
    - Isola lógica de estatísticas do controller
    - Facilita cache e otimização de queries
    - Permite adicionar novas métricas sem modificar controller
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.domain.interfaces import IQuestaoRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    """Serviço de estatísticas do sistema"""

    def __init__(self, questao_repository: IQuestaoRepository):
        """
        Args:
            questao_repository: Repositório de questões
        """
        self.questao_repository = questao_repository

    def obter_estatisticas_gerais(self) -> Dict[str, Any]:
        """Obtém estatísticas gerais do sistema

        Returns:
            Dicionário com estatísticas:
            {
                'total_questoes': int,
                'total_ativas': int,
                'total_inativas': int,
                'por_tipo': {'OBJETIVA': int, 'DISCURSIVA': int},
                'taxa_ativas': float
            }
        """
        try:
            total_ativas = self.questao_repository.contar_total(ativa=True)
            total_todas = self.questao_repository.contar_total(ativa=False)
            total_inativas = total_todas - total_ativas

            por_tipo_ativas = self.questao_repository.contar_por_tipo(ativa=True)

            taxa_ativas = (total_ativas / total_todas * 100) if total_todas > 0 else 0

            estatisticas = {
                'total_questoes': total_todas,
                'total_ativas': total_ativas,
                'total_inativas': total_inativas,
                'por_tipo': por_tipo_ativas,
                'taxa_ativas': round(taxa_ativas, 1)
            }

            logger.info(f"Estatísticas gerais calculadas: {estatisticas}")

            return estatisticas

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas gerais: {e}", exc_info=True)
            return {
                'total_questoes': 0,
                'total_ativas': 0,
                'total_inativas': 0,
                'por_tipo': {},
                'taxa_ativas': 0
            }

    def obter_estatisticas_por_dificuldade(self) -> Dict[int, int]:
        """Obtém contagem de questões por dificuldade

        Returns:
            Dicionário {id_dificuldade: contagem}
            Exemplo: {1: 10, 2: 15, 3: 5}
        """
        try:
            estatisticas = {}

            for id_dificuldade in [1, 2, 3]:  # FACIL, MEDIO, DIFICIL
                questoes = self.questao_repository.buscar_por_filtros(
                    id_dificuldade=id_dificuldade,
                    ativa=True
                )
                estatisticas[id_dificuldade] = len(questoes)

            logger.info(f"Estatísticas por dificuldade: {estatisticas}")

            return estatisticas

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas por dificuldade: {e}", exc_info=True)
            return {1: 0, 2: 0, 3: 0}

    def obter_estatisticas_por_ano(
        self,
        ano_inicio: Optional[int] = None,
        ano_fim: Optional[int] = None
    ) -> Dict[int, int]:
        """Obtém contagem de questões por ano

        Args:
            ano_inicio: Ano inicial (opcional)
            ano_fim: Ano final (opcional)

        Returns:
            Dicionário {ano: contagem}
        """
        try:
            # Se não especificado, usar últimos 10 anos
            if ano_fim is None:
                ano_fim = datetime.now().year

            if ano_inicio is None:
                ano_inicio = ano_fim - 9

            estatisticas = {}

            for ano in range(ano_inicio, ano_fim + 1):
                questoes = self.questao_repository.buscar_por_filtros(
                    ano=ano,
                    ativa=True
                )
                estatisticas[ano] = len(questoes)

            logger.info(
                f"Estatísticas por ano ({ano_inicio}-{ano_fim}): "
                f"{sum(estatisticas.values())} questões"
            )

            return estatisticas

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas por ano: {e}", exc_info=True)
            return {}

    def obter_estatisticas_por_fonte(
        self,
        limite: int = 10
    ) -> Dict[str, int]:
        """Obtém contagem de questões por fonte (top N)

        Args:
            limite: Número máximo de fontes a retornar

        Returns:
            Dicionário {fonte: contagem} ordenado por contagem (decrescente)
        """
        try:
            # Buscar todas as questões ativas
            questoes = self.questao_repository.buscar_por_filtros(ativa=True)

            # Contar por fonte
            contagem = {}
            for questao in questoes:
                fonte = questao.get('fonte', 'Não especificada')
                if fonte:
                    contagem[fonte] = contagem.get(fonte, 0) + 1

            # Ordenar por contagem (decrescente) e limitar
            estatisticas = dict(
                sorted(
                    contagem.items(),
                    key=lambda item: item[1],
                    reverse=True
                )[:limite]
            )

            logger.info(
                f"Top {len(estatisticas)} fontes: "
                f"{sum(estatisticas.values())} questões"
            )

            return estatisticas

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas por fonte: {e}", exc_info=True)
            return {}

    def obter_resumo_completo(self) -> Dict[str, Any]:
        """Obtém resumo completo de estatísticas

        Returns:
            Dicionário com todas as estatísticas disponíveis
        """
        try:
            resumo = {
                'gerais': self.obter_estatisticas_gerais(),
                'por_dificuldade': self.obter_estatisticas_por_dificuldade(),
                'por_ano': self.obter_estatisticas_por_ano(),
                'top_fontes': self.obter_estatisticas_por_fonte(limite=5),
                'timestamp': datetime.now().isoformat()
            }

            logger.info("Resumo completo de estatísticas gerado")

            return resumo

        except Exception as e:
            logger.error(f"Erro ao obter resumo completo: {e}", exc_info=True)
            return {
                'gerais': {},
                'por_dificuldade': {},
                'por_ano': {},
                'top_fontes': {},
                'timestamp': datetime.now().isoformat(),
                'erro': str(e)
            }

    def calcular_taxa_crescimento(
        self,
        periodo_dias: int = 30
    ) -> Dict[str, Any]:
        """Calcula taxa de crescimento de questões

        Args:
            periodo_dias: Número de dias para calcular crescimento

        Returns:
            Dicionário com taxa de crescimento e projeções
            {
                'periodo_dias': int,
                'questoes_novas': int,
                'taxa_diaria': float,
                'projecao_mensal': float
            }
        """
        try:
            # Buscar todas as questões
            questoes = self.questao_repository.buscar_por_filtros(ativa=True)

            # Data de corte
            data_corte = datetime.now() - timedelta(days=periodo_dias)

            # Contar questões novas no período
            questoes_novas = 0
            for questao in questoes:
                data_criacao_str = questao.get('data_criacao')
                if data_criacao_str:
                    try:
                        data_criacao = datetime.fromisoformat(data_criacao_str)
                        if data_criacao >= data_corte:
                            questoes_novas += 1
                    except (ValueError, TypeError):
                        continue

            taxa_diaria = questoes_novas / periodo_dias if periodo_dias > 0 else 0
            projecao_mensal = taxa_diaria * 30

            resultado = {
                'periodo_dias': periodo_dias,
                'questoes_novas': questoes_novas,
                'taxa_diaria': round(taxa_diaria, 2),
                'projecao_mensal': round(projecao_mensal, 1)
            }

            logger.info(
                f"Taxa de crescimento ({periodo_dias} dias): "
                f"{questoes_novas} novas questões ({taxa_diaria:.2f}/dia)"
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao calcular taxa de crescimento: {e}", exc_info=True)
            return {
                'periodo_dias': periodo_dias,
                'questoes_novas': 0,
                'taxa_diaria': 0,
                'projecao_mensal': 0
            }
