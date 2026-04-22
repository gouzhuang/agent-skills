---
name: privacy-review
description: "Scan codebases for privacy data leakage risks such as hardcoded secrets, API keys, passwords, database connection strings, JWT tokens, email addresses, phone numbers, and ID cards. Use when the user wants to check code for privacy compliance, security audit, or before open-sourcing a project. Triggered by requests like 'check for privacy leaks', 'scan for secrets', 'privacy review', 'find hardcoded credentials', or 'check for PII in code'."
---

# privacy-review

扫描代码库中的隐私数据泄漏风险。适用于代码审查、安全审计、开源发布前的隐私合规检查。

## 快速开始

```bash
# 扫描当前目录（JSON 输出）
python skills/privacy-review/scripts/privacy_review.py

# 扫描指定目录，文本输出
python skills/privacy-review/scripts/privacy_review.py /path/to/project --format text

# 只显示高危问题
python skills/privacy-review/scripts/privacy_review.py . --severity high

# 排除特定文件或目录
python skills/privacy-review/scripts/privacy_review.py . --exclude "*.test.js" --exclude "fixtures/"
```

## 检测规则

| 规则名 | 严重级别 | 说明 |
|--------|---------|------|
| Private Key | high | PEM/OPENSSH/DSA/EC/PGP 私钥 |
| AWS Access Key ID | high | AKIA 开头的 AWS Key |
| AWS Secret Access Key | high | AWS Secret Access Key |
| Generic API Key | high | 硬编码 API Key |
| Generic Secret Token | high | Secret / Access Token / Bearer Token |
| Hardcoded Password | high | 硬编码密码 |
| Database Connection String | high | 含密码的数据库连接字符串 |
| GitHub Token | high | GitHub Personal / OAuth / App Token |
| Slack Token | high | Slack Bot / User Token |
| JWT Token | medium | JSON Web Token |
| Email Address | medium | 邮箱地址 |
| Chinese Mobile Number | low | 中国大陆手机号 |
| Chinese ID Card | low | 15 位或 18 位身份证号 |
| IPv4 Address | low | IPv4 地址（排除私有地址段） |

## 命令行参数

```
python privacy_review.py [path] [options]
```

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | - | `.` | 要扫描的路径 |
| `--format` | `-f` | `json` | 输出格式：`json` 或 `text` |
| `--severity` | `-s` | `all` | 按严重级别过滤：`high`、`medium`、`low`、`all` |
| `--exclude` | `-e` | - | 排除模式，可多次使用，支持通配符 |

## 输出格式

### JSON（默认）

```json
{
  "scan_summary": {
    "target_path": "/home/user/project",
    "files_scanned": 42,
    "issues_found": 3,
    "high": 1,
    "medium": 1,
    "low": 1
  },
  "results": [
    {
      "file": "src/config.py",
      "line": 15,
      "rule": "Generic API Key",
      "severity": "high",
      "match": "api_key = \"sk-abc123...\"",
      "description": "检测到硬编码 API Key"
    }
  ]
}
```

### Text

按严重级别分组输出，适合直接在终端阅读。

## 自动排除项

脚本默认跳过以下目录和文件类型，无需手动配置：

- 目录：`.git`、`.svn`、`node_modules`、`__pycache__`、`.venv`、`venv`、`.tox`、`.pytest_cache`、`build`、`dist`、`target`、`vendor`
- 文件：`*.pyc`、`*.min.js`、`*.lock`、`*.sum`、图片、音视频、压缩包、Office 文档、二进制文件
- 超大文件：大于 10MB 的文件

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 扫描完成，未发现高危问题 |
| 1 | 扫描完成，发现至少一个 high 级别问题，或路径不存在 |

## 最佳实践

1. **CI/CD 集成**：在代码提交前或合并请求时运行，设置 `--severity high` 作为门禁条件
2. **开源前检查**：公开发布前扫描整个仓库，确保无硬编码凭证
3. **处理误报**：
   - 测试数据中的假密码可用 `--exclude` 排除测试目录
   - 文档中的示例可用 `--exclude "*.md"` 排除
4. **人工复核**：本工具为辅助扫描，命中结果需人工确认是否为真实泄漏
5. **注意边界**：脚本使用正则匹配，可能出现误报或漏报，重要场景建议配合专用工具（如 git-secrets、truffleHog）使用
