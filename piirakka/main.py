"""Piirakka application entry point."""

import logging

import uvicorn
from setproctitle import setproctitle

from piirakka.__version__ import __version__
from piirakka.core import preflight
from piirakka.core.app_factory import create_app
from piirakka.services.argparser import parser

setproctitle("piirakka")
logger = logging.getLogger(__name__)


def main():
    """Create and run the application."""
    args, _ = parser.parse_known_args()
    spawn_mpv = not args.no_mpv
    app, _, _, _ = create_app(spawn_mpv)
    uvicorn.run(
        app, host="0.0.0.0", port=8000, workers=1, timeout_graceful_shutdown=5, log_config=preflight.LOGGING_CONFIG
    )


if __name__ == "__main__":
    logger.info(f"Starting piirakka v{__version__}")
    main()
