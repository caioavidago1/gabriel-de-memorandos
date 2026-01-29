"""
Sistema de logging centralizado para a aplicação de memorandos.

Substitui os prints por logging adequado para melhor debugging e monitoramento.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configura logger com formatação adequada.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evita duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Handler para console com cores e emojis
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formato: [TIMESTAMP] LEVEL - ModuleName - Message
    formatter = logging.Formatter(
        fmt='%(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Handler para arquivo (opcional - descomente se necessário)
    # log_dir = Path("logs")
    # log_dir.mkdir(exist_ok=True)
    # file_handler = logging.FileHandler(
    #     log_dir / f"memo_{datetime.now().strftime('%Y%m%d')}.log",
    #     encoding='utf-8'
    # )
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    
    return logger


# Pré-configurar loggers para módulos principais
def get_logger(module_name: str = __name__) -> logging.Logger:
    """Helper para obter logger configurado"""
    return setup_logger(module_name)
