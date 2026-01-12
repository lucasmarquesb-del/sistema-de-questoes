-- ============================================
-- SISTEMA DE BANCO DE QUESTÕES EDUCACIONAIS
-- Script de Inicialização do Banco de Dados
-- Versão: 1.0.1
-- Data: Janeiro 2026
-- ============================================

-- ============================================
-- TABELA: TAG
-- ============================================
CREATE TABLE IF NOT EXISTS tag (
    id_tag INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    numeracao VARCHAR(20) UNIQUE,  -- Ex: "1", "1.1", "1.1.2"
    nivel INTEGER NOT NULL DEFAULT 0,  -- Profundidade na hierarquia
    id_tag_pai INTEGER,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    ordem INTEGER,  -- Ordem de exibição entre irmãos
    FOREIGN KEY (id_tag_pai) REFERENCES tag(id_tag),
    UNIQUE(nome, id_tag_pai)  -- Nome único por nível
);

CREATE INDEX IF NOT EXISTS idx_tag_pai ON tag(id_tag_pai);
CREATE INDEX IF NOT EXISTS idx_tag_ativo ON tag(ativo);
CREATE INDEX IF NOT EXISTS idx_tag_numeracao ON tag(numeracao);

-- ============================================
-- TABELA: DIFICULDADE
-- ============================================
CREATE TABLE IF NOT EXISTS dificuldade (
    id_dificuldade INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descricao TEXT,
    ordem INTEGER  -- Para ordenação (1=Fácil, 2=Médio, 3=Difícil)
);

-- ============================================
-- TABELA: QUESTAO
-- ============================================
CREATE TABLE IF NOT EXISTS questao (
    id_questao INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(200),  -- Opcional, para busca
    enunciado TEXT NOT NULL,  -- LaTeX
    tipo VARCHAR(20) NOT NULL CHECK(tipo IN ('OBJETIVA', 'DISCURSIVA')),
    ano INTEGER NOT NULL,  -- Ano da questão
    fonte VARCHAR(100) NOT NULL,  -- Banca/Vestibular ou 'AUTORAL'
    id_dificuldade INTEGER,  -- Relação com tabela dificuldade
    imagem_enunciado VARCHAR(255),  -- Caminho relativo
    escala_imagem_enunciado DECIMAL(3,2) DEFAULT 0.7,  -- Escala para LaTeX
    resolucao TEXT,  -- LaTeX
    gabarito_discursiva TEXT,  -- LaTeX, apenas para discursivas
    observacoes TEXT,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_modificacao DATETIME,
    ativo BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (id_dificuldade) REFERENCES dificuldade(id_dificuldade)
);

CREATE INDEX IF NOT EXISTS idx_questao_tipo ON questao(tipo);
CREATE INDEX IF NOT EXISTS idx_questao_ativo ON questao(ativo);
CREATE INDEX IF NOT EXISTS idx_questao_titulo ON questao(titulo);
CREATE INDEX IF NOT EXISTS idx_questao_ano ON questao(ano);
CREATE INDEX IF NOT EXISTS idx_questao_fonte ON questao(fonte);
CREATE INDEX IF NOT EXISTS idx_questao_dificuldade ON questao(id_dificuldade);

-- Trigger: Atualizar data de modificação
CREATE TRIGGER IF NOT EXISTS questao_update_timestamp
    AFTER UPDATE ON questao
    FOR EACH ROW
    BEGIN
        UPDATE questao SET data_modificacao = CURRENT_TIMESTAMP
        WHERE id_questao = NEW.id_questao;
    END;

-- ============================================
-- TABELA: ALTERNATIVA
-- ============================================
CREATE TABLE IF NOT EXISTS alternativa (
    id_alternativa INTEGER PRIMARY KEY AUTOINCREMENT,
    id_questao INTEGER NOT NULL,
    letra CHAR(1) NOT NULL CHECK(letra IN ('A','B','C','D','E')),
    texto TEXT,  -- LaTeX
    imagem VARCHAR(255),  -- Caminho relativo
    escala_imagem DECIMAL(3,2) DEFAULT 0.7,  -- Escala para LaTeX
    correta BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    UNIQUE(id_questao, letra),
    CHECK (texto IS NOT NULL OR imagem IS NOT NULL)  -- Pelo menos um preenchido
);

CREATE INDEX IF NOT EXISTS idx_alternativa_questao ON alternativa(id_questao);

-- Trigger: Garantir apenas 1 alternativa correta por questão
CREATE TRIGGER IF NOT EXISTS alternativa_unica_correta
    BEFORE INSERT ON alternativa
    FOR EACH ROW
    WHEN NEW.correta = 1
    BEGIN
        SELECT CASE
            WHEN (SELECT COUNT(*) FROM alternativa
                  WHERE id_questao = NEW.id_questao AND correta = 1) > 0
            THEN RAISE(ABORT, 'Questão já possui alternativa correta')
        END;
    END;

-- Trigger: Garantir apenas 1 alternativa correta ao atualizar
CREATE TRIGGER IF NOT EXISTS alternativa_unica_correta_update
    BEFORE UPDATE ON alternativa
    FOR EACH ROW
    WHEN NEW.correta = 1 AND OLD.correta = 0
    BEGIN
        SELECT CASE
            WHEN (SELECT COUNT(*) FROM alternativa
                  WHERE id_questao = NEW.id_questao AND correta = 1 AND id_alternativa != NEW.id_alternativa) > 0
            THEN RAISE(ABORT, 'Questão já possui alternativa correta')
        END;
    END;

-- ============================================
-- TABELA: QUESTAO_TAG (Relacionamento N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS questao_tag (
    id_questao INTEGER NOT NULL,
    id_tag INTEGER NOT NULL,
    data_associacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_questao, id_tag),
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    FOREIGN KEY (id_tag) REFERENCES tag(id_tag) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_questao_tag_questao ON questao_tag(id_questao);
CREATE INDEX IF NOT EXISTS idx_questao_tag_tag ON questao_tag(id_tag);

-- ============================================
-- TABELA: LISTA
-- ============================================
CREATE TABLE IF NOT EXISTS lista (
    id_lista INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo VARCHAR(200) NOT NULL,
    tipo VARCHAR(50),  -- "prova", "lista", "simulado" - nomenclatura livre
    cabecalho TEXT,  -- Texto do cabeçalho personalizado
    instrucoes TEXT,  -- Instruções gerais
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: LISTA_QUESTAO (Relacionamento N:N)
-- ============================================
CREATE TABLE IF NOT EXISTS lista_questao (
    id_lista INTEGER NOT NULL,
    id_questao INTEGER NOT NULL,
    data_adicao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_lista, id_questao),
    FOREIGN KEY (id_lista) REFERENCES lista(id_lista) ON DELETE CASCADE,
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lista_questao_lista ON lista_questao(id_lista);
CREATE INDEX IF NOT EXISTS idx_lista_questao_questao ON lista_questao(id_questao);

-- ============================================
-- TABELA: QUESTAO_VERSAO (Versões Alternativas)
-- ============================================
CREATE TABLE IF NOT EXISTS questao_versao (
    id_questao_original INTEGER NOT NULL,
    id_questao_versao INTEGER NOT NULL,
    observacao TEXT,  -- Nota sobre a relação entre as versões
    data_vinculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_questao_original, id_questao_versao),
    FOREIGN KEY (id_questao_original) REFERENCES questao(id_questao) ON DELETE CASCADE,
    FOREIGN KEY (id_questao_versao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    CHECK (id_questao_original != id_questao_versao)  -- Questão não pode ser versão de si mesma
);

CREATE INDEX IF NOT EXISTS idx_questao_versao_original ON questao_versao(id_questao_original);
CREATE INDEX IF NOT EXISTS idx_questao_versao_versao ON questao_versao(id_questao_versao);

-- ============================================
-- TABELA: CONFIGURACAO (Sistema)
-- ============================================
CREATE TABLE IF NOT EXISTS configuracao (
    chave VARCHAR(50) PRIMARY KEY,
    valor TEXT,
    descricao TEXT
);

-- ============================================
-- DADOS INICIAIS
-- ============================================

-- Dados iniciais de dificuldade
INSERT OR IGNORE INTO dificuldade (nome, descricao, ordem) VALUES
('FÁCIL', 'Questões de nível básico', 1),
('MÉDIO', 'Questões de nível intermediário', 2),
('DIFÍCIL', 'Questões de nível avançado', 3);

-- Configurações padrão do sistema
INSERT OR IGNORE INTO configuracao (chave, valor, descricao) VALUES
('backup_automatico', '0', 'Ativar backup automático (0=não, 1=sim)'),
('backup_periodicidade', '7', 'Dias entre backups automáticos'),
('backup_manter', '5', 'Quantidade de backups a manter'),
('template_padrao', 'default.tex', 'Template LaTeX padrão'),
('latex_colunas_padrao', '1', 'Colunas padrão na exportação (1 ou 2)'),
('latex_incluir_gabarito', '1', 'Incluir gabarito por padrão'),
('latex_incluir_resolucao', '0', 'Incluir resoluções por padrão'),
('latex_escala_imagem_padrao', '0.7', 'Escala padrão para imagens no LaTeX'),
('randomizar_questoes_padrao', '0', 'Randomizar questões por padrão ao exportar');

-- ============================================
-- TAXONOMIA MATEMÁTICA - TAGS HIERÁRQUICAS
-- ============================================

-- Nível 1 - Áreas principais
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) VALUES
('NÚMEROS E OPERAÇÕES', '1', 1, NULL, 1),
('ÁLGEBRA', '2', 1, NULL, 2),
('GEOMETRIA', '3', 1, NULL, 3),
('TRIGONOMETRIA', '4', 1, NULL, 4),
('COMBINATÓRIA', '5', 1, NULL, 5),
('PROBABILIDADE', '6', 1, NULL, 6),
('ESTATÍSTICA', '7', 1, NULL, 7);

-- Nível 2 - Álgebra
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÕES', '2.1', 2, id_tag, 1 FROM tag WHERE numeracao = '2';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'EQUAÇÕES', '2.2', 2, id_tag, 2 FROM tag WHERE numeracao = '2';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'PROGRESSÕES', '2.3', 2, id_tag, 3 FROM tag WHERE numeracao = '2';

-- Nível 3 - Funções
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÃO AFIM', '2.1.1', 3, id_tag, 1 FROM tag WHERE numeracao = '2.1';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÃO QUADRÁTICA', '2.1.2', 3, id_tag, 2 FROM tag WHERE numeracao = '2.1';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÃO EXPONENCIAL', '2.1.3', 3, id_tag, 3 FROM tag WHERE numeracao = '2.1';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÃO LOGARÍTMICA', '2.1.4', 3, id_tag, 4 FROM tag WHERE numeracao = '2.1';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'FUNÇÃO TRIGONOMÉTRICA', '2.1.5', 3, id_tag, 5 FROM tag WHERE numeracao = '2.1';

-- Nível 3 - Progressões
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'PROGRESSÃO ARITMÉTICA', '2.3.1', 3, id_tag, 1 FROM tag WHERE numeracao = '2.3';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'PROGRESSÃO GEOMÉTRICA', '2.3.2', 3, id_tag, 2 FROM tag WHERE numeracao = '2.3';

-- Nível 2 - Geometria
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'GEOMETRIA PLANA', '3.1', 2, id_tag, 1 FROM tag WHERE numeracao = '3';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'GEOMETRIA ESPACIAL', '3.2', 2, id_tag, 2 FROM tag WHERE numeracao = '3';

INSERT OR IGNORE INTO tag (nome, numeracao, nivel, id_tag_pai, ordem)
SELECT 'GEOMETRIA ANALÍTICA', '3.3', 2, id_tag, 3 FROM tag WHERE numeracao = '3';

-- ============================================
-- TAGS DE VESTIBULAR/EXAME
-- ============================================
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, ordem) VALUES
('ENEM', 'V1', 1, 100),
('FUVEST', 'V2', 1, 101),
('UNICAMP', 'V3', 1, 102),
('UNESP', 'V4', 1, 103),
('UERJ', 'V5', 1, 104),
('ITA', 'V6', 1, 105),
('IME', 'V7', 1, 106),
('MILITAR', 'V8', 1, 107);

-- ============================================
-- TAGS DE NÍVEL DE ESCOLARIDADE
-- ============================================
INSERT OR IGNORE INTO tag (nome, numeracao, nivel, ordem) VALUES
('E.F.2', 'N1', 1, 200),
('E.M.', 'N2', 1, 201),
('E.J.A.', 'N3', 1, 202);

-- ============================================
-- FIM DO SCRIPT
-- ============================================
