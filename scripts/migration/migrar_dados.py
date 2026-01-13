#!/usr/bin/env python3
"""
Script de Migração de Dados - V1.x → V2.0

Este script migra todos os dados do banco antigo (INTEGER IDs) para o novo (UUID + ORM)

Etapas:
1. Preparação e mapeamento
2. Migração de dados base (dificuldades, tags, tipos, fontes, anos)
3. Migração de imagens (com deduplicação)
4. Migração de questões
5. Migração de alternativas
6. Migração de respostas (unificadas)
7. Migração de relacionamentos (questao_tag, lista_questao)
8. Validação final

Uso:
    python scripts/migration/migrar_dados.py
"""

import sys
import os
import sqlite3
import uuid as uuid_lib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm import (
    Base, TipoQuestao, FonteQuestao, AnoReferencia, Dificuldade,
    Imagem, Tag, Questao, Alternativa, RespostaQuestao, Lista,
    QuestaoVersao, CodigoGenerator
)


class MigradorDados:
    """Classe responsável pela migração de dados"""

    def __init__(self, db_antigo: str, db_novo: str):
        """
        Inicializa o migrador

        Args:
            db_antigo: Caminho do banco V1
            db_novo: Caminho do banco V2
        """
        self.db_antigo = db_antigo
        self.db_novo = db_novo

        # Mapas de ID antigo → UUID novo
        self.map_dificuldade: Dict[int, str] = {}
        self.map_tag: Dict[int, str] = {}
        self.map_tipo_questao: Dict[str, str] = {}  # codigo → uuid
        self.map_fonte: Dict[str, str] = {}  # sigla → uuid
        self.map_ano: Dict[int, str] = {}  # ano → uuid
        self.map_imagem: Dict[str, str] = {}  # caminho → uuid
        self.map_questao: Dict[int, str] = {}  # id_antigo → uuid_novo
        self.map_alternativa: Dict[int, str] = {}
        self.map_lista: Dict[int, str] = {}

        # Conectar aos bancos
        self.conn_antigo = sqlite3.connect(db_antigo)
        self.conn_antigo.row_factory = sqlite3.Row

        engine_novo = create_engine(f'sqlite:///{db_novo}', echo=False)
        Session = sessionmaker(bind=engine_novo)
        self.session_novo = Session()

        # Estatísticas
        self.stats = {
            'dificuldades': 0,
            'tags': 0,
            'tipos': 0,
            'fontes': 0,
            'anos': 0,
            'imagens': 0,
            'questoes': 0,
            'alternativas': 0,
            'respostas': 0,
            'listas': 0,
            'questao_tag': 0,
            'lista_questao': 0,
        }

    def migrar_dificuldades(self):
        """Migra dificuldades"""
        print("\n📊 Migrando dificuldades...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM dificuldade")

        for row in cursor.fetchall():
            # Mapear nome antigo → código novo
            nome = row['nome'].upper()
            codigo_map = {
                'FÁCIL': 'FACIL',
                'FACIL': 'FACIL',
                'MÉDIO': 'MEDIO',
                'MEDIO': 'MEDIO',
                'DIFÍCIL': 'DIFICIL',
                'DIFICIL': 'DIFICIL'
            }
            codigo = codigo_map.get(nome, nome)

            # Buscar ou criar
            dif = self.session_novo.query(Dificuldade).filter_by(codigo=codigo).first()

            if not dif:
                dif = Dificuldade(codigo=codigo)
                self.session_novo.add(dif)
                self.session_novo.flush()

            self.map_dificuldade[row['id_dificuldade']] = dif.uuid
            self.stats['dificuldades'] += 1
            print(f"   ✓ {row['nome']} → {codigo} → {dif.uuid[:8]}")

        self.session_novo.commit()

    def migrar_tags(self):
        """Migra hierarquia de tags"""
        print("\n🏷️  Migrando tags...")
        cursor = self.conn_antigo.cursor()

        # Buscar todas as tags ordenadas por nível
        cursor.execute("SELECT * FROM tag WHERE ativo = 1 ORDER BY nivel, ordem")
        tags_antigas = cursor.fetchall()

        for row in tags_antigas:
            # Criar nova tag
            tag = Tag(
                nome=row['nome'],
                numeracao=row['numeracao'],
                nivel=row['nivel'],
                ordem=row['ordem']
            )

            # Mapear pai se existir
            if row['id_tag_pai']:
                tag.uuid_tag_pai = self.map_tag.get(row['id_tag_pai'])

            self.session_novo.add(tag)
            self.session_novo.flush()

            self.map_tag[row['id_tag']] = tag.uuid
            self.stats['tags'] += 1
            print(f"   ✓ {row['numeracao']} {row['nome']} → {tag.uuid[:8]}")

        self.session_novo.commit()

    def migrar_tipos_questao(self):
        """Garante que tipos de questão existem"""
        print("\n📝 Verificando tipos de questão...")

        tipos = ['OBJETIVA', 'DISCURSIVA']
        for codigo in tipos:
            tipo = self.session_novo.query(TipoQuestao).filter_by(codigo=codigo).first()
            if tipo:
                self.map_tipo_questao[codigo] = tipo.uuid
                self.stats['tipos'] += 1
                print(f"   ✓ {codigo} → {tipo.uuid[:8]}")

    def migrar_fontes(self):
        """Extrai e cria fontes únicas"""
        print("\n🏫 Migrando fontes...")
        cursor = self.conn_antigo.cursor()

        # Extrair fontes únicas do banco antigo
        cursor.execute("SELECT DISTINCT fonte FROM questao WHERE fonte IS NOT NULL")
        fontes_antigas = cursor.fetchall()

        for row in fontes_antigas:
            sigla = row['fonte']
            if not sigla:
                continue

            # Buscar ou criar fonte
            fonte = self.session_novo.query(FonteQuestao).filter_by(sigla=sigla).first()

            if not fonte:
                # Criar nova fonte
                fonte = FonteQuestao(
                    sigla=sigla,
                    nome_completo=sigla,  # Usar sigla como nome por enquanto
                    tipo_instituicao='VESTIBULAR'  # Padrão
                )
                self.session_novo.add(fonte)
                self.session_novo.flush()

            self.map_fonte[sigla] = fonte.uuid
            self.stats['fontes'] += 1
            print(f"   ✓ {sigla} → {fonte.uuid[:8]}")

        self.session_novo.commit()

    def migrar_anos(self):
        """Extrai e cria anos únicos"""
        print("\n📅 Migrando anos de referência...")
        cursor = self.conn_antigo.cursor()

        # Extrair anos únicos
        cursor.execute("SELECT DISTINCT ano FROM questao WHERE ano IS NOT NULL")
        anos_antigos = cursor.fetchall()

        for row in anos_antigos:
            ano_int = row['ano']
            if not ano_int:
                continue

            # Criar ou obter ano
            ano_ref = AnoReferencia.criar_ou_obter(self.session_novo, ano_int)
            self.map_ano[ano_int] = ano_ref.uuid
            self.stats['anos'] += 1
            print(f"   ✓ {ano_int} → {ano_ref.uuid[:8]}")

        self.session_novo.commit()

    def migrar_imagens(self):
        """Migra imagens com deduplicação"""
        print("\n🖼️  Migrando imagens...")
        cursor = self.conn_antigo.cursor()

        # Buscar todas as imagens (de questões e alternativas)
        imagens_para_migrar = set()

        # Imagens de enunciados
        cursor.execute("SELECT DISTINCT imagem_enunciado FROM questao WHERE imagem_enunciado IS NOT NULL")
        for row in cursor.fetchall():
            if row['imagem_enunciado']:
                imagens_para_migrar.add(row['imagem_enunciado'])

        # Imagens de alternativas
        cursor.execute("SELECT DISTINCT imagem FROM alternativa WHERE imagem IS NOT NULL")
        for row in cursor.fetchall():
            if row['imagem']:
                imagens_para_migrar.add(row['imagem'])

        print(f"   Encontradas {len(imagens_para_migrar)} imagens únicas")

        # Migrar cada imagem
        for caminho_imagem in imagens_para_migrar:
            try:
                # Verificar se arquivo existe
                if not os.path.exists(caminho_imagem):
                    print(f"   ⚠️  Arquivo não encontrado: {caminho_imagem}")
                    continue

                # Criar ou obter imagem (com deduplicação automática)
                imagem = Imagem.criar_de_arquivo(
                    self.session_novo,
                    caminho_imagem
                )

                self.map_imagem[caminho_imagem] = imagem.uuid
                self.stats['imagens'] += 1
                print(f"   ✓ {os.path.basename(caminho_imagem)} → {imagem.uuid[:8]}")

            except Exception as e:
                print(f"   ❌ Erro ao migrar {caminho_imagem}: {e}")

        self.session_novo.commit()

    def migrar_questoes(self):
        """Migra questões"""
        print("\n📚 Migrando questões...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM questao WHERE ativo = 1")

        for row in cursor.fetchall():
            # Gerar código legível
            ano = row['ano'] if row['ano'] else datetime.now().year
            codigo = CodigoGenerator.gerar_codigo_questao(self.session_novo, ano)

            # Determinar tipo
            tipo_codigo = row['tipo'] if row['tipo'] else 'OBJETIVA'
            uuid_tipo = self.map_tipo_questao.get(tipo_codigo)

            # Criar questão
            questao = Questao(
                codigo=codigo,
                titulo=row['titulo'],
                enunciado=row['enunciado'],
                uuid_tipo_questao=uuid_tipo,
                uuid_fonte=self.map_fonte.get(row['fonte']),
                uuid_ano_referencia=self.map_ano.get(row['ano']),
                uuid_dificuldade=self.map_dificuldade.get(row['id_dificuldade']),
                uuid_imagem_enunciado=self.map_imagem.get(row['imagem_enunciado']),
                escala_imagem_enunciado=row['escala_imagem_enunciado'],
                observacoes=row['observacoes']
            )

            self.session_novo.add(questao)
            self.session_novo.flush()

            self.map_questao[row['id_questao']] = questao.uuid
            self.stats['questoes'] += 1

            if self.stats['questoes'] % 10 == 0:
                print(f"   ✓ {self.stats['questoes']} questões migradas...")

        self.session_novo.commit()
        print(f"   ✅ Total: {self.stats['questoes']} questões")

    def migrar_alternativas(self):
        """Migra alternativas"""
        print("\n🔤 Migrando alternativas...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM alternativa")

        # Mapear letra para ordem
        letra_para_ordem = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}

        for row in cursor.fetchall():
            uuid_questao = self.map_questao.get(row['id_questao'])
            if not uuid_questao:
                continue

            # Calcular ordem baseada na letra
            ordem = letra_para_ordem.get(row['letra'], 1)

            alternativa = Alternativa(
                uuid=str(uuid_lib.uuid4()),
                uuid_questao=uuid_questao,
                letra=row['letra'],
                ordem=ordem,
                texto=row['texto'] or '',  # Garantir que não seja None
                uuid_imagem=self.map_imagem.get(row['imagem']) if row['imagem'] else None,
                escala_imagem=row['escala_imagem']
            )

            self.session_novo.add(alternativa)
            self.session_novo.flush()

            self.map_alternativa[row['id_alternativa']] = alternativa.uuid
            self.stats['alternativas'] += 1

        self.session_novo.commit()
        print(f"   ✅ Total: {self.stats['alternativas']} alternativas")

    def migrar_respostas(self):
        """Migra respostas (unificadas)"""
        print("\n✅ Migrando respostas...")
        cursor = self.conn_antigo.cursor()

        # Para cada questão, criar resposta
        cursor.execute("""
            SELECT q.*, a.id_alternativa, a.correta
            FROM questao q
            LEFT JOIN alternativa a ON q.id_questao = a.id_questao AND a.correta = 1
            WHERE q.ativo = 1
        """)

        questoes_processadas = set()

        for row in cursor.fetchall():
            uuid_questao = self.map_questao.get(row['id_questao'])
            if not uuid_questao or uuid_questao in questoes_processadas:
                continue

            # Verificar tipo de questão
            if row['tipo'] == 'OBJETIVA' and row['id_alternativa']:
                # Resposta objetiva
                uuid_alternativa = self.map_alternativa.get(row['id_alternativa'])
                if uuid_alternativa:
                    resposta = RespostaQuestao.criar_resposta_objetiva(
                        self.session_novo,
                        uuid_questao=uuid_questao,
                        uuid_alternativa_correta=uuid_alternativa,
                        resolucao=row['resolucao'] if row['resolucao'] else None,
                        justificativa=None
                    )
                    self.stats['respostas'] += 1

            elif row['tipo'] == 'DISCURSIVA' and row['gabarito_discursiva']:
                # Resposta discursiva
                resposta = RespostaQuestao.criar_resposta_discursiva(
                    self.session_novo,
                    uuid_questao=uuid_questao,
                    gabarito_discursivo=row['gabarito_discursiva'],
                    resolucao=row['resolucao'] if row['resolucao'] else None,
                    justificativa=None
                )
                self.stats['respostas'] += 1

            questoes_processadas.add(uuid_questao)

        self.session_novo.commit()
        print(f"   ✅ Total: {self.stats['respostas']} respostas")

    def migrar_questao_tag(self):
        """Migra relacionamento questão-tag"""
        print("\n🔗 Migrando questao_tag...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM questao_tag")

        for row in cursor.fetchall():
            uuid_questao = self.map_questao.get(row['id_questao'])
            uuid_tag = self.map_tag.get(row['id_tag'])

            if uuid_questao and uuid_tag:
                questao = self.session_novo.query(Questao).filter_by(uuid=uuid_questao).first()
                tag = self.session_novo.query(Tag).filter_by(uuid=uuid_tag).first()

                if questao and tag:
                    questao.adicionar_tag(self.session_novo, tag)
                    self.stats['questao_tag'] += 1

        self.session_novo.commit()
        print(f"   ✅ Total: {self.stats['questao_tag']} associações")

    def migrar_listas(self):
        """Migra listas e lista_questao"""
        print("\n📋 Migrando listas...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM lista")

        for row in cursor.fetchall():
            codigo = CodigoGenerator.gerar_codigo_lista(self.session_novo)

            lista = Lista(
                codigo=codigo,
                titulo=row['titulo'],
                tipo=row['tipo'] if row['tipo'] else 'LISTA',
                cabecalho=row['cabecalho'] if row['cabecalho'] else None,
                instrucoes=row['instrucoes'] if row['instrucoes'] else None
            )

            self.session_novo.add(lista)
            self.session_novo.flush()

            self.map_lista[row['id_lista']] = lista.uuid
            self.stats['listas'] += 1
            print(f"   ✓ {codigo} - {row['titulo']}")

        self.session_novo.commit()

        # Migrar lista_questao
        print("\n📌 Migrando lista_questao...")
        cursor.execute("SELECT * FROM lista_questao")

        # Agrupar por lista para calcular ordem sequencial
        lista_questoes = {}
        for row in cursor.fetchall():
            id_lista = row['id_lista']
            if id_lista not in lista_questoes:
                lista_questoes[id_lista] = []
            lista_questoes[id_lista].append(row['id_questao'])

        # Adicionar questões às listas com ordem sequencial
        for id_lista, questoes_ids in lista_questoes.items():
            uuid_lista = self.map_lista.get(id_lista)
            if not uuid_lista:
                continue

            lista = self.session_novo.query(Lista).filter_by(uuid=uuid_lista).first()
            if not lista:
                continue

            for ordem, id_questao in enumerate(questoes_ids, start=1):
                uuid_questao = self.map_questao.get(id_questao)
                if not uuid_questao:
                    continue

                questao = self.session_novo.query(Questao).filter_by(uuid=uuid_questao).first()
                if questao:
                    lista.adicionar_questao(
                        self.session_novo,
                        questao,
                        ordem=ordem
                    )
                    self.stats['lista_questao'] += 1

        self.session_novo.commit()
        print(f"   ✅ Total: {self.stats['lista_questao']} questões em listas")

    def migrar_questao_versao(self):
        """Migra relacionamento questao_versao"""
        print("\n🔄 Migrando questao_versao...")
        cursor = self.conn_antigo.cursor()
        cursor.execute("SELECT * FROM questao_versao")

        count = 0
        for row in cursor.fetchall():
            uuid_original = self.map_questao.get(row['id_questao_original'])
            uuid_versao = self.map_questao.get(row['id_questao_versao'])

            if uuid_original and uuid_versao:
                versao = QuestaoVersao(
                    uuid_questao_original=uuid_original,
                    uuid_questao_versao=uuid_versao,
                    observacao=row['observacao'] if row['observacao'] else None
                )
                self.session_novo.add(versao)
                count += 1

        self.session_novo.commit()
        print(f"   ✅ Total: {count} versões")

    def validar_migracao(self):
        """Valida a migração"""
        print("\n" + "="*80)
        print("VALIDAÇÃO DA MIGRAÇÃO")
        print("="*80)

        # Contar registros no banco antigo
        cursor = self.conn_antigo.cursor()

        print("\n📊 Comparação de contagens:")
        print(f"   Dificuldades: {self.stats['dificuldades']}")
        print(f"   Tags: {self.stats['tags']}")
        print(f"   Tipos: {self.stats['tipos']}")
        print(f"   Fontes: {self.stats['fontes']}")
        print(f"   Anos: {self.stats['anos']}")
        print(f"   Imagens: {self.stats['imagens']}")
        print(f"   Questões: {self.stats['questoes']}")
        print(f"   Alternativas: {self.stats['alternativas']}")
        print(f"   Respostas: {self.stats['respostas']}")
        print(f"   Listas: {self.stats['listas']}")
        print(f"   Questão-Tag: {self.stats['questao_tag']}")
        print(f"   Lista-Questão: {self.stats['lista_questao']}")

        # Verificações básicas
        cursor.execute("SELECT COUNT(*) FROM questao WHERE ativo = 1")
        count_questoes_antigas = cursor.fetchone()[0]

        if self.stats['questoes'] != count_questoes_antigas:
            print(f"\n⚠️  ATENÇÃO: Contagem de questões diferente!")
            print(f"   Antiga: {count_questoes_antigas}")
            print(f"   Nova: {self.stats['questoes']}")
        else:
            print(f"\n✅ Contagem de questões OK: {self.stats['questoes']}")

    def executar(self):
        """Executa toda a migração"""
        print("\n" + "="*80)
        print("MIGRAÇÃO DE DADOS - V1.x → V2.0")
        print("="*80)

        try:
            self.migrar_dificuldades()
            self.migrar_tags()
            self.migrar_tipos_questao()
            self.migrar_fontes()
            self.migrar_anos()
            self.migrar_imagens()
            self.migrar_questoes()
            self.migrar_alternativas()
            self.migrar_respostas()
            self.migrar_questao_tag()
            self.migrar_listas()
            self.migrar_questao_versao()
            self.validar_migracao()

            print("\n" + "="*80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*80)

        except Exception as e:
            print(f"\n❌ ERRO durante migração: {e}")
            import traceback
            traceback.print_exc()
            self.session_novo.rollback()
            raise

        finally:
            self.conn_antigo.close()
            self.session_novo.close()


def main():
    """Função principal"""
    try:
        # Caminhos
        db_antigo = 'database/questoes.db'
        db_novo = 'database/sistema_questoes_v2.db'

        print(f"\n📂 Banco antigo: {db_antigo}")
        print(f"📂 Banco novo: {db_novo}")

        # Verificar se bancos existem
        if not os.path.exists(db_antigo):
            print(f"\n❌ Banco antigo não encontrado: {db_antigo}")
            sys.exit(1)

        if not os.path.exists(db_novo):
            print(f"\n❌ Banco novo não encontrado: {db_novo}")
            print("   Execute primeiro: python scripts/migration/criar_novo_schema.py")
            sys.exit(1)

        # Confirmar
        print("\n⚠️  Esta operação irá migrar todos os dados do banco antigo para o novo.")
        resposta = input("Deseja continuar? (S/n): ").strip().lower()

        if resposta and resposta != 's':
            print("\n❌ Operação cancelada.")
            return

        # Executar migração
        migrador = MigradorDados(db_antigo, db_novo)
        migrador.executar()

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
