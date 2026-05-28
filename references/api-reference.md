# 邮件协议参考手册 v2.0

## 1. IMAP 协议（Internet Message Access Protocol）

### 连接信息

| 邮箱服务商 | IMAP 服务器 | 端口 | 加密 | 应用专用密码 |
|-----------|-------------|------|------|------------|
| QQ 邮箱 | imap.qq.com | 993 | SSL/TLS | 设置→账户→IMAP/SMTP |
| 163/126 邮箱 | imap.163.com / imap.126.com | 993 | SSL/TLS | 客户端授权码 |
| Gmail | imap.gmail.com | 993 | SSL/TLS | 两步验证→应用专用密码 |
| Outlook/Hotmail | outlook.office365.com | 993 | SSL/TLS | 同Microsoft账户密码 |
| 企业邮箱 | 由管理员提供 | 通常 993 | SSL/TLS | 联系IT获取 |

### 认证方式

```python
import imaplib

# 标准 IMAP SSL 连接
conn = imaplib.IMAP4_SSL(host, port)
conn.login(username, password)  # password 为应用专用密码

# 选择收件箱
conn.select("INBOX")

# 搜索未读邮件
status, data = conn.search(None, "UNSEED")
```

**IMAP 搜索条件**：
- `UNSEED` — 未读邮件
- `SINCE 01-Jan-2026` — 指定日期之后
- `FROM "sender@example.com"` — 特定发件人
- `SUBJECT "关键词"` — 主题包含关键词
- `OR UNSEEN (SINCE 01-Jan-2026)` — 组合条件

### 限流与最佳实践

- QQ 邮箱：每分钟最多 30 次命令
- Gmail：每天最多 2500 次 IMAP 连接
- 建议每封邮件之间间隔 0.5 秒，避免触发限流
- 用完后调用 `conn.logout()` 正确关闭连接
- 首次连接建议用 `--max 1` 测试连通性

### WSL 环境注意事项

- WSL 与 Windows 共享网络栈，SSL 端口连接可能偶尔超时
- 如果 `IMAP4_SSL` 卡住，先用 `openssl s_client -connect imap.qq.com:993` 测试
- WSL2 的 DNS 解析可能有问题，可尝试直接用 IP 地址
- 环境变量需要在当前 shell 中 export，或写入 `~/.bashrc`

---

## 2. Gmail API

### 认证方式

使用 OAuth 2.0，需要 Google Cloud Console 创建凭据。

```bash
# 安装客户端库
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 读取邮件

```python
from googleapiclient.discovery import build

service = build('gmail', 'v1', credentials=creds)

# 列出未读邮件
results = service.users().messages().list(
    userId='me',
    q='is:unread',
    maxResults=20
).execute()

messages = results.get('messages', [])

for msg in messages:
    detail = service.users().messages().get(
        userId='me', id=msg['id'], format='full'
    ).execute()
```

### Gmail 特殊搜索语法

| 语法 | 说明 |
|------|------|
| `is:unread` | 未读邮件 |
| `is:important` | 重要邮件 |
| `label: inbox` | 收件箱 |
| `newer_than:1d` | 最近 1 天 |
| `from:boss@company.com` | 特定发件人 |
| `subject:(deadline OR 截止)` | 主题关键词 |

### 限流

- 免费配额：250 单位/秒
- 每次 list 调用消耗 5 单位
- 每次 get 调用消耗 5 单位
- 超限返回 `429 Too Many Requests`

---

## 3. Microsoft Graph API（Exchange Online / Microsoft 365）

### 认证方式

OAuth 2.0 客户端凭据或授权码流程。需在 Azure AD 注册应用。

```bash
pip install msal requests
```

### 获取访问令牌

```python
import msal

app = msal.ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret,
)

result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)
access_token = result["access_token"]
```

### 读取邮件

```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}

# 获取未读邮件
response = requests.get(
    "https://graph.microsoft.com/v1.0/me/messages",
    headers=headers,
    params={
        "$filter": "isRead eq false",
        "$top": 20,
        "$orderby": "receivedDateTime desc",
        "$select": "subject,from,receivedDateTime,body,isRead,importance"
    }
)
```

### 限流

- 每 10 分钟 10000 请求（个人账户）
- 企业账户由租户配额决定
- 返回 `429` 时读取 `Retry-After` 头部等待

---

## 4. 常见错误代码

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `AUTHENTICATIONFAILED` | 密码错误或未开IMAP | 检查密码；开启IMAP服务；使用应用专用密码 |
| `TOO_MANY_REQUESTS` | 超出频率限制 | 等待 Retry-After 时间后重试 |
| `TIMEOUT` | 连接超时 | 检查网络；确认服务器地址正确；WSL下检查DNS |
| `SSL: WRONG_VERSION_NUMBER` | 端口加密方式不匹配 | 993 用 SSL，143 用 STARTTLS |
| `NOT_FOUND` | 邮箱/文件夹不存在 | 检查文件夹名称（大小写敏感） |
| `Socket timeout` | WSL网络问题 | 用 openssl 测试连通性；尝试重启 WSL 网络 |

---

## 5. 脚本使用示例

### 快速预览（推荐首选）

```bash
export EMAIL_PASSWORD="your_app_password"
python scripts/fetch_emails.py --account user@qq.com --mode headers --max 50
```

耗时：2-5秒。输出邮件标题列表，可快速判断哪些需要处理。

### 完整拉取

```bash
python scripts/fetch_emails.py --account user@qq.com --mode full --max 15
```

耗时：10-30秒。拉取完整正文，适合邮件数量较少时使用。

### 指定邮件拉取正文

```bash
python scripts/fetch_emails.py --account user@qq.com --mode body --body-uid 152
```

耗时：1-2秒。只拉取指定UID的邮件正文。

### 带日期范围

```bash
python scripts/fetch_emails.py --account user@qq.com --mode headers --since 2026-05-01 --max 30
```

只拉取 2026-05-01 之后的未读邮件。
