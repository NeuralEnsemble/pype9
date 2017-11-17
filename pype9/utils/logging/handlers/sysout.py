import sys
import logging
from .. import loglevel, logger

logger.setLevel(loglevel)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
