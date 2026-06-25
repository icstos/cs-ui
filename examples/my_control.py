import flet as ft


@ft.control
class MyControl(ft.Container):
    removable: bool = False

    def init(self):
        self.content = ft.Text(value="test")

    def delete(self, e):

        def traverse_controls(controls, control_to_delete):
            for c in controls:
                if c == control_to_delete:
                    controls.remove(c)
                    return
                if hasattr(c, "controls") and len(c.controls) > 0:
                    traverse_controls(c.controls, control_to_delete)

        if self.removable:
            p = self.page
            traverse_controls(p.controls, self)
            p.update()

    def did_mount(self):
        return super().did_mount()

    def will_unmount(self):
        return super().will_unmount()


def main(page: ft.Page):
    # 透明效果
    page.bgcolor = ft.Colors.TRANSPARENT
    page.window.bgcolor = ft.Colors.TRANSPARENT
    my_control = MyControl(removable=True)
    my_control.content = ft.Text(value="test")
    my_btn = ft.Button(ft.Text(value="test"), on_click=my_control.delete)
    page.add(ft.Column(controls=[my_control, my_btn]))


if __name__ == "__main__":
    ft.run(main)
