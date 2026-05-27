from pathlib import Path
from ui.core.constants import RUN_MODE


class Config:
    def __init__(self) -> None:
        self.root_dir = Path(__file__).parents[2]
        self.run_mode = RUN_MODE.DEV

        self.output_dir = Path(self.root_dir, "output")
        self.log_dir = Path(self.root_dir, "output", "log")
        self.log_dir.mkdir(exist_ok=True, parents=True)

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
if __name__ == "__main__":
    print(config)
