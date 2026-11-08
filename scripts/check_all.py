"""一条命令跑完全部回归（静态门禁 + 一致性审计 + 逻辑测试 + 文档/注册表校验）。

为什么需要它：框架里这些检查各自都是对的，**但没人记得全跑一遍**。
漏跑一次的代价很具体 —— ``color_picker`` 里一个未定义的令牌名
（``size=ICON_SIZE["lg"]``）就活过了一整天：写在函数体里，import 不报错，
只有真的切到禁用态才抛 NameError，而示例页恰好都不走那条分支。
一条命令跑完，才能让"我改完顺手验一下"变成零决策成本。

分三档，按改动范围选：

===================  ==========================================  ==========
档位                 内容                                        大致耗时
===================  ==========================================  ==========
``static``           ruff：未定义名 / 重复定义 / 无用局部变量      快
``audit``            设计令牌一致性审计（8 条规则）                快
``logic``            19 个纯逻辑测试（无需窗口）                   中
``docs``             组件文档规格 + 导出注册表                     中
``all``（默认）      以上全部                                      中
``visual``           真机截图 + 灰块检测（**需要桌面，不进 all**）   数分钟
===================  ==========================================  ==========

用法::

    python scripts/check_all.py                 # 全部（不含真机截图）
    python scripts/check_all.py --stage fast    # 只跑 static + audit（改样式时够用）
    python scripts/check_all.py --stage visual  # 真机截图校验（会开窗口）
    python scripts/check_all.py -k pagination   # 只跑名字里含 pagination 的项
    python scripts/check_all.py --verbose       # 失败时打印完整输出
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


@dataclass(frozen=True)
class Stage:
    """一项检查。``key`` 用于 ``-k`` 过滤，``tier`` 决定 -stage 选哪几档。"""

    key: str
    title: str
    argv: tuple[str, ...]
    tier: str  # "fast" | "logic" | "docs"
    timeout: int = 300


def _logic_tests() -> list[Stage]:
    """把 scripts/_*_logic.py 全部收进来 —— 命名约定即注册表。

    新写一个逻辑测试不需要改这里，丢进目录就会被跑到（也就不会被忘掉）。
    """
    return [
        Stage(
            key=path.stem,
            title=path.stem.removeprefix("_").removesuffix("_logic").replace("_", " "),
            argv=(sys.executable, str(path)),
            tier="logic",
        )
        for path in sorted(SCRIPTS.glob("_*_logic.py"))
    ]


def stages() -> list[Stage]:
    return [
        Stage(
            key="ruff",
            title="静态门禁（未定义名 / 重复定义 / 无用局部变量）",
            argv=(
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select",
                "F821,F811,F841",
                "--no-cache",
                str(ROOT / "src"),
                str(ROOT / "scripts"),
            ),
            tier="fast",
            timeout=180,
        ),
        Stage(
            key="audit",
            title="令牌一致性审计（8 条规则）",
            argv=(sys.executable, str(SCRIPTS / "audit_consistency.py"), "--check"),
            tier="fast",
            timeout=180,
        ),
        *_logic_tests(),
        Stage(
            key="docs",
            title="组件文档规格（SPEC / 示例 / API）",
            argv=(sys.executable, str(SCRIPTS / "_doc_check.py")),
            tier="docs",
            timeout=300,
        ),
        Stage(
            key="registry",
            title="导出注册表（ui.__all__ 与 _registry 对齐）",
            argv=(sys.executable, str(SCRIPTS / "gen_ui_registry.py"), "--check"),
            tier="docs",
            timeout=180,
        ),
        Stage(
            key="i18n-catalogs",
            title="站点三语语言包（651 键 × 3 语言）",
            argv=(sys.executable, str(SCRIPTS / "build_docs_i18n.py"), "--check"),
            tier="docs",
            timeout=180,
        ),
        Stage(
            key="visual",
            title="真机截图（13 页灰块检测）",
            argv=(sys.executable, "-u", str(SCRIPTS / "_visual_check.py")),
            tier="visual",
            timeout=900,
        ),
    ]


def run(stage: Stage) -> tuple[bool, float, str]:
    """跑一项，返回 (是否通过, 秒, 输出)。超时也算失败但不算崩溃。"""
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            list(stage.argv),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=stage.timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return False, time.perf_counter() - started, f"超时（>{stage.timeout}s）"
    except OSError as exc:
        return False, time.perf_counter() - started, f"无法启动：{exc}"
    output = f"{proc.stdout}\n{proc.stderr}".strip()
    return proc.returncode == 0, time.perf_counter() - started, output


def _display_width(text: str) -> int:
    """终端显示宽度：CJK 字符占两列，``str.ljust`` 按字符数补空格会错位。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def main() -> int:
    parser = argparse.ArgumentParser(description="跑完全部回归检查")
    parser.add_argument(
        "--stage",
        choices=("all", "fast", "logic", "docs", "visual"),
        default="all",
        help="all=全部（不含真机截图）；fast=静态门禁+审计；logic=只跑逻辑测试；"
        "docs=文档/注册表；visual=真机截图",
    )
    parser.add_argument("-k", "--filter", default="", help="只跑名字含该子串的项")
    parser.add_argument("--verbose", action="store_true", help="失败时打印完整输出")
    args = parser.parse_args()

    selected: list[Stage]
    if args.stage == "all":
        # 真机截图要开窗口、跑几分钟，默认不放进日常回归
        selected = [s for s in stages() if s.tier != "visual"]
    elif args.stage == "fast":
        selected = [s for s in stages() if s.tier == "fast"]
    elif args.stage == "logic":
        selected = [s for s in stages() if s.tier == "logic"]
    elif args.stage == "visual":
        selected = [s for s in stages() if s.tier == "visual"]
    else:
        selected = [s for s in stages() if s.tier in ("docs", "fast")]

    if args.filter:
        selected = [s for s in selected if args.filter.lower() in s.key.lower()]

    if not selected:
        print("没有匹配的检查项。")
        return 1

    width = max(_display_width(s.title) for s in selected)
    failures: list[tuple[Stage, str]] = []
    started = time.perf_counter()

    for stage in selected:
        ok, seconds, output = run(stage)
        mark = "OK  " if ok else "FAIL"
        print(f"[{mark}] {_pad(stage.title, width)}  {seconds * 1000:7.0f}ms", flush=True)
        if not ok:
            failures.append((stage, output))

    total = time.perf_counter() - started
    print()
    if not failures:
        print(f"全部通过 ✓  {len(selected)} 项 / {total:.1f}s")
        return 0

    print(f"{len(failures)} 项失败（共 {len(selected)} 项 / {total:.1f}s）：")
    for stage, output in failures:
        print(f"\n--- {stage.title}  [{stage.key}] ---")
        lines = output.splitlines()
        shown = lines if args.verbose else lines[-25:]
        for line in shown:
            print(f"    {line}")
        if not args.verbose and len(lines) > len(shown):
            print(f"    …（前 {len(lines) - len(shown)} 行已省略，加 --verbose 看全部）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
