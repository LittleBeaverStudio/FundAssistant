---
name: littlebeaver-fund-assistant
description: 读取并分析本机小河狸资金助手中的数据。当用户要求连接小河狸资金助手、查询银行账户与余额、汇总收支、看月度资金趋势、查具体流水、统计往来单位、或核对票款核销（回款）情况时使用。通过应用的 localhost Skill API 在本机处理数据，不上传任何流水。
license: 小河狸非转售许可 1.0（企业内部使用免费，转售收费需授权）
slug: littlebeaver-fund-assistant
displayName: 小河狸资金助手
version: 1.0.0
summary: 读取并分析本机小河狸资金助手中的银行流水：账户余额、收支汇总与月度趋势、流水明细、往来单位、票款核销（回款）。只走 localhost 只读接口，不上传任何流水。
tags: [小河狸, 资金管理, 银行流水, 票款核销, localhost, 只读]
metadata:
  author: 小河狸工作室
  version: 1.0.0
---

## 许可与使用范围

本 Skill 采用「小河狸工作室非转售许可 1.0」，完整条款见本目录 `LICENSE.md` 文件。

- ✅ **免费使用**：
  - 个人学习、研究或个人事务；
  - **企业内部使用**——某一组织（无论是否为营利单位）为**其自身**业务运营而使用，包括内部办公、内部财务与会计处理、内部管理与报表、内部系统集成；同一控股关联实体使用视同内部使用。
- ✅ 可为上述用途自行修改本 Skill。
- ❌ **须另行取得书面授权**：对外销售、出租、许可；集成进对外收费的产品或服务；托管 / SaaS / 代运营；打包进收费课程、付费社群或付费安装包；收费的实施与咨询培训；**以及利用本 Skill 向任何第三方交付成果或提供服务**（含代理记账、为客户提供账目或报表服务等）。
- 📌 **区分标准只有一条**：**是否以本 Skill 向本组织之外的第三方交付成果或提供服务**。仅为自身业务使用 → 免费；向第三方交付或服务 → 需授权。
- 📌 再分发须保留本许可、版权声明与来源：小河狸工作室 LittleBeaverStudio · https://littlebeaver.top

**商业授权申请**：https://littlebeaver.top （邮箱 yk.niu@outlook.com）

---

# 小河狸资金助手 Skill

通过用户本机运行的「小河狸资金助手」桌面应用读取银行流水数据。确保应用与智能体运行在同一台电脑上。仅调用本机 API，不通过本 Skill 上传流水数据。

默认使用简体中文回答。金额默认按人民币格式显示并保留两位小数；使用「收入 / 支出 / 借方 / 贷方 / 交易后余额 / 票款核销 / 往来单位 / 未达账」等中国财会常用术语。除非用户明确要求，否则不要把资金流水推算结果表述为经审计结论或纳税申报依据。

## 连接应用

1. 优先使用 `scripts/fund_assistant_client.py`。
2. 用户提供地址时，传入 `--base-url http://127.0.0.1:<port>`。
3. 用户未提供地址时，扫描 `http://127.0.0.1:8865` 至 `http://127.0.0.1:8885`，通过 `/api/skill/health` 的 `service` 标识（`fund-assistant`）自动发现应用。
4. 自动发现失败时，请用户先打开「小河狸资金助手」，然后重试。

可选环境变量：

- `FUND_ASSISTANT_BASE_URL`：指定应用地址，例如 `http://127.0.0.1:8865`。
- `FUND_ASSISTANT_PORTS`：指定逗号分隔的端口或端口范围，例如 `8865-8885,9000`。

## 常用查询

在 Skill 目录中运行：

```bash
python scripts/fund_assistant_client.py info
python scripts/fund_assistant_client.py companies
python scripts/fund_assistant_client.py summary --company-id 1 --months 12
python scripts/fund_assistant_client.py accounts --company-id 1
python scripts/fund_assistant_client.py statements --company-id 1 --direction in --page-size 50
python scripts/fund_assistant_client.py pay-links --company-id 1
python scripts/fund_assistant_client.py parties --company-id 1 --page-size 100
```

处理自然语言分析请求时，先取满足问题所需的最小数据集：

- 选组织：运行 `companies`。
- 看余额、月度收付、资金趋势：运行 `summary`。
- 看开户行与账号清单：运行 `accounts`。
- 查具体流水（对方、金额、日期、余额）：运行 `statements`，按需设 `--direction`、`--page`、`--page-size`。
- 核对某张发票收/付了多少钱：运行 `pay-links`（按 `invoice_key` 聚合，只含已确认关联）。
- 看哪些单位有过往来、最近一次往来时间：运行 `parties`（只出名字与统计，不出流水明细）。

## API 规则

使用以下本机 Skill API：

- `/api/skill/health`
- `/api/skill/info`
- `/api/skill/companies`
- `/api/skill/bank/summary`
- `/api/skill/bank/accounts`
- `/api/skill/bank/statements`
- `/api/skill/pay-links`
- `/api/skill/parties`

参数约定：

- `company_id`：可重复传入，多个值取并集；令牌访问时与实际授权范围取交集。
- `months`：`summary` 返回最近几个月（1–36，默认 12）。
- `direction`：`in`（收入）或 `out`（支出）。
- `page` / `page_size`：明细分页，`statements` 每页最大 500，`pay-links` / `parties` 每页最大 1000。

金额均为人民币元、两位小数；`balance_after` 是流水发生后的账户余额。

## 写作与分析要求

回答财务问题时，明确说明所选组织、时间范围，以及数据来自哪本账（本机导入的银行流水）。

- 余额、收支合计以 `summary` 的 `totals` 为准；分账户明细以 `accounts` 的 `last_balance`（最新余额水位）为准。
- 「期末余额合计」是各账户最新余额之和，**不是**某个日期区间的净额；不要把两者混为一谈。
- 分析「钱去哪了 / 谁在付我们钱」时先读 `parties` 或 `statements` 的对方单位聚合，再按需下钻明细。
- 票款核销口径：`paid_amount` 是该发票已确认关联的流水金额合计；**一张发票可能分多次收付**，`paid_count > 1` 属正常，未完全核销不等于异常。
- 流水存在「余额断链」「疑似重复入账」等体检项时，如实说明是**待核对**提示，不要直接下结论说账错了。

需要完整字段说明时，读取 `references/api.md`。
