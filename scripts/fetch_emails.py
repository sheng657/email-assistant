#!/usr/bin/env python3
"""
Email Fetcher v2.0 — 从 IMAP 邮箱读取未读邮件

用法:
    # 快速模式：只拉取头部（几秒完成，适合大量邮件）
    python fetch_emails.py --account user@qq.com --mode headers

    # 完整模式：拉取头部+正文（较慢，建议 --max <= 20）
    python fetch_emails.py --account user@qq.com --mode full --max 20

    # 指定正文模式：拉取头部后，再拉取指定 UID 的正文
    python fetch_emails.py --account user@qq.com --mode body --body-uid 152

环境变量:
    EMAIL_PASSWORD    邮箱密码或应用专用密码（必需）
    EMAIL_IMAP_HOST   IMAP 服务器地址（imap 类型自动检测时可不设）
    EMAIL_IMAP_PORT   IMAP 端口（默认 993）

输出:
    JSON 数组，每项包含: uid, from, to, subject, date, body, has_attachments, deadlines

依赖:
    Python 3.9+ 标准库（imaplib, email, json, argparse, os, re, socket, ssl）
"""

import imaplib
import email
from email.message import Message
from email.header import decode_header
from email.utils import parsedate_to_datetime
import json
import argparse
import os
import re
import sys
import socket
from datetime import datetime, timedelta

# 版本检测
if sys.version_info < (3, 9):
    print(json.dumps([{
        "error": "version_check_failed",
        "message": f"当前 Python 版本 {sys.version} 过低，需要 3.9+\n"
                   "安装方法：\n"
                   "  Ubuntu/Debian: sudo apt install python3.9\n"
                   "  macOS: brew install python@3.9\n"
                   "  Windows: 下载 https://www.python.org/downloads/\n"
                   "  WSL: sudo apt update && sudo apt install python3.9",
        "current_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "required_version": "3.9"
    }]), ensure_ascii=False)
    sys.exit(1)


# ===== 常量 =====

IMAP_HOSTS = {
    "qq": "imap.qq.com",
    "163": "imap.163.com",
    "126": "imap.126.com",
    "gmail": "imap.gmail.com",
    "outlook": "outlook.office365.com",
    "exchange": "outlook.office365.com",
}

IMAP_PORT = 993
CONNECT_TIMEOUT = 10  # 连接超时秒数
COMMAND_TIMEOUT = 15  # 单条命令超时秒数

# deadline 正则模式
DEADLINE_PATTERNS = [
    r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',                           # 2026-05-28
    r'(\d{1,2}月\d{1,2}[日号])',                                  # 5月28日
    r'(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',                          # 28.05.2026
    r'((?:下|这|本)(?:周|星期)[一二三四五六日天])',                 # 下周一
    r'((?:明天|今日|今天|后天|大后天))',                           # 明天
    r'(月底前|月底|月初|年末|年底前)',                              # 月底前
    r'((?:请|务必|需要).{0,10}(?:之前|以前|前|内|完成|提交|回复|确认))',
    r'(ASAP|asap|尽快|加急)',
]

# 安全/运维告警关键词
SECURITY_KEYWORDS = [
    "exposed", "leak", "secret", "token", "api key", "password", "credential",
    "安全", "泄露", "告警", "alert", "warning", "suspended", "挂起",
    "unauthorized", "breach", "suspicious", "异常登录",
]

# 垃圾邮件/营销关键词
SPAM_KEYWORDS = [
    "unsubscribe", "退订", "取消订阅", "marketing", "promotion", "优惠",
    "折扣", "限时", "免费领取", "earn rewards", "积分兑换",
]


def detect_host(account: str, email_type: str) -> str:
    """根据邮箱地址或类型推断 IMAP 主机"""
    domain = account.split("@")[-1].lower() if "@" in account else ""
    if email_type in IMAP_HOSTS:
        return IMAP_HOSTS[email_type]
    for key, host in IMAP_HOSTS.items():
        if key in domain:
            return host
    return os.environ.get("EMAIL_IMAP_HOST", "")


def decode_mime_header(header_value: str) -> str:
    """解码 MIME 编码的邮件头"""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def html_to_text(html: str) -> str:
    """HTML 转纯文本，保留基本结构"""
    if not html:
        return ""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(p|div|tr|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<(p|div|tr|li|h[1-6])[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_body(msg: Message) -> str:
    """从邮件消息中提取正文"""
    body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode(charset, errors="replace")
    else:
        content_type = msg.get_content_type()
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload:
            raw = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                html_body = raw
            else:
                body = raw
    if body.strip():
        return body.strip()
    if html_body:
        return html_to_text(html_body)
    return ""


def extract_deadlines(text: str) -> list:
    """从文本中提取 deadline 日期"""
    deadlines = []
    for pattern in DEADLINE_PATTERNS:
        matches = re.findall(pattern, text)
        deadlines.extend(matches)
    return list(dict.fromkeys(deadlines))


def check_attachments(msg: Message) -> bool:
    """检查邮件是否包含附件"""
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                return True
    return False


def classify_email(subject: str, body: str, from_addr: str) -> str:
    """快速分类邮件，返回类别标识"""
    text = (subject + " " + body[:500]).lower()
    # 安全告警优先
    for kw in SECURITY_KEYWORDS:
        if kw.lower() in text:
            return "security_alert"
    # 垃圾邮件
    for kw in SPAM_KEYWORDS:
        if kw.lower() in text:
            return "spam"
    # 验证码邮件
    if re.search(r'(验证码|verif|code.*\d{4,6})', text):
        return "verification"
    return "normal"


def connect_imap(host: str, port: int, account: str, password: str):
    """连接 IMAP 服务器并登录"""
    try:
        conn = imaplib.IMAP4_SSL(host, port)
    except socket.timeout:
        raise ConnectionError(f"连接 {host}:{port} 超时（{CONNECT_TIMEOUT}秒），请检查网络")
    except Exception as e:
        raise ConnectionError(f"连接 {host}:{port} 失败: {e}")
    try:
        conn.login(account, password)
    except imaplib.IMAP4.error as e:
        conn.logout()
        raise PermissionError(f"登录失败: {e}，请检查密码或应用专用密码")
    return conn


def fetch_headers(conn, search_str: str, max_emails: int) -> list:
    """快速模式：只拉取邮件头"""
    status, data = conn.search(None, search_str)
    if status != "OK" or not data[0]:
        return []

    msg_ids = data[0].split()[:max_emails]
    results = []
    for mid in msg_ids:
        try:
            s, d = conn.fetch(mid, "(BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
            if d[0] and d[0][1]:
                raw = d[0][1].decode("utf-8", errors="replace")
                msg = email.message_from_string(raw)
                from_addr = decode_mime_header(msg.get("From", ""))
                to_addr = decode_mime_header(msg.get("To", ""))
                subject = decode_mime_header(msg.get("Subject", ""))
                date_str = msg.get("Date", "")
                try:
                    dt = parsedate_to_datetime(date_str)
                    date_fmt = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_fmt = date_str[:16] if date_str else ""

                quick_cat = classify_email(subject, "", from_addr)
                results.append({
                    "uid": mid.decode(),
                    "from": from_addr.strip(),
                    "to": to_addr.strip(),
                    "subject": subject.strip(),
                    "date": date_fmt,
                    "body": "",
                    "has_attachments": False,
                    "deadlines": [],
                    "quick_category": quick_cat,
                })
        except Exception:
            continue
    return results


def fetch_full(conn, msg_id: bytes) -> dict | None:
    """完整模式：拉取单封邮件的 RFC822"""
    try:
        status, msg_data = conn.fetch(msg_id, "(RFC822)")
        if status != "OK" or not msg_data[0]:
            return None
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        body = extract_body(msg)
        return {
            "uid": msg_id.decode(),
            "from": decode_mime_header(msg.get("From", "")),
            "to": decode_mime_header(msg.get("To", "")),
            "subject": decode_mime_header(msg.get("Subject", "")),
            "date": msg.get("Date", ""),
            "body": body,
            "has_attachments": check_attachments(msg),
            "deadlines": extract_deadlines(body),
        }
    except Exception:
        return None


def fetch_emails(account: str, email_type: str, max_emails: int,
                 since_date: str, mode: str, body_uid: str = None,
                 fetch_all: bool = False) -> list:
    """主函数"""
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        print(json.dumps({"error": "缺少 EMAIL_PASSWORD 环境变量"}))
        sys.exit(1)

    host = detect_host(account, email_type)
    if not host:
        print(json.dumps({"error": f"无法推断 IMAP 主机，请设置 EMAIL_IMAP_HOST 或指定 --type"}))
        sys.exit(1)

    port = int(os.environ.get("EMAIL_IMAP_PORT", IMAP_PORT))

    try:
        conn = connect_imap(host, port, account, password)
    except (ConnectionError, PermissionError) as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    conn.select("INBOX")

    search_criteria = [] if fetch_all else ["UNSEEN"]
    if since_date:
        # 支持相对时间如 30d/7d
        if re.match(r'^\d+d$', since_date):
            days = int(since_date[:-1])
            dt = datetime.now() - timedelta(days=days)
        else:
            dt = datetime.strptime(since_date, "%Y-%m-%d")
        imap_date = dt.strftime("%d-%b-%Y")
        search_criteria.append(f'SINCE {imap_date}')
    if not search_criteria:
        search_criteria = ["ALL"]
    search_str = f'({" ".join(search_criteria)})' if len(search_criteria) > 1 else search_criteria[0]

    if mode == "body" and body_uid:
        # 单封正文模式：先搜索找到对应邮件，然后拉正文
        item = fetch_full(conn, body_uid.encode())
        conn.logout()
        print(json.dumps([item] if item else [], ensure_ascii=False, indent=2))
        return

    if mode == "headers":
        results = fetch_headers(conn, search_str, max_emails)
    else:
        # full 模式：搜索后逐封拉取
        status, data = conn.search(None, search_str)
        if status != "OK" or not data[0]:
            conn.logout()
            print(json.dumps([]))
            return
        msg_ids = data[0].split()[:max_emails]
        results = []
        for mid in msg_ids:
            item = fetch_full(conn, mid)
            if item:
                item["quick_category"] = classify_email(item["subject"], item["body"], item["from"])
                results.append(item)

    conn.logout()
    print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="从 IMAP 邮箱读取未读邮件")
    parser.add_argument("--account", required=True, help="邮箱地址")
    parser.add_argument("--type", default="imap", choices=["imap", "gmail", "exchange"], help="邮箱类型")
    parser.add_argument("--max", type=int, default=20, help="最大处理数量")
    parser.add_argument("--since", default="", help="起始日期 YYYY-MM-DD 或相对时间如 30d/7d")
    parser.add_argument("--all", action="store_true", help="搜索全部邮件（不仅是未读），需配合 --since 使用")
    parser.add_argument("--mode", default="full", choices=["headers", "full", "body"],
                        help="headers=快速仅头部, full=完整拉取, body=拉取指定邮件正文")
    parser.add_argument("--body-uid", default="", help="--mode body 时指定邮件 UID")
    args = parser.parse_args()

    fetch_emails(args.account, args.type, args.max, args.since, args.mode, args.body_uid, args.all)


if __name__ == "__main__":
    main()
