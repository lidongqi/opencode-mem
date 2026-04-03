# OpenCode mem0 Memory Plugin

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript 5.8+](https://img.shields.io/badge/typescript-5.8+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**真正可用的 OpenCode 插件**：基于混合架构的持久化记忆系统，Python FastAPI 后端 + TypeScript OpenCode 插件。

## 🎯 项目架构

```
opencode-mem0/
├── backend/              # Python FastAPI 后端
│   ├── src/
│   │   ├── api/         # REST API 接口
│   │   ├── services/    # 业务逻辑（mem0 封装）
│   │   ├── models/      # Pydantic 数据模型
│   │   ├── opencode_mem0/ # Python 核心库
│   │   └── main.py      # 服务入口
│   ├── tests/           # 单元测试
│   ├── examples/        # 示例代码
│   ├── test_api.sh      # API 测试脚本
│   ├── test_intelligent_api.sh  # 智能记忆 API 测试
│   ├── TESTING.md       # 测试指南
│   ├── pyproject.toml   # Python 依赖
│   └── start.sh         # 启动脚本
│
├── plugin/               # TypeScript OpenCode 插件
│   ├── src/
│   │   ├── tools/       # 6个工具定义
│   │   ├── client.ts    # API 客户端
│   │   └── index.ts     # 插件入口
│   ├── package.json     # npm 配置
│   ├── README.md        # 插件文档
│   └── build.sh         # 构建脚本
│
├── docs/                 # 文档
│   ├── API.md           # API 文档
│   ├── API_TESTING.md   # API 测试示例
│   ├── AUTH.md          # 认证指南
│   ├── DEPLOYMENT.md    # 部署指南
│   ├── INTELLIGENT_MEMORY_IMPLEMENTATION.md  # 智能记忆实现
│   └── CODE_REVIEW_AND_FIXES.md  # 代码审查记录
│
├── deploy.sh             # 一键部署脚本
├── generate-api-key.sh   # API Key 生成脚本
└── README.md             # 项目说明
```

## 🚀 快速开始

### 一键部署

```bash
./deploy.sh
```

### 分步安装

#### 1. 启动 Python 后端

```bash
cd backend
./start.sh
```

首次运行会自动创建 `.env` 配置文件。配置环境变量：

```bash
# 编辑 backend/.env
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=glm-4.7-flash:latest
LLM_BASE_URL=                    # 可选，OpenAI 兼容 API 地址
LLM_API_KEY=                     # 可选，LLM API 密钥

# Embedding Configuration
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
EMBEDDING_BASE_URL=              # 可选，Embedding API 地址
EMBEDDING_API_KEY=               # 可选，Embedding API 密钥

# Legacy Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Authentication
MEM0_API_KEY=                    # 可选，生产环境启用认证
```

后端运行在 http://localhost:8000

#### 2. 构建插件

```bash
cd plugin
./build.sh
```

#### 3. 配置 OpenCode

在 `~/.config/opencode/opencode.json` 中添加：

```json
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "your-api-key"  // 可选，与后端 MEM0_API_KEY 对应
    }]
  ]
}
```

#### 4. 在 OpenCode 中使用

```
You: 帮我记住我喜欢用 Python 做数据分析
OpenCode: [调用 memory_add 工具] 已添加记忆

You: 搜索我的编程偏好
OpenCode: [调用 memory_search 工具] 找到记忆：我喜欢用 Python 做数据分析
```

## 📦 组件说明

### Python 后端 (`backend/`)

**技术栈**：
- FastAPI - 高性能异步 Web 框架
- mem0 - 记忆存储核心库
- Ollama - 本地 LLM 服务

**API 端点**：
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/memory/add` | POST | 添加记忆 |
| `/api/memory/search` | POST | 搜索记忆 |
| `/api/memory/all` | GET | 获取所有记忆 |
| `/api/memory/update` | PUT | 更新记忆 |
| `/api/memory/{id}` | DELETE | 删除记忆 |
| `/api/memory/{id}/history` | GET | 获取历史 |

### TypeScript 插件 (`plugin/`)

**提供的工具**：

1. **memory_add** - 添加记忆
2. **memory_search** - 搜索记忆
3. **memory_get_all** - 获取所有记忆
4. **memory_update** - 更新记忆
5. **memory_delete** - 删除记忆
6. **memory_history** - 查看历史

## 🔧 配置选项

### 后端配置（环境变量）

编辑 `backend/.env` 文件：

```bash
# LLM Configuration
LLM_PROVIDER=ollama          # ollama / openai / azure
LLM_MODEL=glm-4.7-flash:latest
LLM_BASE_URL=                # 可选，OpenAI 兼容 API 地址
LLM_API_KEY=                 # 可选，LLM API 密钥

# Embedding Configuration
EMBEDDING_PROVIDER=ollama    # ollama / openai
EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
EMBEDDING_BASE_URL=          # 可选，Embedding API 地址
EMBEDDING_API_KEY=           # 可选，Embedding API 密钥

# Legacy Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Vector Store Configuration
VECTOR_STORE=chroma          # chroma / qdrant / pgvector
CHROMA_PATH=./mem0_db

# User Configuration
DEFAULT_USER_ID=default_user

# Authentication
MEM0_API_KEY=                # 可选，启用 API Key 认证
```

### 插件配置

```json
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "your-api-key",    // 可选，与后端对应
      "timeout": 30000
    }]
  ]
}
```

### API Key 认证

生产环境推荐启用认证：

```bash
# 生成 API Key
./generate-api-key.sh

# 配置后端
echo 'MEM0_API_KEY=generated-key' >> backend/.env

# 配置插件
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "apiKey": "generated-key"
    }]
  ]
}
```

详见 [认证配置指南](./docs/AUTH.md)

## 📊 性能优化

- 使用本地 Ollama 模型避免 API 延迟
- FastAPI 异步处理提升并发性能
- 可选 Qdrant/pgvector 替代 Chroma 提升规模

## 📝 开发指南

```bash
# 后端开发
cd backend
python -m backend.src.main

# 插件开发
cd plugin
bun run dev  # 监听模式
```

## 🧪 测试

### 后端测试

项目包含完整的测试套件：

```bash
cd backend

# 运行单元测试
pytest tests/ -v

# 运行 API 测试脚本
./test_api.sh                    # 基础 API 测试
./test_intelligent_api.sh        # 智能记忆 API 测试

# 运行示例代码
python examples/example_basic.py
python examples/example_ollama_integration.py
```

详细测试指南请参考 [backend/TESTING.md](./backend/TESTING.md)。

### 插件测试

```bash
cd plugin

# 运行测试
bun test

# 类型检查
bun run typecheck
```

### API 测试文档

详细的 API 测试命令和示例请参考 [API_TESTING.md](./docs/API_TESTING.md)。

## 📄 许可证

MIT License

---

**关键改进**：
✅ 真正符合 OpenCode 插件标准（TypeScript）
✅ 生产可用的 REST API 后端（FastAPI）
✅ 完整的 6 个工具实现
✅ 类型安全（TypeScript + Zod + Pydantic）

**最后更新**: 2025-01-01 | **版本**: 0.1.0