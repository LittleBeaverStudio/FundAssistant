> **许可**：本项目采用**「小河狸工作室非转售许可 1.0」**——
> 个人使用与**企业内部使用免费**（含内部办公、财务与会计处理、内部系统集成）；
> 对外销售、集成进收费产品或服务、托管 / SaaS / 代运营、以及**向第三方交付成果或提供服务，须事先取得书面授权**。
> 许可全文见 [LICENSE.md](./LICENSE.md)。商业授权：https://littlebeaver.top

![License](https://img.shields.io/github/license/LittleBeaverStudio/FundAssistant?label=license)
# 小河狸资金助手 Skill

这是给本机智能体使用的「小河狸资金助手」数据读取 Skill。它通过小河狸资金助手提供的本机只读接口，查询已导入的银行账户、收支汇总、月度趋势、流水明细、往来单位与票款核销结果。

仓库地址：

https://github.com/LittleBeaverStudio/FundAssistant

## 适用场景

- 让本机智能体回答「现在账上有多少钱」「各账户余额多少」。
- 汇总近 N 个月的收入、支出与净额，看哪个月资金最紧。
- 按对方单位、金额、日期查具体流水；统计谁在给我们打钱、哪些单位很久没往来。
- 核对某张发票收/付了几笔、还差多少没回款（票款核销）。
- 在智能体工作流里补充本地资金数据上下文，不上传流水到云端。

## 使用前提

- 已安装并打开小河狸资金助手 `v1.2.8` 或更高版本。
- 智能体与小河狸资金助手运行在同一台电脑。
- 应用默认端口 `8865`；Skill 会自动扫描 `8865-8885`，靠 `/api/skill/health` 的 `service=fund-assistant` 识别实际端口，不必手工填地址。
- 也可以用 `FUND_ASSISTANT_BASE_URL` 显式指定地址，或用 `FUND_ASSISTANT_PORTS` 指定端口范围。

## 安全说明

- 本 Skill 只访问 `127.0.0.1` 或 `localhost`。
- 只调用 `/api/skill/*`、`/api/pay-links`、`/api/parties` 等只读接口；不直接读数据库文件。
- 不支持通过智能体导入、修改、删除流水或账户。唯一例外是 `POST /api/annotations`——`collect` 令牌可以写标注（体检待办/说明），碰不到流水本身。
- 返回的银行流水属于用户本地私有数据，未经用户明确要求，不应发送给云端模型做深度分析。

## 安装

方式一（SkillHub，推荐）：

```bash
skillhub install littlebeaver-fund-assistant --dir ~/.workbuddy/skills
```

方式二（GitHub）：

```bash
git clone https://github.com/LittleBeaverStudio/FundAssistant.git \
  ~/.workbuddy/skills/littlebeaver-fund-assistant
```

也可以直接把本仓库目录放进智能体的 skills 目录。

## 命令示例

```bash
python scripts/fund_assistant_client.py info
python scripts/fund_assistant_client.py companies
python scripts/fund_assistant_client.py summary --company-id 1 --months 12
python scripts/fund_assistant_client.py accounts --company-id 1
python scripts/fund_assistant_client.py statements --company-id 1 --direction in --page-size 50
python scripts/fund_assistant_client.py pay-links --company-id 1
python scripts/fund_assistant_client.py parties --company-id 1 --page-size 100
```

接口字段说明见 [references/api.md](./references/api.md)。

## 目录结构

```
SKILL.md                          技能说明（触发条件、调用规约、写作口径）
agents/openai.yaml                界面展示名与默认提示词
references/api.md                 本机接口字段说明
scripts/fund_assistant_client.py  只读客户端（自动发现端口）
LICENSE.md                        小河狸工作室非转售许可 1.0
```
