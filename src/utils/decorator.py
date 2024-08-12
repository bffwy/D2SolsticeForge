from functools import wraps
from loguru import logger


def timer_log(func: callable):
    @wraps(func)
    def inner(*args, **kwargs):
        import time

        start_time = time.monotonic()
        result = func(*args, **kwargs)
        if args:
            logger.debug(f"[{func.__name__}]:{args[0]} 耗时: {time.monotonic() - start_time:.3f}s")
        else:
            logger.debug(f"[{func.__name__}]: 耗时: {time.monotonic() - start_time:.3f}s")
        return result

    return inner


def result_log(func: callable):
    from loguru import logger
    from functools import wraps

    @wraps(func)
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.debug(f"[{func.__name__}] 结果: {result:.3f}")
        return result

    return inner
