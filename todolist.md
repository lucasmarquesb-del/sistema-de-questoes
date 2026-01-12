📋 PRÓXIMOS CRUDs E FUNCIONALIDADES A IMPLEMENTAR

  🔴 PRIORIDADE ALTA (Essenciais para uso básico)

  1. CRUD de Listas

  Status: View criada, Model existe, Controller faltando
  - View: lista_form.py (já existe)
  - Model: lista.py (já existe)
  - Controller refatorado seguindo SOLID
  - Repository implementation
  - DTOs (ListaCreateDTO, ListaUpdateDTO, ListaResponseDTO) - JÁ EXISTEM
  - Integrar controller na view

  Funcionalidades:
  - Criar lista de questões
  - Adicionar/remover questões da lista
  - Reordenar questões
  - Editar metadados (título, tipo, cabeçalho, instruções)
  - Deletar lista
  - Listar todas as listas
  - Visualizar questões de uma lista

  ---
  2. CRUD de Tags

  Status: View criada, Model existe, Controller faltando
  - View: tag_manager.py (já existe)
  - Model: tag.py (já existe)
  - Controller refatorado
  - Repository implementation (TagRepositoryImpl - JÁ EXISTE)
  - DTOs
  - Integrar controller na view

  Funcionalidades:
  - Criar tag (nível 1, 2 ou 3)
  - Editar tag
  - Deletar tag (verificar se tem questões vinculadas)
  - Visualizar hierarquia completa
  - Buscar tags por nível
  - Buscar tags filhas
  - Carregar tags na árvore do QuestaoForm

  ---
  3. Exportação LaTeX

  Status: Dialog criado, lógica faltando
  - View: export_dialog.py (já existe)
  - Service de exportação LaTeX
  - Templates LaTeX (default, prova, lista, simulado)
  - Compilação automática (se selecionado)
  - Geração de gabarito
  - Randomização de questões
  - Controle de imagens e escala

  Funcionalidades:
  - Exportar lista para arquivo .tex
  - Compilar para PDF (opcional)
  - Incluir/excluir gabarito
  - Incluir/excluir resoluções
  - Randomizar questões
  - Configurar layout (colunas, espaçamento)
  - Escalar imagens
  - Escolher template

  ---
  🟡 PRIORIDADE MÉDIA (Melhorias importantes)

  4. Preview de Questões

  Status: View criada, necessita integração
  - View: questao_preview.py (já existe)
  - Integrar com QuestaoForm (botão Preview)
  - Integrar com SearchPanel (visualizar questão)
  - Renderizar LaTeX (via PyLaTeX ou imagem)
  - Exibir alternativas
  - Exibir resolução
  - Exibir tags

  ---
  5. Edição de Questões

  Status: Parcialmente implementado
  - View suporta edição (QuestaoForm com questao_id)
  - Controller tem método atualizar_questao_completa
  - Método load_questao() implementar (carregar dados existentes)
  - Testar atualização via UI
  - Atualização de alternativas (deletar e recriar)
  - Atualização de tags (sync)

  ---
  6. Inativação/Reativação de Questões

  Status: Implementado no controller, falta UI
  - Controller: inativar_questao(), reativar_questao()
  - Botão "Inativar" nos cards do SearchPanel
  - Filtro "Mostrar inativas" no SearchPanel
  - Confirmação antes de inativar
  - Visual diferenciado para questões inativas

  ---
  7. Dashboard / Estatísticas

  Status: Service implementado, View faltando
  - StatisticsService (já implementado)
  - View de dashboard
  - Gráficos (total por tipo, por dificuldade, por ano)
  - Cards com números principais
  - Taxa de crescimento
  - Top fontes
  - Últimas questões criadas

  ---
  🟢 PRIORIDADE BAIXA (Nice to have)

  8. Versões de Questões

  Status: Tabela existe, funcionalidade não implementada
  - Model para questao_versao
  - Controller para gerenciar versões
  - View para vincular versões alternativas
  - Visualizar histórico de versões

  ---
  9. Configurações do Sistema

  Status: Tabela existe, funcionalidade não implementada
  - Model para configuracao
  - Controller para gerenciar configs
  - View de configurações
  - Configurações por categoria (LaTeX, UI, Exportação)

  Configurações sugeridas:
  - Diretório padrão de imagens
  - Templates LaTeX customizados
  - Tema da interface
  - Formato de data preferido
  - Auto-backup

  ---
  10. Busca Avançada

  Status: Busca básica implementada
  - Busca por título, tipo, ano, fonte, dificuldade
  - Busca por tags (árvore hierárquica no SearchPanel)
  - Busca por texto no enunciado (full-text)
  - Busca por data de criação/modificação
  - Salvar filtros favoritos
  - Histórico de buscas

  ---
  11. Importação de Questões

  Status: Não implementado
  - Importar de arquivo LaTeX
  - Importar de arquivo JSON/CSV
  - Parser de questões de PDFs
  - Mapeamento automático de campos

  ---
  12. Backup e Restore

  Status: Database tem método, UI não implementada
  - database.py tem backup_database()
  - UI para criar backup manual
  - Agendamento de backups automáticos
  - Restore de backup
  - Listagem de backups disponíveis

  ---
  13. Relatórios

  Status: Não implementado
  - Relatório de questões por tag
  - Relatório de questões por fonte/ano
  - Relatório de uso de listas
  - Exportar relatórios (PDF, Excel)

  ---
  📊 RESUMO POR STATUS
  ┌──────────────────────┬───────┬─────────────┬──────────────┬────────────────────────┐
  │      Categoria       │ Total │  Completo   │ Em andamento │      Não iniciado      │
  ├──────────────────────┼───────┼─────────────┼──────────────┼────────────────────────┤
  │ CRUDs                │ 4     │ 1 (Questão) │ 0            │ 3 (Lista, Tag, Config) │
  ├──────────────────────┼───────┼─────────────┼──────────────┼────────────────────────┤
  │ Funcionalidades Core │ 13    │ 2           │ 3            │ 8                      │
  ├──────────────────────┼───────┼─────────────┼──────────────┼────────────────────────┤
  │ Total                │ 17    │ 3 (18%)     │ 3 (18%)      │ 11 (64%)               │
  └──────────────────────┴───────┴─────────────┴──────────────┴────────────────────────┘
  ---
  🎯 RECOMENDAÇÃO DE ORDEM DE IMPLEMENTAÇÃO

  1. CRUD de Tags (necessário para o QuestaoForm funcionar 100%)
  2. Load de Questão (completar edição)
  3. CRUD de Listas (funcionalidade core)
  4. Exportação LaTeX (funcionalidade principal do sistema)
  5. Preview de Questões (melhora UX)
  6. Dashboard (visibilidade do sistema)
  7. Inativação via UI (gerenciamento)
  8. Demais funcionalidades conforme prioridade