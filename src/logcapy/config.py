from typing import Optional, Literal
from .backends.base import LoggerBackend
from .backends.stdlib import StandardLogger

class Config:
    _instance: Optional["Config"] = None
    _logger: Optional[LoggerBackend] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def configure(self, backend: Literal["stdlib", "loguru"] = "stdlib", json_output: bool = True) -> None:
        if backend == "stdlib":
            self._logger = StandardLogger(json_output=json_output)
        elif backend == "loguru":
            # Lazy import to avoid hard dependency
            try:
                from .backends.loguru_impl import LoguruLogger
                self._logger = LoguruLogger(json_output=json_output)
            except ImportError:
                raise ImportError("Loguru is not installed. Run `pip install logcapy[loguru]`")
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def get_logger(self) -> LoggerBackend:
        if self._logger is None:
            # Default configuration
            self._logger = StandardLogger()
        return self._logger

global_config = Config()

def configure(backend: Literal["stdlib", "loguru"] = "stdlib", json_output: bool = True) -> None:
    """Global configuration entry point."""
    global_config.configure(backend=backend, json_output=json_output)

def get_logger() -> LoggerBackend:
    return global_config.get_logger()
