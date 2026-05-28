---
name: email-assistant
description: 自动分类邮件、写摘要、生成回复草稿、提取待办事项
version: 2.2.0
tags: [email, triage, summarization, reply, productivity]
---

# Email Assistant — 邮件助手

## Quick Start（新用户首次使用）

### 环境要求
- Python 3.9 或更高版本（标准库即可，无需安装第三方包）
- 能访问 IMAP 服务器的网络（如 imap.qq.com:993）

### 一键检测
```bash
bash ~/.hermes/skills/email/email-assistant/setup.sh
```
脚本会自动检测 Python 版本、创建虚拟环境、验证脚本可运行。如果 Python 版本不够，会给出各平台的安装命令。

### 手动配置
```bash
# 设置环境变量（QQ邮箱示例）
export EMAIL_PASSWORD='你的16位授权码'

# 测试连接（1封邮件，headers模式，几秒完成）
python3 scripts/fetch_emails.py --account 你的邮箱@qq.com --mode headers --max 1
```

### 各邮箱授权码获取方式
| 邮箱 | 设置路径 | 说明 |
|------|----------|------|
| QQ邮箱 | 设置 → 账户 → IMAP/SMTP → 开启 → 生成授权码 | 16位，含大写字母 |
| Gmail | Google账户 → 安全性 → 两步验证 → 应用专用密码 | 需先开启两步验证 |
| 163/126 | 设置 → POP3/SMTP/IMAP → 开启IMAP → 客户端授权码 | 需手机验证 |

## When to Use

Use when the user says "帮我处理邮件", "看看有什么重要邮件", "生成邮件回复", "邮件分类", "邮件摘要", "查邮件", or asks to triage/summarize/respond to emails in any form.

## Quick Reference

| 项目 | 说明 |
|------|------|
| 脚本 | `scripts/fetch_emails.py` — IMAP 读取未读邮件 |
| 模板 | `assets/email-template.md` — 处理报告模板 |
| 回复模板 | `assets/reply-templates.md` — 三种回复风格 |
| 参考 | `reference/api-reference.md` — 协议与认证说明 |
| 规范 | `reference/best-practices.md` — 分类与隐私规范 |
| 依赖 | Python 3.9+, `imaplib`(标准库) |

**输入参数**

| 参数 | 类型 | 必需 | 默认 | 说明 |
|------|------|------|------|------|
| `email_account` | string | 是 | — | 邮箱地址 |
| `email_type` | enum | 否 | `imap` | `imap` / `gmail` / `exchange` |
| `max_emails` | int | 否 | `20` | 最大处理邮件数 |
| `since_date` | string | 否 | 今天 | 起始日期，YYYY-MM-DD |
| `sync_calendar` | bool | 否 | `false` | 是否提取 deadline 同步日历 |

**输出格式**：结构化 Markdown 报告，见 `assets/email-template.md`

**脚本运行模式**

| 模式 | 命令 | 耗时 | 用途 |
|------|------|------|------|
| `headers` | `--mode headers` | 2-5秒 | 快速预览所有未读邮件标题 |
| `full` | `--mode full` | 10-60秒 | 拉取完整正文+分类 |
| `body` | `--mode body --body-uid 152` | 1-2秒 | 拉取单封邮件正文 |

## Procedure

### Step 1: 快速预览（headers 模式）

**动作**：先用 headers 模式快速获取所有未读邮件的标题列表。

```bash
python scripts/fetch_emails.py \
  --account {{email_account}} \
  --type {{email_type}} \
  --mode headers \
  --max 50
```

**环境变量**（运行前必须设置）：
- `EMAIL_PASSWORD` — 邮箱密码或应用专用密码（IMAP/Gmail）
- `EMAIL_IMAP_HOST` — IMAP 服务器地址（自动检测时可不设）
- `EMAIL_IMAP_PORT` — IMAP 端口（默认 993）

**成功标准**：脚本返回 JSON 数组，每项含 `uid`、`from`、`subject`、`date`、`quick_category` 字段。
**失败处理**：连接失败→检查网络和环境变量；返回空数组→执行 **Step 1b 降级拉取**。

### Step 1b: 无未读邮件时降级拉取最近30天邮件

**触发条件**：Step 1 返回空数组（0封未读邮件）。

**动作**：用 `--all --since 30d` 拉取最近30天的全部邮件。

```bash
python scripts/fetch_emails.py \
  --account {{email_account}} \
  --type {{email_type}} \
  --mode headers \
  --all \
  --since 30d \
  --max 50
```

**输出格式**：告知用户"该邮箱没有未读邮件，以下为最近30天的邮件分类"，然后进入标准分类流程（Step 3）。

**说明**：
- 这种情况下跳过 Step 2（用户确认范围），直接全量分类
- `--all` 表示搜索全部邮件（不仅是未读），`--since 30d` 表示最近30天
- `--since` 支持相对时间（`30d`/`7d`）和绝对日期（`2026-05-01`）
- 如果30天内也无邮件，输出"该邮箱最近30天没有任何邮件"

### Step 2: 用户确认处理范围

**动作**：展示 headers 概览后，询问用户：
- 是否全部处理？（默认 yes）
- 是否只处理某些类别的邮件？
- 是否需要拉取正文做详细分类？

**注意**：如果通过 Step 1b 降级进入，跳过此步，直接处理全部邮件。

### Step 3: 邮件分类

**动作**：根据 `quick_category`（脚本自动标注）和正文内容（如有），按以下规则分类：

| 级别 | 标识 | 判断依据 |
|------|------|----------|
| 🔴 安全告警 | `security_alert` | API Key泄露、账户异常、安全通知、服务挂起 |
| 🟠 紧急 | `urgent` | 发件人为VIP/包含deadline/明确催促 |
| 🟡 待回复 | `needs_reply` | 邮件问了问题/请求确认/需决策 |
| 🟢 仅阅读 | `info_only` | 通知类/CC抄送/公告/订阅/系统通知 |
| 🔘 验证码 | `verification` | 验证码邮件（均已过期可跳过） |
| 📰 自发送 | `self_sent` | 发件人是自己（定时任务推送等） |
| ⚫ 垃圾邮件 | `spam` | 退订链接为主/营销内容/可疑发件人 |

**详细判断标准**见 `reference/best-practices.md`。

**成功标准**：每封邮件有且仅有一个分类标签。
**失败处理**：无法判断时默认归为 🟢 仅阅读。

### Step 4: 按需拉取正文

**动作**：对需要详细处理的邮件（安全告警、待回复、紧急），用 body 模式逐封拉取正文：

```bash
python scripts/fetch_emails.py \
  --account {{email_account}} \
  --mode body \
  --body-uid {{uid}}
```

**成功标准**：返回完整正文。
**失败处理**：拉取失败则仅用头部信息分类。

### Step 5: 生成摘要

**动作**：为每封非垃圾/非验证码邮件生成 1 句话中文摘要。

**摘要规则**：
- 不超过 40 个汉字
- 包含：谁 + 什么事 + 关键信息
- 敏感信息（薪资/合同/身份证号）脱敏处理
- 垃圾邮件和验证码直接跳过，不生成摘要

**成功标准**：每封邮件有独立中文摘要。
**失败处理**：HTML 解析失败时降级为纯文本提取。

### Step 6: 生成回复草稿

**动作**：对 🟡 待回复 邮件，按 `assets/reply-templates.md` 生成 3 个回复选项。

三个选项：
1. **正式版** — 商务正式语气，适合对外/上级
2. **简洁版** — 直接了当，适合同事/日常
3. **追问版** — 提出跟进问题，适合信息不足时

**安全约束**：生成后展示给用户，**自动发送前必须获得用户明确确认**。

**成功标准**：每封待回复邮件有 3 个风格选项。
**失败处理**：邮件内容无法理解时跳过回复生成，标注"内容较复杂，建议人工处理"。

### Step 7: 提取 Deadline 和待办

**动作**：扫描所有邮件正则提取日期和待办事项。

**提取规则**：
- 日期模式：`YYYY-MM-DD`、`MM月DD日`、`下周五`、`月底前`、`asap`
- 待办关键词：`请`、`请确认`、`需要`、`务必`、`回复`、`提交`、`完成`
- 安全告警类邮件自动标注"建议立即处理"
- 若 `sync_calendar=true`，标注"需要同步日历"标记

**成功标准**：列表格式输出 deadline 和待办，含来源邮件引用。
**失败处理**：无 deadline 则输出"暂未发现明确截止日期"。

### Step 8: 输出结构化报告

**动作**：按 `assets/email-template.md` 模板生成最终报告。

**报告结构**（按视觉优先级排列）：

1. **📊 总览仪表盘** — 顶部 ASCII 表格，一目了然看到各类邮件数量和占比
2. **⚡ 需要立即行动** — 按严重程度从高到低排列，每封邮件包含：
   - 完整发件人信息（姓名+邮箱）
   - 时间 + 相对时间（如"2小时前"）
   - 来源平台识别（GitHub/GitGuardian/Zilliz 等）
   - 分类标签徽章（emoji + 文字）
   - 附件信息（有无+文件名）
   - 内容摘要（引用块格式，清晰醒目）
   - 截止日期（如有）
   - 需要做的事（列表）
   - 回复草稿（3种风格，待回复邮件）
   - 风险等级 + 建议操作（安全告警邮件）
3. **📋 其他邮件一览** — 用表格汇总仅阅读/自发送/垃圾/验证码，节省篇幅
4. **📌 待办事项汇总** — 表格形式，含优先级徽章
5. **📅 日历提醒** — 表格形式
6. **🎯 建议操作清单** — 按优先级排序，带严重程度图标

**输出规则**：
- 每封需要行动的邮件，**摘要必须包含具体信息**（如 API Key 名称、账户名、具体金额等），不能只有笼统描述
- 垃圾邮件和验证码只用表格汇总，**不展开详情**
- 如果某分类为空，显示"暂无"而非跳过
- 建议操作清单必须给出**可执行的具体操作**，不能是泛泛建议
- 安全告警必须标注**风险等级**（高/中/低）和**具体建议操作**（如"立即轮换 xxx API Key"）

**成功标准**：报告完整、格式规范、无遗漏邮件、每封需要行动的邮件有具体可操作信息。

## Pitfalls

### 1. Gmail 应用专用密码 ≠ 登录密码
Gmail 默认禁用 IMAP 明文登录。必须开启"两步验证"后生成应用专用密码。直接用 Gmail 登录密码连接会报 `AUTHENTICATIONFAILED`。

### 2. QQ邮箱授权码是16位，注意大小写
QQ邮箱的授权码（非QQ登录密码）在 设置→账户→IMAP/SMTP服务 中生成。授权码16位，通常含大写字母。复制时务必完整。

### 3. full 模式拉取大量邮件会超时
IMAP 逐封拉取 RFC822 全文，20封以上可能超过60秒。解决策略：
- **先用 `--mode headers` 快速预览**（2-5秒）
- **再用 `--mode body --body-uid N` 逐封拉取感兴趣的邮件**
- `--mode full` 仅用于 `--max <= 15` 的场景

### 4. WSL 环境下 IMAP 连接可能不稳定
WSL 的网络栈与 Windows 共享，某些 SSL 端口连接可能超时。如果脚本卡住：
- 检查是否设置了 `EMAIL_PASSWORD` 环境变量
- 用 `openssl s_client -connect imap.qq.com:993` 测试网络连通性
- 尝试先拉取1封测试：`--max 1 --mode headers`

### 5. 密码泄露风险
绝对不要在对话中明文展示 `EMAIL_PASSWORD`。使用环境变量传递，脚本从 `os.environ` 读取。若用户不小心在对话中粘贴了密码，立即提醒并建议更换。

### 6. 验证码邮件全部已过期
大多数验证码邮件的有效期仅5-15分钟。处理邮件时，验证码类邮件统一跳过，不生成摘要和回复，直接标记为"已过期/可忽略"。

### 7. 自发送邮件（发件人=自己）
定时任务（如每日新闻推送）会发送到自己的邮箱。这类邮件标记为"自发送"，仅摘要不回复。

### 8. 安全告警必须优先处理
GitHub/GitGuardian/Zilliz 等平台的安全告警（API Key泄露、账户异常）必须标注为🔴紧急，建议用户立即处理。

## Verification

完成处理后，逐项自检：

- [ ] 所有邮件均已分类（无遗漏）
- [ ] 安全告警类邮件已标注为🔴紧急
- [ ] 每封非垃圾/非验证码邮件有中文摘要
- [ ] 待回复邮件均有 3 个回复选项
- [ ] Deadline 和待办已提取并列表展示
- [ ] 敏感信息已脱敏
- [ ] 报告格式符合模板
- [ ] 未在任何地方明文展示密码/Token
- [ ] 回复草稿未自动发送（等待用户确认）
