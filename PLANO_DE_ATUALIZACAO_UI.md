### **Plano de Ação: Atualização da Interface Gráfica (UI)**

O objetivo é substituir a interface gráfica atual, implementada em `src/views/`, pela nova interface de `src/views/novas-views/`, garantindo que toda a lógica de controllers e serviços seja mantida e reaproveitada.

#### **Fase 1: Preparação e Configuração do Ambiente**

1.  **Mover Novos Arquivos:**
    *   Copiar todos os arquivos de `src/views/novas-views/` diretamente para `src/views/`.
    *   Renomear `mathbank_styles.css` para `styles.qss` para corresponder ao que o `mathbank_main.py` espera carregar.

2.  **Atualizar o Ponto de Entrada Principal:**
    *   Analisar o arquivo `src/main.py`. Atualmente, ele deve instanciar e exibir a `MainWindow` (de `main_window.py`).
    *   **Ação:** Modificar `src/main.py` para importar e instanciar a `DashboardWindow` de `mathbank_dashboard.py` como a janela principal da aplicação. Isso ativará a nova interface, ainda com dados estáticos (mock).

#### **Fase 2: Integração do Dashboard Principal (Leitura e Visualização de Dados)**

1.  **Carregamento Dinâmico de Questões:**
    *   **Análise:** O arquivo `src/views/mathbank_dashboard.py` atualmente usa uma lista de "mock questions" para popular a grade de cartões. A lógica real de busca de questões deve estar no `SearchPanel` ou `MainWindow` antigos, que se comunicam com `questao_controller_orm.py`.
    *   **Ação:**
        *   Na classe `DashboardWindow`, conectar-se aos controllers necessários (ex: `QuestaoController`, `TagController`).
        *   Modificar o método `create_main_content` para, em vez de usar os dados mockados, chamar a função do controller que busca as questões no banco de dados (ex: `self.questao_controller.listar_todas_as_questoes()`).
        *   Iterar sobre os resultados reais e criar um `QuestionCard` para cada questão, passando os dados dinâmicos (ID, título, tags, etc.).

2.  **Implementação da Lógica de Filtro e Busca:**
    *   **Análise:** A nova UI (`mathbank_dashboard.py`) possui uma barra de busca e botões de filtro (`create_filters`). A lógica de busca atual reside no `SearchPanel`.
    *   **Ação:**
        *   Conectar os sinais da nova UI (ex: `search.textChanged` e `filter_button.clicked`) a novos métodos na `DashboardWindow`.
        *   Esses métodos devem chamar as funções apropriadas do `QuestaoController` (ex: `buscar_questoes_por_texto_e_tags(...)`), que já contêm a lógica de negócio.
        *   Após receber os resultados da busca, a grade de `QuestionCard`s deve ser limpa e recriada com os novos dados.

3.  **Carregamento Dinâmico da Sidebar (Tags e Tópicos):**
    *   **Análise:** A `src/views/mathbank_sidebar.py` possui uma árvore de navegação estática. A lógica para carregar tags e listas está provavelmente no `lista_controller_orm.py` ou `tag_controller_orm.py`.
    *   **Ação:**
        *   Modificar o método `create_tree` na `SidebarWidget`.
        *   Chamar os métodos do controller para obter a estrutura de tags/listas hierárquicas (ex: `self.tag_controller.get_tag_tree()`).
        *   Construir a árvore de navegação dinamicamente com base nos dados recebidos.
        *   Conectar o sinal de clique de cada item da árvore para acionar a filtragem de questões no dashboard principal.

#### **Fase 3: Integração das Funcionalidades de Edição e Criação**

1.  **Reaproveitamento do Formulário de Questão:**
    *   **Análise:** O diretório `novas-views` não contém um novo formulário de criação/edição. O formulário existente é o `src/views/questao_form.py`, que já possui toda a lógica de validação e salvamento.
    *   **Ação:**
        *   Na `DashboardWindow`, conectar o sinal `clicked` do botão `"+ Create Question"` a uma função.
        *   Essa função irá instanciar e exibir a classe `QuestaoForm` *existente*. Não há necessidade de recriá-la, apenas de chamá-la a partir da nova interface.

2.  **Visualização e Edição de Questões:**
    *   **Análise:** Clicar em uma questão na lista deve abrir sua visualização ou formulário de edição.
    *   **Ação:**
        *   Tornar o `QuestionCard` um widget clicável (implementando `mousePressEvent`).
        *   Ao clicar em um card, obter o ID da questão associada.
        *   Chamar a função que abre o `QuestaoForm` ou o `QuestaoPreview` (o que for mais apropriado), passando o ID da questão para que ele carregue os dados corretos para edição ou visualização.

#### **Fase 4: Integração das Funcionalidades Auxiliares**

1.  **Funcionalidade de Exportação:**
    *   **Análise:** A nova sidebar possui um botão "Export to PDF". A lógica de exportação está encapsulada em `export_controller.py` e `export_dialog.py`.
    *   **Ação:**
        *   Conectar o sinal `clicked` do botão de exportação na `SidebarWidget`.
        *   Chamar a função do `ExportController` que inicia o processo de exportação, reutilizando a lógica existente para gerar o PDF.

2.  **Gerenciamento de Tags:**
    *   **Análise:** O `tag_manager.py` existente fornece uma UI para gerenciar tags. A nova UI não tem um ponto de entrada visível para isso.
    *   **Ação:**
        *   Adicionar um novo botão na interface (ex: no menu "⋮" da sidebar ou no header principal) com o texto "Gerenciar Tags".
        *   Conectar o clique deste botão para instanciar e exibir a janela `TagManager` existente.

#### **Fase 5: Limpeza e Finalização**

1.  **Verificação Completa:**
    *   Navegar por toda a aplicação, testando cada botão e funcionalidade: busca, filtro, criação, edição, exportação, etc., para garantir que a nova UI está corretamente conectada à lógica antiga.

2.  **Remoção de Arquivos Obsoletos:**
    *   Após a confirmação de que todas as funcionalidades foram migradas com sucesso, os seguintes arquivos de view antigos podem ser removidos com segurança:
        *   `main_window.py`
        *   `search_panel.py`
        *   `lista_panel.py`
        *   `questao_preview.py` (se a funcionalidade for totalmente absorvida pelo novo layout)
        *   Outros widgets que se tornaram redundantes.
    *   O diretório `src/views/novas-views/` pode ser removido, pois seu conteúdo já terá sido movido.
