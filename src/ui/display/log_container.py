import asyncio
import re
from dataclasses import field, dataclass

import flet as ft


@ft.observable
@dataclass
class LogContainer:
    logs: list[str] = field(default_factory=list)
    height: int = 200

    async def add(self, log: str):
        self.logs.append(log)
        await asyncio.sleep(0)

    def clear(self):
        self.logs = []

    @ft.component
    def ui(self):
        v_vlogs = []
        for log in self.logs:
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
            v_vlogs.append(ft.Text(log, color=log_color))
        return ft.Container(
            content=ft.SelectionArea(
                content=ft.ListView(
                    controls=v_vlogs, expand=1, spacing=2, padding=4, auto_scroll=True
                )
            ),
            border=ft.Border.all(1, ft.Colors.GREY_300),
            margin=ft.Margin.all(4),
            border_radius=ft.BorderRadius.all(4),
            height=self.height,
        )


@ft.component
def App():
    log_container = LogContainer()

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
        log_container.clear()

    return ft.Column(
        [
            log_container.ui(),
            ft.Button("Add Log", on_click=add_log),
            ft.Button("Clear Logs", on_click=clear_logs),
            ft.Button('show now logs', on_click=lambda e: print(log_container.logs)),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
