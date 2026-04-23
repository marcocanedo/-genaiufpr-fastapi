"""Pacote didático de identificação de idioma com orientação a objetos."""

from .models import AppConfig, IdentificationResult, LanguageProfile
from .service import LanguageIdentifierService

__all__ = [
    "AppConfig",
    "IdentificationResult",
    "LanguageProfile",
    "LanguageIdentifierService",
]
