import asyncio
import re
from dataclasses import field

import flet as ft


@ft.control
class LogContainer(ft.Container):
    height: int = 200
    border: ft.Border = field(
        default_factory=lambda: ft.Border.all(1, ft.Colors.GREY_300)
    )
    margin: ft.Margin = field(default_factory=lambda: ft.Margin.all(4))
    border_radius: ft.BorderRadius = field(
        default_factory=lambda: ft.BorderRadius.all(4)
    )

    def init(self):
        self.logs = ft.ListView(
            expand=1, spacing=2, padding=4, auto_scroll=True, height=self.height
        )
        self.content = ft.SelectionArea(content=self.logs)

    async def add(self, log: str):
        log_color = ft.Colors.BLACK
        if re.search(r"error|fail|exception", log, re.IGNORECASE):
            log_color = ft.Colors.RED
        elif re.search(r"warning|warn", log, re.IGNORECASE):
            log_color = ft.Colors.ORANGE
        elif re.search(r"success|pass|ok", log, re.IGNORECASE):
            log_color = ft.Colors.GREEN
        elif re.search(r"info|debug", log, re.IGNORECASE):
            log_color = ft.Colors.BLUE
        else:
            log_color = ft.Colors.BLACK
        self.logs.controls.append(ft.Text(log, color=log_color))
        self.update()
        await asyncio.sleep(0)

    def clear_logs(self):
        self.logs.controls.clear()
        self.update()


def main(page: ft.Page):
    log_container = LogContainer()
    page.add(log_container)

    async def add_log(e):
        await log_container.add("New log message after clearing.")
        await asyncio.sleep(1)
        await log_container.add("error: error log message after clearing.")
        await asyncio.sleep(1)
        await log_container.add("warning: warning log message after clearing.")
        await asyncio.sleep(1)
        await log_container.add("pass: pass log message after clearing.")
        await asyncio.sleep(1)
        await log_container.add("info: info log message after clearing.")

    def clear_logs(e):
        log_container.clear_logs()

    page.add(ft.Button("Add Log", on_click=add_log))
    page.add(ft.Button("Clear Logs", on_click=clear_logs))


if __name__ == "__main__":
    ft.run(main)
