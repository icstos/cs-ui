class Control:
    """Base UI control for the cs_ui framework."""

    def __init__(
        self,
        visible: bool = True,
        width=None,
        height=None,
        expand: bool = False,
        bgcolor=None,
        opacity: float = 1.0,
    ):
        self.visible = visible
        self.width = width
        self.height = height
        self.expand = expand
        self.bgcolor = bgcolor
        self.opacity = opacity

    def build(self):
        control = self._create()
        return self._apply_common_props(control)

    def _create(self):
        raise NotImplementedError("_create() must be implemented by subclasses")

    def _apply_common_props(self, control):
        if not control:
            return control

        if hasattr(control, "visible"):
            control.visible = self.visible
        if hasattr(control, "width") and self.width is not None:
            control.width = self.width
        if hasattr(control, "height") and self.height is not None:
            control.height = self.height
        if hasattr(control, "expand"):
            control.expand = self.expand
        if hasattr(control, "bgcolor") and self.bgcolor is not None:
            control.bgcolor = self.bgcolor
        if hasattr(control, "opacity"):
            control.opacity = self.opacity

        return control

    @staticmethod
    def _build_child(child):
        return child.build() if isinstance(child, Control) else child
