"""
AlternativaController - Nova versão usando ORM + Service Layer
"""
from typing import Dict, List, Optional, Any
from services import services


class AlternativaControllerORM:
    """
    Controller para operações de alternativas usando ORM e Service Layer

    IMPORTANTE: Este controller usa a Service Facade com UUIDs
    """

    @staticmethod
    def criar_alternativa(
        codigo_questao: str,
        letra: str,
        texto: str,
        uuid_imagem: Optional[str] = None,
        escala_imagem: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        Cria uma alternativa para uma questão

        Args:
            codigo_questao: Código da questão (Q-2024-0001)
            letra: Letra da alternativa (A-E)
            texto: Texto da alternativa
            uuid_imagem: UUID da imagem opcional
            escala_imagem: Escala da imagem (padrão: 1.0)

        Returns:
            Dict com dados da alternativa criada ou None

        Exemplo:
            alternativa = AlternativaControllerORM.criar_alternativa(
                codigo_questao='Q-2024-0001',
                letra='A',
                texto='Brasília'
            )
            print(f"Alternativa criada: {alternativa['letra']}")
        """
        try:
            with services.transaction() as svc:
                return svc.alternativa.criar_alternativa(
                    codigo_questao=codigo_questao,
                    letra=letra,
                    texto=texto,
                    uuid_imagem=uuid_imagem,
                    escala_imagem=escala_imagem
                )
        except ValueError as e:
            print(f"Erro de validação: {e}")
            return None
        except Exception as e:
            print(f"Erro ao criar alternativa: {e}")
            return None

    @staticmethod
    def listar_alternativas(codigo_questao: str) -> List[Dict[str, Any]]:
        """
        Lista alternativas de uma questão

        Args:
            codigo_questao: Código da questão (Q-2024-0001)

        Returns:
            Lista de alternativas ordenadas por letra
        """
        try:
            return services.alternativa.listar_alternativas(codigo_questao)
        except Exception as e:
            print(f"Erro ao listar alternativas: {e}")
            return []

    @staticmethod
    def buscar_alternativa_correta(codigo_questao: str) -> Optional[Dict[str, Any]]:
        """
        Busca a alternativa correta de uma questão

        Args:
            codigo_questao: Código da questão (Q-2024-0001)

        Returns:
            Dict com dados da alternativa correta ou None
        """
        try:
            return services.alternativa.buscar_alternativa_correta(codigo_questao)
        except Exception as e:
            print(f"Erro ao buscar alternativa correta: {e}")
            return None
