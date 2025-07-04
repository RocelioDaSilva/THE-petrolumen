import logging
import sys
from backend.gaia_genesis_new.config import settings # To use settings.DEBUG_MODE

# Determine log level based on settings
log_level = logging.DEBUG if settings.DEBUG_MODE else logging.INFO

# Create a logger
logger = logging.getLogger("petrolumen_backend")
logger.setLevel(log_level)

# Create a handler (console handler for now)
# You could add FileHandlers or other handlers here as needed
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)

# Create a formatter and set it for the handler
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
)
console_handler.setFormatter(formatter)

# Add the handler to the logger
# Check if handlers are already added to prevent duplication if this module is reloaded
if not logger.handlers:
    logger.addHandler(console_handler)

# Example usage:
# from backend.gaia_genesis_new.logger import logger
# logger.debug("This is a debug message.")
# logger.info("This is an info message.")
# logger.warning("This is a warning message.")
# logger.error("This is an error message.")
# logger.critical("This is a critical message.")
