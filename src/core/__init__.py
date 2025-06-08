"""
Módulo core - Componentes principais de processamento de documentos

Este módulo contém as classes e funções fundamentais para processamento
de documentos, incluindo extração de texto, análise de conteúdo e
manipulação de arquivos.
"""

from .document_processor import DocumentProcessor
from .cloud_document_processor import CloudDocumentProcessor

__all__ = ['DocumentProcessor', 'CloudDocumentProcessor'] 