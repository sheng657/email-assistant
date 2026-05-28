# 📬 邮件处理报告

> **处理时间**：{{current_datetime}}　|　**邮箱**：{{email_account}}　|　**范围**：{{since_date}} ~ 今天

---

## 📊 总览仪表盘

```
┌──────────────────────────────────────────────────────┐
│  📧 邮件总数: {{total_count}}                          │
│                                                      │
│  🔴 安全告警   {{security_bar}}  {{security_count}}封 ({{security_pct}}%)     │
│  🟠 紧急       {{urgent_bar}}     {{urgent_count}}封 ({{urgent_pct}}%)     │
│  🟡 待回复     {{needs_reply_bar}}  {{needs_reply_count}}封 ({{needs_reply_pct}}%)     │
│  🟢 仅阅读     {{info_only_bar}}  {{info_only_count}}封 ({{info_only_pct}}%)     │
│  🔘 验证码     {{verification_bar}}  {{verification_count}}封 ({{verification_pct}}%)     │
│  📰 自发送     {{self_sent_bar}}   {{self_sent_count}}封 ({{self_sent_pct}}%)     │
│  ⚫ 垃圾邮件   {{spam_bar}}  {{spam_count}}封 ({{spam_pct}}%)     │
└──────────────────────────────────────────────────────┘
```

---

## ⚡ 需要立即行动

> 以下邮件需要你 **立即处理**，按严重程度从高到低排列：

{{#each priority_actions}}

### {{severity_icon}} {{subject}}

| 字段 | 内容 |
|------|------|
| **发件人** | {{from_name}} <{{from_email}}> |
| **时间** | {{date}} ({{time_ago}}) |
| **来源平台** | {{platform}} |
| **分类** | {{category_badge}} |
| **附件** | {{attachments_info}} |

**📋 内容摘要**：
> {{summary}}

{{#if deadlines}}
**⏰ 截止日期**：
{{#each deadlines}}
- {{.}}
{{/each}}
{{/if}}

{{#if action_items}}
**✅ 需要做的事**：
{{#each action_items}}
- {{.}}
{{/each}}
{{/if}}

{{#if reply_needed}}
**💬 回复选项**：

**① 正式版**：
{{reply_formal}}

**② 简洁版**：
{{reply_concise}}

**③ 追问版**：
{{reply_question}}
{{/if}}

{{#if risk_level}}
**⚠️ 风险等级**：{{risk_level}}
**🔧 建议操作**：
{{action_suggestion}}
{{/if}}

---

{{/each}}

{{#unless priority_actions}}
> ✅ 暂无需要紧急处理的邮件。

---

{{/unless}}

## 📋 其他邮件一览

### 🟢 仅阅读（{{info_only_count}}封）

> 以下邮件已阅即可，无需回复：

| # | 标题 | 发件人 | 时间 | 摘要 |
|---|------|--------|------|------|
{{#each info_only_emails}}
| {{index}} | {{subject_short}} | {{from_short}} | {{date_short}} | {{summary_short}} |
{{/each}}

{{#unless info_only_emails}}
暂无。

{{/unless}}

### 📰 自发送邮件（{{self_sent_count}}封）

> 以下为定时任务推送，已自动处理：

| # | 标题 | 时间 | 摘要 |
|---|------|------|------|
{{#each self_sent_emails}}
| {{index}} | {{subject_short}} | {{date_short}} | {{summary_short}} |
{{/each}}

{{#unless self_sent_emails}}
暂无。

{{/unless}}

### ⚫ 垃圾邮件（{{spam_count}}封）

> 以下邮件已自动过滤：

| # | 标题 | 发件人 | 时间 |
|---|------|--------|------|
{{#each spam_emails}}
| {{index}} | {{subject_short}} | {{from_short}} | {{date_short}} |
{{/each}}

{{#unless spam_emails}}
暂无。

{{/unless}}

### 🔘 验证码邮件（{{verification_count}}封）

> 共 {{verification_count}} 封验证码邮件，全部已过期，无需处理。

---

## 📌 待办事项汇总

| # | 待办事项 | 来源邮件 | Deadline | 优先级 |
|---|----------|----------|----------|--------|
{{#each todo_items}}
| {{index}} | {{action}} | {{source_short}} | {{deadline}} | {{priority_badge}} |
{{/each}}

{{#unless todo_items}}
> 暂未发现明确的待办事项。

{{/unless}}

---

## 📅 日历提醒

{{#if calendar_items}}
| 日期 | 事件 | 来源邮件 | 是否同步 |
|------|------|----------|----------|
{{#each calendar_items}}
| {{date}} | {{event_description}} | {{source_short}} | {{sync_text}} |
{{/each}}
{{else}}
> 无需同步日历的事项。

{{/if}}

---

## 🎯 建议操作清单

> 按优先级排序，从上到下依次处理：

{{#each suggested_actions}}
{{index}}. {{severity_icon}} **{{action}}**
{{/each}}

{{#unless suggested_actions}}
> ✅ 当前无需特别操作，一切正常。

{{/unless}}

---

*本报告由邮件助手自动生成 | 回复草稿需用户确认后方可发送*
