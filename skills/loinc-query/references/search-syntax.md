# LOINC 搜索语法参考

## 基本规则

- 搜索不区分大小写
- 多个词之间默认使用 AND 连接

## 特殊字符

| 符号 | 示例 | 说明 |
|------|------|------|
| `" "` | `influenza "virus A"` | 引号内视为短语 |
| `AND` | `morphine AND cutoff` | 两者都必须存在（可省略） |
| `OR` | `influenza OR parainfluenza` | 任一存在即可 |
| `NOT` | `influenza NOT equine` | 排除后面词 |
| `?` | `80619-?` | 单字符通配符，不可用于短语 |
| `*` | `allergy artemi*` | 多字符通配符，不可用于短语 |
| `FieldName:` | `Component:opiates System:hair` | 限定搜索字段 |

## 基本 LOINC 字段名

| 字段 | 示例 |
|------|------|
| `LOINC:` | `LOINC:12628-4` |
| `Component:` | `Component:chemotherapy` |
| `Property:` | `glucose Property:CCnc` |
| `Timing:` | `glucose Timing:24H` |
| `System:` | `glucose System:CSF` |
| `Scale:` | `glucose Scale:Nar` |
| `Method:` | `mycobacterium Method:IA` |
| `Class:` | `glucose Class:UA` |

字段限定符只对紧随其后的搜索词有效：`Component:opiates confirm` 会在 Component 字段搜索 opiates，在所有字段搜索 confirm。

## Part 字段名

| 字段 | 示例 |
|------|------|
| `Part:` | `Part:LP16708-7` |
| `Name:` | `Name:giemsa` |
| `Type:` | `Type:Component` |

## Answer List 字段名

| 字段 | 示例 |
|------|------|
| `AnswerList:` | `AnswerList:LL512-5` |
| `Name:` | `Name:care*` |
| `Description:` | `Description:sock` |

## 高级搜索语法

### + 加号（必需）

要求结果包含该词：

```
bacillus +anthracis
```

### - 减号（排除）

排除包含该词的结果：

```
bacillus -anthracis
```

### ( ) 括号分组

控制布尔逻辑优先级：

```
(influenza OR rhinovirus) -haemophilus
```

多词搜索同字段：

```
Component:(opiates confirm)
Component:(opiates OR confirm)
```

### ~ 模糊搜索

搜索拼写相似的词，默认相似度 0.5：

```
haemofhilus~
haemofhilus~0.8
```

### " "~ 邻近搜索

搜索短语中词之间的距离：

```
"function panel"~1
```

### [ ] { } 范围搜索

方括号包含边界，花括号不包含：

```
createdon:[20170101 TO 20170601]
createdon:{20170101 TO 20170601}
```

### 转义特殊字符

以下特殊字符需要反斜杠转义：

```
+ - && || ! ( ) { } [ ] ^ " ~ * ? : \
```

示例：搜索 `O157:H7`：

```
O157\:H7
```

## 常用高级字段名

| 字段 | 允许值 | 说明 |
|------|--------|------|
| `Status:` | `Active` `Trial` `Discouraged` `Deprecated` | 术语状态 |
| `OrderObs:` | `Both` `Observation` `Order` `Subset` | 用途类型 |
| `TypeName:` | `Lab` `Clinical` `Attachment` `Survey` | 类别名称 |
| `Ranked:` | `True` `False` | 是否在前 20000 常用代码中 |
| `CommonOrder:` | `True` `False` | 是否为常用订单 |
| `AnswerList:` | `True` `False` | 是否有答案列表 |
| `Methodless:` | `True` `False` | 是否无方法字段 |
| `NonroutineChallenge:` | `True` `False` | 是否为非例行挑战测试 |
| `Categorization:` | 多种类别名 | 临床专科分类 |
| `MapToLOINC:` | LOINC 代码 | 替代已弃用代码 |
| `VersionLastChanged:` | 版本号 | 最后修改版本 |

完整的高级字段列表请参考 LOINC Users' Guide。
