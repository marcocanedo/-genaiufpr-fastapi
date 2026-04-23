from __future__ import annotations


class DomainError(Exception):
    """Erro base do domínio da aplicação.

    Ter uma classe base facilita tratar erros de forma centralizada na CLI.
    """


class InvalidInputError(DomainError):
    """Erro para entradas inválidas do usuário (URL, timeout, etc.)."""


class DownloadError(DomainError):
    """Erro durante o download de conteúdo da internet."""


class ProfileLoadError(DomainError):
    """Erro ao carregar/percorrer o CSV de perfis de idioma."""


class EmptyTextError(DomainError):
    """Erro quando o texto limpo fica vazio e não pode ser classificado."""
