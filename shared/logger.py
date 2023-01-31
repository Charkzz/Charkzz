import logging

logger = logging.getLogger("frontend")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

class Log:
    @staticmethod
    def error(msg: str):
        logger.error(msg, exc_info=True)

    @staticmethod
    def debug(msg: str):
        logger.debug(msg, exc_info=True)

    @staticmethod
    def info(msg: str):
        logger.info(msg, exc_info=True)

    log = logger.log


