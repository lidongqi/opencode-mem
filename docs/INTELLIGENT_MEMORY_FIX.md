# 智能记忆匹配修复说明

## 问题描述

用户报告记忆添加和检索匹配存在问题：
1. 添加记忆"用户名字是李二"后，询问"我是谁？"没有检索到相关记忆
2. 日志显示 `Total existing memories: 0`，说明查询返回空结果
3. 数据库中实际有记忆，但查询不到

## 根本原因

### 1. user_id 不匹配（核心问题）⚠️

**问题**：
- 插件默认使用 `userId = "default"` 保存记忆
- 后端默认使用 `user_id = "default_user"` 查询记忆
- 数据库中的记忆 `user_id = "default"`，但查询时使用 `user_id = "default_user"`

**影响**：
- 所有记忆都无法被查询到
- 智能检索完全失效

**证据**：
```bash
# 数据库中的实际记忆
$ python3 -c "import chromadb; ..."
Collection: mem0
  Count: 2
  Sample metadata: [
    {'user_id': 'default', 'data': 'Name is 李二'},
    {'user_id': 'default', 'data': '询问如何读取记忆'}
  ]

# 后端查询使用的 user_id
routes.py: user_id=os.getenv("DEFAULT_USER_ID", "default_user")  # 默认值是 "default_user"
```

**修复**：
```python
# backend/src/opencode_mem0/config.py
user_id: str = Field(
    default="default",  # 改为 "default"，与插件一致
    description="Default user ID for memories"
)

# backend/.env
DEFAULT_USER_ID=default  # 改为 "default"
```

### 2. 数据库路径问题

**问题**：
- `.env` 文件中配置了绝对路径 `CHROMA_PATH=/Users/lidongqi/work/lidongqi/opencode_memory/backend/mem0_db`
- 但日志显示使用的是相对路径 `./mem0_db`
- 原因：`routes.py` 没有正确加载 `.env` 文件

**影响**：
- 每次请求可能使用不同的数据库路径
- 添加的记忆无法被后续查询找到

**修复**：
```python
# backend/src/api/routes.py
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"[CONFIG] Loaded .env from {env_path}")

# 确保使用绝对路径
def get_memory_service() -> MemoryService:
    chroma_path = os.getenv("CHROMA_PATH", "./mem0_db")
    if not Path(chroma_path).is_absolute():
        backend_dir = Path(__file__).parent.parent.parent
        chroma_path = str(backend_dir / chroma_path)
        logger.info(f"[CONFIG] Converted relative path to absolute: {chroma_path}")
    ...
```

### 3. 自动保存逻辑问题

**问题**：
- 插件的 `chat.message` hook 自动保存所有用户消息
- 问题类消息（如"我是谁？"、"你知道..."）也被保存为记忆
- 这些问题不应该被保存，而应该触发记忆检索

**影响**：
- 数据库中充斥着无意义的问题
- 真正有价值的信息被淹没

**修复**：
```typescript
// plugin/src/index.ts

// 判断是否为问题
function isQuestion(content: string): boolean {
  const questionPatterns = [
    /^(谁|什么|哪|怎么|如何|为什么|哪位|多少|几时|何时)/,
    /\?|？$/,
    /^(我是谁|你知道|还记得|告诉我|请问|能不能|可以|是否|有没有)/,
  ];
  return questionPatterns.some(pattern => pattern.test(content.trim()));
}

// 判断是否值得记忆
function isWorthRemembering(content: string): boolean {
  if (content.trim().length < 5) return false;
  if (isQuestion(content)) return false;
  
  const informativePatterns = [
    /(我叫|我的名字|我是|我喜欢|我偏好|我习惯|我想要|我希望)/,
    /(记住|记得|别忘了|记下来)/,
    /(邮箱|电话|地址|生日|职业|工作)/,
  ];
  return informativePatterns.some(pattern => pattern.test(content));
}

// 自动保存时过滤
if (!isWorthRemembering(content)) {
  console.log("[opencode-mem0] content not worth remembering, skipping save");
  return;
}
```

### 3. 智能检索调试不足

**问题**：
- 智能记忆检索流程缺乏详细日志
- 难以追踪为什么没有找到记忆

**修复**：
在 `intelligent_memory_service.py` 中添加详细日志：
```python
# 意图分析
logger.info(f"[IntelligentMemory] Analyzing user input: '{user_input}'")
logger.info(f"[IntelligentMemory] Quick check result: potential_need={quick_check['potential_need']}, keywords={quick_check['keywords']}, types={quick_check['types']}")

# 搜索执行
logger.info(f"[IntelligentMemory] Executing search - query: '{intent.search_query}', user_id: {user_id}")
logger.info(f"[IntelligentMemory] Semantic search found {len(found_memories)} memories")

# 结果汇总
logger.info(f"[IntelligentMemory] Total unique memories found: {len(unique_memories)}")
```

## 测试验证

### 1. 重启后端服务

```bash
cd backend
# 停止旧服务
pkill -f "python.*main.py"

# 启动新服务
./start.sh
```

查看日志确认：
```
[CONFIG] Loaded .env from /Users/lidongqi/work/lidongqi/opencode_memory/backend/.env
[CONFIG] CHROMA_PATH: /Users/lidongqi/work/lidongqi/opencode_memory/backend/mem0_db
```

### 2. 重新构建插件

```bash
cd plugin
bun run build
```

### 3. 测试场景

#### 场景 1：添加事实性信息

**用户输入**：
```
我叫李二，是一名软件工程师
```

**预期日志**：
```
[opencode-mem0] extracted content: 我叫李二，是一名软件工程师
[opencode-mem0] saving memory for user: default
[opencode-mem0] memory save result: success
```

#### 场景 2：询问个人信息

**用户输入**：
```
我是谁？
```

**预期日志**：
```
[opencode-mem0] intelligent memory query triggered
[IntelligentMemory] Analyzing user input: '我是谁？'
[IntelligentMemory] Quick check result: potential_need=True, keywords=['我', '是谁'], types=['personal', 'questions']
[IntelligentMemory] Rule-based intent: needed=True, type=personal, search_query='用户身份 名字 个人信息 我 是谁'
[IntelligentMemory] Executing search - query: '用户身份 名字 个人信息 我 是谁', user_id: default
[IntelligentMemory] Semantic search found 1 memories
[IntelligentMemory] Total unique memories found: 1
[opencode-mem0] injected intelligent memories - count: 1, latency: XXms, cache_hit: false
```

**注意**：问题类消息不会被保存：
```
[opencode-mem0] content not worth remembering (question or too short), skipping save
```

#### 场景 3：偏好信息

**用户输入**：
```
我喜欢用 Python 做数据分析
```

**预期**：会被保存为记忆

**后续查询**：
```
搜索我的编程偏好
```

**预期**：能检索到相关记忆

## 工作流程说明

### 完整的记忆匹配流程

```
用户输入
    ↓
┌─────────────────────────────────────┐
│ 1. 智能检索 Hook 触发                │
│    (experimental.chat.system.transform) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 意图分析                          │
│    - 关键词检测                      │
│    - 问题类型识别                    │
│    - 构建搜索查询                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 记忆检索                          │
│    - 语义搜索                        │
│    - 身份搜索（personal 类型）       │
│    - 缓存检查                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. 结果注入                          │
│    - 格式化记忆                      │
│    - 注入系统提示                    │
└─────────────────────────────────────┘
    ↓
AI 回复（基于记忆上下文）

    ↓
┌─────────────────────────────────────┐
│ 5. 自动保存 Hook 触发                │
│    (chat.message)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. 内容过滤                          │
│    - 是否为问题？                    │
│    - 是否值得记忆？                  │
└─────────────────────────────────────┘
    ↓
  保存 / 跳过
```

## 配置说明

### 环境变量

确保 `backend/.env` 配置正确：

```bash
# 使用绝对路径
CHROMA_PATH=/Users/lidongqi/work/lidongqi/opencode_memory/backend/mem0_db

# 或者使用相对路径（会自动转换为绝对路径）
CHROMA_PATH=./mem0_db
```

### 插件配置

在 `~/.config/opencode/opencode.json` 中：

```json
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "autoSave": true,
      "enableMemoryQuery": true,
      "userId": "default"
    }]
  ]
}
```

## 故障排查

### 问题：仍然找不到记忆

**检查步骤**：

1. **验证数据库路径**
```bash
# 查看后端日志，确认路径
grep "CHROMA_PATH" backend.log

# 检查数据库文件
ls -la /Users/lidongqi/work/lidongqi/opencode_memory/backend/mem0_db/
```

2. **验证记忆是否保存**
```bash
# 使用 API 查询所有记忆
curl http://localhost:8000/api/memory/all?user_id=default | jq .
```

3. **查看智能检索日志**
```bash
# 查看意图分析
grep "IntelligentMemory" backend.log

# 查看搜索结果
grep "Semantic search found" backend.log
```

4. **检查插件日志**
```bash
# OpenCode 控制台应该显示
# [opencode-mem0] intelligent memory query triggered
# [opencode-mem0] injected intelligent memories
```

### 问题：问题被保存为记忆

**检查**：
- 确认插件已重新构建：`cd plugin && bun run build`
- 查看插件日志：应该显示 "content not worth remembering"

## 性能优化

### 缓存机制

智能记忆服务实现了三层缓存：

1. **会话缓存**：同一会话内的记忆缓存
2. **查询缓存**：相同查询的结果缓存
3. **LRU 缓存**：热点记忆的快速访问

### 监控指标

```bash
# 获取性能指标
curl http://localhost:8000/api/metrics | jq .

# 获取缓存统计
curl http://localhost:8000/api/cache/stats | jq .
```

## 相关文档

- [测试指南](../backend/TESTING.md)
- [API 文档](./API.md)
- [API 测试示例](./API_TESTING.md)
- [智能记忆实现](./INTELLIGENT_MEMORY_IMPLEMENTATION.md)
