"""Sistema de logging para debugging."""

import logging
import os
from datetime import datetime
from typing import Optional


class DebugLogger:
    """Logger personalizado para debugging de la aplicación."""

    _instance: Optional["DebugLogger"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not DebugLogger._initialized:
            self.logger = logging.getLogger("interactive_git_versioneer")
            self.logger.setLevel(logging.DEBUG)

            # Obtener el directorio home del usuario
            home_dir = os.path.expanduser("~")
            log_dir = os.path.join(home_dir, ".igv_logs")

            # Crear directorio de logs si no existe
            os.makedirs(log_dir, exist_ok=True)

            # Crear nombre de archivo con timestamp
            log_filename = f"igv_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            log_path = os.path.join(log_dir, log_filename)

            # Configurar handler para archivo
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)

            # Formato detallado
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(funcName)-30s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

            # Log inicial
            self.logger.info("=" * 80)
            self.logger.info("NUEVA SESIÓN DE DEBUG INICIADA")
            self.logger.info(f"Archivo de log: {log_path}")
            self.logger.info("=" * 80)

            print(f"\n📝 Logging habilitado: {log_path}\n")

            DebugLogger._initialized = True
            self.log_path = log_path

    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)

    def function_enter(self, func_name: str, **kwargs):
        """Log function entry with parameters."""
        params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f">>> ENTRANDO a {func_name}({params_str})")

    def function_exit(self, func_name: str, return_value=None):
        """Log function exit with return value."""
        if return_value is not None:
            self.logger.info(f"<<< SALIENDO de {func_name} -> {return_value}")
        else:
            self.logger.info(f"<<< SALIENDO de {func_name}")

    def dialog_shown(self, dialog_type: str, message: str):
        """Log when a dialog is shown to the user."""
        self.logger.warning(f"🔔 DIÁLOGO MOSTRADO [{dialog_type}]: {message[:100]}")

    def user_input(self, prompt: str, response: str):
        """Log user input."""
        self.logger.info(f"👤 INPUT: '{prompt[:50]}...' -> Respuesta: '{response}'")

    def get_log_path(self) -> str:
        """Retorna la ruta del archivo de log actual."""
        return self.log_path


# Instancia global del logger
_debug_logger: Optional[DebugLogger] = None


def get_logger() -> DebugLogger:
    """Obtiene la instancia global del logger."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger


def is_logging_enabled() -> bool:
    """Verifica si el logging está habilitado."""
    return _debug_logger is not None
