# ANÁLISE DE REQUISITOS - SISTEMA DE BANCO DE QUESTÕES EDUCACIONAIS

**Versão:** 1.0.1
**Data:** Janeiro 2026
**Última Atualização:** Janeiro 2026
**Plataforma:** Desktop (Windows)
**Stack:** Python 3.11 + PyQt6 + SQLite  

---

## 1. VISÃO GERAL DO SISTEMA

### 1.1 Objetivo
Aplicação desktop para gerenciamento de banco de questões educacionais focado em Matemática, com sistema robusto e flexível de tags hierárquicas, suporte completo a LaTeX e exportação profissional para PDF.

### 1.2 Características Principais
- **Uso pessoal** sem necessidade de autenticação
- **Sistema híbrido de tags** (hierarquia estruturada + tags livres)
- **Suporte nativo a LaTeX** (notação matemática completa)
- **Busca avançada** com filtros cumulativos
- **Exportação profissional** para PDF/LaTeX
- **Arquitetura extensível** para outras disciplinas no futuro

---

## 2. REQUISITOS FUNCIONAIS

### RF01 - Gerenciamento de Tags

#### RF01.1 - Estrutura de Tags
**Descrição:** Sistema deve suportar tags hierárquicas organizadas numericamente.

**Características:**
- Tags organizadas em níveis (ex: `1-PROGRESSÕES`, `1.1-PA`, `1.2-PG`)
- Numeração reflete hierarquia e ordem
- Cada tag possui ID único no banco
- Tags podem ser ativadas/desativadas (soft delete)

**Regras de Negócio:**
- Tag pai pode ter múltiplas tags filhas
- Tag filha só pode ter um pai
- Numeração deve ser única por nível
- Sistema vem com taxonomia matemática pré-definida
- Usuário pode criar novas tags e reorganizar hierarquia

#### RF01.2 - Gerenciamento de Tags
**Operações disponíveis:**
- ✅ Criar nova tag (livre ou dentro de hierarquia)
- ✅ Editar nome da tag (atualiza em todas as questões vinculadas)
- ✅ Reorganizar hierarquia (mover tag de posição)
- ✅ Inativar tag (soft delete - não exclui, apenas oculta)
- ✅ Reativar tag inativada

**Interface:**
- Tela de gerenciamento em árvore hierárquica
- Drag-and-drop para reorganizar (opcional)
- Validação de nomes duplicados no mesmo nível

---

### RF02 - Cadastro de Questões

#### RF02.1 - Campos da Questão

**Campos Obrigatórios:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `enunciado` | TEXT (LaTeX) | Texto principal da questão |
| `tipo` | ENUM | 'OBJETIVA' ou 'DISCURSIVA' |
| `ano` | INTEGER | Ano da questão (ex: 2024, 2025) |
| `fonte` | VARCHAR(100) | Banca/Vestibular ou 'AUTORAL' |

**Campos Opcionais:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `titulo` | VARCHAR(200) | Título curto para busca |
| `resolucao` | TEXT (LaTeX) | Resolução detalhada |
| `observacoes` | TEXT | Comentários internos |
| `imagem_enunciado` | BLOB/PATH | Imagem principal |
| `gabarito_discursiva` | TEXT (LaTeX) | Resposta esperada (discursivas) |

**Campos Automáticos:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `data_criacao` | DATETIME | Timestamp de criação |
| `data_modificacao` | DATETIME | Última edição |
| `ativo` | BOOLEAN | Soft delete (padrão: TRUE) |

#### RF02.2 - Questões Objetivas (Múltipla Escolha)

**Estrutura de Alternativas:**
- Sempre **5 alternativas fixas** (A, B, C, D, E)
- Cada alternativa pode conter:
  - ✅ Texto LaTeX
  - ✅ Imagem
  - ✅ Texto + Imagem (combinados)

**Campos por Alternativa:**
| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `letra` | CHAR(1) | SIM (A-E) |
| `texto` | TEXT (LaTeX) | NÃO* |
| `imagem` | BLOB/PATH | NÃO* |
| `correta` | BOOLEAN | SIM (apenas 1 = TRUE) |

*Pelo menos um dos dois (texto ou imagem) deve estar preenchido.

#### RF02.3 - Questões Discursivas

**Características:**
- Não possui alternativas
- Campo `gabarito_discursiva` é opcional
- Suporta resposta completa em LaTeX

#### RF02.4 - Sistema de Imagens

**Decisão Técnica:** Armazenamento em arquivos separados (Opção B)

**Estrutura:**
```
/projeto
  /database
    questoes.db
  /imagens
    /enunciados
      questao_001_img1.png
      questao_001_img2.jpg
    /alternativas
      questao_001_alt_B.png
```

**Formato de Referência no Banco:**
```
caminho_relativo: "imagens/enunciados/questao_001_img1.png"
```

**Formatos Suportados:** PNG, JPG, JPEG, SVG

---

### RF03 - Sistema de Vinculação Tags-Questões

#### RF03.1 - Associação de Tags
**Descrição:** Questões podem ter múltiplas tags de diferentes categorias.

**Características:**
- Relação N:N (questão ↔ tags)
- Sem limite de tags por questão
- Tags obrigatórias: mínimo 1 tag por questão

**Categorias de Tags (Sugeridas):**
1. **Conteúdo Matemático** (hierárquica)
   - Ex: 1-ÁLGEBRA → 1.1-FUNÇÕES → 1.1.1-FUNÇÃO EXPONENCIAL

2. **Vestibular/Exame**
   - Ex: ENEM, FUVEST, UNICAMP, UERJ

3. **Nível de Escolaridade**
   - Ex: E.F.2 (Ensino Fundamental 2), E.M. (Ensino Médio), E.J.A. (Educação de Jovens e Adultos)

4. **Tags Livres** (criadas pelo usuário)
   - Ex: REVISÃO, IMPORTANTE, GRÁFICOS

#### RF03.2 - Interface de Tageamento
**Durante cadastro/edição:**
- Checkboxes agrupados por categoria
- Campo "Criar nova tag" para tags não listadas
- Autocomplete baseado em tags existentes
- Visual hierárquico (indentação por nível)

---

### RF04 - Busca e Filtros

#### RF04.1 - Busca por Texto
**Campo pesquisável:** `titulo` (campo opcional da questão)

**Características:**
- Busca case-insensitive
- Busca por correspondência parcial (LIKE '%termo%')
- Não busca dentro do LaTeX do enunciado/alternativas

#### RF04.2 - Filtros por Tags
**Lógica:** Filtros cumulativos (AND)

**Comportamento:**
```
Filtro aplicado: "Função Exponencial" AND "ENEM" AND "Difícil"

Resultado 1: 0 questões encontradas com TODOS os filtros
Exibição adicional:
  - "Função Exponencial": 45 questões
  - "ENEM": 120 questões  
  - "Difícil": 30 questões
```

**Interface de Filtros:**
- Painel lateral com árvore de tags
- Checkboxes para seleção múltipla
- Contador de questões por tag
- Botão "Limpar filtros"

#### RF04.3 - Visualização de Resultados
**Formato:** Cards com preview

**Informações no Card:**
- ID da questão
- Título (se preenchido) ou primeiras 60 caracteres do enunciado
- Tags principais (máximo 5 visíveis)
- Tipo (ícone: 📝 Objetiva / ✍️ Discursiva)
- Status (ativo/inativo)

**Ações por Card:**
- Visualizar completo
- Editar
- Adicionar à lista atual
- Inativar/Reativar

---

### RF05 - Visualização de Questões

#### RF05.1 - Preview de Questão
**Janela Modal com:**
- Enunciado renderizado (LaTeX compilado)
- Imagem do enunciado (se houver)
- Alternativas renderizadas (para objetivas)
  - Texto LaTeX compilado
  - Imagens (se houver)
  - Indicação visual da alternativa correta (modo revisão)
- Resolução (se preenchida)
- Tags aplicadas
- Metadados (data criação, última edição)

**Modo de Renderização LaTeX:**
- Preview estático (após salvar/carregar)
- Botão "Atualizar Preview" na tela de edição

---

### RF06 - Edição de Questões

#### RF06.1 - Operações de Edição
**Campos editáveis:**
- ✅ Todos os campos da questão
- ✅ Tags (adicionar/remover)
- ✅ Alternativas (texto, imagem, gabarito)
- ✅ Imagens (substituir/remover)

**Não mantém:**
- ❌ Histórico de alterações
- ❌ Versionamento

**Validações:**
- Enunciado não pode ser vazio
- Questões objetivas devem ter exatamente 5 alternativas
- Apenas 1 alternativa pode ser correta
- Mínimo 1 tag por questão

#### RF06.2 - Exclusão (Soft Delete)
**Comportamento:**
- Questão não é excluída do banco
- Campo `ativo` é marcado como FALSE
- Questão não aparece em buscas padrão
- Questão permanece em listas já criadas (com aviso)
- Interface deve permitir "ver questões inativas" e reativar

---

### RF07 - Criação de Listas/Provas

#### RF07.1 - Estrutura de Lista

**Campos da Lista:**
| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `titulo` | VARCHAR(200) | SIM |
| `tipo` | VARCHAR(50) | NÃO (nomenclatura livre) |
| `cabecalho` | TEXT | NÃO |
| `instrucoes` | TEXT | NÃO |
| `data_criacao` | DATETIME | AUTO |

**Campos do Cabeçalho Personalizado:**
- Nome da escola
- Nome do professor
- Data/Turma/Disciplina
- Instruções gerais

#### RF07.2 - Adicionar Questões à Lista
**Características:**
- Questão pode estar em múltiplas listas
- Ordem das questões pode ser randomizada (opcional)
- Suporte a versões alternativas da mesma questão (questões equivalentes)
- Adicionar questões por:
  - Busca e seleção individual
  - Seleção múltipla de resultados de busca
  - Arrastar e soltar (opcional)

**Randomização de Provas:**
- Opção para embaralhar ordem das questões ao exportar
- Permite criar múltiplas versões de uma mesma prova
- Sistema mantém rastreabilidade entre versões

**Versões de Questões:**
- Possibilidade de vincular questões como "versões alternativas"
- Útil para criar provas diferentes mas equivalentes
- Sistema pode substituir automaticamente questões por suas versões ao gerar provas

#### RF07.3 - Gerenciamento de Listas
**Operações:**
- ✅ Criar nova lista
- ✅ Editar metadados (título, cabeçalho, instruções)
- ✅ Adicionar/remover questões
- ✅ Duplicar lista
- ✅ Excluir lista (exclusão permanente, não soft delete)
- ✅ Visualizar preview da lista

---

### RF08 - Exportação LaTeX/PDF

#### RF08.1 - Fluxo de Exportação
**Opções de Exportação:**

**Opção A - Exportação Direta:**
1. Selecionar lista
2. Configurar opções de exportação
3. Sistema gera .tex e compila automaticamente
4. Abre PDF gerado

**Opção B - Exportação Manual:**
1. Selecionar lista
2. Sistema gera arquivo .tex
3. Usuário edita .tex manualmente (editor externo)
4. Usuário compila quando quiser

**Interface:** Radio buttons para escolher fluxo

#### RF08.2 - Opções de Exportação

**Configurações Disponíveis:**
| Opção | Valores |
|-------|---------|
| **Layout** | 1 coluna / 2 colunas |
| **Incluir Gabarito** | Sim / Não |
| **Incluir Resoluções** | Sim / Não |
| **Espaço para Respostas** | Sim (X linhas) / Não |
| **Randomizar Questões** | Sim / Não |
| **Escala de Imagens** | Valor decimal (ex: 0.5, 0.7, 1.0) |
| **Template LaTeX** | [Lista de templates salvos] |

**Randomização:**
- Quando ativada, a ordem das questões é embaralhada aleatoriamente
- Permite gerar múltiplas versões diferentes de uma mesma prova
- Sistema pode opcionalmente usar versões alternativas de questões vinculadas

**Templates:**
- Sistema vem com 1 template padrão
- Usuário pode importar templates personalizados (.cls ou .sty)
- Templates salvos em `/templates/latex/`

#### RF08.3 - Geração de Arquivo .tex

**Estrutura do .tex gerado:**
```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[brazilian]{babel}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{enumitem}  % Para customizar listas
\usepackage{multicol}  % se 2 colunas

\begin{document}

% CABEÇALHO PERSONALIZADO
\noindent
\textbf{[NOME DA ESCOLA]} \\
Professor: [NOME] \\
Data: [DATA] \hfill Turma: [TURMA]

\begin{center}
\Large\textbf{[TÍTULO DA LISTA]}
\end{center}

% INSTRUÇÕES
\textit{[INSTRUÇÕES GERAIS]}

\vspace{1cm}

% QUESTÕES
\begin{enumerate}
  \item [ENUNCIADO LaTeX]

  \includegraphics[scale=0.7]{[caminho_imagem]} % se houver, usuário define escala

  \begin{enumerate}[label=\Alph*)]
    \item [ALTERNATIVA A]
    \item [ALTERNATIVA B]
    ...
  \end{enumerate}

  % Espaço para resposta (se configurado)
  \vspace{3cm}

\end{enumerate}

% GABARITO (se configurado)
\newpage
\section*{Gabarito}
1. [LETRA CORRETA] \\
...

% RESOLUÇÕES (se configurado)
\newpage
\section*{Resoluções}
\textbf{Questão 1:} [RESOLUÇÃO LaTeX]

\end{document}
```

#### RF08.4 - Compilação LaTeX
**Requisitos Técnicos:**
- Sistema deve detectar se LaTeX está instalado
- Se não instalado: instruir usuário a instalar TeX Live/MiKTeX
- Comando de compilação: `pdflatex arquivo.tex`
- Tratamento de erros de compilação

**Distribuições Suportadas (Windows):**
- MiKTeX (recomendado para Windows)
- TeX Live

---

### RF09 - Editor LaTeX com Preview

#### RF09.1 - Interface de Edição
**Campos com LaTeX:**
- Enunciado
- Alternativas (A-E)
- Resolução
- Gabarito (discursivas)

**Modo de Operação (Opção D):**
- Campo de texto para código LaTeX
- Botão "Visualizar Preview"
- Preview abre em janela/painel separado
- Preview é estático (não atualiza em tempo real)

#### RF09.2 - Renderização de Preview
**Biblioteca:** matplotlib + LaTeX backend

**Processo:**
1. Usuário digita LaTeX no campo
2. Clica "Visualizar Preview"
3. Sistema gera imagem PNG do LaTeX renderizado
4. Exibe imagem em QLabel do PyQt

**Fallback:** Se erro de compilação, exibir mensagem de erro detalhada

---

### RF10 - Backup e Recuperação

#### RF10.1 - Backup Manual
**Funcionalidade:**
- Menu: Arquivo → Fazer Backup
- Cria cópia de:
  - `questoes.db`
  - Pasta `/imagens/`
  - Pasta `/templates/`
- Compacta em arquivo ZIP
- Nome padrão: `backup_questoes_YYYYMMDD_HHMMSS.zip`

#### RF10.2 - Restaurar Backup
**Funcionalidade:**
- Menu: Arquivo → Restaurar Backup
- Selecionar arquivo .zip
- Sistema valida estrutura
- Sobrescreve banco e arquivos atuais (com confirmação)

#### RF10.3 - Backup Automático (Opcional - Baixa Prioridade)
**Configuração:**
- Ativar/desativar em Configurações
- Periodicidade: diária/semanal
- Local padrão: `/backups/`
- Manter últimos X backups

---

## 3. REQUISITOS NÃO FUNCIONAIS

### RNF01 - Usabilidade
- Interface intuitiva estilo aplicação desktop moderna
- Atalhos de teclado para operações frequentes
- Feedback visual para todas as operações
- Mensagens de erro claras e orientativas
- Tempo máximo de aprendizado: 30 minutos

### RNF02 - Desempenho
- Tempo de resposta de busca: < 2 segundos (até 10.000 questões)
- Renderização de preview LaTeX: < 5 segundos
- Geração de PDF: < 10 segundos (lista com 50 questões)
- Inicialização da aplicação: < 3 segundos

### RNF03 - Confiabilidade
- Taxa de falha de renderização LaTeX: < 5%
- Proteção contra perda de dados (salvamento automático)
- Validação de integridade do banco ao iniciar
- Tratamento de exceções com logs

### RNF04 - Manutenibilidade
- Código modular (separação Model-View-Controller)
- Comentários em português
- Docstrings em todas as funções
- Facilidade de adicionar novas disciplinas

### RNF05 - Portabilidade
- Sistema operacional: Windows 10/11
- Python 3.11
- Banco de dados portável (SQLite arquivo único)
- Dependências gerenciadas via requirements.txt

### RNF06 - Segurança
- Validação de entrada em todos os formulários
- Proteção contra SQL Injection (uso de prepared statements)
- Validação de tipos de arquivo de imagem
- Backup antes de operações destrutivas

---

## 4. MODELO DE BANCO DE DADOS

### 4.1 Diagrama Entidade-Relacionamento

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│     TAG     │────────<│  QUESTAO_TAG     │>────────│   QUESTAO   │
│             │   N:N   │                  │   N:N   │             │
└─────────────┘         └──────────────────┘         └─────────────┘
                                                            │
                                                            │ 1:N
                                                            ↓
                                                      ┌─────────────┐
                                                      │ ALTERNATIVA │
                                                      └─────────────┘
                                                            ↑
                                                            │ N:1
                                                      ┌─────────────┐
                                                      │ DIFICULDADE │
                                                      └─────────────┘

┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│    LISTA    │────────<│  LISTA_QUESTAO   │>────────│   QUESTAO   │
│             │   N:N   │                  │   N:N   │             │
└─────────────┘         └──────────────────┘         └─────────────┘

┌─────────────┐         ┌──────────────────┐
│   QUESTAO   │────────<│ QUESTAO_VERSAO   │  (versões alternativas)
│             │   N:N   │                  │
└─────────────┘         └──────────────────┘
```

### 4.2 Script DDL (SQLite)

```sql
-- ============================================
-- TABELA: TAG
-- ============================================
CREATE TABLE tag (
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

CREATE INDEX idx_tag_pai ON tag(id_tag_pai);
CREATE INDEX idx_tag_ativo ON tag(ativo);
CREATE INDEX idx_tag_numeracao ON tag(numeracao);

-- ============================================
-- TABELA: DIFICULDADE
-- ============================================
CREATE TABLE dificuldade (
    id_dificuldade INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descricao TEXT,
    ordem INTEGER  -- Para ordenação (1=Fácil, 2=Médio, 3=Difícil)
);

-- Dados iniciais de dificuldade
INSERT INTO dificuldade (nome, descricao, ordem) VALUES
('FÁCIL', 'Questões de nível básico', 1),
('MÉDIO', 'Questões de nível intermediário', 2),
('DIFÍCIL', 'Questões de nível avançado', 3);

-- ============================================
-- TABELA: QUESTAO
-- ============================================
CREATE TABLE questao (
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

CREATE INDEX idx_questao_tipo ON questao(tipo);
CREATE INDEX idx_questao_ativo ON questao(ativo);
CREATE INDEX idx_questao_titulo ON questao(titulo);
CREATE INDEX idx_questao_ano ON questao(ano);
CREATE INDEX idx_questao_fonte ON questao(fonte);
CREATE INDEX idx_questao_dificuldade ON questao(id_dificuldade);
CREATE TRIGGER questao_update_timestamp
    AFTER UPDATE ON questao
    FOR EACH ROW
    BEGIN
        UPDATE questao SET data_modificacao = CURRENT_TIMESTAMP
        WHERE id_questao = NEW.id_questao;
    END;

-- ============================================
-- TABELA: ALTERNATIVA
-- ============================================
CREATE TABLE alternativa (
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

CREATE INDEX idx_alternativa_questao ON alternativa(id_questao);

-- Trigger: Garantir apenas 1 alternativa correta por questão
CREATE TRIGGER alternativa_unica_correta
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

-- ============================================
-- TABELA: QUESTAO_TAG (Relacionamento N:N)
-- ============================================
CREATE TABLE questao_tag (
    id_questao INTEGER NOT NULL,
    id_tag INTEGER NOT NULL,
    data_associacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_questao, id_tag),
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    FOREIGN KEY (id_tag) REFERENCES tag(id_tag) ON DELETE CASCADE
);

CREATE INDEX idx_questao_tag_questao ON questao_tag(id_questao);
CREATE INDEX idx_questao_tag_tag ON questao_tag(id_tag);

-- ============================================
-- TABELA: LISTA
-- ============================================
CREATE TABLE lista (
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
CREATE TABLE lista_questao (
    id_lista INTEGER NOT NULL,
    id_questao INTEGER NOT NULL,
    data_adicao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_lista, id_questao),
    FOREIGN KEY (id_lista) REFERENCES lista(id_lista) ON DELETE CASCADE,
    FOREIGN KEY (id_questao) REFERENCES questao(id_questao) ON DELETE CASCADE
);

CREATE INDEX idx_lista_questao_lista ON lista_questao(id_lista);
CREATE INDEX idx_lista_questao_questao ON lista_questao(id_questao);

-- ============================================
-- TABELA: QUESTAO_VERSAO (Versões Alternativas)
-- ============================================
CREATE TABLE questao_versao (
    id_questao_original INTEGER NOT NULL,
    id_questao_versao INTEGER NOT NULL,
    observacao TEXT,  -- Nota sobre a relação entre as versões
    data_vinculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_questao_original, id_questao_versao),
    FOREIGN KEY (id_questao_original) REFERENCES questao(id_questao) ON DELETE CASCADE,
    FOREIGN KEY (id_questao_versao) REFERENCES questao(id_questao) ON DELETE CASCADE,
    CHECK (id_questao_original != id_questao_versao)  -- Questão não pode ser versão de si mesma
);

CREATE INDEX idx_questao_versao_original ON questao_versao(id_questao_original);
CREATE INDEX idx_questao_versao_versao ON questao_versao(id_questao_versao);

-- ============================================
-- TABELA: CONFIGURACAO (Sistema)
-- ============================================
CREATE TABLE configuracao (
    chave VARCHAR(50) PRIMARY KEY,
    valor TEXT,
    descricao TEXT
);

-- Configurações padrão
INSERT INTO configuracao (chave, valor, descricao) VALUES
('backup_automatico', '0', 'Ativar backup automático (0=não, 1=sim)'),
('backup_periodicidade', '7', 'Dias entre backups automáticos'),
('backup_manter', '5', 'Quantidade de backups a manter'),
('template_padrao', 'default.tex', 'Template LaTeX padrão'),
('latex_colunas_padrao', '1', 'Colunas padrão na exportação (1 ou 2)'),
('latex_incluir_gabarito', '1', 'Incluir gabarito por padrão'),
('latex_incluir_resolucao', '0', 'Incluir resoluções por padrão'),
('latex_escala_imagem_padrao', '0.7', 'Escala padrão para imagens no LaTeX'),
('randomizar_questoes_padrao', '0', 'Randomizar questões por padrão ao exportar');
```

### 4.3 Dados Iniciais - Taxonomia Matemática

```sql
-- Tags de Conteúdo Matemático (Hierárquica)
INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) VALUES
-- Nível 1
('NÚMEROS E OPERAÇÕES', '1', 1, NULL, 1),
('ÁLGEBRA', '2', 1, NULL, 2),
('GEOMETRIA', '3', 1, NULL, 3),
('TRIGONOMETRIA', '4', 1, NULL, 4),
('COMBINATÓRIA', '5', 1, NULL, 5),
('PROBABILIDADE', '6', 1, NULL, 6),
('ESTATÍSTICA', '7', 1, NULL, 7);

-- Nível 2 - Álgebra
INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÕES', '2.1', 2, id_tag, 1 FROM tag WHERE numeracao = '2';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'EQUAÇÕES', '2.2', 2, id_tag, 2 FROM tag WHERE numeracao = '2';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'PROGRESSÕES', '2.3', 2, id_tag, 3 FROM tag WHERE numeracao = '2';

-- Nível 3 - Funções
INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÃO AFIM', '2.1.1', 3, id_tag, 1 FROM tag WHERE numeracao = '2.1';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÃO QUADRÁTICA', '2.1.2', 3, id_tag, 2 FROM tag WHERE numeracao = '2.1';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÃO EXPONENCIAL', '2.1.3', 3, id_tag, 3 FROM tag WHERE numeracao = '2.1';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÃO LOGARÍTMICA', '2.1.4', 3, id_tag, 4 FROM tag WHERE numeracao = '2.1';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'FUNÇÃO TRIGONOMÉTRICA', '2.1.5', 3, id_tag, 5 FROM tag WHERE numeracao = '2.1';

-- Nível 3 - Progressões
INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'PROGRESSÃO ARITMÉTICA', '2.3.1', 3, id_tag, 1 FROM tag WHERE numeracao = '2.3';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'PROGRESSÃO GEOMÉTRICA', '2.3.2', 3, id_tag, 2 FROM tag WHERE numeracao = '2.3';

-- Nível 2 - Geometria
INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'GEOMETRIA PLANA', '3.1', 2, id_tag, 1 FROM tag WHERE numeracao = '3';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'GEOMETRIA ESPACIAL', '3.2', 2, id_tag, 2 FROM tag WHERE numeracao = '3';

INSERT INTO tag (nome, numeracao, nivel, id_tag_pai, ordem) 
SELECT 'GEOMETRIA ANALÍTICA', '3.3', 2, id_tag, 3 FROM tag WHERE numeracao = '3';

-- Tags de Vestibular (Sem hierarquia - nível 1)
INSERT INTO tag (nome, numeracao, nivel, ordem) VALUES
('ENEM', 'V1', 1, 100),
('FUVEST', 'V2', 1, 101),
('UNICAMP', 'V3', 1, 102),
('UNESP', 'V4', 1, 103),
('UERJ', 'V5', 1, 104),
('ITA', 'V6', 1, 105),
('IME', 'V7', 1, 106),
('MILITAR', 'V8', 1, 107);

-- Tags de Nível de Escolaridade
INSERT INTO tag (nome, numeracao, nivel, ordem) VALUES
('E.F.2', 'N1', 1, 200),
('E.M.', 'N2', 1, 201),
('E.J.A.', 'N3', 1, 202);
```

---

## 5. ARQUITETURA DO SISTEMA

### 5.1 Estrutura de Diretórios

```
/sistema-questoes/
│
├── /src/
│   ├── /models/          # Camada de dados (ORM/DAO)
│   │   ├── database.py   # Conexão e inicialização do banco
│   │   ├── questao.py    # Model Questão
│   │   ├── tag.py        # Model Tag
│   │   ├── lista.py      # Model Lista
│   │   └── alternativa.py
│   │
│   ├── /views/           # Interface PyQt6
│   │   ├── main_window.py
│   │   ├── questao_form.py
│   │   ├── tag_manager.py
│   │   ├── search_panel.py
│   │   ├── lista_form.py
│   │   └── export_dialog.py
│   │
│   ├── /controllers/     # Lógica de negócio
│   │   ├── questao_controller.py
│   │   ├── tag_controller.py
│   │   ├── lista_controller.py
│   │   └── export_controller.py
│   │
│   ├── /utils/           # Utilitários
│   │   ├── latex_renderer.py
│   │   ├── image_handler.py
│   │   ├── backup_manager.py
│   │   └── validators.py
│   │
│   └── main.py           # Ponto de entrada
│
├── /database/
│   └── questoes.db       # Banco SQLite
│
├── /imagens/
│   ├── /enunciados/
│   └── /alternativas/
│
├── /templates/
│   └── /latex/
│       └── default.tex   # Template padrão
│
├── /exports/             # PDFs e .tex gerados
│
├── /backups/             # Backups automáticos
│
├── /logs/                # Logs da aplicação
│
├── requirements.txt      # Dependências Python
├── config.ini            # Configurações da aplicação
└── README.md
```

### 5.2 Stack Tecnológico

**Linguagem:** Python 3.11

**Framework GUI:** PyQt6
- `PyQt6` - Framework principal
- `PyQt6.QtWidgets` - Componentes de interface
- `PyQt6.QtGui` - Recursos gráficos
- `PyQt6.QtCore` - Funcionalidades core

**Banco de Dados:** SQLite 3
- `sqlite3` (biblioteca padrão Python)

**LaTeX:**
- `matplotlib` - Renderização de LaTeX para preview
- Distribuição TeX externa (MiKTeX/TeX Live) para compilação de PDF

**Manipulação de Imagens:**
- `Pillow` - Processamento de imagens
- `PyQt6.QtGui.QPixmap` - Exibição de imagens

**Outras Dependências:**
- `python-dateutil` - Manipulação de datas
- `pylatex` (opcional) - Geração programática de LaTeX

### 5.3 Padrão Arquitetural

**MVC (Model-View-Controller)**

**Model:**
- Classes representando entidades do banco
- Métodos CRUD básicos
- Validações de dados

**View:**
- Componentes PyQt6
- Apenas responsável por exibição e captura de eventos
- Não contém lógica de negócio

**Controller:**
- Intermediário entre Model e View
- Lógica de negócio
- Coordenação de operações complexas

---

## 6. FLUXOS PRINCIPAIS

### 6.1 Fluxo de Cadastro de Questão

```
[Usuário clica "Nova Questão"]
    ↓
[Abre formulário vazio]
    ↓
[Usuário preenche campos obrigatórios]
    ↓
[Usuário seleciona tipo: OBJETIVA/DISCURSIVA]
    ↓
[Se OBJETIVA → Habilita campos de 5 alternativas]
[Se DISCURSIVA → Habilita campo gabarito_discursiva]
    ↓
[Usuário seleciona tags (mínimo 1)]
    ↓
[Usuário clica "Visualizar Preview" (opcional)]
    ↓
[Sistema renderiza LaTeX em painel de preview]
    ↓
[Usuário clica "Salvar"]
    ↓
[Sistema valida:]
  - Enunciado não vazio
  - Tipo selecionado
  - Se OBJETIVA: 5 alternativas + 1 correta
  - Mínimo 1 tag
    ↓
[Se válido → Salva no banco + copia imagens]
[Se inválido → Exibe erros no formulário]
    ↓
[Fecha formulário e atualiza lista de questões]
```

### 6.2 Fluxo de Busca e Filtros

```
[Usuário acessa tela de busca]
    ↓
[Painel lateral exibe árvore de tags com contadores]
    ↓
[OPÇÃO A: Busca por texto]
  → Usuário digita no campo "Título"
  → Sistema busca no campo `titulo` (LIKE)
  → Exibe resultados
    ↓
[OPÇÃO B: Filtros por tags]
  → Usuário marca checkboxes de tags
  → Sistema aplica filtro cumulativo (AND)
  → Exibe contadores por tag mesmo sem resultado
    ↓
[Resultados exibidos em cards]
    ↓
[Usuário seleciona ações por card:]
  - Visualizar preview completo
  - Editar questão
  - Adicionar à lista atual
  - Inativar/Reativar
```

### 6.3 Fluxo de Criação de Lista

```
[Usuário clica "Nova Lista"]
    ↓
[Abre formulário de lista]
    ↓
[Usuário preenche:]
  - Título (obrigatório)
  - Tipo (opcional - texto livre)
  - Cabeçalho personalizado (opcional)
  - Instruções (opcional)
    ↓
[Usuário adiciona questões:]
  - Via busca e seleção individual
  - Via seleção múltipla de resultados
  - Via arrastar e soltar (opcional)
    ↓
[Sistema exibe questões adicionadas]
    ↓
[Usuário clica "Salvar Lista"]
    ↓
[Sistema salva metadados + relacionamentos]
    ↓
[Usuário pode:]
  - Visualizar preview da lista
  - Exportar para LaTeX/PDF
  - Editar metadados
  - Adicionar/remover questões
```

### 6.4 Fluxo de Exportação LaTeX/PDF

```
[Usuário seleciona lista existente]
    ↓
[Clica "Exportar"]
    ↓
[Abre diálogo de exportação]
    ↓
[Usuário configura opções:]
  - Layout (1 ou 2 colunas)
  - Incluir gabarito (Sim/Não)
  - Incluir resoluções (Sim/Não)
  - Espaço para respostas (X linhas)
  - Template LaTeX
    ↓
[Usuário escolhe fluxo:]
    ↓
[OPÇÃO A - Exportação Direta]
  → Sistema gera .tex
  → Sistema compila automaticamente (pdflatex)
  → Sistema abre PDF
    ↓
[OPÇÃO B - Exportação Manual]
  → Sistema gera .tex
  → Sistema salva em /exports/
  → Usuário edita manualmente (editor externo)
  → Usuário compila quando quiser
    ↓
[Sistema verifica se LaTeX está instalado]
  → Se não: exibe instruções de instalação
  → Se sim: prossegue com compilação
    ↓
[Se erro de compilação:]
  → Exibe log de erros
  → Mantém arquivo .tex para correção manual
```

---

## 7. CASOS DE USO DETALHADOS

### UC01 - Cadastrar Nova Questão

**Ator:** Professor/Usuário

**Pré-condições:** Sistema inicializado

**Fluxo Principal:**
1. Usuário clica em "Nova Questão" no menu
2. Sistema abre formulário vazio
3. Usuário preenche enunciado (LaTeX)
4. Usuário seleciona tipo (OBJETIVA/DISCURSIVA)
5. Usuário preenche alternativas (se OBJETIVA)
6. Usuário seleciona tags (mínimo 1)
7. Usuário clica "Salvar"
8. Sistema valida dados
9. Sistema salva questão no banco
10. Sistema fecha formulário

**Fluxo Alternativo 3A - Adicionar imagem ao enunciado:**
- 3.1. Usuário clica "Adicionar Imagem"
- 3.2. Sistema abre seletor de arquivo
- 3.3. Usuário seleciona imagem (PNG/JPG/JPEG/SVG)
- 3.4. Sistema valida formato
- 3.5. Sistema copia imagem para `/imagens/enunciados/`
- 3.6. Sistema salva caminho relativo no banco

**Fluxo Alternativo 8A - Validação falha:**
- 8.1. Sistema destaca campos com erro
- 8.2. Sistema exibe mensagens de erro
- 8.3. Retorna ao passo 7

**Pós-condições:** Questão salva e disponível para busca

---

### UC02 - Buscar Questões por Tags

**Ator:** Professor/Usuário

**Pré-condições:** Sistema possui questões cadastradas

**Fluxo Principal:**
1. Usuário acessa tela de busca
2. Sistema exibe painel de filtros com árvore de tags
3. Usuário marca checkbox de tag desejada
4. Sistema aplica filtro e atualiza resultados
5. Usuário marca checkbox de segunda tag
6. Sistema aplica filtro cumulativo (AND)
7. Sistema exibe resultados em cards
8. Sistema exibe contadores por tag

**Fluxo Alternativo 6A - Nenhuma questão encontrada:**
- 6.1. Sistema exibe mensagem "0 questões encontradas"
- 6.2. Sistema mantém contadores individuais por tag
- 6.3. Sistema sugere remover filtros

**Pós-condições:** Lista de questões filtradas exibida

---

### UC03 - Criar Lista de Exercícios

**Ator:** Professor/Usuário

**Pré-condições:** Sistema possui questões cadastradas

**Fluxo Principal:**
1. Usuário clica "Nova Lista"
2. Sistema abre formulário de lista
3. Usuário preenche título
4. Usuário preenche cabeçalho personalizado (opcional)
5. Usuário clica "Adicionar Questões"
6. Sistema abre painel de busca
7. Usuário busca e seleciona questões
8. Sistema adiciona questões à lista temporária
9. Usuário revisa lista
10. Usuário clica "Salvar Lista"
11. Sistema salva lista no banco

**Fluxo Alternativo 7A - Seleção múltipla:**
- 7.1. Usuário marca múltiplas questões
- 7.2. Usuário clica "Adicionar Selecionadas"
- 7.3. Sistema adiciona todas à lista

**Pós-condições:** Lista criada e disponível para exportação

---

### UC04 - Exportar Lista para PDF

**Ator:** Professor/Usuário

**Pré-condições:**
- Lista criada com questões
- LaTeX instalado no sistema (para exportação direta)

**Fluxo Principal:**
1. Usuário seleciona lista
2. Usuário clica "Exportar PDF"
3. Sistema abre diálogo de exportação
4. Usuário configura opções (layout, gabarito, resoluções)
5. Usuário escolhe "Exportação Direta"
6. Usuário clica "Exportar"
7. Sistema gera arquivo .tex
8. Sistema compila com pdflatex
9. Sistema abre PDF gerado
10. Sistema exibe mensagem de sucesso

**Fluxo Alternativo 5A - Exportação Manual:**
- 5.1. Usuário escolhe "Exportação Manual"
- 5.2. Usuário clica "Gerar .tex"
- 5.3. Sistema gera arquivo .tex
- 5.4. Sistema salva em `/exports/`
- 5.5. Sistema exibe caminho do arquivo
- 5.6. Fim do caso de uso

**Fluxo Alternativo 8A - Erro de compilação:**
- 8.1. Sistema detecta erro
- 8.2. Sistema exibe log de erros
- 8.3. Sistema mantém arquivo .tex para correção
- 8.4. Sistema sugere compilação manual

**Pós-condições:** PDF gerado e disponível

---

## 8. PRIORIZAÇÃO E ROADMAP

### 8.1 MVP (Versão 1.0)

**Funcionalidades Essenciais:**
- ✅ RF01 - Gerenciamento de Tags (básico)
- ✅ RF02 - Cadastro de Questões (OBJETIVA e DISCURSIVA)
- ✅ RF03 - Vinculação Tags-Questões
- ✅ RF04 - Busca por texto e filtros por tags
- ✅ RF05 - Visualização de questões
- ✅ RF06 - Edição e soft delete
- ✅ RF07 - Criação de listas
- ✅ RF08 - Exportação LaTeX/PDF (básica)
- ✅ RF09 - Editor LaTeX com preview estático

**Prioridade:** ALTA

---

### 8.2 Versão 1.1 (Melhorias)

**Funcionalidades:**
- ✅ RF01.2 - Drag-and-drop para reorganizar tags
- ✅ RF02.4 - Suporte a SVG
- ✅ RF08.2 - Templates LaTeX personalizados
- ✅ RF10.1 - Backup manual

**Prioridade:** MÉDIA

---

### 8.3 Versão 1.2 (Extensões)

**Funcionalidades:**
- ✅ RF10.3 - Backup automático
- ✅ Estatísticas de uso (questões mais usadas, tags mais aplicadas)
- ✅ Histórico de listas geradas
- ✅ Duplicação de questões

**Prioridade:** BAIXA

---

### 8.4 Futuro (Extensibilidade)

**Funcionalidades Planejadas:**
- Suporte a outras disciplinas (Física, Química, etc.)
- Sistema de autenticação multi-usuário
- Sincronização em nuvem
- Importação de questões de outros formatos
- Gerador automático de listas por critérios

---

## 9. CONSIDERAÇÕES TÉCNICAS

### 9.1 Renderização LaTeX

**Opção Escolhida:** matplotlib + LaTeX backend

**Processo:**
```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['text.usetex'] = True

def render_latex_preview(latex_code):
    fig = plt.figure(figsize=(6, 2))
    fig.text(0.5, 0.5, f'${latex_code}$',
             fontsize=14, ha='center', va='center')
    plt.axis('off')

    # Salvar como imagem temporária
    plt.savefig('temp_preview.png', bbox_inches='tight', dpi=150)
    plt.close()

    return 'temp_preview.png'
```

**Limitações:**
- Requer LaTeX instalado no sistema
- Preview não é em tempo real
- Erros de sintaxe devem ser tratados

---

### 9.2 Armazenamento de Imagens

**Decisão:** Arquivos separados (não BLOB no banco)

**Vantagens:**
- Performance superior
- Facilidade de backup
- Possibilidade de edição externa
- Menor tamanho do banco de dados

**Convenção de Nomenclatura:**
```
questao_{id_questao}_enunciado.{ext}
questao_{id_questao}_alt_{letra}.{ext}
```

**Gestão de Imagens Órfãs:**
- Ao excluir questão (soft delete): manter imagens
- Limpeza manual via ferramenta administrativa
- Verificação de integridade no startup

---

### 9.3 Tratamento de Erros

**Categorias:**

1. **Erros de Validação:**
   - Exibidos no formulário
   - Campos destacados em vermelho
   - Mensagens claras e orientativas

2. **Erros de Banco:**
   - Log detalhado em `/logs/`
   - Mensagem genérica ao usuário
   - Sugestão de restaurar backup

3. **Erros de LaTeX:**
   - Exibir log completo do compilador
   - Destacar linha com erro (se possível)
   - Sugerir correções comuns

4. **Erros de Sistema:**
   - Dialog de erro crítico
   - Salvamento emergencial de dados
   - Log completo + stack trace

---

### 9.4 Performance

**Otimizações Planejadas:**

1. **Busca:**
   - Índices em campos de busca frequente
   - Lazy loading de resultados (paginação)
   - Cache de contadores de tags

2. **Renderização:**
   - Cache de previews LaTeX
   - Carregamento assíncrono de imagens
   - Thumbnails para preview rápido

3. **Exportação:**
   - Processamento em thread separada
   - Barra de progresso
   - Cancelamento de operação

---

## 10. GLOSSÁRIO

**Alternativa:** Opção de resposta em questão objetiva (A, B, C, D, E)

**Enunciado:** Texto principal da questão, pode conter LaTeX

**Gabarito:** Resposta correta de uma questão

**LaTeX:** Sistema de composição tipográfica para notação matemática

**Lista:** Conjunto de questões agrupadas para exportação (prova/lista/simulado)

**Preview:** Visualização renderizada do LaTeX antes da exportação

**Soft Delete:** Exclusão lógica (marca como inativo) sem remover do banco

**Tag:** Rótulo para categorização de questões

**Tag Hierárquica:** Tag organizada em níveis (ex: ÁLGEBRA > FUNÇÕES > FUNÇÃO AFIM)

**Tag Livre:** Tag criada pelo usuário sem hierarquia pré-definida

**Template LaTeX:** Arquivo modelo para formatação de documentos exportados

---

## 11. REFERÊNCIAS

**Tecnologias:**
- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- SQLite Documentation: https://www.sqlite.org/docs.html
- LaTeX Project: https://www.latex-project.org/
- Matplotlib: https://matplotlib.org/

**Padrões:**
- PEP 8 - Style Guide for Python Code
- SQLite Best Practices
- MVC Pattern Documentation

---

## 12. APROVAÇÃO

**Versão:** 1.0.1
**Status:** ✅ APROVADO PARA DESENVOLVIMENTO
**Data:** Janeiro 2026

**Próximos Passos:**
1. Configuração do ambiente de desenvolvimento
2. Criação da estrutura de diretórios
3. Implementação do banco de dados
4. Desenvolvimento do MVP (Versão 1.0)

---

## 13. HISTÓRICO DE ALTERAÇÕES

### Versão 1.0.1 - Janeiro 2026

**Alterações Realizadas:**

1. **RF02.1 - Campos Obrigatórios da Questão**
   - ✅ Adicionado campo `ano` (INTEGER) como obrigatório
   - ✅ Adicionado campo `fonte` (VARCHAR) como obrigatório (Banca/Vestibular ou 'AUTORAL')
   - ✅ Adicionado campo `escala_imagem_enunciado` (DECIMAL) para controlar escala das imagens

2. **RF03.1 - Categorias de Tags**
   - ✅ Removida categoria "Dificuldade" (agora é tabela separada)
   - ✅ Removida categoria "Ano/Série" (substituída por "Nível de Escolaridade")
   - ✅ Removida categoria "Ano do Exame" (agora é campo direto na questão)
   - ✅ Adicionada categoria "Nível de Escolaridade": E.F.2, E.M., E.J.A.

3. **RF07.2 - Criação de Listas/Provas**
   - ✅ Adicionada funcionalidade de randomização de questões
   - ✅ Adicionado suporte a versões alternativas de questões
   - ✅ Nova tabela `questao_versao` para vincular questões equivalentes
   - ✅ Sistema pode substituir questões por versões ao gerar provas

4. **RF08.2 - Opções de Exportação**
   - ✅ Adicionada opção "Randomizar Questões" (Sim/Não)
   - ✅ Adicionada opção "Escala de Imagens" (valor decimal configurável)

5. **RF08.3 - Template LaTeX**
   - ✅ Corrigido uso de `\includegraphics` com parâmetro `scale` configurável
   - ✅ Adicionado pacote `enumitem` para alternativas com `[label=\Alph*)]`
   - ✅ Imagens com escala definida pelo usuário: `\includegraphics[scale=0.7]{...}`

6. **Modelo de Banco de Dados**
   - ✅ Nova tabela `dificuldade` (id_dificuldade, nome, descricao, ordem)
   - ✅ Dados iniciais: FÁCIL, MÉDIO, DIFÍCIL
   - ✅ Campo `id_dificuldade` na tabela `questao` (FK para dificuldade)
   - ✅ Nova tabela `questao_versao` (relacionamento N:N entre questões)
   - ✅ Campo `escala_imagem` na tabela `alternativa`
   - ✅ Novos índices para melhor performance
   - ✅ Atualizadas tags iniciais conforme novas categorias

7. **Configurações do Sistema**
   - ✅ Nova configuração: `latex_escala_imagem_padrao` (default: 0.7)
   - ✅ Nova configuração: `randomizar_questoes_padrao` (default: 0)

**Diagrama ER Atualizado:**
- Relacionamento QUESTAO ↔ DIFICULDADE (N:1)
- Relacionamento QUESTAO ↔ QUESTAO_VERSAO (N:N)
- Relacionamento QUESTAO ↔ QUESTAO_TAG (N:N) - mantido
- Relacionamento QUESTAO ↔ ALTERNATIVA (1:N) - mantido

---

**FIM DO DOCUMENTO**