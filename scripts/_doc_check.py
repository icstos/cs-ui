"""组件文档（``SPEC``）体检：结构 + 登记一致性 + 真实渲染。

三件事：

1. **登记一致** —— 每个组件都能从实现模块里拿到属于自己的 ``SPEC``
   （共模块的用 ``SPECS`` 字典），且 ``key`` / ``group`` / ``source`` 与
   :mod:`ui.core.catalog` 一致。
2. **结构完整** —— 定义 / 组件构成 / 何时使用 / 示例 / API / 备注都写够了，
   页面排版依赖这些段落存在。
3. **渲染自检** —— 把 ``ui.core.doc.page(SPEC)`` 真渲染一遍，抓构建期异常
   （组件树里抛的错在 flet 里不会冒泡到调用方，只能靠这一步发现）。

用法::

    python scripts/_doc_check.py                       # 全部组件
    python scripts/_doc_check.py --group form          # 只查一个分类
    python scripts/_doc_check.py src/ui/input/input.py # 只查指定文件
    python scripts/_doc_check.py --no-render           # 只做静态校验

退出码：0 = 全部通过；1 = 有失败。
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.core import catalog
from ui.core import doc as doc_kit

#: 结构下限：低于这个数就算"内容单薄"，写出来是提醒而不是失败（``--strict`` 才拦）。
LIMITS = {
    "definition": 40,  # 定义至少 40 字
    "anatomy": 2,  # 组件构成至少 2 条
    "when": 2,
    "avoid": 2,
    "examples": 2,
    "api": 4,
    "notes": 1,
}

FAIL: list[str] = []
WARN: list[str] = []


def _module_name(path: Path) -> str:
    rel = path.resolve().relative_to(ROOT / "src")
    return ".".join(rel.with_suffix("").parts)


def check_structure(label: str, spec: doc_kit.Spec, *, strict: bool) -> None:
    problems: list[str] = []
    if not spec.name:
        problems.append("name 为空")
    if not spec.summary:
        problems.append("summary 为空")
    if len(spec.definition) < LIMITS["definition"]:
        problems.append(f"definition 仅 {len(spec.definition)} 字")
    if len(spec.anatomy) < LIMITS["anatomy"]:
        problems.append(f"anatomy 仅 {len(spec.anatomy)} 条")
    if len(spec.when) < LIMITS["when"]:
        problems.append(f"when 仅 {len(spec.when)} 条")
    if len(spec.avoid) < LIMITS["avoid"]:
        problems.append(f"avoid 仅 {len(spec.avoid)} 条")
    if len(spec.examples) < LIMITS["examples"]:
        problems.append(f"examples 仅 {len(spec.examples)} 个")
    if len(spec.rows) < LIMITS["api"]:
        problems.append(f"api 仅 {len(spec.rows)} 行")
    if len(spec.notes_norm) < LIMITS["notes"]:
        problems.append(f"notes 仅 {len(spec.notes_norm)} 条")
    if problems:
        (FAIL if strict else WARN).append(f"{label}: " + "；".join(problems))


def collect(items: list[catalog.Entry]) -> list[tuple[str, doc_kit.Spec]]:
    """按目录条目取说明，顺手做登记一致性校验。"""
    modules: dict[str, object] = {}
    out: list[tuple[str, doc_kit.Spec]] = []

    for item in items:
        try:
            module = modules.setdefault(
                item.module, importlib.import_module(item.module)
            )
        except Exception as exc:  # noqa: BLE001
            FAIL.append(f"{item.key}: 导入失败 {type(exc).__name__}: {exc}")
            continue

        raw = catalog._spec_from(module, item)  # noqa: SLF001 - 同仓工具，故意复用
        if raw is None:
            shared = len({e.module for e in catalog.ENTRIES.values() if e.module == item.module})
            hint = "（同文件多组件，请用 SPECS 字典）" if shared > 1 else ""
            FAIL.append(f"{item.key}: 模块里没有属于它的 SPEC{hint}")
            continue

        spec = raw.bound(
            key=item.key, group=catalog.GROUP_OF[item.key], source=item.file
        )
        if spec.key != item.key:
            FAIL.append(f"{item.key}: Spec.key={spec.key!r} 与目录键不一致")
        out.append((item.key, spec))

    return out


async def render_all(page: ft.Page, specs: list[tuple[str, doc_kit.Spec]]) -> None:
    """在一个隐藏窗口里逐个渲染，收集构建期异常。"""
    for key, spec in specs:
        try:
            page.render(lambda s=spec: doc_kit.page(s))
            page.update()
            await asyncio.sleep(0.45)
        except Exception as exc:  # noqa: BLE001
            FAIL.append(f"{key}: 渲染失败 {type(exc).__name__}: {exc}")
            traceback.print_exception(type(exc), exc, exc.__traceback__)


def main() -> None:
    parser = argparse.ArgumentParser(description="SPEC 体检")
    parser.add_argument("paths", nargs="*", help="实现文件路径；留空 = 全部组件")
    parser.add_argument("--group", default="", help="只查某个分类键")
    parser.add_argument("--strict", action="store_true", help="结构缺项也算失败")
    parser.add_argument("--no-render", action="store_true", help="只做静态校验")
    args = parser.parse_args()

    if args.paths:
        # 一个文件可能登记了多个组件（``display/text.py`` 有 7 个），
        # 所以按文件展开成"该模块对应的全部条目"，而不是只认文件名那一个。
        modules = set()
        for raw in args.paths:
            module = _module_name(Path(raw))
            modules.add(module)
            if not any(e.module == module for e in catalog.ENTRIES.values()):
                FAIL.append(f"{module}: 不在 ui.core.catalog 的登记模块里")
        items = [
            item
            for item in catalog.ENTRIES.values()
            if item.module in modules and not item.hidden
        ]
    else:
        items = [
            item
            for item in catalog.ENTRIES.values()
            if not item.hidden
            and (not args.group or catalog.GROUP_OF[item.key] == args.group)
        ]

    specs = collect(list(items))
    for key, spec in specs:
        check_structure(key, spec, strict=args.strict)

    if args.no_render or not specs:
        _report(len(specs))
        return

    def _run(page: ft.Page) -> None:
        page.run_task(_job, page)

    async def _job(page: ft.Page) -> None:
        await render_all(page, specs)
        try:
            await page.window.close()
        except Exception:  # noqa: BLE001, S110 - 关窗失败不影响结论
            pass
        _report(len(specs))

    ft.run(_run, view=ft.AppView.FLET_APP_HIDDEN)


def _report(total: int) -> None:
    print(f"\n{'=' * 66}", file=sys.stderr)
    print(f"DOC CHECK: specs={total} fail={len(FAIL)} warn={len(WARN)}", file=sys.stderr)
    for item in FAIL:
        print(f"  FAIL  {item}", file=sys.stderr)
    for item in WARN:
        print(f"  warn  {item}", file=sys.stderr)
    print(f"{'=' * 66}\n", file=sys.stderr)
    sys.stderr.flush()
    os._exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
