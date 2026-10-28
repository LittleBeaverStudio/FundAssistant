# 小河狸资金助手 · 本机 Skill API

基础地址由软件运行端口决定，通常是 `http://127.0.0.1:8865/api/skill`；端口被占用时软件会自动顺延到后续端口。优先用 `scripts/fund_assistant_client.py` 自动发现，或设置 `FUND_ASSISTANT_BASE_URL`。

所有接口返回 `{"success": true, "data": ...}`；失败时返回 `{"success": false, "error": "中文原因"}` 并带 HTTP 状态码。

**访问范围**：仅本机，或持有 `view` / `collect` 只读令牌的调用方。`edit` 令牌不用于 Skill 读取。令牌只放行其授权公司范围内的数据。

---

## GET /api/skill/health

无需令牌，用于端口发现。

| 字段 | 说明 |
| --- | --- |
| `service` | 固定 `fund-assistant`，用来确认「这是资金助手，不是同端口的其他程序」 |
| `app` / `version` | 软件名与版本号 |
| `skill_api` | 当前 Skill API 的完整地址 |
| `permission` | 本次请求的权限（本机为 `edit`） |

## GET /api/skill/info

返回应用名、版本、模块清单、可用导出端点、标注写入端点（`/api/annotations`）以及 `collect` 令牌的写权限说明。

## GET /api/skill/companies

返回组织列表：`id`、`name`、`tax_id`。`company_id` 在其他接口中即取这里的 `id`。

## GET /api/skill/bank/summary

参数：`company_id`（可重复）、`months`（1–36，默认 12）。

```json
{
  "accounts": [
    {"id": 1, "bank_name": "中国银行", "account_no": "337661881270",
     "account_name": "北京埃诺登科技有限公司", "currency": "人民币",
     "opening_balance": 0.0, "last_balance": 27581.99, "last_txn_date": "2026-09-21"}
  ],
  "monthly": [
    {"month": "2026-09", "income": 7621.0, "expense": 7620.83, "count": 3}
  ],
  "totals": {"count": 8783, "income": 213377683.31, "expense": 211000000.0}
}
```

- `accounts[].last_balance`：该账户最新一笔流水的「交易后余额」（余额水位），**不受月份参数影响**。
- `monthly`：按自然月聚合，升序返回，最多 `months` 个月。
- `totals`：全量（不按月份截断）的笔数与收付合计。

## GET /api/skill/bank/accounts

参数：`company_id`。返回账户清单（`id`、`bank_name`、`account_no`、`account_name`、`currency`、`opening_balance`、`last_balance`、`last_txn_date`）。

## GET /api/skill/bank/statements

参数：`company_id`、`direction`（`in` / `out`）、`page`（默认 1）、`page_size`（默认 100，最大 500）。

返回分页流水，按日期倒序：

```json
{
  "rows": [
    {"id": 8533, "account_id": 9, "txn_date": "2026-09-21", "txn_time": "04:28:08",
     "direction": "out", "amount": 7620.83, "balance_after": 27581.99,
     "counterparty_name": "北京埃诺登科技有限公司", "counterparty_account": "",
     "counterparty_bank": "", "summary": "", "purpose": "",
     "txn_ref": "", "receipt_ref": "", "no_invoice": 0}
  ],
  "page": 1, "page_size": 100, "total": 8783, "pages": 88
}
```

- `direction`：`in`＝收入，`out`＝支出。
- `amount` 恒为正数，方向看 `direction`。
- `balance_after` 可能为空（该行未解析到余额）。
- `no_invoice = 1` 表示用户已手工标记「无票业务」。

## GET /api/skill/pay-links

参数：`company_id`、`page`、`page_size`（默认 500，最大 1000）。

按 `invoice_key` 聚合的票款核销结果，只含已确认关联：

```json
{
  "rows": [
    {"invoice_key": "91110000...\u001f开具\u001f25112000000209453504\u001f",
     "invoice_number": "25112000000209453504", "direction": "开具",
     "paid_amount": 350.0, "paid_count": 1, "last_paid_at": "2026-10-15 15:00:35"}
  ],
  "page": 1, "page_size": 500, "total": 1234, "pages": 3
}
```

- `invoice_key` 与发票索引镜像同构（`税号 \x1f 方向 \x1f 发票号码 \x1f 数电号`），可直接与合同助手的 `node_invoice_links` 对接。
- `paid_amount` 是该发票已关联流水的金额合计；分次收付时 `paid_count > 1` 属正常。

## GET /api/skill/parties

参数：`company_id`、`page`、`page_size`（默认 500，最大 1000）。

网银往来单位聚合，只出名字与统计，**不出流水明细**：

```json
{
  "rows": [
    {"party_name": "北京埃诺登科技有限公司", "txn_count": 128,
     "in_amount": 1234567.89, "out_amount": 765432.1,
     "first_txn_date": "2024-06-26", "last_txn_date": "2026-09-21"}
  ],
  "page": 1, "page_size": 500, "total": 210, "pages": 1
}
```

按最近往来时间倒序。

---

## 写接口（仅 `collect` 令牌可用，且只写标注）

`POST /api/annotations` —— 往标注表插入一条待办/说明，不触碰流水、账户与关联数据。

请求体：`title`（必填）、`detail`、`severity`（`info` / `warning` / `critical`）、`rule_code`、`ref_type`（如 `statement`）、`ref_id`、`period_key`、`source`（`cfo`）。

`POST /api/annotations/{id}` —— 更新标注状态：`status` 取 `open` / `resolved` / `dismissed`（本机或 `edit` 令牌）。
