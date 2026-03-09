"""Piirakka application entry point."""

import logging

import uvicorn
from setproctitle import setproctitle

import piirakka.core.preflight as preflight
from piirakka.__version__ import __version__
from piirakka.core.app_factory import create_app

setproctitle("piirakka")
logger = logging.getLogger(__name__)


def main():
    """Create and run the application."""
    app, _, _, _ = create_app()
    uvicorn.run(
        app, host="0.0.0.0", port=8000, workers=1, timeout_graceful_shutdown=5, log_config=preflight.LOGGING_CONFIG
    )


if __name__ == "__main__":
    logger.info(f"Starting piirakka v{__version__}")
    main()
