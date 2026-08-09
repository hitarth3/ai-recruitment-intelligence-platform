"""
Simple Logging Utility.
Provides a unified logger instance for tracking application events, database connections, and errors.
"""

import logging
import sys

# Ensure UTF-8 output stream handler for Windows console compatibility
stream_handler = logging.StreamHandler(sys.stdout)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[stream_handler]
)

# Shared logger instance
logger = logging.getLogger("ai_recruitment")
