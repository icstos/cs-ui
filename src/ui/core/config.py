from pathlib import Path
from ui.core.constants import RUN_MODE
from .logger import Logger


class Config:
    def __init__(self) -> None:
        self.root_dir = Path(__file__).parents[2]
        self.run_mode = RUN_MODE.DEV

        self.output_dir = Path(self.root_dir, "output")
        self.log_dir = Path(self.root_dir, "output", "log")
        self.log_dir.mkdir(exist_ok=True, parents=True)

        self.logger = Logger(file=Path(self.log_dir, "ui.log"))

        self.language = "zh_CN"

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
