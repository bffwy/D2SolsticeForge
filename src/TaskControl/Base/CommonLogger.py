from loguru import logger

logger.add("./logs/running.log", level="INFO")

my_logger = logger
