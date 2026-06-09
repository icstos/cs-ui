import flet as ft
from dataclasses import dataclass
from ui.input.input import Label


@ft.observable
@dataclass
class Switch(Label):
    """开关组件，继承自 Label，支持标签显示和垂直/水平布局。"""

    value: bool = False
    """开关的当前状态（True 为开启，False 为关闭）。"""

    def on_change(self, e):
        """开关状态变更回调，同步更新 value 属性。"""
        self.value = e.control.value

    @ft.component
    def ui(self) -> ft.Control:
        """渲染开关 UI。

        Returns:
            包含 ft.Switch 及可选标签的控件。
        """

        def _on_change(e):
            self.on_change(e)
            self.notify()

        v_ui = ft.Switch(
            value=self.value,
            on_change=_on_change,
            active_color=ft.Colors.WHITE,
            active_track_color=ft.Colors.BLUE,
            # label_position=ft.LabelPosition.RIGHT,
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=[self.v_label, v_ui])
        else:
            return v_ui


@ft.component
def App() -> ft.Control:
    switch = Switch(
        label="启用通知",
        value=True,
        is_required=True,
    )

    return ft.Column(
        controls=[
            switch.ui(),
            Switch(
                label="暗黑模式",
                value=False,
                is_vertical=True,
            ).ui(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(f"启用通知: {switch.value}"),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
