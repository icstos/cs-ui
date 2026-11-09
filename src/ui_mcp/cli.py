"""命令行：``ui-mcp [serve|build|check|guide]``。

没有子命令时默认 ``serve`` —— 这样 MCP 客户端配置里直接写
``{"command": "ui-mcp"}`` 就能用，和 ``flet mcp`` 的手感一致。

    ui-mcp                                  # stdio 服务（给 MCP 客户端）
    ui-mcp build                            # 重建索引（改了 src/ui 之后）
    ui-mcp build --root D:/Projects/cs-ui   # 指定仓库根
    ui-mcp serve --transport http --port 8000
    ui-mcp check                            # 索引是否过期 + 统计
    ui-mcp guide overview                   # 终端里直接看经验条款
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ui_mcp import paths
from ui_mcp.__about__ import __pkg_name__, __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ui-mcp",
        description="cs-ui 组件库的 MCP 服务 / 索引构建工具",
    )
    parser.add_argument("--version", action="version", version=f"{__pkg_name__} {__version__}")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="启动 MCP 服务（默认子命令）")
    serve.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http", "streamable-http", "sse"],
        help="传输方式，默认 stdio",
    )
    serve.add_argument("--host", default="127.0.0.1", help="HTTP 监听地址")
    serve.add_argument("--port", type=int, default=8000, help="HTTP 端口")
    serve.add_argument("--quiet", action="store_true", help="不打印 banner")

    build = sub.add_parser("build", help="重建 API / 示例 / 文档索引")
    build.add_argument("--root", type=Path, default=None, help="cs-ui 仓库根目录")
    build.add_argument("--no-examples", action="store_true", help="跳过 examples")
    build.add_argument("--no-docs", action="store_true", help="跳过 Markdown 文档")
    build.add_argument("--quiet", action="store_true", help="只输出错误")

    check = sub.add_parser("check", help="检查索引新鲜度与统计")
    check.add_argument("--root", type=Path, default=None)

    guide = sub.add_parser("guide", help="在终端查看经验条款")
    guide.add_argument("topic", nargs="?", default=None)
    return parser


def _serve(args: argparse.Namespace) -> int:
    from ui_mcp.server import mcp

    kwargs = {}
    if args.transport in ("http", "streamable-http", "sse"):
        kwargs = {"host": args.host, "port": args.port}
    mcp.run(transport=args.transport, show_banner=not args.quiet, **kwargs)
    return 0


def _build(args: argparse.Namespace) -> int:
    from ui_mcp.build import build

    try:
        summary = build(
            root=args.root,
            with_examples=not args.no_examples,
            with_docs=not args.no_docs,
        )
    except RuntimeError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2

    meta = summary["meta"]
    counts = meta.get("counts", {})
    if not args.quiet:
        print(f"✓ 索引已生成 → {paths.data_dir()}")
        print(f"  组件 {counts.get('components', 0)} / 数据类 {counts.get('types', 0)}"
              f" / 函数 {counts.get('functions', 0)} / 枚举 {counts.get('enums', 0)}"
              f" / 常量 {counts.get('constants', 0)}"
              f" / 外部祖先 {counts.get('ancestors', 0)}")
        if "examples" in summary:
            print(f"  示例 {summary['examples']} 段（{summary['usage_components']} 个组件有真实用法）")
        if "docs" in summary:
            print(f"  文档 {summary['docs']} 段")
        for name, size in summary["files"].items():
            print(f"  {name:<14} {size / 1024:6.1f} KB")
    return 0


def _check(args: argparse.Namespace) -> int:
    from ui_mcp.build import staleness
    from ui_mcp.store import api_store

    meta = api_store.meta
    if "error" in meta:
        print(f"✗ {meta['error']}", file=sys.stderr)
        return 2
    status = staleness(args.root)
    counts = meta.get("counts", {})
    print(f"{__pkg_name__} {__version__} | ui {meta.get('version')} | flet {meta.get('flet')}")
    print(f"索引时间：{meta.get('generated_at')}　模块 {meta.get('modules')} 个")
    print(f"条目：{counts}")
    versions = status.get("versions") or {}
    if versions:
        runtime = versions.get("runtime") or {}
        print(
            "版本：索引 ui {0} / flet {1}　运行 ui {2} / flet {3}".format(
                (versions.get("index") or {}).get("ui", "?"),
                (versions.get("index") or {}).get("flet", "?"),
                runtime.get("ui") or "?",
                runtime.get("flet") or "?",
            )
        )
    print(f"新鲜度：{'✓ ' if status['ok'] else '✗ '}{status['reason']}")
    if not status["ok"] and status.get("stale_sources"):
        for name in status["stale_sources"]:
            print(f"  - {name}")
        return 1
    return 0


def _guide(args: argparse.Namespace) -> int:
    from ui_mcp import guidelines

    result = guidelines.get(args.topic)
    if "body" in result:
        print(f"# {result['title']}\n")
        print(result["body"])
        return 0
    if "topics" in result:
        for item in result["topics"]:
            print(f"{item['topic']:<18} {item['title']}  [{item['tags']}]")
        return 0
    print(result.get("error", "没有这条"), file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(argv)
    if args.command is None:
        # 没给子命令 → 默认 serve（MCP 客户端里只写 command 就能跑）
        args = parser.parse_args(["serve", *argv])
    if args.command == "serve":
        return _serve(args)
    if args.command == "build":
        return _build(args)
    if args.command == "check":
        return _check(args)
    if args.command == "guide":
        return _guide(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
