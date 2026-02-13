# src/views/design/constants.py

# Cores
class Color:
    PRIMARY_BLUE = "#1258e2"
    HOVER_BLUE = "#0d47b8"
    LIGHT_BLUE_BG_1 = "rgba(18, 88, 226, 0.1)"
    LIGHT_BLUE_BG_2 = "rgba(18, 88, 226, 0.05)"
    LIGHT_BLUE_BORDER = "rgba(18, 88, 226, 0.2)"

    WHITE = "#ffffff"
    BLACK = "#000000"
    DARK_TEXT = "#111318"
    GRAY_TEXT = "#616f89"
    LIGHT_BACKGROUND = "#f6f6f8"
    BORDER_LIGHT = "#f0f2f4"
    BORDER_MEDIUM = "#e0e0e0"
    LIGHT_GRAY_BACKGROUND = "#f8f9fa"

    # Tag/Badge Colors
    TAG_BLUE = "#2563eb"
    TAG_GREEN = "#16a34a"
    TAG_RED = "#dc2626"
    TAG_YELLOW = "#ca8a04"
    TAG_PURPLE = "#9333ea"
    TAG_ORANGE = "#ea580c"
    TAG_GRAY = "#616f89"

    # Difficulty Colors
    DIFFICULTY_EASY = "#16a34a"
    DIFFICULTY_MEDIUM = "#ca8a04"
    DIFFICULTY_HARD = "#ea580c"
    DIFFICULTY_VERY_HARD = "#dc2626"

    # Chart Colors
    CHART_LINE = "#2563eb"
    CHART_AREA = "rgba(37, 99, 235, 0.1)"


# Espaçamentos (Padding, Margin, Gap)
class Spacing:
    NONE = 0
    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# Tipografia
class Typography:
    FONT_FAMILY = "Segoe UI, Arial, sans-serif"
    FONT_SIZE_XS = "10px"
    FONT_SIZE_SM = "12px"
    FONT_SIZE_MD = "14px"
    FONT_SIZE_LG = "16px"
    FONT_SIZE_XL = "18px"
    FONT_SIZE_XXL = "20px"
    FONT_SIZE_PAGE_TITLE = "24px"

    FONT_WEIGHT_LIGHT = 300
    FONT_WEIGHT_REGULAR = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700


# Dimensões
class Dimensions:
    NAVBAR_HEIGHT = 60
    SIDEBAR_WIDTH = 280
    SIDEBAR_COLLAPSED_WIDTH = 60
    CARD_MIN_WIDTH = 280
    CARD_MAX_WIDTH = 350
    BUTTON_HEIGHT = 40
    INPUT_HEIGHT = 40
    BORDER_RADIUS_SM = "4px"
    BORDER_RADIUS_MD = "8px"
    BORDER_RADIUS_LG = "12px"
    BORDER_RADIUS_CIRCLE = "50%"
    TAXONOMY_TREE_WIDTH = 300
    EXAM_LIST_WIDTH = 250
    EXPORT_CONFIG_WIDTH = 320


# Caminhos de ícones centralizados
class IconPath:
    # Layout icons
    COLLAPSE = "resources/icons/collapse.png"
    EXPAND = "resources/icons/expand.png"
    ARROW_DOWN = "resources/icons/arrow_down.png"
    ARROW_RIGHT = "resources/icons/arrow_right.png"
    ARROW_LEFT = "resources/icons/arrow_left.png"

    # Action icons
    SEARCH = "resources/icons/search.png"
    SETTINGS = "resources/icons/settings.png"
    BELL = "resources/icons/bell.png"
    USER = "resources/icons/user.png"
    HELP = "resources/icons/help.png"
    PDF = "resources/icons/pdf.png"
    EXPORT = "resources/icons/export.png"
    ADD_IMAGE = "resources/icons/add_image.png"
    EDIT = "resources/icons/edit.png"
    DELETE = "resources/icons/delete.png"
    VIEW = "resources/icons/view.png"

    # Preview icons
    ZOOM_IN = "resources/icons/zoom_in.png"
    ZOOM_OUT = "resources/icons/zoom_out.png"
    PRINT = "resources/icons/print.png"
    DOWNLOAD = "resources/icons/download.png"

    # Tab icons
    EDITOR = "resources/icons/editor.png"
    PREVIEW = "resources/icons/preview.png"
    TAGS = "resources/icons/tags.png"

    # Calendar
    CALENDAR = "resources/icons/calendar.png"

    # Loading
    LOADING = "resources/loaders/loading.gif"


# Textos/Labels da interface (i18n-ready)
# Textos/Labels da interface (pt-BR)
class Text:
    # App
    APP_TITLE = "OharaBank"
    APP_TITLE_ANALYTICS = "OharaBank Analytics"

    # Navigation
    NAV_DASHBOARD = "Painel"
    NAV_QUESTION_BANK = "Banco de Questões"
    NAV_EXAMS = "Listas"
    NAV_REPORTS = "Relatórios"
    NAV_SETTINGS = "Configurações"
    NAV_COMMUNITY = "Comunidade"
    NAV_TAXONOMY = "Tags"

    # Buttons
    BUTTON_CREATE = "Criar Nova"
    BUTTON_CREATE_QUESTION = "Criar Questão"
    BUTTON_SAVE = "Salvar"
    BUTTON_SAVE_QUESTION = "Salvar Questão"
    BUTTON_CANCEL = "Cancelar"
    BUTTON_DELETE = "Excluir"
    BUTTON_EDIT = "Editar"
    BUTTON_EXPORT_PDF = "Exportar PDF"
    BUTTON_EXPORT_LATEX = "Exportar LaTeX"
    BUTTON_GENERATE_PDF = "Gerar PDF"
    BUTTON_ADD_TO_LIST = "Adicionar à Lista"
    BUTTON_VIEW_PREVIEW = "Pré-visualização"
    BUTTON_COLLAPSE_ALL = "Recolher Tudo"
    BUTTON_EXPAND_ALL = "Expandir Tudo"
    BUTTON_FILTER = "Filtrar"
    BUTTON_ADD_FROM_BANK = "+ Adicionar do Banco de Questões"

    # Search
    SEARCH_PLACEHOLDER = "Buscar por ID, trecho do enunciado ou tags..."
    SEARCH_TAGS_PLACEHOLDER = "Buscar áreas de conhecimento..."

    # Dashboard
    DASHBOARD_TITLE = "Painel"
    DASHBOARD_TOTAL_QUESTIONS = "Total de Questões"
    DASHBOARD_NEW_THIS_MONTH = "Novas Neste Mês"
    DASHBOARD_SUCCESS_RATE = "Taxa de Acerto"
    DASHBOARD_AVG_RESOLUTION = "Tempo Médio de Resolução"
    DASHBOARD_QUESTIONS_OVER_TIME = "Questões Adicionadas ao Longo do Tempo"
    DASHBOARD_DIFFICULTY_DISTRIBUTION = "Distribuição de Dificuldade"
    DASHBOARD_ACCURACY_BY_TOPIC = "Taxa de Acerto por Tópico"
    DASHBOARD_TOP_HARDEST = "Top 10 Questões Mais Difíceis"
    DASHBOARD_VIEW_ALL_DIFFICULT = "VER TODAS AS QUESTÕES DIFÍCEIS"
    DASHBOARD_EXPORT_CSV = "Exportar CSV"

    # Filters
    FILTER_PERIOD = "Período"
    FILTER_LAST_30_DAYS = "Últimos 30 Dias"
    FILTER_TAGS = "Tags"
    FILTER_DIFFICULTY = "Dificuldade"
    FILTER_TYPE = "Tipo"
    FILTER_ALL = "Todos"

    # Question Bank
    QUESTION_BANK_TITLE = "Explorador de Questões"
    QUESTION_BANK_SHOWING = "Exibindo {current} de {total} resultados"
    QUESTION_BANK_FILTERS = "Filtros"

    # Question Editor
    EDITOR_TAB = "Editor"
    PREVIEW_TAB = "Pré-visualização"
    TAGS_TAB = "Tags"
    METADATA_MODE = "METADADOS & MODO"
    ACADEMIC_YEAR = "ANO LETIVO"
    ORIGIN_SOURCE = "ORIGEM / FONTE"
    QUESTION_STATEMENT = "ENUNCIADO DA QUESTÃO"
    MULTIPLE_CHOICE_ALTERNATIVES = "ALTERNATIVAS DE MÚLTIPLA ESCOLHA"
    ANSWER_KEY = "GABARITO / SOLUÇÃO ESPERADA"
    AUTO_SAVED = "Salvo automaticamente há {time}"
    QUESTION_LANGUAGE = "IDIOMA DA QUESTÃO"

    # Question Types
    TYPE_OBJECTIVE = "Objetiva"
    TYPE_DISCURSIVE = "Discursiva"

    # Difficulty Levels
    DIFFICULTY_EASY = "Fácil"
    DIFFICULTY_MEDIUM = "Média"
    DIFFICULTY_HARD = "Difícil"
    DIFFICULTY_VERY_HARD = "Muito Difícil"

    # Taxonomy
    TAXONOMY_TITLE = "Gerenciador de TAGS"
    TAXONOMY_MATH = "TAGS"
    TAXONOMY_TAGS_COUNT = "{count} tags ativas"
    TAXONOMY_EDIT_TAG = "Editar Tag: {name}"
    TAXONOMY_BASIC_INFO = "Informações Básicas"
    TAXONOMY_VISUAL_IDENTITY = "Identidade Visual"
    TAXONOMY_TAG_STATISTICS = "Estatísticas da Tag"
    TAXONOMY_QUICK_ACTIONS = "Ações Rápidas"
    TAXONOMY_ASSOCIATED_EXAMS = "Listas Associadas"
    TAXONOMY_MERGE_WITH = "Mesclar com outra..."
    TAXONOMY_DELETE_TAG = "Inativar Tag"
    TAXONOMY_SAVE_CHANGES = "Salvar Alterações"
    TAXONOMY_SELECT_DISCIPLINE = "Selecione a disciplina..."
    TAXONOMY_TAG_NAME = "Nome da Tag:"
    TAXONOMY_TAG_NUM = "Numeração:"
    TAXONOMY_CREATE_ROOT = "+ Tag Raiz"
    TAXONOMY_CREATE_SUB = "+ Sub-tag"
    TAXONOMY_TAB_DISCIPLINES = "Disciplinas"
    TAXONOMY_TAB_SOURCES = "Fontes"
    TAXONOMY_TAB_LEVELS = "Níveis Escolares"
    TAXONOMY_CODE = "Código:"
    TAXONOMY_NAME = "Nome:"
    TAXONOMY_DESCRIPTION = "Descrição:"
    TAXONOMY_COLOR = "Cor:"
    TAXONOMY_ORDER = "Ordem:"
    TAXONOMY_FULL_NAME = "Nome Completo:"
    TAXONOMY_TYPE = "Tipo:"
    TAXONOMY_BTN_NEW = "Novo"
    TAXONOMY_BTN_SAVE = "Salvar"
    TAXONOMY_BTN_DELETE = "Inativar"
    TAXONOMY_NO_DISCIPLINE = "Selecione uma disciplina para ver as tags."
    TAXONOMY_TAGS_OF = "Tags de {name}"

    # Exam Lists
    EXAM_MY_EXAMS = "MINHAS LISTAS"
    EXAM_CREATE_NEW = "+ Criar Nova Lista"
    EXAM_HEADER_INSTRUCTIONS = "CABEÇALHO & INSTRUÇÕES DA LISTA"
    EXAM_QUESTIONS_TOTAL = "Questões ({count} no Total)"
    EXAM_EXPORT_CONFIG = "Configuração de Exportação"
    EXAM_SINGLE_COLUMN = "Coluna Única"
    EXAM_TWO_COLUMNS = "Duas Colunas"
    EXAM_INCLUDE_ANSWER_KEY = "Incluir Gabarito"
    EXAM_INCLUDE_POINTS = "Incluir Pontuação"
    EXAM_INCLUDE_WORKSPACE = "Incluir Espaço de Resolução"

    # Sidebar
    SIDEBAR_MATH_CONTENT = "CONTEÚDO DE MATEMÁTICA"
    SIDEBAR_HIERARCHICAL_TAGS = "Tags Hierárquicas"
    SIDEBAR_HELP_CENTER = "Central de Ajuda"

    # Table Headers
    TABLE_ID = "ID"
    TABLE_TOPIC = "TÓPICO"
    TABLE_TAG = "TAG"
    TABLE_SUCCESS_RATE = "TAXA DE ACERTO"
    TABLE_ACTIONS = "AÇÕES"
    TABLE_EXAM_NAME = "NOME DA LISTA"
    TABLE_WEIGHT = "PESO"
    TABLE_DATE_ADDED = "DATA DE CRIAÇÃO"

    # Form Labels
    LABEL_NAME = "Nome da Tag"
    LABEL_SLUG = "Slug"
    LABEL_DESCRIPTION = "Descrição"
    LABEL_COLOR = "Cor da Tag"
    LABEL_ICON = "Seleção de Ícone"
    LABEL_SCHOOL_NAME = "Nome da Escola"
    LABEL_PROFESSOR = "Nome do Professor"
    LABEL_EXAM_DATE = "Data da Prova"
    LABEL_DEPARTMENT = "Departamento"
    LABEL_INSTRUCTIONS = "Instruções (Suporte a LaTeX Ativado)"

    # Stats
    STAT_QUESTIONS = "Questões"
    STAT_AVG_SUCCESS = "Média de Acerto"
    STAT_DIFFICULTY = "Dificuldade"

    # Empty states
    EMPTY_NO_QUESTIONS = "Nenhuma questão encontrada"
    EMPTY_NO_TAGS = "Nenhuma tag disponível"
    EMPTY_NO_EXAMS = "Nenhuma lista criada ainda"

    # Pagination
    PAGINATION_CONTROLS = "Controles de paginação"

# Rotas/Páginas disponíveis
class Page:
    DASHBOARD = "dashboard"
    QUESTION_BANK = "question_bank"
    LISTS = "lists"
    TAXONOMY = "taxonomy"
    QUESTION_EDITOR = "question_editor"


# Tamanhos de ícone
class IconSize:
    SM = 16
    MD = 18
    LG = 24
    XL = 32
