# @marvel.li/opencode-mem0-plugin

OpenCode Memory Plugin - 为 OpenCode 提供持久化记忆能力的 TypeScript 插件。

## 简介

本插件是 [OpenCode Memory](../README.md) 项目的前端插件部分，通过调用 Python FastAPI 后端实现记忆的存储、检索和管理。

## 功能特性

- ✅ **2 个核心工具**：添加记忆、搜索记忆
- ✅ **智能记忆注入**：自动查询相关记忆并注入到对话上下文
- ✅ **自动保存**：自动保存有价值的聊天内容
- ✅ **类型安全**：TypeScript + Zod 运行时验证
- ✅ **API 认证**：支持 API Key 认证
- ✅ **错误处理**：完善的错误处理和重试机制
- ✅ **OpenCode 集成**：完全符合 OpenCode 插件标准

## 安装

### 前置要求

- Node.js 18+ 或 Bun
- OpenCode CLI
- 运行中的后端服务（见 [后端部署](../backend/README.md)）

### 构建插件

```bash
# 安装依赖
bun install

# 构建
./build.sh

# 或手动构建
bun run build
```

## 配置


插件支持从独立配置文件加载配置，路径为：

```
~/.config/opencode/.opencode-mem0.json
```

配置文件示例：

```json
{
  "backendUrl": "http://localhost:8000",
  "apiKey": "your-api-key",
  "userId": "your-user-id",
  "timeout": 30000,
  "autoSave": true,
  "enableMemoryQuery": true,
  "memoryQueryLimit": 5
}
```

### 配置选项

| 选项 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `backendUrl` | string | 否 | http://localhost:8000 | 后端 API 地址 |
| `apiKey` | string | 否 | - | API Key（与后端配置对应） |
| `userId` | string | 否 | default | 用户 ID，用于隔离不同用户的记忆 |
| `timeout` | number | 否 | 30000 | 请求超时时间（毫秒） |
| `autoSave` | boolean | 否 | true | 是否自动保存有价值的聊天内容 |
| `enableMemoryQuery` | boolean | 否 | true | 是否启用智能记忆查询和注入 |
| `memoryQueryLimit` | number | 否 | 5 | 智能记忆查询时返回的最大记忆数量 |

## 快速开始

### 1. 部署后端服务

首先需要部署后端服务，详见 [后端部署文档](../backend/README.md)。

```bash
# 克隆项目
git clone <repository-url>
cd opencode_memory/backend

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 MEM0_API_KEY

# 启动服务
docker-compose up -d
```

### 2. 安装并配置插件

```bash
# 进入插件目录
cd ../plugin

# 构建插件
./build.sh

# 方式一：发布到 npm（可选）
bun publish --access public

# 方式二：本地链接测试
bun link
```

### 3. 配置 OpenCode

编辑 `~/.config/opencode/opencode.json`：

```json
{
  "plugin": [
    ["@marvel.li/opencode-mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "your-backend-api-key"
    }]
  ]
}
```

### 4. 验证安装

启动 OpenCode 并测试：

```
You: 帮我记住我的名字是张三
OpenCode: [调用 memory_add] 已添加记忆

You: 你知道我的名字吗？
OpenCode: [自动检索记忆] 根据记忆，你的名字是张三
```

## 提供的工具

### 1. memory_add

添加新记忆到记忆库。

**参数**：
- `content` (string, 必需): 记忆内容
- `user_id` (string, 可选): 用户 ID，默认使用配置文件中的 userId
- `metadata` (object, 可选): 元数据

**示例**：
```
You: 帮我记住我喜欢用 Python 做数据分析
OpenCode: [调用 memory_add] 已添加记忆
```

### 2. memory_search

搜索相关记忆。

**参数**：
- `query` (string, 必需): 搜索查询
- `user_id` (string, 可选): 用户 ID，默认使用配置文件中的 userId
- `limit` (number, 可选): 返回数量限制，默认 5

**示例**：
```
You: 搜索我的编程偏好
OpenCode: [调用 memory_search] 找到记忆：我喜欢用 Python 做数据分析
```

## 智能功能

### 自动记忆注入

插件会自动分析用户的问题，智能检索相关记忆并注入到对话上下文中，无需手动调用搜索工具。

**工作原理**：
1. 监听 `experimental.chat.system.transform` hook
2. 分析用户的最新问题
3. 调用后端的智能记忆接口 `/api/memory/intelligent`
4. 将相关记忆注入到系统提示中

**配置**：
- `enableMemoryQuery`: 启用/禁用智能记忆注入（默认启用）
- `memoryQueryLimit`: 控制注入的记忆数量（默认 5）

### 自动保存记忆

插件会自动识别有价值的聊天内容并保存到记忆库中。

**工作原理**：
1. 监听 `chat.message` hook
2. 分析 AI 的回复内容
3. 判断内容是否值得记忆（排除问题、过短内容等）
4. 自动调用后端的添加记忆接口

**配置**：
- `autoSave`: 启用/禁用自动保存（默认启用）

## 开发

### 项目结构

```
plugin/
├── src/
│   ├── tools/          # 工具定义
│   │   ├── memory_add.ts
│   │   └── memory_search.ts
│   ├── client.ts       # API 客户端
│   └── index.ts        # 插件入口
├── package.json
├── tsconfig.json
└── build.sh
```

### 开发模式

```bash
# 监听模式构建
bun run dev

# 运行测试
bun test
```

### API 客户端

插件使用自定义的 API 客户端与后端通信：

```typescript
import { MemoryClient } from './client';

const client = new MemoryClient({
  backendUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// 添加记忆
const result = await client.addMemory({
  content: '测试记忆',
  user_id: 'user_001'
});

// 搜索记忆
const searchResult = await client.searchMemories({
  query: '编程',
  user_id: 'user_001',
  limit: 5
});
```

## 故障排查

### 常见问题

1. **插件无法连接后端**
   - 检查后端服务是否运行：`curl http://localhost:8000/health`
   - 验证 `backendUrl` 配置是否正确
   - 检查防火墙设置

2. **认证失败**
   - 确认 `apiKey` 与后端 `MEM0_API_KEY` 一致
   - 检查 API Key 格式是否正确
   - 查看后端日志确认认证状态

3. **工具调用超时**
   - 增加 `timeout` 配置值
   - 检查后端性能和响应时间
   - 查看后端日志排查性能问题

4. **构建失败**
   - 清除依赖重新安装：`rm -rf node_modules && bun install`
   - 检查 TypeScript 编译错误：`bun run typecheck`
   - 确认 Node.js/Bun 版本符合要求

## 相关文档

- [主项目文档](../README.md)
- [后端文档](../backend/README.md)
- [API 文档](../docs/API.md)
- [认证配置](../docs/AUTH.md)
- [部署指南](../docs/DEPLOYMENT.md)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**: 2026-04-03 | **版本**: 0.1.0
