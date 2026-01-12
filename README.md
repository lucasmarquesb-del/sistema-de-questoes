# Sistema de Banco de Questões Educacionais

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6.1-green)
![SQLite](https://img.shields.io/badge/SQLite-3-orange)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

Sistema desktop para gerenciamento de banco de questões educacionais focado em Matemática, com sistema robusto de tags hierárquicas, suporte completo a LaTeX e exportação profissional para PDF.

---

## 📋 Características Principais

- ✅ **Uso Pessoal** - Sem necessidade de autenticação
- ✅ **Sistema Híbrido de Tags** - Hierarquia estruturada + tags livres
- ✅ **Suporte Nativo a LaTeX** - Notação matemática completa
- ✅ **Busca Avançada** - Filtros cumulativos e busca por texto
- ✅ **Exportação Profissional** - PDF/LaTeX com templates customizáveis
- ✅ **Randomização de Provas** - Múltiplas versões da mesma prova
- ✅ **Versões de Questões** - Vincule questões equivalentes
- ✅ **Arquitetura Extensível** - Preparado para outras disciplinas

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.11 ou superior
- MiKTeX ou TeX Live (para compilação de PDFs)
- Windows 10/11 (testado)

### Passo a Passo

1. **Clone ou baixe o repositório**
   ```bash
   cd "sistema de questoes"
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicialize o banco de dados**
   ```bash
   python src/models/database.py
   ```

6. **Execute o sistema**
   ```bash
   python src/main.py
   ```

---

## 📂 Estrutura do Projeto

```
sistema-questoes/
│
├── src/
│   ├── models/              # Camada de dados (ORM/DAO)
│   │   ├── database.py      # Conexão e inicialização do banco
│   │   ├── questao.py       # Model Questão
│   │   ├── tag.py           # Model Tag
│   │   ├── lista.py         # Model Lista
│   │   └── alternativa.py   # Model Alternativa
│   │
│   ├── views/               # Interface PyQt6
│   │   ├── main_window.py   # Janela principal
│   │   ├── questao_form.py  # Formulário de questões
│   │   ├── tag_manager.py   # Gerenciador de tags
│   │   ├── search_panel.py  # Painel de busca
│   │   ├── lista_form.py    # Formulário de listas
│   │   └── export_dialog.py # Diálogo de exportação
│   │
│   ├── controllers/         # Lógica de negócio
│   │   ├── questao_controller.py
│   │   ├── tag_controller.py
│   │   ├── lista_controller.py
│   │   └── export_controller.py
│   │
│   ├── utils/               # Utilitários
│   │   ├── latex_renderer.py
│   │   ├── image_handler.py
│   │   ├── backup_manager.py
│   │   └── validators.py
│   │
│   └── main.py              # Ponto de entrada
│
├── database/
│   ├── init_db.sql          # Script de inicialização
│   └── questoes.db          # Banco SQLite (gerado)
│
├── imagens/
│   ├── enunciados/          # Imagens dos enunciados
│   └── alternativas/        # Imagens das alternativas
│
├── templates/
│   └── latex/
│       └── default.tex      # Template LaTeX padrão
│
├── exports/                 # PDFs e .tex gerados
├── backups/                 # Backups automáticos
├── logs/                    # Logs da aplicação
│
├── requirements.txt         # Dependências Python
├── config.ini               # Configurações da aplicação
└── README.md                # Este arquivo
```

---

## 🗄️ Modelo de Dados

### Tabelas Principais

- **`tag`** - Tags hierárquicas para categorização
- **`dificuldade`** - Níveis de dificuldade (Fácil, Médio, Difícil)
- **`questao`** - Questões (objetivas e discursivas)
- **`alternativa`** - Alternativas de questões objetivas
- **`questao_tag`** - Relacionamento N:N entre questões e tags
- **`lista`** - Listas/Provas
- **`lista_questao`** - Relacionamento N:N entre listas e questões
- **`questao_versao`** - Versões alternativas de questões
- **`configuracao`** - Configurações do sistema

### Relacionamentos

```
QUESTAO ↔ TAG (N:N)
QUESTAO → DIFICULDADE (N:1)
QUESTAO → ALTERNATIVA (1:N)
QUESTAO ↔ QUESTAO_VERSAO (N:N)
LISTA ↔ QUESTAO (N:N)
```

---

## 💡 Uso Básico

### 1. Cadastrar uma Questão

1. Clique em "Nova Questão" no menu
2. Preencha os campos obrigatórios:
   - Enunciado (pode usar LaTeX: `$x^2 + 2x + 1 = 0$`)
   - Tipo (Objetiva ou Discursiva)
   - Ano (ex: 2024)
   - Fonte (ex: ENEM, FUVEST, ou AUTORAL)
3. Selecione a dificuldade
4. Selecione pelo menos 1 tag
5. Para questões objetivas, preencha as 5 alternativas
6. Clique em "Visualizar Preview" para ver como ficará
7. Salve a questão

### 2. Buscar Questões

1. Acesse o painel de busca
2. Use filtros por tags (seleção múltipla)
3. Ou busque por título
4. Resultados são exibidos em cards com preview

### 3. Criar uma Lista/Prova

1. Clique em "Nova Lista"
2. Preencha título e cabeçalho personalizado
3. Adicione questões via busca
4. Salve a lista

### 4. Exportar para PDF

1. Selecione uma lista
2. Clique em "Exportar PDF"
3. Configure opções:
   - Layout (1 ou 2 colunas)
   - Incluir gabarito
   - Incluir resoluções
   - Randomizar questões
   - Escala de imagens
4. Escolha entre exportação direta ou manual
5. Sistema gera o PDF

---

## ⚙️ Configuração

Edite o arquivo `config.ini` para personalizar:

- Caminhos de diretórios
- Opções de LaTeX
- Configurações de backup
- Tema da interface
- Nível de logging

---

## 📝 LaTeX Suportado

O sistema suporta comandos LaTeX padrão para notação matemática:

```latex
$x^2 + 2x + 1 = 0$                    # Equação inline
$$\int_{0}^{1} x^2 dx$$               # Equação display
\frac{a}{b}                            # Frações
\sqrt{x}                               # Raiz quadrada
\sum_{i=1}^{n} i                       # Somatório
\lim_{x \to \infty} f(x)              # Limite
```

---

## 🔄 Backup e Recuperação

### Backup Manual

- Menu → Arquivo → Fazer Backup
- Cria arquivo ZIP com banco e imagens
- Salvo em `/backups/`

### Backup Automático

- Configure em `config.ini`:
  ```ini
  [BACKUP]
  auto_backup = True
  periodicidade_dias = 7
  manter_backups = 5
  ```

### Restaurar Backup

- Menu → Arquivo → Restaurar Backup
- Selecione arquivo .zip
- Sistema valida e restaura

---

## 🧪 Testes

Para testar o módulo do banco de dados:

```bash
python src/models/database.py
```

Saída esperada:
```
============================================================
TESTE DO MÓDULO DATABASE
============================================================

1. Inicializando banco de dados...
✓ Banco inicializado com sucesso!

2. Verificando integridade...
✓ Integridade verificada!

3. Testando queries básicas...
   - Dificuldades cadastradas: 3
   - Tags cadastradas: 27
   - Configurações: 9

4. Listando dificuldades:
   - FÁCIL: Questões de nível básico
   - MÉDIO: Questões de nível intermediário
   - DIFÍCIL: Questões de nível avançado

============================================================
TESTE CONCLUÍDO COM SUCESSO!
============================================================
```

---

## 🛠️ Stack Tecnológico

- **Linguagem:** Python 3.11
- **Framework GUI:** PyQt6
- **Banco de Dados:** SQLite 3
- **Renderização LaTeX:** matplotlib + LaTeX backend
- **Processamento de Imagens:** Pillow
- **Padrão Arquitetural:** MVC (Model-View-Controller)

---

## 📚 Taxonomia Matemática Pré-definida

O sistema vem com uma taxonomia matemática hierárquica:

```
1. NÚMEROS E OPERAÇÕES
2. ÁLGEBRA
   2.1. FUNÇÕES
       2.1.1. FUNÇÃO AFIM
       2.1.2. FUNÇÃO QUADRÁTICA
       2.1.3. FUNÇÃO EXPONENCIAL
       2.1.4. FUNÇÃO LOGARÍTMICA
       2.1.5. FUNÇÃO TRIGONOMÉTRICA
   2.2. EQUAÇÕES
   2.3. PROGRESSÕES
       2.3.1. PROGRESSÃO ARITMÉTICA
       2.3.2. PROGRESSÃO GEOMÉTRICA
3. GEOMETRIA
   3.1. GEOMETRIA PLANA
   3.2. GEOMETRIA ESPACIAL
   3.3. GEOMETRIA ANALÍTICA
4. TRIGONOMETRIA
5. COMBINATÓRIA
6. PROBABILIDADE
7. ESTATÍSTICA
```

Tags adicionais:
- **Vestibulares:** ENEM, FUVEST, UNICAMP, UNESP, UERJ, ITA, IME, MILITAR
- **Escolaridade:** E.F.2, E.M., E.J.A.

---

## 🐛 Troubleshooting

### Erro ao compilar LaTeX

- Verifique se MiKTeX ou TeX Live está instalado
- Verifique se `pdflatex` está no PATH
- Teste no terminal: `pdflatex --version`

### Erro ao conectar ao banco

- Verifique permissões da pasta `/database/`
- Delete `questoes.db` e execute `database.py` novamente

### Imagens não aparecem

- Verifique se o caminho em `config.ini` está correto
- Verifique permissões das pastas `/imagens/`

---

## 🗺️ Roadmap

### Versão 1.0 (MVP) - Em Desenvolvimento
- ✅ Estrutura base do projeto
- ✅ Banco de dados e migrations
- ⏳ Interface gráfica principal
- ⏳ Cadastro de questões
- ⏳ Sistema de tags
- ⏳ Busca e filtros
- ⏳ Criação de listas
- ⏳ Exportação para PDF

### Versão 1.1 (Melhorias)
- Drag-and-drop para reorganizar tags
- Suporte completo a SVG
- Templates LaTeX personalizados
- Backup manual

### Versão 1.2 (Extensões)
- Backup automático
- Estatísticas de uso
- Histórico de listas geradas
- Duplicação de questões

### Futuro
- Suporte a outras disciplinas (Física, Química)
- Sistema multi-usuário
- Sincronização em nuvem
- Importação de questões de outros formatos

---

## 📄 Licença

Este projeto é de uso pessoal e educacional.

---

## 👤 Autor

Sistema desenvolvido como ferramenta auxiliar para professores de Matemática.

---

## 📞 Suporte

Para reportar bugs ou sugerir melhorias, crie uma issue no repositório.

---

**Versão:** 1.0.1
**Última Atualização:** Janeiro 2026
