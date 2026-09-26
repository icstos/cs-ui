"""Timeline 纯逻辑单测（不需要窗口）。

覆盖：向后兼容、参数归一、语义色映射、节点尺寸与颜色优先级、对齐模式、
时间戳位置、pending 归一、行结构（对侧时间列占位 / 内容左右 / intrinsic_height）、
连接线开关与末段渐隐。

用法::

    python scripts/_time_line_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.layout.time_line import (  # noqa: E402
    DENSITIES,
    DOT_SIZES,
    FIRST_LINE_H,
    TYPE_COLORS,
    Timeline,
    TimelineItem,
)

_fails: list[str] = []
_passed = 0


def check(name: str, got: object, want: object) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def section(title: str) -> None:
    print(f"\n== {title} ==")


# ---------------------------------------------------------------------------
section("向后兼容（旧签名必须原样可用）")
item = TimelineItem("提交申请", "09:12", "材料已上传完成", done=True)
check("位置参数仍是 title/time/subtitle", (item.title, item.time, item.subtitle),
      ("提交申请", "09:12", "材料已上传完成"))
check("done 关键字仍在", item.done, True)
check("新增字段默认值", (item.type, item.variant, item.size, item.content),
      (None, None, None, None))

old = Timeline(
    items=[TimelineItem("提交代码", "10:00"), TimelineItem("通过 CI", "10:05")],
    line_color="#d1d5db",
    dot_size=22,
)
check("旧 line_color 生效", old.line_color, "#d1d5db")
check("旧 dot_size 生效", old._dot_h(old.items[0]), 22)
check("show_last_line 默认 False", old.show_last_line, False)
check("行数 = items 数", len(old.controls), 2)

# ---------------------------------------------------------------------------
section("参数归一（非法值回退默认）")
bad = Timeline(items=[TimelineItem("a")], mode="xxx", time_position="yyy",
               density="zzz", variant="www", line_style="vvv")
check("mode 非法 -> right", bad._mode, "right")
check("time_position 非法 -> opposite", bad._time_position, "opposite")
check("density 非法 -> default", bad._density, DENSITIES["default"])
check("variant 非法 -> filled", bad._item_variant(bad.items[0]), "filled")
check("line_style 非法时仍按实线画",
      bad._rail(bad.items[0], True, True, False).controls[0].bgcolor,
      bad.line_color)

# ---------------------------------------------------------------------------
section("语义色")
probe = Timeline(items=[TimelineItem("a")])
check("primary -> 主题色", probe._type_color("primary"), ft.Colors.PRIMARY)
check("success -> 固定绿", probe._type_color("success"), TYPE_COLORS["success"])
check("warning -> 固定琥珀", probe._type_color("warning"), TYPE_COLORS["warning"])
check("danger -> 固定红", probe._type_color("danger"), TYPE_COLORS["danger"])
check("info -> 固定灰", probe._type_color("info"), TYPE_COLORS["info"])
check("neutral -> 主题描边色", probe._type_color("neutral"), ft.Colors.OUTLINE)
check("未知语义色 -> None", probe._type_color("nope"), None)

# ---------------------------------------------------------------------------
section("节点尺寸 / 首行行盒")
check("默认 size=default -> 26", probe._dot_h(probe.items[0]), DOT_SIZES["default"])
check("_node_h = max(22, dot+2)", probe._node_h, max(FIRST_LINE_H, 26 + 2))

small = Timeline(items=[TimelineItem("a")], size="small")
check("全局 small -> 18", small._dot_h(small.items[0]), 18)
large = Timeline(items=[TimelineItem("a", size="large")])
check("item.size 覆盖全局 -> 34", large._dot_h(large.items[0]), 34)
check("large 的 _node_h", large._node_h, 36)

forced = Timeline(items=[TimelineItem("a", size="large")], dot_size=20)
check("dot_size 压过 size", forced._dot_h(forced.items[0]), 20)
check("dot_size 也决定 _node_h", forced._node_h, 22)

# ---------------------------------------------------------------------------
section("节点颜色优先级")
prio = Timeline(items=[TimelineItem("a")], type="warning")
i_plain = TimelineItem("a")
check("全局 type 兜底", prio._item_color(i_plain), TYPE_COLORS["warning"])
i_type = TimelineItem("a", type="danger")
check("item.type 覆盖全局", prio._item_color(i_type), TYPE_COLORS["danger"])
i_color = TimelineItem("a", color="#123456", type="danger")
check("item.color 压过 item.type", prio._item_color(i_color), "#123456")
i_done = TimelineItem("a", done=True)
check("done 且未给色 -> success", prio._item_color(i_done), TYPE_COLORS["success"])
i_done_color = TimelineItem("a", done=True, color="#abcdef")
check("done + color -> 用 color", prio._item_color(i_done_color), "#abcdef")
check("pending -> 主题色", prio._item_color(i_plain, True), ft.Colors.PRIMARY)
check("pending 但显式 color 优先", prio._item_color(i_done_color, True), "#abcdef")

# ---------------------------------------------------------------------------
section("节点图标")
check("无 icon 无 done -> None", probe._item_icon(i_plain), None)
check("done -> CHECK", probe._item_icon(i_done), ft.Icons.CHECK)
i_icon = TimelineItem("a", icon=ft.Icons.ROCKET_LAUNCH, done=True)
check("显式 icon 压过 done", probe._item_icon(i_icon), ft.Icons.ROCKET_LAUNCH)

# ---------------------------------------------------------------------------
section("对齐模式")
alt = Timeline(items=[TimelineItem(f"i{i}") for i in range(4)], mode="alternate")
check("alternate: 0/2 在右, 1/3 在左",
      [alt._content_on_right(i) for i in range(4)], [True, False, True, False])
right = Timeline(items=[TimelineItem("a")], mode="right")
check("right: 全在右", right._content_on_right(0), True)
left = Timeline(items=[TimelineItem("a")], mode="left")
check("left: 全在左", left._content_on_right(0), False)

# ---------------------------------------------------------------------------
section("pending 归一")
check("None -> 无", Timeline(items=[])._pending_item(), None)
check("False -> 无", Timeline(items=[], pending=False)._pending_item(), None)
check("True -> 默认文案", Timeline(items=[], pending=True)._pending_item().title, "进行中")
check("字符串 -> 自定义标题",
      Timeline(items=[], pending="待全量")._pending_item().title, "待全量")
_pi = TimelineItem("自己给")
check("TimelineItem -> 原样", Timeline(items=[], pending=_pi)._pending_item() is _pi, True)
check("pending 计入行数", len(Timeline(items=[TimelineItem("a")], pending="x").controls), 2)

# ---------------------------------------------------------------------------
section("行结构")
row_tl = Timeline(
    items=[TimelineItem("第一行", "10:00", "副"), TimelineItem("第二行", "11:00")],
    pending="进行中",
)
check("行数 = items + pending", len(row_tl.controls), 3)
first_row = row_tl.controls[0]
last_row = row_tl.controls[2]
check("每行是 Row", isinstance(first_row, ft.Row), True)
check("Row 打开 intrinsic_height", first_row.intrinsic_height, True)
check("Row 交叉轴 STRETCH",
      first_row.vertical_alignment, ft.CrossAxisAlignment.STRETCH)
check("opposite + 内容在右 -> 3 列",
      [type(c).__name__ for c in first_row.controls], ["Container", "Stack", "Container"])
check("时间列在首位（宽度 = time_width）",
      first_row.controls[0].width, row_tl.time_width)
check("轴轨是 Stack", isinstance(first_row.controls[1], ft.Stack), True)
check("pending 行也有时间列占位（轴线不断）", len(last_row.controls), 3)
check("pending 行时间列同样撑位", last_row.controls[0].width, row_tl.time_width)

left_row = Timeline(items=[TimelineItem("a", "10:00")], mode="left").controls[0]
check("mode=left: 内容列在首位", left_row.controls[0].width, None)
check("mode=left: 时间列在末位", left_row.controls[2].width, 112)

hidden_row = Timeline(
    items=[TimelineItem("a", "10:00")], time_position="hidden"
).controls[0]
check("time_position=hidden -> 只有 2 列（无时间列）", len(hidden_row.controls), 2)

alt_hidden = Timeline(
    items=[TimelineItem("a")], mode="alternate", time_position="hidden"
).controls[0]
check("alternate + hidden 仍保留占位列（中轴不偏）", len(alt_hidden.controls), 3)
check("alternate + hidden 的时间列不显示文字",
      alt_hidden.controls[0].content.controls[0].content.value, "")

# ---------------------------------------------------------------------------
section("轴轨（线 + 节点）")
rail = row_tl._rail(row_tl.items[0], first=True, last=False, is_pending=False)
check("轴轨含线 + 节点两项", len(rail.controls), 2)
line = rail.controls[0]
check("首行线从节点中心开始", line.top, row_tl._node_h / 2)
check("非末行线延伸到行底", line.bottom, 0)
check("线宽 = line_width", line.width, row_tl.line_width)
check("线色 = line_color", line.bgcolor, row_tl.line_color)
node = rail.controls[1]
check("节点垂直居中于首行行盒",
      node.top, (row_tl._node_h - row_tl._dot_h(row_tl.items[0])) / 2)
check("节点水平居中于轴轨",
      node.left, (rail.width - row_tl._dot_h(row_tl.items[0])) / 2)

last_rail = row_tl._rail(row_tl.items[0], first=False, last=True, is_pending=False)
check("末行默认不画线（留出 gap）", last_rail.controls[0].bottom, row_tl._gap)
show_last = Timeline(items=[TimelineItem("a")], show_last_line=True)
check("show_last_line=True 时画到行底",
      show_last._rail(show_last.items[0], first=False, last=True,
                      is_pending=False).controls[0].bottom, 0)

faded = Timeline(items=[TimelineItem("a")], line_fade=True)
fade_line = faded._rail(faded.items[0], first=False, last=True, is_pending=False).controls[0]
check("line_fade=True 用渐变而非纯色", fade_line.gradient is not None, True)
check("line_fade 时不再依赖 bgcolor", fade_line.bgcolor, None)
check("line_fade 时末段照样延伸（bottom=0）", fade_line.bottom, 0)

no_line = Timeline(items=[TimelineItem("a")], line_style="none")
no_line_ctrl = no_line._rail(no_line.items[0], first=False, last=False,
                             is_pending=False).controls[0]
check("line_style=none 不画线", (no_line_ctrl.bgcolor, no_line_ctrl.gradient), (None, None))

# ---------------------------------------------------------------------------
section("时间戳位置")
base = TimelineItem("标题", "09:30", "副标题")
top_lines = Timeline(items=[base], time_position="top")._content_lines(base, True)
check("top: 首行是时间", isinstance(top_lines[0], ft.Text) and top_lines[0].value, "09:30")
check("top: 次行是标题", top_lines[1].value, "标题")
inline_lines = Timeline(items=[base], time_position="inline")._content_lines(base, True)
check("inline: 首行是 Row", isinstance(inline_lines[0], ft.Row), True)
check("inline: Row 里是标题 + 时间",
      [c.value for c in inline_lines[0].controls], ["标题", "09:30"])
opp_lines = Timeline(items=[base], time_position="opposite")._content_lines(base, True)
check("opposite: 首行是标题（时间另起一列）", opp_lines[0].value, "标题")

check("无 subtitle 时不产生空行",
      len(Timeline(items=[base])._content_lines(TimelineItem("只有标题"), True)), 1)
rich = TimelineItem("标题", content=ft.Divider())
check("content 追加在末尾", isinstance(
    Timeline(items=[rich])._content_lines(rich, True)[-1], ft.Divider), True)

# ---------------------------------------------------------------------------
section("内容行盒与密度")
check("首行行盒高 = _node_h",
      row_tl._build_content(row_tl.items[0], True, False).content.content.controls[0].height,
      row_tl._node_h)
check("compact gap", Timeline(items=[], density="compact")._gap, DENSITIES["compact"]["gap"])
check("comfortable gap",
      Timeline(items=[], density="comfortable")._gap, DENSITIES["comfortable"]["gap"])

# ---------------------------------------------------------------------------
section("交互（点击回调 + ink）")
calls: list[str] = []
clickable = Timeline(
    items=[TimelineItem("可点", "10:00"), TimelineItem("禁用", disabled=True)],
    on_item_click=lambda it: calls.append(it.title),
)
box_ok = clickable._build_content(clickable.items[0], True, False).content
check("可点项开启 ink", box_ok.ink, True)
check("可点项挂了 on_click", callable(box_ok.on_click), True)
box_off = clickable._build_content(clickable.items[1], True, False).content
check("disabled 项不开 ink", box_off.ink, False)
check("disabled 项无 on_click", box_off.on_click, None)
box_ok.on_click(None)
check("回调被触发", calls, ["可点"])

no_cb = Timeline(items=[TimelineItem("a")])
check("没给回调时不开 ink",
      no_cb._build_content(no_cb.items[0], True, False).content.ink, False)

check("ink=False 可关掉反馈",
      Timeline(items=[TimelineItem("a")], ink=False,
               on_item_click=lambda it: None)
      ._build_content(TimelineItem("a"), True, False).content.ink, False)

# ---------------------------------------------------------------------------
section("混合尺寸共用同一条中轴")
mixed = Timeline(
    items=[
        TimelineItem("大", "1", size="large"),
        TimelineItem("小", "2", size="small"),
        TimelineItem("默认", "3"),
    ]
)
check("_dot_max 取最大节点（34）", mixed._dot_max, 34)
check("_node_h 跟着最大节点（36）", mixed._node_h, 36)
rail_large = mixed._rail(mixed.items[0], first=True, last=False, is_pending=False)
rail_small = mixed._rail(mixed.items[1], first=False, last=False, is_pending=False)
check("不同尺寸的轴轨同宽（轴线不会左右跳）", rail_large.width, rail_small.width)
check("大节点居中于轴轨",
      rail_large.controls[1].left + 34 / 2, rail_large.width / 2)
check("小节点居中于同一条中轴",
      rail_small.controls[1].left + 18 / 2, rail_small.width / 2)
check("小节点的首行行盒仍是 _node_h（与标题对中）",
      mixed._build_content(mixed.items[1], True, False)
      .content.content.controls[0].height, 36)

# ---------------------------------------------------------------------------
section("reverse 倒序")
rev = Timeline(
    items=[TimelineItem("早", "09:00"), TimelineItem("晚", "18:00")],
    reverse=True,
    pending="进行中",
)


def _row_title(row: ft.Control) -> str:
    """从一行里取出内容首行的文字（内容列 = 那个 expand 的 Container）。"""
    for cell in row.controls:
        if isinstance(cell, ft.Container) and cell.expand:
            return cell.content.content.controls[0].content.value
    raise AssertionError("行里找不到内容列")


check("reverse: 后续项排到最上", [_row_title(r) for r in rev.controls],
      ["晚", "早", "进行中"])
check("reverse: pending 仍在末尾（不被倒序）", _row_title(rev.controls[-1]), "进行中")
check("reverse: 行数仍为 items + pending", len(rev.controls), 3)

# ---------------------------------------------------------------------------
section("无轴线时节点仍居中")
no_line_big = Timeline(items=[TimelineItem("a", size="large")], line_style="none")
none_rail = no_line_big._rail(
    no_line_big.items[0], first=True, last=False, is_pending=False
)
check("line_style=none 的轴轨宽度仍按最大节点算", none_rail.width, 34 + 6 * 2)
check("line_style=none 的节点仍水平居中",
      none_rail.controls[1].left, (none_rail.width - 34) / 2)
check("line_style=none 时线控件仍占位（不影响列结构）", len(none_rail.controls), 2)

# ---------------------------------------------------------------------------
print(f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
      f"  (passed={_passed})")
for f in _fails:
    print("  FAIL", f)
sys.exit(1 if _fails else 0)
