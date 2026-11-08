"""
日志器组件: copyed from cs-utils

**惰性初始化**：``Logger`` 对象本身在导入时只记下参数，真正的 handler（以及
"创建日志目录 / 打开文件"这两步 I/O）推迟到**第一条日志**才发生。

这不只是省几毫秒。``import ui`` 会顺着组件模块走到这里 —— 如果构造即建目录，
那么「装到只读的 site-packages 里」或「冻结成单文件 exe」时，任何一次 import
都会因为 ``mkdir`` 失败而炸掉，而调用方根本没打算写日志。日志是**旁路能力**，
它坏了不该拖垮主流程：文件 sink 失败时降级成控制台并警告一次，不留异常。
"""

import logging
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pathlib import Path


class LogType(Enum):
    FILE_SIZE = "filesize"
    TIMED = "timed"


class RunMode(Enum):
    DEV = "dev"
    TEST = "test"
    RELEASE = "release"


_LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class Logger:
    """统一的日志器封装，支持按大小/按时间轮转，以及开发/测试/发布三种运行模式。

    第一次调用 :meth:`debug` / :meth:`info` 等方法时才真正建立 handler；
    在此之前只有几个字段，构造是常数时间、且不碰磁盘。
    """

    def __init__(
        self,
        file: str | Path,
        name: str = "logger",
        log_type: LogType = LogType.FILE_SIZE,
        run_mode: RunMode = RunMode.TEST,
    ) -> None:
        self.file = Path(file)
        self.name = name
        self.log_type = log_type
        self.run_mode = run_mode
        self._logger: logging.Logger | None = None  # 首次写日志时才建

    # ---- 惰性建链 ----
    @property
    def logger(self) -> logging.Logger:
        """底层 :class:`logging.Logger`（首次访问时完成配置）。"""
        if self._logger is None:
            self._logger = self._build_logger()
        return self._logger

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        # 防止重复添加 handler
        if logger.handlers:
            return logger

        logger.setLevel(self._get_log_level())
        formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

        # 控制台输出（仅在 DEV / TEST 模式）
        if self.run_mode in (RunMode.DEV, RunMode.TEST):
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        # 文件 handler：建目录 / 开文件都在这一步，失败就降级为「只走控制台」
        try:
            self.file.parent.mkdir(exist_ok=True, parents=True)
            if self.log_type == LogType.FILE_SIZE:
                file_handler = self._build_filesize_handler(formatter)
            else:
                file_handler = self._build_timed_handler(formatter)
            logger.addHandler(file_handler)
        except OSError as exc:  # 只读安装、权限不足、磁盘满……
            logger.warning("日志文件不可写（%s），本次仅输出到控制台", exc)

        return logger

    def _get_log_level(self) -> int:
        if self.run_mode == RunMode.DEV:
            return logging.DEBUG
        return logging.INFO

    def _build_filesize_handler(
        self,
        formatter: logging.Formatter,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 10,
    ) -> logging.Handler:
        from logging.handlers import RotatingFileHandler  # 6ms，只有真写文件才需要

        handler = RotatingFileHandler(
            filename=self.file,
            mode="a",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        return handler

    def _build_timed_handler(
        self,
        formatter: logging.Formatter,
        when: str = "midnight",
        interval: int = 4,
        backup_count: int = 10,
    ) -> logging.Handler:
        from logging.handlers import TimedRotatingFileHandler

        # 微秒级时间戳后缀，避免多进程写同一文件冲突，年份取后两位
        timestamp = time.strftime("%y%m%d%H%M%S", time.localtime())
        microsecond = f"{time.time() % 1:.6f}"[2:]
        log_file = f"{self.file}_{timestamp}{microsecond}"

        handler = TimedRotatingFileHandler(
            filename=log_file,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.suffix = "%Y-%m-%d.log"
        handler.setFormatter(formatter)
        return handler

    # ---- 代理方法 ----
    # 签名故意与 ``logging.Logger`` 一致（``msg, *args, **kwargs``）。收窄成
    # ``debug(self, msg)`` 会让 ``logger.debug("...", exc_info=True)`` 抛 TypeError
    # —— 而那正是"已经在处理异常"的分支，报错会顶掉原始异常，现场全丢。
    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: object, **kwargs: object) -> None:
        self.logger.critical(msg, *args, **kwargs)


def timed_log(show_time: bool = False) -> Callable:
    """装饰器：记录被调用方法的类名.方法名，可选展示耗时。"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            cls_name = args[0].__class__.__name__ if args else ""
            log_msg = f"{cls_name}.{func.__name__}" if cls_name else func.__name__

            if show_time:
                start = time.perf_counter()
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                logger.info("%s (%.4fs)", log_msg, elapsed)
            else:
                result = func(*args, **kwargs)
                logger.info(log_msg)
            return result

        return wrapper

    return decorator


if __name__ == "__main__":
    logger = Logger(file="test.log", run_mode=RunMode.DEV)
    logger.debug("这是一条 debug 日志")
    logger.info("这是一条 info 日志")
    logger.warning("这是一条 warning 日志")
    logger.error("这是一条 error 日志")
