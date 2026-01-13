"""
Gerador de Códigos Legíveis para Questões e Listas
"""
from datetime import datetime
from sqlalchemy import func


class CodigoGenerator:
    """
    Classe utilitária para gerar códigos legíveis

    Padrões:
    - Questões: Q-{ANO}-{SEQUENCIAL:04d} (ex: Q-2026-0001)
    - Listas: LST-{ANO}-{SEQUENCIAL:04d} (ex: LST-2026-0001)
    """

    @staticmethod
    def gerar_codigo_questao(session, ano: int = None) -> str:
        """
        Gera código único para questão

        Args:
            session: Sessão do SQLAlchemy
            ano: Ano para o código (usa ano atual se None)

        Returns:
            String no formato Q-AAAA-NNNN

        Example:
            >>> CodigoGenerator.gerar_codigo_questao(session, 2026)
            'Q-2026-0001'
        """
        from .questao import Questao

        if not ano:
            ano = datetime.now().year

        # Buscar último código do ano
        ultimo = session.query(Questao)\
            .filter(Questao.codigo.like(f"Q-{ano}-%"))\
            .order_by(Questao.codigo.desc())\
            .first()

        if ultimo:
            # Extrair sequencial do último código
            try:
                seq = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"Q-{ano}-{seq:04d}"

    @staticmethod
    def gerar_codigo_lista(session, ano: int = None) -> str:
        """
        Gera código único para lista

        Args:
            session: Sessão do SQLAlchemy
            ano: Ano para o código (usa ano atual se None)

        Returns:
            String no formato LST-AAAA-NNNN

        Example:
            >>> CodigoGenerator.gerar_codigo_lista(session, 2026)
            'LST-2026-0001'
        """
        from .lista import Lista

        if not ano:
            ano = datetime.now().year

        # Buscar último código do ano
        ultimo = session.query(Lista)\
            .filter(Lista.codigo.like(f"LST-{ano}-%"))\
            .order_by(Lista.codigo.desc())\
            .first()

        if ultimo:
            # Extrair sequencial do último código
            try:
                seq = int(ultimo.codigo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"LST-{ano}-{seq:04d}"

    @staticmethod
    def validar_codigo_questao(codigo: str) -> bool:
        """
        Valida formato de código de questão

        Args:
            codigo: Código a validar

        Returns:
            True se válido, False caso contrário

        Example:
            >>> CodigoGenerator.validar_codigo_questao('Q-2026-0001')
            True
            >>> CodigoGenerator.validar_codigo_questao('INVALID')
            False
        """
        import re
        pattern = r'^Q-\d{4}-\d{4}$'
        return bool(re.match(pattern, codigo))

    @staticmethod
    def validar_codigo_lista(codigo: str) -> bool:
        """
        Valida formato de código de lista

        Args:
            codigo: Código a validar

        Returns:
            True se válido, False caso contrário

        Example:
            >>> CodigoGenerator.validar_codigo_lista('LST-2026-0001')
            True
            >>> CodigoGenerator.validar_codigo_lista('INVALID')
            False
        """
        import re
        pattern = r'^LST-\d{4}-\d{4}$'
        return bool(re.match(pattern, codigo))

    @staticmethod
    def extrair_ano_codigo(codigo: str) -> int:
        """
        Extrai o ano de um código

        Args:
            codigo: Código no formato Q-AAAA-NNNN ou LST-AAAA-NNNN

        Returns:
            Ano como inteiro, ou None se inválido

        Example:
            >>> CodigoGenerator.extrair_ano_codigo('Q-2026-0001')
            2026
        """
        try:
            partes = codigo.split('-')
            if len(partes) == 3:
                return int(partes[1])
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def extrair_sequencial_codigo(codigo: str) -> int:
        """
        Extrai o sequencial de um código

        Args:
            codigo: Código no formato Q-AAAA-NNNN ou LST-AAAA-NNNN

        Returns:
            Sequencial como inteiro, ou None se inválido

        Example:
            >>> CodigoGenerator.extrair_sequencial_codigo('Q-2026-0001')
            1
        """
        try:
            partes = codigo.split('-')
            if len(partes) == 3:
                return int(partes[2])
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def contar_questoes_ano(session, ano: int) -> int:
        """
        Conta quantas questões existem em um ano

        Args:
            session: Sessão do SQLAlchemy
            ano: Ano a contar

        Returns:
            Número de questões do ano
        """
        from .questao import Questao
        return session.query(func.count(Questao.uuid))\
            .filter(Questao.codigo.like(f"Q-{ano}-%"))\
            .scalar() or 0

    @staticmethod
    def contar_listas_ano(session, ano: int) -> int:
        """
        Conta quantas listas existem em um ano

        Args:
            session: Sessão do SQLAlchemy
            ano: Ano a contar

        Returns:
            Número de listas do ano
        """
        from .lista import Lista
        return session.query(func.count(Lista.uuid))\
            .filter(Lista.codigo.like(f"LST-{ano}-%"))\
            .scalar() or 0
