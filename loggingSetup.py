import logging
import sys

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
ANSI_RESET = "\033[0m"
LEVEL_COLORS = {
    logging.DEBUG: "\033[90m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;41m",
}


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = LEVEL_COLORS.get(record.levelno)
        if not color:
            return message
        return f"{color}{message}{ANSI_RESET}"


class ExitOnErrorHandler(logging.Handler):
    """Stops the app on the first error so later steps never run on bad state."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        # Must be registered after the file/console handlers so they write first.
        sys.exit(1)


def setup_logging(log_filename: str) -> None:
    console_handler = logging.StreamHandler()
    if console_handler.stream.isatty():
        console_handler.setFormatter(ColoredFormatter(LOG_FORMAT))
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler, ExitOnErrorHandler()],
    )
