"""输入类组件：按钮、文本框、选择器、滑块等。

门面惰性（见 :mod:`ui._lazy`）：``Button`` 只加载 ``button``；颜色选择器、级联、
穿梭框这些重量级组件不再陪跑。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Button": ".button",
        "Cascader": ".cascader",
        "CascaderNode": ".cascader",
        "Checkbox": ".checkbox",
        "CheckboxGroup": ".checkbox",
        "Chip": ".chip",
        "ColorPicker": ".color_picker",
        "DateInput": ".date_input",
        "DateTimeInput": ".datetime_input",
        "DirPicker": ".file_picker",
        "FileDialog": ".file_picker",
        "FileDialogError": ".file_picker",
        "FilePicker": ".file_picker",
        "FileSaver": ".file_picker",
        "ImagePicker": ".image_picker",
        "Input": ".input",
        "MultiSelect": ".multi_select",
        "NumberInput": ".number_input",
        "Radio": ".radio",
        "RangeSlider": ".slider",
        "Rating": ".rating",
        "SearchBar": ".search_bar",
        "SegmentedButton": ".segmented_button",
        "SelectBox": ".select_box",
        "SelectOption": ".select_box",
        "Slider": ".slider",
        "Switch": ".switch",
        "Transfer": ".transfer",
        "TransferItem": ".transfer",
    },
    __name__,
)
