"""设计令牌 (Design Tokens)。

组件里**不要**再出现裸色值（``"#6B7280"``）、裸圆角（``8``）、裸字号（``14``）——
一律走本模块。理由不是洁癖，而是三条硬需求：

1. **明暗主题**：Flet / Flutter 的颜色串支持 ``"<角色名>,<透明度>"``（由
   :func:`flet.Colors.with_opacity` 生成，如 ``"onsurface,0.06"``），
   **由 Flutter 在运行时按当前 ``ColorScheme`` 解析**。把 ``ft.Colors.ON_SURFACE``
   交给 Flutter，明暗切换是零成本且必然正确的；把 ``"#6B7280"`` 写死，暗色下必瞎。
2. **主色可切**：一个品牌色由 :func:`ui.core.palette.build_scheme` 算成整套 M3
   色板（46 个角色，明暗各一套，见 :mod:`ui.core.theme`），组件只引用角色、
   不引用具体色值。
3. **一处修改全局生效**：圆角 / 间距 / 字号改一个数，全框架跟着走。

令牌分两类，用途不同，不要混：

* **主题感知令牌**（本模块上半部分）—— 直接就是 :class:`flet.Colors` 的**角色枚举**，
  原样传给 Flutter 即可，明暗与主色全自动跟随。
* **框架解析令牌**（:data:`SEMANTIC`）—— Material 3 **没有** ``success`` /
  ``warning`` / ``info`` / ``neutral`` 这几个语义角色，而桌面端的状态提示离不开它们。
  它们由本模块按当前模式给出一对具体色值（见 :func:`semantic`）。

配色分层
--------

颜色不是一个"色板"，是五层，每层只有一种表达手段 —— **不要跨层借用**，
跨层就是"同一种绿在五个地方长得不一样"的来源：

=========  ===============================================  ==============
层        角色                                              谁来解析
=========  ===============================================  ==============
表面      ``SURFACE`` / ``SURFACE_CONTAINER_LOWEST..HIGHEST``  Flutter
前景      ``ON_SURFACE`` / ``ON_SURFACE_VARIANT`` /           Flutter
          ``OUTLINE`` / ``OUTLINE_VARIANT``
交互      ``state_layer()`` / ``selected_layer()`` /           Flutter
          ``disabled_layer()``（角色 + 透明度）
强调      ``accent_fill/on/text/soft()``（主色 + 五个语义角色） 混合
数据      图表分类色 / 热力图色阶（:mod:`ui.core.color` 派生）    Python
=========  ===============================================  ==============

第 1、2、3 层直接用 M3 角色：**换主色、切明暗都不需要重建控件**，Flutter 在
渲染时解析。第 4 层里 ``primary`` 也走角色；``success`` / ``warning`` / ``info``
这三个 M3 没有的角色只能在 Python 侧按当前模式拍定色值（见 :data:`SEMANTIC`），
所以组件必须"渲染时现取"，不要把结果存进模块级常量。第 5 层同理，见
:func:`ui.core.color.categorical` / :func:`~ui.core.color.ramp`。

固定的、与主题无关的只有两类地方，各有各的理由，都写了注释：
媒体上压字（图片上的白字、遮罩）与代码块的深底 —— 它们压在**图片或代码**上，
不压在表面色上，跟着主题变反而会糊掉。

用法::

    from ui.core.tokens import SPACE, RADIUS, accent_fill, accent_soft, overlay

    ft.Container(
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border_radius=RADIUS["lg"],
        padding=SPACE["3"],
    )
    ft.Text("已保存", color=accent_text("success"))
"""

from __future__ import annotations

import flet as ft

from ui.core import palette

__all__ = [
    "ACCENT_ROLES",
    "BREAKPOINT",
    "CONTENT_MAX",
    "CONTROL_HEIGHT",
    "DISABLED_OPACITY",
    "DURATION",
    "ELEVATION",
    "FONT_SIZE",
    "FONT_WEIGHT",
    "GAP",
    "GAP_LOOSE",
    "GAP_TIGHT",
    "ICON_SIZE",
    "M3_ACCENT",
    "PAD",
    "PAD_LOOSE",
    "PAGE_PAD",
    "PRIMARY_SEEDS",
    "RADIUS",
    "SELECTED_OPACITY",
    "SEMANTIC",
    "SEMANTIC_ON",
    "SEMANTIC_ROLES",
    "SEMANTIC_TEXT",
    "SEMANTIC_TINT",
    "SEMANTIC_WASH",
    "SPACE",
    "SPACE_STEPS",
    "STATE",
    "accent_fill",
    "accent_on",
    "accent_soft",
    "accent_text",
    "accent_wash",
    "disabled_layer",
    "elevation",
    "focus_border",
    "hairline",
    "on_semantic",
    "overlay",
    "scrim",
    "selected_layer",
    "semantic",
    "semantic_text",
    "state_layer",
]

# ---------------------------------------------------------------------------
# 间距：4px 基准网格，键是"步数"（0 / 1 / 2 / 3 …），值是逻辑像素。
# 键用字符串是因为步数可以 >9（``SPACE["12"]``），用 int 键会和枚举混淆。
# ---------------------------------------------------------------------------
SPACE_STEPS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40)

SPACE: dict[str, int] = {
    str(step): step * 4 for step in SPACE_STEPS
}  # 0 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 80 / 96 / 128 / 160

#: 常用间距的语义别名（读代码时比记数字清楚）
GAP_TIGHT = SPACE["1"]  # 4  同行元素
GAP = SPACE["2"]  # 8   控件内元素
GAP_LOOSE = SPACE["4"]  # 16  组之间
PAD = SPACE["3"]  # 12  面板内边距
PAD_LOOSE = SPACE["6"]  # 24  卡片内边距

# ---------------------------------------------------------------------------
# 圆角
# ---------------------------------------------------------------------------
RADIUS: dict[str, int] = {
    "none": 0,
    "xs": 2,
    "sm": 4,  # 小色块 / 徽标
    "md": 6,  # 输入框 / 按钮
    "lg": 8,  # 面板 / 卡片
    "xl": 12,  # 大容器
    "full": 999,  # 胶囊 / 头像
}

# ---------------------------------------------------------------------------
# 字号：与 Material 3 的 type scale 对齐的桌面端档位。
#
# **正文是 14**，这是整个刻度的锚点：``body`` 既是表单值、表格单元格、列表
# 主行的尺寸，也是 ``ft.Text`` 不写 ``size`` 时由主题给出的默认值（见
# :func:`ui.core.theme.build_theme` 里的 ``text_theme``）。改这一个数，全框架
# 正文跟着走；改别的档位只影响局部。
#
# 刻度取 M3 的子集而不是等比数列：每档之间至少差 2px —— 1px 的差肉眼分不出，
# 只会让调用方纠结"这段该用 13 还是 14"，然后随手写个字面量。
#
#   caption     11  labelSmall    标签 / 计数 / 单位
#   small       12  labelMedium   次要说明 / 脚注 / 副行
#   body        14  bodyMedium    **正文**、表单值、表格单元格、列表主行
#   title       16  titleMedium   卡片标题 / 大号控件（44 高）内的文字
#   headline    20  headlineSmall 分区标题
#   headline_lg 24  页面标题
#   display     28  空状态 / 结果页
#   display_lg  36  文档页主标题
#
# 这里**故意没有** subtitle：11/12/13/14 每 1px 一档时，"列表主行"比正文大
# 1px 还算个档位；正文升到 14 之后它与 body 同值，留着只会让人在两个等价
# 名字之间选。要比正文"重"一档，用 ``body`` + ``FONT_WEIGHT["medium"]``；
# 要比正文"大"一档，那就是 ``title``。
# ---------------------------------------------------------------------------
FONT_SIZE: dict[str, int] = {
    "caption": 11,
    "small": 12,
    "body": 14,
    "title": 16,
    "headline": 20,
    "headline_lg": 24,
    "display": 28,
    "display_lg": 36,
}

FONT_WEIGHT: dict[str, ft.FontWeight] = {
    "regular": ft.FontWeight.W_400,
    "medium": ft.FontWeight.W_500,
    "semibold": ft.FontWeight.W_600,
    "bold": ft.FontWeight.W_700,
}

# ---------------------------------------------------------------------------
# 图标尺寸：**与字号是两套刻度，不要互相借**。
#
# 图标必须比同行文字略大才"站得稳"：14px 正文配 16px 图标是桌面端的常态，
# 而按钮内的图标又要比正文小、免得把字挤扁。把图标硬塞进 FONT_SIZE 的键里
# （``size=FONT_SIZE["body"]``）会得到一个视觉上偏小的图标 —— 这是最容易被
# 写成"随手一个数字"的地方，实测全框架曾出现 11/12/13/14/15/16/18/20/22/24
# 十种取值，同一个列表里的勾和箭头能差 3px。
#
# 档位按"和谁同行"来记，不按绝对大小：
#   xs  与 caption（11）同行的小标识
#   sm  与 small（12）同行 / 徽标内
#   md  与 body（14）同行 —— 列表行、字段前缀、按钮内（最常用）
#   lg  与 title（16）同行 / 工具栏
#   xl  独立图标按钮 / 强调操作
#   2xl 顶栏、空状态
#   3xl 结果页
# ---------------------------------------------------------------------------
ICON_SIZE: dict[str, int] = {
    "xs": 12,
    "sm": 14,
    "md": 16,
    "lg": 18,
    "xl": 20,
    "2xl": 24,
    "3xl": 32,
}

# ---------------------------------------------------------------------------
# 控件高度：同一行表单里，输入框 / 下拉 / 按钮 / 日期选择必须等高，
# 否则一行里会看出"台阶"。实测曾并存 34 / 36 / 40 / 42 四种。
#
#   sm  28  行内小控件（表格里的筛选、标签内的按钮）
#   md  36  表单与按钮的默认高度 —— 绝大多数场合用它
#   lg  44  主操作按钮 / 触屏友好
# ---------------------------------------------------------------------------
CONTROL_HEIGHT: dict[str, int] = {
    "sm": 28,
    "md": 36,
    "lg": 44,
}

# ---------------------------------------------------------------------------
# 断点（响应式）
#
# 六个断点与 ``flet.ResponsiveRowBreakpoint`` **同值**。这不是巧合，是硬约束：
# ``ResponsiveRow`` 换列发生在 Flutter 侧，用的是这套边界；若我们另采一套（比如
# Material 的 600 / 840 / 1200），同一个窗口里就会出现"栅格已经排成三列、页面
# 还认为自己是窄屏"的错位 —— 两套边界交错，比只有一套粗边界糟得多。
#
#   xs  0      手机竖屏
#   sm  576    手机横屏 / 小平板
#   md  768    平板竖屏   —— 「紧凑 / 中等」的分界
#   lg  992    平板横屏 / 小笔记本
#   xl  1200   桌面       —— 「中等 / 宽敞」的分界
#   xxl 1400   宽屏
#
# **组件行为只需要三档**（见 :data:`~ui.core.responsive.SIZE_CLASSES`），六档是给
# 栅格列数用的：中间那两档（md / lg）在布局策略上是同一件事，都叫"中等"，只是
# 能塞下几列不同。
# ---------------------------------------------------------------------------
BREAKPOINT: dict[str, int] = {
    "xs": 0,
    "sm": 576,
    "md": 768,
    "lg": 992,
    "xl": 1200,
    "xxl": 1400,
}

#: 页面内边距：窄屏要"靠边站"（留白吃掉的是内容宽度），宽屏才敢留白。
#: 实测窄窗口若沿用 32px，一张三列表格的可视宽度会少掉 64px —— 正好是一列的宽度。
PAGE_PAD: dict[str, int] = {
    "compact": 16,
    "medium": 24,
    "expanded": 32,
}

#: 内容最大宽度：**不是所有内容都该随窗口无限拉长**。
#:
#: 一行 60~75 个字符最好读（约 700~780px @14px），超过这个宽度，眼睛回行的距离
#: 变长，阅读速度反而下降；表单与设置页同理会显得"左一个标签右一个输入框，
#: 中间空一大片"。所以宽屏上的正解是**居中限宽**，而不是把内容拉满。
#:
#:   reading  720   文章、说明、表单 —— 一列文字
#:   content  1120  常规页面（卡片墙、表格、设置分区）
#:   wide     1440   Dashboard、多列数据面板
CONTENT_MAX: dict[str, int] = {
    "reading": 720,
    "content": 1120,
    "wide": 1440,
}

# ---------------------------------------------------------------------------
# 动效时长（毫秒）：够短到"跟手"，够长到"看得见"
# ---------------------------------------------------------------------------
DURATION: dict[str, int] = {
    "instant": 0,
    "fast": 120,
    "normal": 200,
    "slow": 320,
}

# ---------------------------------------------------------------------------
# 交互状态层 (state layer)
#
# Material 3 的规则是：**同一个控件在 hover / focus / pressed 三态下，用的都是
# 「前景色 + 一层半透明覆盖」，只改透明度**。透明度是规范值，不该由各组件自己
# 拍脑袋 —— 实测框架内悬停曾同时存在 0.02 / 0.04 / 0.06 / 0.08 / 0.12 五种，
# 于是"轻轻划过"在菜单里几乎看不见、在日历里却像被选中。
#
# 取规范值而不是自选值有一个额外好处：**和 flet 内置控件对齐**。
# ``MenuButton`` / ``ListTile`` / ``IconButton`` 内部就是按这套值画的，
# 自研组件沿用同一组数字，并排放置时不会有"谁更亮一点"的错觉。
#
#   hover    0.08  划过
#   focus    0.12  键盘走焦（与 pressed 同值：M3 如此）
#   pressed  0.12  按下
#   dragged  0.16  拖动中
# ---------------------------------------------------------------------------
STATE: dict[str, float] = {
    "hover": 0.08,
    "focus": 0.12,
    "pressed": 0.12,
    "dragged": 0.16,
}

#: 选中态的强调档：同一件事在"轻提示"与"当前视图"两种场合轻重不同。
#:   subtle  0.08 —— 多选中的一行、路径上的一环（前景仍是普通文字色）
#:   normal  0.12 —— 单选选中的一行（默认，多数场合）
#:   strong  —— 主色容器实底，用于"当前页 / 当前标签"这种必须一眼看到的
SELECTED_OPACITY: dict[str, float] = {"subtle": 0.08, "normal": 0.12}

# ---------------------------------------------------------------------------
# 禁用态：Material 3 规定 **label 38% / container 12%**。
#
# 这两个数字在框架里出现过十几次（按钮、复选框、单选、评分、穿梭框、菜单、
# 分页、日历），全部手抄 0.38 / 0.12 —— 值一样，但"谁是标签灰、谁是容器灰"
# 只在人脑里。一次抄错 0.35 就会让某一处的"变灰"比其他处淡一档，而这种差别
# 用户说不出来，只会觉得"这里好像没禁用干净"。
#
#   label      0.38  文字、图标、描边
#   container  0.12  禁用控件的底色 / 边线
# ---------------------------------------------------------------------------
DISABLED_OPACITY: dict[str, float] = {"label": 0.38, "container": 0.12}


# ---------------------------------------------------------------------------
# 语义色：Material 3 没有的角色，由框架补齐，明暗各一套。
#
# 每个角色给**三档**（与 M3 的 primary / on-primary / primary-container 同构）——
# 一个色值不可能同时当"填充"和"文字"，实测差得很远：
#   ``#10B981`` 对白底只有 2.54:1，``#F59E0B`` 只有 2.15:1，
#   在它们上面压白字同样只有 2.54 / 2.15 —— 徽标上的字是**读不出来**的。
#
#   SEMANTIC      填充：徽标实底 / 状态点 / 进度段
#   SEMANTIC_ON   该填充上的前景（徽标里的文字与图标）
#   SEMANTIC_TEXT 该角色作为页面文字 / 图标 / 细边框时的颜色
#
# 取值不再手挑，而是由 :func:`ui.core.palette.semantic_scale` **按目标对比度
# 解出来**：四个角色都解到同一个 5.0:1（深色 7.0:1），于是"成功"与"警告"在
# 界面上的视觉重量一样。手挑色值时最容易出的问题正是这个 —— 原来四个填充色
# 的明度分别是 0.51 / 0.56 / 0.58 / 0.50，对比度 5.48 / 5.02 / 4.83 / 5.93，
# 并排放在一起时"信息"明显比其他三个轻，"危险"反而最淡。
#
# 色相是**固定**的（见 :data:`ui.core.palette.SEMANTIC_HUES`）：成功在任何
# 品牌色下都必须是绿的，否则语义就失效了。
# ---------------------------------------------------------------------------
SEMANTIC_ROLES: tuple[str, ...] = ("success", "warning", "danger", "info", "neutral")

SEMANTIC: dict[str, dict[str, str]] = {
    role: {
        mode: palette.semantic_scale(role, mode)[0] for mode in ("light", "dark")
    }
    for role in SEMANTIC_ROLES
}

#: 铺在语义色**实底**上的前景色（徽标 / 状态胶囊里的文字与图标）
SEMANTIC_ON: dict[str, dict[str, str]] = {
    role: {
        mode: palette.semantic_scale(role, mode)[1] for mode in ("light", "dark")
    }
    for role in SEMANTIC_ROLES
}

#: 语义色作为**页面上的文字 / 图标 / 细边框**时的取值（不做背景）
SEMANTIC_TEXT: dict[str, dict[str, str]] = {
    role: {
        mode: palette.semantic_scale(role, mode)[2] for mode in ("light", "dark")
    }
    for role in SEMANTIC_ROLES
}

#: 铺在语义色**实底**上的那一层淡色的透明度（图标底座、徽标、选中胶囊）。
#:
#: 以前这个数字散在九个组件里各写一遍（0.10 / 0.12 / 0.15 / 0.18 都有），
#: 于是"轻轻染一点色"在不同控件上是深浅不同的四种红。取 12% 与 M3 的
#: "selected state layer" 同值 —— 这是唯一一个 flet 内置控件也在用的档位。
SEMANTIC_TINT: float = 0.12

#: 大面积淡底（对话框标题带、提示条整行）的透明度。
#:
#: 为什么比 :data:`SEMANTIC_TINT` 低一档：同一个透明度，面积越大看着越重。
#: 12% 放在 22×22 的图标底座上正好，铺满一整条标题栏就成了一块彩色横带，
#: 把"提示"喊成了"警报"。所以按**面积**分两档，不是按重要性。
SEMANTIC_WASH: float = 0.08

#: M3 自带的强调角色 → (实底, 实底上的前景)。这三个角色的具体色值由
#: :mod:`ui.core.palette` 算进 ``ColorScheme``，这里只是引用**角色名**，
#: 所以换主色 / 切明暗时不需要重建任何控件。
M3_ACCENT: dict[str, tuple[ft.Colors, ft.Colors]] = {
    "primary": (ft.Colors.PRIMARY, ft.Colors.ON_PRIMARY),
    "secondary": (ft.Colors.SECONDARY, ft.Colors.ON_SECONDARY),
    "tertiary": (ft.Colors.TERTIARY, ft.Colors.ON_TERTIARY),
}

#: 全部可用的强调角色：M3 的三个 + 框架补的五个语义角色。
ACCENT_ROLES: tuple[str, ...] = (*M3_ACCENT, *SEMANTIC_ROLES)

# ---------------------------------------------------------------------------
# 预设品牌色：交给 ``ui.core.palette.build_scheme`` 算出整套 M3 色板
# （primary / secondary / surface / outline … 全部 46 个角色）。
# ---------------------------------------------------------------------------
PRIMARY_SEEDS: dict[str, str] = {
    "blue": "#1F6FEB",
    "indigo": "#4F46E5",
    "violet": "#7C3AED",
    "teal": "#0D9488",
    "green": "#16A34A",
    "orange": "#EA580C",
    "red": "#DC2626",
    "slate": "#475569",
}

# ---------------------------------------------------------------------------
# 高度：阴影 = 模糊半径 + Y 偏移 + 黑色透明度
# ---------------------------------------------------------------------------
_ELEVATION: dict[int, tuple[float, float, float]] = {
    0: (0.0, 0.0, 0.00),
    1: (2.0, 1.0, 0.06),
    2: (6.0, 2.0, 0.08),
    3: (12.0, 4.0, 0.10),
    4: (24.0, 8.0, 0.12),
}
ELEVATION = tuple(sorted(_ELEVATION))


# ---------------------------------------------------------------------------
# 取值函数
# ---------------------------------------------------------------------------
def _opt_mode(mode: str | None) -> str:
    """把模式归一成 ``"light"`` / ``"dark"``（非法值退回浅色）。

    ``mode=None`` 时取**当前全局主题**解析出的实际模式 —— 这样调用方写
    ``semantic("success")`` 就能自动跟随主题，不必到处传参。
    """
    if mode in ("light", "dark"):
        return mode
    if mode is None:
        # 延迟导入：theme 依赖 tokens，反向依赖会成环
        from ui.core.theme import current_mode

        return current_mode()
    return "light"


def semantic(role: str, mode: str | None = None) -> str:
    """取语义色**填充**（``success`` / ``warning`` / ``danger`` / ``info`` / ``neutral``）。

    用于徽标实底、状态点、进度段这类"要压住内容"的地方 —— 取值保证与白字
    对比度 >= 4.5:1，所以 :func:`on_semantic` 给的白字一定读得出来。

    要给**文字 / 图标 / 细边框**用，请改 :func:`semantic_text`。

    Args:
        role: 语义角色名。非法值退回 ``neutral``（不给调用方抛异常的机会 ——
            状态色错一次的代价远小于让整页崩掉）。
        mode: ``"light"`` / ``"dark"``；``None`` 表示跟随当前主题。

    Returns:
        ``"#RRGGBB"`` 形式的色串。
    """
    return SEMANTIC.get(role, SEMANTIC["neutral"])[_opt_mode(mode)]


def on_semantic(role: str, mode: str | None = None) -> str:
    """取语义色**实底上的前景色**（配 :func:`semantic` 用）。"""
    return SEMANTIC_ON.get(role, SEMANTIC_ON["neutral"])[_opt_mode(mode)]


def semantic_text(role: str, mode: str | None = None) -> str:
    """取语义色作为**页面文字 / 图标 / 细边框**时的取值（不做背景）。"""
    return SEMANTIC_TEXT.get(role, SEMANTIC_TEXT["neutral"])[_opt_mode(mode)]


# ---------------------------------------------------------------------------
# 强调角色四联（实底 / 前景 / 文字 / 淡底）
#
# 一个"强调色"在界面上有四种用法，四个取值**不可能一样**：
#
#   fill  实底（主按钮、徽标、进度段）—— 要深到扛得住 on 上的字
#   on    fill 上的前景（按钮文字、徽标图标）
#   text  压在**表面色**上的文字 / 图标（镂空按钮的字、提示条标题）
#   soft  12% 淡底（图标底座、选中胶囊、提示条底）
#
# 以前每个组件自己拼这四样，于是同一个"成功"在消息条里是 ``#047857``、
# 在按钮里是 ``ft.Colors.GREEN``、淡底是一处 0.10 一处 0.12。下面四个函数
# 是唯一入口：组件只说"我要 success 的实底"，不再关心它是角色还是色值。
#
# 为什么 primary / secondary / tertiary 走 M3 角色：它们是**运行时**解析的，
# 换主色和切明暗都不用重建控件；而 success / warning 这类 M3 没有的角色只能
# 在 Python 侧按当前模式拍定一个色值。
# ---------------------------------------------------------------------------
def accent_fill(role: str = "primary", mode: str | None = None) -> ft.ColorValue:
    """强调色的**实底**颜色。

    传 ``primary`` / ``secondary`` / ``tertiary`` 得到 M3 角色（运行时解析，
    永远跟着品牌色走）；传 ``success`` 这类语义角色得到明暗各一套的具体色值。
    """
    if role in M3_ACCENT:
        return M3_ACCENT[role][0]
    return semantic(role, mode)


def accent_on(role: str = "primary", mode: str | None = None) -> ft.ColorValue:
    """强调色**实底上**的前景（文字与图标）。"""
    if role in M3_ACCENT:
        return M3_ACCENT[role][1]
    return on_semantic(role, mode)


def accent_text(role: str = "primary", mode: str | None = None) -> ft.ColorValue:
    """强调色压在**表面色**上时（镂空按钮的字、提示条标题）的取值。

    与 :func:`accent_fill` 刻意不同：实底要够深扛白字，压在白底上的字要够深
    扛白底 —— 两者在浅色主题下恰好同档，在深色主题下必须分开（实底变亮、
    文字也得变亮，但亮的幅度不一样）。
    """
    if role in M3_ACCENT:
        return M3_ACCENT[role][0]
    return semantic_text(role, mode)


def accent_soft(role: str = "primary", mode: str | None = None) -> str:
    """强调色的**小面积**淡底（12%，见 :data:`SEMANTIC_TINT`）。

    图标底座、状态胶囊、计数徽标这类 20~30px 的小块用它。
    铺满一整行的底请改 :func:`accent_wash`。
    """
    return ft.Colors.with_opacity(SEMANTIC_TINT, accent_text(role, mode))


def accent_wash(role: str = "primary", mode: str | None = None) -> str:
    """强调色的**大面积**淡底（8%，见 :data:`SEMANTIC_WASH`）。

    对话框标题带、提示条整行这类铺满宽度的地方用它 —— 同一透明度下面积越大
    看着越重，所以大块要比小块淡一档。
    """
    return ft.Colors.with_opacity(SEMANTIC_WASH, accent_text(role, mode))


def overlay(alpha: float, *, role: str = ft.Colors.ON_SURFACE) -> str:
    """主题感知的半透明覆盖色 —— 悬停底色 / 按下态 / 选中底都用它。

    产出 ``"onsurface,0.06"`` 这类**角色名 + 透明度**串，Flutter 会按当前
    ``ColorScheme`` 解析，所以明暗主题下都正确，不需要框架侧做任何事。
    """
    return ft.Colors.with_opacity(alpha, role)


def state_layer(
    state: str = "hover", *, role: ft.ColorValue = ft.Colors.ON_SURFACE
) -> str:
    """取交互状态覆盖色（悬停 / 聚焦 / 按下 / 拖动中）。

    产出 ``"onsurface,0.08"`` 这类**角色名 + 透明度**串，明暗主题下由 Flutter
    自动解析，与 flet 内置控件同一套取值。

    Args:
        state: ``hover`` / ``focus`` / ``pressed`` / ``dragged``。未知值退回
            ``hover``（状态色错一档的代价远小于让整页崩掉）。
        role: 用哪个颜色打底。默认 ``ON_SURFACE``（中性）；选中项上的悬停传
            ``ft.Colors.PRIMARY``，让"已选中 + 正划过"读起来仍是选中色。

    Returns:
        ``"<角色>,<透明度>"`` 形式的色串。
    """
    return ft.Colors.with_opacity(STATE.get(state, STATE["hover"]), role)


def selected_layer(
    strength: str = "normal", *, role: ft.ColorValue = ft.Colors.PRIMARY
) -> str:
    """取选中态底色。

    三档语义（见 :data:`SELECTED_OPACITY`）：

    * ``subtle`` —— 多选里的一行、路径上的一环：能看出选中，但不抢视线。
    * ``normal`` —— 单选选中的一行（默认）。
    * ``strong`` —— 主色容器实底，留给"当前页 / 当前标签"这种必须一眼看到的。

    Args:
        strength: ``subtle`` / ``normal`` / ``strong``；未知值退回 ``normal``。
        role: 打底角色，默认主色。
    """
    if strength == "strong":
        return ft.Colors.PRIMARY_CONTAINER
    return ft.Colors.with_opacity(
        SELECTED_OPACITY.get(strength, SELECTED_OPACITY["normal"]), role
    )


def disabled_layer(
    kind: str = "label", *, role: ft.ColorValue = ft.Colors.ON_SURFACE
) -> str:
    """取禁用态覆盖色（文字/图标用 ``label``，控件底/边线用 ``container``）。

    禁用不是"把颜色调浅一点"，而是**整块控件统一退到同一档**。走这个函数，
    所有组件的"变灰"才是同一个灰；也顺带解决深色主题 —— 半透明的 on-surface
    在深底上会自动反成"提亮一档"，写死 GREY_400 就做不到。

    Args:
        kind: ``label``（38%，默认）/ ``container``（12%）；未知值退回 ``label``。
        role: 打底角色，默认 ``ON_SURFACE``。
    """
    return ft.Colors.with_opacity(
        DISABLED_OPACITY.get(kind, DISABLED_OPACITY["label"]), role
    )


def scrim(alpha: float = 0.32) -> str:
    """浮层遮罩色（点面板外部收起时铺的那层）。基于 ``on_surface`` 而非纯黑，
    这样深色主题下遮罩是"压暗"而不是"加一层灰纱"。"""
    return ft.Colors.with_opacity(alpha, ft.Colors.ON_SURFACE)


def elevation(level: int = 1) -> ft.BoxShadow:
    """按档位取阴影。``level`` 越高层数越高，超界夹到最近的一档。"""
    blur, dy, alpha = _ELEVATION[min(max(level, 0), max(ELEVATION))]
    if level <= 0:
        return ft.BoxShadow(blur_radius=0, spread_radius=0, color=ft.Colors.TRANSPARENT)
    return ft.BoxShadow(
        blur_radius=blur,
        spread_radius=0,
        color=ft.Colors.with_opacity(alpha, ft.Colors.SHADOW),
        offset=ft.Offset(0, dy),
    )


def focus_border(width: float = 2.0) -> ft.BorderSide:
    """聚焦描边（键盘 Tab 走焦用）。用主色 + 2px，与 Material 规范一致。"""
    return ft.BorderSide(width, ft.Colors.PRIMARY)


def hairline() -> ft.BorderSide:
    """1px 分隔线。走 ``OUTLINE_VARIANT`` 而不是固定灰 —— 这是"统一风格"里
    最容易被忽略、但明暗主题下最刺眼的一处。"""
    return ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
