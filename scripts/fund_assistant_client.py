#!/usr/bin/env python3
"""小河狸资金助手 · 本机 Skill API 客户端。

只调用 127.0.0.1 上的本地服务，不上传任何数据。

用法：
    python scripts/fund_assistant_client.py info
    python scripts/fund_assistant_client.py companies
    python scripts/fund_assistant_client.py summary --months 12
    python scripts/fund_assistant_client.py accounts
    python scripts/fund_assistant_client.py statements --page-size 50
    python scripts/fund_assistant_client.py pay-links
    python scripts/fund_assistant_client.py parties --page-size 100

环境变量：
    FUND_ASSISTANT_BASE_URL   指定地址，例如 http://127.0.0.1:8865
    FUND_ASSISTANT_PORTS      指定端口或端口范围，例如 8865-8885,9000
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

APP_NAME = "小河狸资金助手"
SERVICE_NAME = "fund-assistant"
DEFAULT_PORT_RANGE = range(8865, 8886)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_ports(value: str | None) -> list[int]:
    if not value:
        return list(DEFAULT_PORT_RANGE)
    ports: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            ports.extend(range(int(start), int(end) + 1))
        else:
            ports.append(int(part))
    return sorted(dict.fromkeys(ports))


def http_json(url: str, timeout: float = 2.5, method: str = "GET") -> dict[str, Any]:
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "LittleBeaverFundAssistantSkill/1.0",
        },
        method=method,
    )
    with urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.loads(resp.read().decode(charset))


def normalize_base_url(value: str) -> str:
    value = (value or "").strip().rstrip("/")
    if not value:
        raise ValueError("base_url is empty")
    if not value.startswith(("http://", "https://")):
        value = "http://" + value
    return value


def discover_base_url(base_url: str | None = None, ports: list[int] | None = None) -> str:
    """优先用显式地址；否则扫端口，靠 /api/skill/health 的 service 标识认人。"""
    if base_url:
        return normalize_base_url(base_url)
    env_base = os.environ.get("FUND_ASSISTANT_BASE_URL")
    if env_base:
        return normalize_base_url(env_base)
    env_ports = os.environ.get("FUND_ASSISTANT_PORTS")
    for port in parse_ports(env_ports):
        candidate = f"http://127.0.0.1:{port}"
        try:
            payload = http_json(f"{candidate}/api/skill/health", timeout=0.6)
        except (URLError, HTTPError, OSError, ValueError):
            continue
        if payload.get("service") == SERVICE_NAME:
            return candidate
    raise SystemExit(
        f"没找到正在运行的{APP_NAME}。请先打开软件（或设置 FUND_ASSISTANT_BASE_URL 指定地址）。"
    )


def request_skill(base_url: str, path: str, query: str = "") -> dict[str, Any]:
    url = f"{base_url}{path}" + (f"?{query}" if query else "")
    try:
        payload = http_json(url, timeout=30.0)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"接口返回 {exc.code}：{detail[:300]}")
    except URLError as exc:
        raise SystemExit(f"连接失败：{exc.reason}")
    if not payload.get("success", True):
        raise SystemExit(f"接口报错：{payload.get('error') or payload}")
    return payload


def build_query(args: argparse.Namespace, fields: list[str]) -> str:
    params: list[tuple[str, Any]] = []
    for field in fields:
        value = getattr(args, field, None)
        if value in (None, "", []):
            continue
        if isinstance(value, list):
            params.extend((field, item) for item in value)
        else:
            params.append((field, value))
    return urlencode(params)


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def add_company(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--company-id", type=int, action="append", default=[],
                        help="组织 ID，可重复传（默认全部组织）")


def add_paging(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page", type=int, default=1, help="页码，从 1 起")
    parser.add_argument("--page-size", type=int, default=100, help="每页条数（最大 500/1000）")


def main() -> int:
    root = argparse.ArgumentParser(description=f"读取本机{APP_NAME}的只读数据")
    root.add_argument("--base-url", help="软件地址，例如 http://127.0.0.1:8865")
    root.add_argument("--ports", help="端口或端口范围，例如 8865-8885,9000")
    sub = root.add_subparsers(dest="command", required=True)

    sub.add_parser("health")
    sub.add_parser("info")
    sub.add_parser("companies")

    summary = sub.add_parser("summary", help="账户余额 + 月度收付汇总")
    add_company(summary)
    summary.add_argument("--months", type=int, default=12, help="返回最近几个月（1-36）")

    accounts = sub.add_parser("accounts", help="银行账户列表")
    add_company(accounts)

    statements = sub.add_parser("statements", help="流水分页明细")
    add_company(statements)
    add_paging(statements)
    statements.add_argument("--direction", choices=["in", "out"], help="按收/付方向过滤")

    links = sub.add_parser("pay-links", help="票款核销结果（按发票聚合）")
    add_company(links)
    add_paging(links)

    parties = sub.add_parser("parties", help="往来单位聚合（笔数/收付合计/首末日期）")
    add_company(parties)
    add_paging(parties)

    args = root.parse_args()
    base_url = discover_base_url(args.base_url, parse_ports(args.ports))

    if args.command == "health":
        print_json(request_skill(base_url, "/api/skill/health"))
        return 0
    if args.command == "info":
        print_json(request_skill(base_url, "/api/skill/info"))
        return 0
    if args.command == "companies":
        print_json(request_skill(base_url, "/api/skill/companies"))
        return 0
    if args.command == "summary":
        query = build_query(args, ["company_id", "months"])
        print_json(request_skill(base_url, "/api/skill/bank/summary", query))
        return 0
    if args.command == "accounts":
        query = build_query(args, ["company_id"])
        print_json(request_skill(base_url, "/api/skill/bank/accounts", query))
        return 0
    if args.command == "statements":
        query = build_query(args, ["company_id", "direction", "page", "page_size"])
        print_json(request_skill(base_url, "/api/skill/bank/statements", query))
        return 0
    if args.command == "pay-links":
        query = build_query(args, ["company_id", "page", "page_size"])
        print_json(request_skill(base_url, "/api/skill/pay-links", query))
        return 0
    if args.command == "parties":
        query = build_query(args, ["company_id", "page", "page_size"])
        print_json(request_skill(base_url, "/api/skill/parties", query))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
