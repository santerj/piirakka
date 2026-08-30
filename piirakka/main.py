"""Piirakka application entry point."""

import logging
from pprint import pformat

import uvicorn
from dataclasses import asdict
from setproctitle import setproctitle

from piirakka.core import preflight
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
    logger.info(f"Starting app with config \n {pformat(asdict(preflight.APP_CONFIG))}")
    main()
