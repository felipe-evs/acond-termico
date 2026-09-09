import logging

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level, format=LOG_FORMAT)
    return logging.getLogger(__name__)
