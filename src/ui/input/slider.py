import flet as ft


@ft.control
class Slider(ft.Slider):
    pass


@ft.control
class RangeSlider(ft.RangeSlider):
    min: ft.Number = 0
    max: ft.Number = 1
    start_value: ft.Number = 0
    end_value: ft.Number = 0

    def init(self):
        self.start_value = self.start_value or (self.max - self.min) * 1 / 5
        self.end_value = self.end_value or (self.max - self.min) * 2 / 5


@ft.component
def App():

    return ft.Column([Slider(), RangeSlider(start_value=0.1)])


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
