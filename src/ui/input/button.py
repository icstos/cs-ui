from dataclasses import field

import flet as ft
from ui.core.constants import StyleType, FeedbackStyle, ButtonShape


BORDER_RADIUS = 6
BUTTON_HEIGHT = 36


@ft.control
class Button(ft.Button):
    # 注意（flet 1.0.0）：基类的 height 是 kw_only 字段；子类若用裸注解重新声明，
    # dataclasses 会把它换成 kw_only=False 的新 Field，而位置仍沿用基类顺序 ——
    # 结果是 height 抢到第 0 个位置参数，Button("文字") 会把文字塞进 height。
    # 因此重新声明继承字段时必须显式 kw_only=True。
    height: int = field(default=BUTTON_HEIGHT, kw_only=True)

    style_type: StyleType = StyleType.DEFAULT
    shape: ButtonShape = ButtonShape.ROUND
    plain: bool = False  # 中心是否镂空
    is_primary: bool = False

    def init(self):
        if self.is_primary:
            self.style_type = StyleType.PRIMARY
        self._style = FeedbackStyle(*self.style_type.value)
        self.style = self.style or ft.ButtonStyle(
            padding=ft.Padding.all(10), alignment=ft.Alignment.CENTER
        )
        if self.disabled:
            self.style.bgcolor = self.style.bgcolor or ft.Colors.GREY_300
        if self.style_type == StyleType.DEFAULT:
            self.style.color = self.style.color or {
                ft.ControlState.DEFAULT: ft.Colors.BLACK
            }
        else:
            if self.plain:
                self.style.color = self.style.color or {
                    ft.ControlState.DEFAULT: self._style.color
                }
            else:
                self.style.color = self.style.color or {
                    ft.ControlState.DEFAULT: ft.Colors.WHITE
                }
        if self.plain:
            self.style.bgcolor = self.style.bgcolor or {
                ft.ControlState.DEFAULT: ft.Colors.WHITE
            }
            self.style.overlay_color = self.style.overlay_color or {
                ft.ControlState.DEFAULT: ft.Colors.WHITE
            }
            self.style.shadow_color = self.style.shadow_color or {
                ft.ControlState.DEFAULT: ft.Colors.WHITE
            }
            self.style.side = self.style.side or {
                ft.ControlState.DEFAULT: ft.BorderSide(1, self._style.color),
                ft.ControlState.HOVERED: ft.BorderSide(
                    1, self._style.color_light, style=ft.BorderStyle.NONE
                ),
                ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.GREY),
                ft.ControlState.PRESSED: ft.BorderSide(1, self._style.color_accent),
            }
            self.style.color = self.style.color or {
                ft.ControlState.DEFAULT: self._style.color,
                ft.ControlState.HOVERED: self._style.color_accent,
                ft.ControlState.PRESSED: self._style.color,
            }
            self.style.elevation = self.style.elevation or {
                ft.ControlState.DEFAULT: 0,
                ft.ControlState.PRESSED: 0,
                ft.ControlState.HOVERED: 0,
            }
        else:
            self.style.bgcolor = {
                ft.ControlState.DEFAULT: self._style.color,
                ft.ControlState.HOVERED: self._style.color_accent,
                ft.ControlState.DISABLED: ft.Colors.GREY_300,
                ft.ControlState.PRESSED: self._style.color_light,
            }
            self.style.overlay_color = self.style.overlay_color or {
                ft.ControlState.DEFAULT: self._style.color,
                ft.ControlState.HOVERED: self._style.color_accent,
                ft.ControlState.DISABLED: ft.Colors.GREY_300,
                ft.ControlState.PRESSED: self._style.color_light,
                # ft.ControlState.PRESSED: ft.Colors.RED,
            }

            self.style.shadow_color = self.style.shadow_color or {
                ft.ControlState.DEFAULT: self._style.color,
                ft.ControlState.HOVERED: self._style.color_accent,
                ft.ControlState.DISABLED: ft.Colors.GREY_300,
                ft.ControlState.PRESSED: self._style.color_light,
                # ft.ControlState.PRESSED: ft.Colors.RED,
            }

            self.style.elevation = self.style.elevation or {
                ft.ControlState.DEFAULT: 0,
                ft.ControlState.PRESSED: 0,
                ft.ControlState.HOVERED: 0,
            }
            self.style.side = self.style.side or {
                ft.ControlState.DEFAULT: ft.BorderSide(1, self._style.color),
                ft.ControlState.HOVERED: ft.BorderSide(1, self._style.color_light),
                ft.ControlState.DISABLED: ft.BorderSide(1, ft.Colors.GREY),
                ft.ControlState.PRESSED: ft.BorderSide(1, self._style.color_accent),
            }

        if self.style is not None:
            if self.shape == ButtonShape.RECTANGLE:
                self.style.shape = ft.ContinuousRectangleBorder()
            elif self.shape == ButtonShape.ROUND:
                self.style.shape = ft.RoundedRectangleBorder(radius=BORDER_RADIUS)
            elif self.shape == ButtonShape.CIRCLE:
                self.style.shape = ft.StadiumBorder()


@ft.component
def App():
    return ft.Column(
        controls=[
            Button(content="test"),
            Button(content="test", is_primary=True),
            ft.Text("主按钮"),
            ft.Row(
                controls=[
                    Button(content="default_button", style_type=StyleType.DEFAULT),
                    Button(content="primary_button", style_type=StyleType.PRIMARY),
                    Button(content="success_button", style_type=StyleType.SUCCESS),
                    Button(content="info_button", style_type=StyleType.INFO),
                    Button(content="warning_button", style_type=StyleType.WARNING),
                    Button(content="error_button", style_type=StyleType.ERROR),
                ]
            ),
            ft.Text("次按钮，描边按钮，plain"),
            ft.Row(
                controls=[
                    Button(
                        content="color_button", style_type=StyleType.DEFAULT, plain=True
                    ),
                    Button(
                        content="primary_button",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                    ),
                    Button(
                        content="success_button",
                        style_type=StyleType.SUCCESS,
                        plain=True,
                    ),
                    Button(
                        content="info_button", style_type=StyleType.INFO, plain=True
                    ),
                    Button(
                        content="warning_button",
                        style_type=StyleType.WARNING,
                        plain=True,
                    ),
                    Button(
                        content="error_button", style_type=StyleType.ERROR, plain=True
                    ),
                ]
            ),
            ft.Text("rectangle-round-circle"),
            ft.Row(
                controls=[
                    Button(
                        content="ButtonShape.rect",
                        style_type=StyleType.DEFAULT,
                        plain=True,
                        shape=ButtonShape.RECTANGLE,
                    ),
                    Button(
                        content="ButtonShape.round",
                        style_type=StyleType.DEFAULT,
                        plain=True,
                        shape=ButtonShape.ROUND,
                    ),
                    Button(
                        content="ButtonShape.circle",
                        style_type=StyleType.DEFAULT,
                        plain=True,
                        shape=ButtonShape.CIRCLE,
                    ),
                ]
            ),
            ft.Text("disabled"),
            ft.Row(
                controls=[
                    Button(
                        content="color_button",
                        style_type=StyleType.DEFAULT,
                        plain=True,
                        disabled=True,
                    ),
                    Button(
                        content="primary_button",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        disabled=True,
                    ),
                    Button(
                        content="success_button",
                        style_type=StyleType.SUCCESS,
                        plain=True,
                        disabled=True,
                    ),
                    Button(
                        content="info_button",
                        style_type=StyleType.INFO,
                        plain=True,
                        disabled=True,
                    ),
                    Button(
                        content="warning_button",
                        style_type=StyleType.WARNING,
                        plain=True,
                        disabled=True,
                    ),
                    Button(
                        content="error_button",
                        style_type=StyleType.ERROR,
                        plain=True,
                        disabled=True,
                    ),
                ]
            ),
            ft.Text("icon_button"),
            Button(content="icon_button", icon=ft.Icons.ADD),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
