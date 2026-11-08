"""一致性审计：把「整齐」这件事变成可执行的检查。

为什么需要这个脚本
------------------
设计令牌的价值取决于**执行率**。写完 ``tokens.py`` 之后，框架里仍然可以随手
写 ``size=15``、``border_radius=7``、``color="#6B7280"`` —— 代码能跑、界面能看，
只是全框架悄悄有了十几种字号和五种悬停灰度。这类漂移**靠人眼 review 挡不住**：
它单点看都对，只有横向摆在一起才刺眼。

本脚本用 AST 而不是正则：正则分不清 ``Text(size=15)`` 与 ``Icon(size=15)``
（前者是排版错误，后者是图标刻度错误），也分不清 ``bgcolor=Colors.WHITE``
（深色主题下会瞎）与 ``color=Colors.WHITE``（压在深色实底上，正确）。

八条规则
--------
============  ==========================================================
裸色值        组件里出现 ``"#RRGGBB"``
字号           ``Text(size=N)`` 的 N 不在 ``FONT_SIZE`` 里
图标尺寸       ``Icon(size=N)`` 的 N 不在 ``ICON_SIZE`` 里
图标借字号     ``Icon(size=FONT_SIZE[...])`` —— 走了令牌但借错刻度
圆角           ``border_radius=N`` 的 N 不在 ``RADIUS`` 里
奇数留白       ``spacing`` / ``padding`` / ``height`` 出现奇数
              （框架按 2px 步进排版，奇数不可能是刻意设计）
文字色误用     ``Text(color=Colors.OUTLINE)`` —— outline 是边框角色，
              次要文字应为 ``ON_SURFACE_VARIANT``
暗色隐患       ``bgcolor=Colors.WHITE / BLACK / GREY_*``
============  ==========================================================

用法::

    python scripts/audit_consistency.py              # 报告
    python scripts/audit_consistency.py --check      # 有违规则退出码 1
    python scripts/audit_consistency.py --rule 字号   # 只看一条规则
    python scripts/audit_consistency.py --json out.json

已知盲区（有意留白，不是忘写）
------------------------------
只认 ``Text(size=N)`` 里的**字面量**。写成模块级常量就绕过去了::

    TEXT_SIZE = 13        # 审计看不见，但正文早就不是 13 了
    ...
    ft.Text(..., size=TEXT_SIZE)

这类常量靠 ``scripts/_tokens_logic.py`` 的「同源引用」一节守：它逐个断言
``cascader.ITEM_SIZE`` / ``multi_select.TEXT_SIZE`` / ``panel_field`` 三档等都
**赋自** ``FONT_SIZE``。要新增组件字号常量，就往那张表里加一行 —— 比让审计
去猜"哪个 SIZE 是字号、哪个是图片边长"可靠得多。
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ui.core.tokens import FONT_SIZE, ICON_SIZE, RADIUS

# ---------------------------------------------------------------------------
# 豁免表：**每一条都要写清理由**，否则"白名单"会变成"别管它"。
#
# 键是相对 src/ui 的路径；值是允许的规则集合（"*" 表示整份文件豁免）。
# ---------------------------------------------------------------------------
ALLOW: dict[str, set[str]] = {
    # 调色板的数据本体就是色值，没有"令牌化"的意义。
    "input/color_picker.py": {"裸色值", "暗色隐患"},
    # ↑ 暗色隐患豁免理由：色条上的拖拽滑块的**必须**是固定的白色 ——
    #   它要压在任意色相上（从纯黑到纯白都能被拖到），换成主题角色就会
    #   在某一段色相上彻底看不见。这是"刻意不跟随主题"的正当场合。
    # 图表配色是数据可视化取值，不跟随界面主题的语义色。
    "chart/_data.py": {"裸色值"},
    "display/heatmap.py": {"裸色值"},  # 热力图色阶
    # 示例代码块里的展示尺寸（大号数字、结果页巨字）本来就是一次性的。
    "display/number_animation.py": {"字号"},
}

#: 允许的"非令牌"字号：只在示例里出现的展示型数字。
_EXTRA_FONT_SIZE: frozenset[int] = frozenset({90})

#: 允许的"非令牌"图标尺寸：图表/媒体预览里的超大图标。
_EXTRA_ICON_SIZE: frozenset[int] = frozenset({36, 40, 48})

#: 暗色主题下会失效的硬编码底色。
_DARK_HOSTILE = ("WHITE", "BLACK", "GREY_")

#: 走 2px 步进时允许的偶数留白（4px 网格以下的紧凑间距）。
_RULES = (
    "裸色值",
    "字号",
    "图标尺寸",
    "图标借字号",
    "圆角",
    "奇数留白",
    "文字色误用",
    "暗色隐患",
)


@dataclass(frozen=True)
class Violation:
    """一条违规。``line`` 是从 1 开始的源码行号。"""

    rule: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}  [{self.rule}] {self.message}"


# ---------------------------------------------------------------------------
# AST 辅助
# ---------------------------------------------------------------------------
def _call_name(node: ast.Call) -> str:
    """``ft.Icon(...)`` → ``Icon``；``Icon(...)`` → ``Icon``。"""
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _kwarg(node: ast.Call, name: str) -> ast.expr | None:
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _int_of(node: ast.expr | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    return None


def _color_member(node: ast.expr | None) -> str | None:
    """``ft.Colors.WHITE`` → ``"WHITE"``；其余返回 ``None``。"""
    if not isinstance(node, ast.Attribute) or not isinstance(node.value, ast.Attribute):
        return None
    if node.value.attr != "Colors":
        return None
    return node.attr


def _mentions(node: ast.expr, name: str) -> bool:
    """表达式里是否**引用**了某个模块级名字（``FONT_SIZE["body"]`` 算，``"FONT_SIZE"`` 不算）。

    用来抓"数字被常量包起来"的违规 —— ``Icon(size=FONT_SIZE["body"])`` 的 size
    不是字面量，按值比对的那几条规则全都看不见它。
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id == name:
            return True
    return False


def _padding_ints(node: ast.expr) -> Iterator[int]:
    """收集 ``Padding.*(...)`` / ``Margin.*(...)`` 里的整数字面量。"""
    if not isinstance(node, ast.Call):
        return
    if _call_name(node) not in ("all", "only", "symmetric"):
        return
    for arg in node.args:
        v = _int_of(arg)
        if v is not None:
            yield v
    for kw in node.keywords:
        v = _int_of(kw.value)
        if v is not None:
            yield v


# ---------------------------------------------------------------------------
# 规则实现：每个函数产出一批 Violation
# ---------------------------------------------------------------------------
def _named_color_constants(tree: ast.Module) -> set[int]:
    """收集「具名色板」里的色值节点 id。

    规则不是"禁止十六进制"，而是**禁止匿名的十六进制**。给色值起个名字写进
    模块常量（``_CODE_BG = "#0E1117"``）意味着"这是刻意的"，评审时看得见；
    随手写在参数里（``bgcolor="#0E1117"``）则是漂移的开始 —— 同样的颜色第二
    次出现时会被再抄一遍，改的时候只改一处。

    判定条件：模块级 ``NAME = "..."``，且名字全大写（含数字/下划线）。
    """
    allowed: set[int] = set()
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        else:
            continue
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names or not all(n.isupper() or n.replace("_", "").isalnum() for n in names):
            continue
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.Constant)
                and isinstance(sub.value, str)
                and sub.value.startswith("#")
            ):
                allowed.add(id(sub))
    return allowed


def _audit_module(path: Path, rel: str, allowed: set[str]) -> list[Violation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    out: list[Violation] = []
    named_colors = _named_color_constants(tree)

    def add(rule: str, node: ast.AST, message: str) -> None:
        if rule in allowed:
            return
        out.append(Violation(rule, rel, getattr(node, "lineno", 0), message))

    font_values = set(FONT_SIZE.values())
    icon_values = set(ICON_SIZE.values())
    radius_values = set(RADIUS.values())

    for node in ast.walk(tree):
        # ---- 裸色值 ----------------------------------------------------
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) in (4, 5, 7, 9) and s.startswith("#") and id(node) not in named_colors:
                add("裸色值", node, f'"{s}" 应改用令牌、ft.Colors 角色，或提取为具名常量')

        if not isinstance(node, ast.Call):
            continue

        callee = _call_name(node)

        # ---- 字号 ------------------------------------------------------
        if callee in ("Text", "TextField", "TextButton"):
            v = _int_of(_kwarg(node, "size"))
            if v is not None and v not in font_values and v not in _EXTRA_FONT_SIZE:
                add("字号", node, f"{callee}(size={v}) 不在 FONT_SIZE 刻度内 {sorted(font_values)}")

        # ---- 图标尺寸 --------------------------------------------------
        if callee in ("Icon", "IconButton"):
            v = _int_of(_kwarg(node, "size"))
            if v is not None and v not in icon_values and v not in _EXTRA_ICON_SIZE:
                add("图标尺寸", node, f"{callee}(size={v}) 不在 ICON_SIZE 刻度内 {sorted(icon_values)}")

        # ---- 图标借字号 ------------------------------------------------
        # ``Icon(size=FONT_SIZE["body"])`` 看起来"走了令牌"，其实借错了刻度：
        # 字号一改图标跟着动，两个本来独立的设计维度被绑死。数字被常量包起来时
        # 上面那条规则看不见，所以这里专门认表达式里的 FONT_SIZE。
        if callee in ("Icon", "IconButton"):
            for key in ("size", "icon_size"):
                arg = _kwarg(node, key)
                if arg is not None and _mentions(arg, "FONT_SIZE"):
                    add("图标借字号", node, f"{callee}({key}=FONT_SIZE[...]) 应改用 ICON_SIZE")

        # ---- 圆角 ------------------------------------------------------
        v = _int_of(_kwarg(node, "border_radius"))
        if v is not None and v not in radius_values:
            add("圆角", node, f"border_radius={v} 不在 RADIUS 刻度内 {sorted(radius_values)}")

        # ---- 奇数留白 --------------------------------------------------
        # 只查"节奏类"数值（间隙、内边距）。width / height 是几何尺寸，
        # 3px 的标记点、15px 的细条都是正当的，不该报。
        for key in ("spacing", "run_spacing"):
            v = _int_of(_kwarg(node, key))
            if v is not None and v > 1 and v % 2 == 1:
                add("奇数留白", node, f"{callee}({key}={v}) 是奇数，2px 步进下不可能是刻意设计")
        for key in ("padding", "margin"):
            arg = _kwarg(node, key)
            if arg is None:
                continue
            for v in _padding_ints(arg):
                if v > 1 and v % 2 == 1:
                    add("奇数留白", node, f"{callee}({key}) 含奇数 {v}")

        # ---- 文字色误用 ------------------------------------------------
        if callee == "Text" and _color_member(_kwarg(node, "color")) == "OUTLINE":
            add("文字色误用", node, "OUTLINE 是边框角色，次要文字应用 ON_SURFACE_VARIANT")

        # ---- 暗色隐患 --------------------------------------------------
        member = _color_member(_kwarg(node, "bgcolor"))
        if member and member.startswith(_DARK_HOSTILE):
            add("暗色隐患", node, f"bgcolor=Colors.{member} 在深色主题下会失效")

    return out


def audit(*, rules: Iterable[str] | None = None) -> list[Violation]:
    """扫描 ``src/ui`` 下所有组件模块，返回违规清单（按文件、行号排序）。"""
    wanted = set(rules) if rules else set(_RULES)
    found: list[Violation] = []
    for path in sorted(SRC.joinpath("ui").rglob("*.py")):
        rel = path.relative_to(SRC / "ui").as_posix()
        # 令牌与主题的定义处本来就是"字面量该出现的地方"
        if rel in ("core/tokens.py", "core/theme.py", "core/empty.py"):
            continue
        allowed = ALLOW.get(rel, set())
        if "*" in allowed:
            continue
        found.extend(v for v in _audit_module(path, rel, allowed) if v.rule in wanted)
    return sorted(found, key=lambda v: (v.path, v.line, v.rule))


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------
def report(violations: list[Violation]) -> str:
    lines: list[str] = []
    by_rule: dict[str, list[Violation]] = {r: [] for r in _RULES}
    for v in violations:
        by_rule.setdefault(v.rule, []).append(v)

    for rule in _RULES:
        items = by_rule.get(rule) or []
        if not items:
            continue
        lines.append(f"\n── {rule}（{len(items)}）")
        for v in items[:14]:
            lines.append(f"   {v}")
        if len(items) > 14:
            lines.append(f"   … 另有 {len(items) - 14} 处")

    total = len(violations)
    head = f"一致性审计：{total} 处违规" if total else "一致性审计：全部通过 ✓"
    return "\n".join([head, *lines])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="扫描 UI 框架的一致性违规")
    parser.add_argument("--check", action="store_true", help="有违规时以退出码 1 结束")
    parser.add_argument("--rule", action="append", choices=_RULES, help="只检查指定规则")
    parser.add_argument("--json", type=Path, help="把结果写成 JSON")
    args = parser.parse_args(argv)

    violations = audit(rules=args.rule)
    print(report(violations))

    if args.json:
        args.json.write_text(
            json.dumps([asdict(v) for v in violations], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n已写入 {args.json}")

    return 1 if (args.check and violations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
