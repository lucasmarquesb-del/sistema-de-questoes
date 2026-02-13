# src/views/design/enums.py
from enum import Enum

class PageEnum(Enum):
    DASHBOARD = "dashboard"
    QUESTION_BANK = "question_bank"
    LISTS = "lists"
    TAXONOMY = "taxonomy"
    QUESTION_EDITOR = "question_editor"
    USER_MANAGEMENT = "user_management"

class ActionEnum(Enum):
    CREATE_NEW = "create_new"
    EDIT = "edit"
    DELETE = "delete"
    EXPORT = "export"
    HELP = "help"
    SETTINGS = "settings"
    PROFILE = "profile"
    LOGOUT = "logout"

class ButtonTypeEnum(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    ICON = "icon"
    CONTEXTUAL = "contextual"

class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard" # Added based on common practice, can be adjusted
