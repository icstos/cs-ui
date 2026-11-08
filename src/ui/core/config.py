from pathlib import Path

from ui.core.constants import RUN_MODE
from ui.core.paths import log_dir as _user_log_dir

from .logger import Logger


class Config:
    def __init__(self) -> None:
        self.root_dir = Path(__file__).parents[2]
        self.run_mode = RUN_MODE.DEV

        self.output_dir = Path(self.root_dir, "output")
        # 日志落到**用户可写目录**（``%LOCALAPPDATA%\\cs-ui\\log`` 等），不是包目录：
        # ``Path(__file__)`` 装成 wheel 之后指向 site-packages，往那儿写日志轻则
        # 散落、重则只读盘报错。目录也不在导入期创建 —— 真正的 mkdir 推迟到
        # 第一条日志（见 :class:`ui.core.logger.Logger`）。
        self.log_dir = _user_log_dir()

        self.logger = Logger(file=Path(self.log_dir, "ui.log"))

        self.language = "zh_CN"
        self.title = "cs-ui"
        self.theme_mode = "dark"

    class App:
        name: str = "UI"

    def __repr__(self):
        return f"""
- {self.output_dir=}
- {self.log_dir=}
"""

    def get(self, key_name):
        pass

    def set(self, key_name, value):
        pass


config = Config()
logger = config.logger


if __name__ == "__main__":
    print(config)
