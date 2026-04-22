---
name: loinc-query
description: Query the LOINC medical terminology database via the Regenstrief Search API. Use when the user needs to search for LOINC codes, parts, answer lists, or groups. Supports advanced search syntax including field restrictions (Component:, System:, etc.), boolean operators (AND/OR/NOT), wildcards, fuzzy search, and phrase search. Triggered by requests like "find LOINC code for X", "search LOINC", "look up LOINC term", "LOINC code for glucose/blood test/etc.", or any medical terminology lookup task involving LOINC.
---

# LOINC 查询

通过 Regenstrief Search API 查询 LOINC 医学术语数据库。输出结构化 JSON（Summary + Results）。

## 快速开始

运行脚本进行查询（需要 `httpx` 已安装：`pip install httpx`）：

```bash
# 搜索 LOINC 术语
python scripts/loinc_search.py search "glucose"

# 限定字段搜索
python scripts/loinc_search.py search "Component:glucose System:Ser/Plas"

# 搜索 Parts
python scripts/loinc_search.py parts 'Ser/Plas PartTypeName:SYSTEM Status:ACTIVE'

# 查看特定代码详情
python scripts/loinc_search.py details "2339-0"

# 限制结果数量
python scripts/loinc_search.py search "glucose" -n 10

# 控制输出详细程度
python scripts/loinc_search.py search "glucose" -d brief
python scripts/loinc_search.py details "2339-0" -d moderate
```

## 认证

脚本按以下优先级读取认证信息：

1. `~/.loincrc` 文件（格式：`username=xxx\npassword=yyy`）
2. 环境变量 `LOINC_USERNAME` 和 `LOINC_PASSWORD`

如果均未配置，脚本返回错误 JSON 并退出码 1。

## 搜索端点

| 命令 | 端点 | 用途 |
|------|------|------|
| `search` | `loincs` | 搜索 LOINC 术语代码（默认） |
| `parts` | `parts` | 搜索 LOINC 部件（Component, Method, System 等） |
| `answers` | `answerlists` | 搜索答案列表 |
| `groups` | `groups` | 搜索 LOINC 组 |
| `details` | `loincs` | 查看指定 LOINC 代码详情 |

## 搜索语法

### 字段限定搜索

使用 `字段名:值` 将搜索限定到特定字段：

```
Component:glucose System:Bld
Component:(opiates confirm)        # Component 中同时包含两个词
Component:(opiates OR confirm)     # Component 中包含任一
```

常用字段：`LOINC`, `Component`, `Property`, `Timing`, `System`, `Scale`, `Method`, `Class`

### 布尔运算

```
glucose AND blood                  # 两者都必须存在（AND 可省略）
influenza OR parainfluenza         # 任一存在
glucose NOT urine                  # 排除 urine
(influenza OR rhinovirus) -haemophilus   # 分组 + 排除
```

### 短语与通配符

```
"viral load"                       # 精确短语
80619-?                            # 单字符通配符（查找校验位）
allergy artemi*                    # 多字符通配符
```

### 模糊与邻近搜索

```
haemofhilus~                       # 模糊搜索，默认相似度 0.5
haemofhilus~0.8                    # 指定相似度
"function panel"~1                 # 两词距离不超过 1
```

### 范围搜索

```
createdon:[20230101 TO 20231231]   # 包含边界
createdon:{20230101 TO 20231231}   # 不包含边界
```

### 状态与分类过滤

```
glucose Status:Active
glucose OrderObs:both
glucose Ranked:true
platelet CommonOrder:true
hemoglobin Methodless:true
glucose Class:CHEM
```

### 转义特殊字符

需要转义的字符：`+ - && || ! ( ) { } [ ] ^ " ~ * ? : \`

示例：搜索 `O157:H7` 需写作 `O157\:H7`

完整语法参考见 [references/search-syntax.md](references/search-syntax.md)。

## 常用查询示例

| 场景 | 查询 |
|------|------|
| 血糖检测 | `glucose System:blood` |
| 活跃的血小板计数 | `platelet Status:Active` |
| 常见订单 | `hemoglobin CommonOrder:true` |
| 特定代码 | `LOINC:2339-0` 或直接用 `2339-0` |
| 排除已弃用 | `glucose -Status:Deprecated` |
| 无方法版本 | `glucose Methodless:true` |
| 含答案列表 | `pain AnswerList:true` |
| 前 20000 常用 | `creatinine Ranked:true` |
| 模糊拼写 | `hemofhilus~` |
| 特定属性 | `glucose Property:MCnc Scale:Qn` |

## 输出格式

输出为 Pretty JSON，包含两部分：

- `Summary` — 查询摘要（端点、查询词、总记录数、偏移量、返回行数）
- `Results` — 查询结果列表

```json
{
  "Summary": {
    "Endpoint": "loincs",
    "Query": "glucose",
    "TotalCount": 145,
    "Offset": 0,
    "Rows": 20
  },
  "Results": [...]
}
```

## 输出详细程度

使用 `--detail` / `-d` 控制结果字段的详细程度：

| 级别 | 说明 |
|------|------|
| `brief` | 仅保留核心字段（LOINC_NUM、COMPONENT、SYSTEM 等） |
| `moderate` | 包含常用扩展字段（SHORTNAME、DisplayName 等） |
| `full` | 保留 API 返回的全部字段（默认） |

```bash
python scripts/loinc_search.py search "glucose" -d brief
python scripts/loinc_search.py parts "System" -d moderate
```

各端点保留的字段定义见脚本中的 `DETAIL_FIELDS`。

## 错误处理

错误以 JSON 格式输出到 stderr，并返回非零退出码：

```json
{"error": "Authentication failed. Check your LOINC credentials.", "status_code": 401}
```

常见退出码：
- `0` — 成功
- `1` — API 错误或业务错误（无结果、认证失败等）
- `2` — 参数错误（未指定命令等）

## 分页

使用 `--offset` 翻页，配合 `--rows / -n` 控制每页数量：

```bash
python scripts/loinc_search.py search "glucose" -n 20 --offset 0
python scripts/loinc_search.py search "glucose" -n 20 --offset 20
```
