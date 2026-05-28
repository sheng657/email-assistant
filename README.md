# 📧 Email Assistant — 智能邮件助手

一款基于纯 Python 标准库的智能邮件处理工具。通过 IMAP 协议连接邮箱，自动完成邮件分类、摘要生成、回复草稿撰写和待办事项提取，帮助你高效管理收件箱。

零依赖、零配置、开箱即用。

---

## ✨ 功能特性

### 🔍 快速预览（headers 模式）

几秒钟拉取所有未读邮件的标题、发件人和时间，不下载正文，速度极快。适合每天快速扫一眼有没有重要邮件。

### 📊 智能 7 级分类

每封邮件自动归类到 7 个优先级，帮你一眼看出哪些需要立即处理：

| 级别 | 标识 | 说明 | 示例 |
|------|------|------|------|
| 🔴 安全告警 | `security_alert` | API Key 泄露、账户异常登录、安全通知 | "您的 GitHub Token 已被泄露" |
| 🟠 紧急 | `urgent` | VIP 联系人、含截止日期、明确催促 | "请在周五前提交报告" |
| 🟡 待回复 | `needs_reply` | 对方问了问题、请求确认、需要决策 | "你对这个方案有什么意见？" |
| 🟢 仅阅读 | `info_only` | 通知类、CC 抄送、公告、系统通知 | "GitHub Actions 运行完成" |
| 🔘 验证码 | `verification` | 各类验证码邮件（已过期可跳过） | "您的验证码是 123456" |
| 📰 自发送 | `self_sent` | 发件人是自己的邮件（定时任务推送等） | 自动化脚本的定时报告 |
| ⚫ 垃圾邮件 | `spam` | 退订链接为主、营销内容、可疑发件人 | 各种促销广告 |

### 📝 自动摘要

为每封邮件生成一句话中文摘要，不用打开就能了解邮件内容。摘要基于发件人、主题和正文关键信息综合生成。

### 💬 回复草稿

对待回复类邮件，自动生成 3 种风格的回复草稿供你选择：

- **正式风格**：适合商务邮件、客户沟通
- **简洁风格**：适合同事之间快速回复
- **友好风格**：适合朋友、熟人之间的轻松回复

### ⏰ 待办事项提取

自动识别邮件中的截止日期和待办事项，提取为结构化列表。支持识别"请在 X 日前完成"、"deadline"等表述。

### 🔒 安全告警检测

自动识别以下安全风险：

- API Key / Access Token 泄露通知
- 账户异常登录告警
- 可疑活动通知
- 密码修改确认

发现安全告警后立即置顶提醒，不遗漏任何安全事件。

### 🎯 智能降级拉取

- 邮箱有未读邮件时 → 优先拉取未读
- 没有未读邮件时 → 自动降级为拉取最近 30 天的全部邮件
- 无任何邮件时 → 返回"收件箱已清空"提示

### 📊 可视化报告

处理完成后生成 ASCII 仪表盘风格的报告，包含：

- 邮件总数和各分类数量
- 优先级排序列表
- 待回复邮件标记
- 安全告警高亮

---

## 🚀 快速开始

### 环境要求

- **Python 3.9+**（仅需标准库，无需安装任何第三方包）
- 能访问 IMAP 服务器的网络连接
- 支持系统：Linux / macOS / Windows / WSL

### 一键检测

```bash
# 下载项目
git clone git@github.com:sheng657/email-assistant.git
cd email-assistant

# 运行环境检测脚本
bash setup.sh
```

`setup.sh` 会自动检测：

- ✅ Python 版本是否满足要求（3.9+）
- ✅ 网络连接是否正常
- ✅ 环境变量是否已设置
- ✅ IMAP 服务器是否可达

### 手动配置

```bash
# 1. 设置邮箱授权码（QQ邮箱示例）
export EMAIL_PASSWORD='你的16位授权码'

# 2. 测试连接（拉取1封邮件验证）
python3 scripts/fetch_emails.py --account 你的邮箱@qq.com --mode headers --max 1
```

> ⚠️ 重要：`EMAIL_PASSWORD` 填写的是邮箱的**授权码**，不是登录密码！
> 各邮箱授权码获取方式见下方「各邮箱授权码获取」章节。

---

## 📖 详细用法

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--account` | 邮箱地址 | 必填 |
| `--mode` | 拉取模式：`headers`（信封）、`body`（正文）、`full`（完整） | `headers` |
| `--max` | 最多拉取的邮件数量 | 20 |
| `--all` | 拉取所有邮件（忽略 `--max`） | false |
| `--since` | 拉取最近 N 天的邮件（如 `7d`、`30d`） | 无 |
| `--body-uid` | 指定拉取某封邮件的正文（配合 `--mode body` 使用） | 无 |

### 三种拉取模式

#### 1️⃣ headers 模式（推荐日常使用）

只拉取邮件的标题、发件人、时间等元信息，不下载正文。速度最快，适合每天快速查看。

```bash
# 查看最多 50 封未读邮件
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --max 50

# 没有未读时，自动拉取最近 30 天全部邮件
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --all --since 30d
```

#### 2️⃣ body 模式（按需查看正文）

指定某封邮件的 UID，只拉取该封邮件的完整正文。适合对感兴趣的邮件深入阅读。

```bash
# 先用 headers 模式查看邮件列表，找到感兴趣的 UID
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --max 20

# 再用 body 模式拉取指定邮件的正文
python3 scripts/fetch_emails.py --account xxx@qq.com --mode body --body-uid 152
```

#### 3️⃣ full 模式（批量完整处理）

同时拉取邮件元信息和正文，适用于需要批量分析或生成回复草稿的场景。建议数量 ≤ 15 封，否则耗时较长。

```bash
# 完整处理最近 15 封邮件（含分类、摘要、回复草稿、待办提取）
python3 scripts/fetch_emails.py --account xxx@qq.com --mode full --max 15
```

### 实际使用场景

#### 场景 1：每天早上快速扫邮件

```bash
# 30秒看完所有未读邮件的分类和摘要
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --max 50
```

#### 场景 2：检查安全告警

```bash
# 拉取最近 7 天邮件，重点关注安全告警
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --all --since 7d
```

#### 场景 3：批量生成回复

```bash
# 处理待回复邮件，自动生成 3 种风格的回复草稿
python3 scripts/fetch_emails.py --account xxx@qq.com --mode full --max 15
```

#### 场景 4：WSL 环境下使用

```bash
# WSL 中同样可以直接运行
export EMAIL_PASSWORD='你的授权码'
python3 scripts/fetch_emails.py --account xxx@qq.com --mode headers --max 20
```

---

## 📋 各邮箱授权码获取

| 邮箱 | 设置路径 | 说明 |
|------|----------|------|
| **QQ 邮箱** | 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务 → 开启 IMAP → 生成授权码 | 16 位，含大写字母 |
| **Gmail** | Google 账户 → 安全性 → 两步验证 → 应用专用密码 | 需先开启两步验证 |
| **163 / 126** | 设置 → POP3/SMTP/IMAP → 开启 IMAP → 客户端授权码 | 需手机验证 |
| **Outlook / Hotmail** | Outlook 设置 → 同步电子邮件 → 开启应用密码 | 需先开启两步验证 |

### IMAP 服务器地址（自动检测）

脚本会根据邮箱后缀自动选择 IMAP 服务器，一般无需手动设置：

| 邮箱后缀 | IMAP 服务器 | 端口 |
|----------|-------------|------|
| `@qq.com` | `imap.qq.com` | 993 |
| `@gmail.com` | `imap.gmail.com` | 993 |
| `@163.com` | `imap.163.com` | 993 |
| `@126.com` | `imap.126.com` | 993 |
| `@outlook.com` | `outlook.office365.com` | 993 |
| `@hotmail.com` | `outlook.office365.com` | 993 |

---

## 📁 项目结构

```
email-assistant/
├── README.md                   # 项目说明（本文档）
├── SKILL.md                    # AI 助手技能说明文档
├── setup.sh                    # 一键环境检测与安装脚本
├── scripts/
│   └── fetch_emails.py         # 核心脚本：IMAP 邮件拉取与分类
├── assets/
│   ├── email-template.md       # 处理报告的 Markdown 模板
│   └── reply-templates.md      # 三种回复风格的模板
└── references/
    ├── api-reference.md        # IMAP 协议与认证参考文档
    └── best-practices.md       # 分类规范与隐私保护建议
```

### 各文件说明

- **`scripts/fetch_emails.py`** — 核心脚本，负责 IMAP 连接、邮件拉取、7 级分类、摘要生成、回复草稿、待办提取
- **`setup.sh`** — 环境检测脚本，检查 Python 版本、网络、环境变量
- **`assets/email-template.md`** — 生成邮件处理报告时使用的 Markdown 模板
- **`assets/reply-templates.md`** — 正式 / 简洁 / 友好三种回复风格的模板
- **`references/api-reference.md`** — IMAP 协议细节、各邮箱服务器地址、认证方式参考
- **`references/best-practices.md`** — 邮件分类标准详细说明、隐私保护和数据安全建议

---

## 🔧 环境变量

| 变量 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `EMAIL_PASSWORD` | ✅ 是 | 邮箱密码或授权码 | `abcdefghijklmnop` |
| `EMAIL_IMAP_HOST` | ❌ 否 | IMAP 服务器地址（自动检测时可不设） | `imap.qq.com` |
| `EMAIL_IMAP_PORT` | ❌ 否 | IMAP 端口（默认 993） | `993` |

> 💡 建议将环境变量写入 `~/.bashrc` 或 `~/.zshrc`，避免每次都要手动设置：
> ```bash
> echo "export EMAIL_PASSWORD='你的授权码'" >> ~/.bashrc
> source ~/.bashrc
> ```

---

## ⚠️ 常见问题

### 1. 连接超时

**原因**：网络不通或防火墙拦截了 IMAP 端口（993）。

**解决**：
```bash
# 测试 IMAP 服务器是否可达
openssl s_client -connect imap.qq.com:993

# 如果超时，检查防火墙或尝试更换网络
```

### 2. 登录失败 (AUTHENTICATIONFAILED)

**原因**：使用了登录密码而非授权码。

**解决**：去邮箱设置中生成授权码（见「各邮箱授权码获取」章节），用授权码替换密码。

### 3. Python 版本过低

**原因**：Python < 3.9，缺少部分标准库功能。

**解决**：
```bash
# Ubuntu/Debian
sudo apt install python3.11

# macOS
brew install python@3.11

# 或使用 pyenv 安装指定版本
pyenv install 3.11
```

### 4. WSL 环境不稳定

**原因**：WSL 中 SSL 端口可能有兼容问题。

**解决**：
```bash
# 尝试降低超时时间
export EMAIL_IMAP_TIMEOUT=10

# 或在 WSL 中使用代理
export https_proxy=http://127.0.0.1:7890
```

### 5. 中文乱码

**原因**：部分邮件使用了非 UTF-8 编码。

**解决**：脚本已内置 GB2312/GBK/GB18030 自动解码，如仍有乱码请提 Issue。

### 6. 邮件数量为 0

**原因**：所有邮件已读，或邮箱为空。

**解决**：脚本会自动降级拉取最近 30 天的全部邮件（包括已读），用 `--since` 参数调整时间范围。

---

## 🛡️ 隐私与安全

- 所有数据处理均在本地完成，**不会上传任何邮件内容到外部服务器**
- 授权码通过环境变量传入，**不会写入代码或配置文件**
- 建议定期轮换授权码，降低泄露风险
- 脚本不会删除或修改邮箱中的任何邮件，只做只读操作

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到远程 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 License

MIT License

Copyright (c) 2025 sheng657
