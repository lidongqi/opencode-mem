# 测试指南

本文档说明如何运行 OpenCode Memory Backend 的各种测试。

## 测试类型

### 1. 单元测试

单元测试位于 `tests/` 目录，使用 pytest 框架。

```bash
# 运行所有单元测试
cd backend
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_plugin.py -v
pytest tests/test_intelligent_memory.py -v

# 运行特定测试类
pytest tests/test_plugin.py::TestMem0Config -v

# 运行特定测试方法
pytest tests/test_plugin.py::TestMem0Config::test_default_config -v
```

### 2. 集成测试

#### API 测试脚本

**基础 API 测试** (`test_api.sh`)

测试所有基础 API 端点：

```bash
# 无认证模式
./test_api.sh

# 有认证模式
./test_api.sh http://localhost:8000 your-api-key
```

测试内容包括：
- 健康检查
- 添加记忆
- 搜索记忆
- 获取所有记忆
- 更新记忆
- 删除记忆
- 获取记忆历史
- 获取队列状态

**智能记忆 API 测试** (`test_intelligent_api.sh`)

测试智能记忆查询功能：

```bash
# 设置 API Key（如果需要）
export MEM0_API_KEY="your-api-key"

# 运行测试
./test_intelligent_api.sh
```

测试内容包括：
- 智能查询 - 个人信息
- 智能查询 - 不需要记忆的场景
- 缓存命中测试
- 性能指标获取
- 缓存统计获取

#### 手动 API 测试

详细的 curl 命令示例请参考 [API_TESTING.md](../docs/API_TESTING.md)。

### 3. 示例代码

`examples/` 目录包含示例代码，展示如何使用插件：

**基础示例** (`example_basic.py`)

展示基本的插件配置和使用：

```bash
cd backend
python examples/example_basic.py
```

**Ollama 集成示例** (`example_ollama_integration.py`)

展示如何与 Ollama 集成：

```bash
cd backend
python examples/example_ollama_integration.py
```

**基础使用示例** (`basic_usage.py`)

展示记忆服务的基本使用方法。

## 测试环境配置

### 环境变量

测试前确保配置正确的环境变量（`.env` 文件）：

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=glm-4.7-flash:latest
LLM_BASE_URL=

# Embedding Configuration
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
EMBEDDING_BASE_URL=

# Legacy Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Authentication (可选)
MEM0_API_KEY=
```

### 依赖安装

```bash
# 安装开发依赖
cd backend
pip install -e ".[dev]"
```

## 测试最佳实践

### 1. 测试顺序

建议按以下顺序运行测试：

1. **单元测试** - 确保核心功能正常
2. **启动后端服务** - `./start.sh`
3. **API 测试** - 验证 API 端点
4. **集成测试** - 测试完整流程

### 2. 测试数据清理

测试完成后，建议清理测试数据：

```bash
# 删除测试数据库
rm -rf ./mem0_db
rm -rf ./test_*
```

### 3. 持续集成

在 CI/CD 环境中运行测试：

```bash
# 完整测试流程
pytest tests/ -v --cov=src --cov-report=xml
```

## 故障排查

### 常见问题

1. **Ollama 连接失败**
   - 确保 Ollama 服务正在运行
   - 检查 `OLLAMA_BASE_URL` 配置
   - 验证模型已下载：`ollama list`

2. **API 认证失败**
   - 检查 API Key 是否正确
   - 确认后端 `MEM0_API_KEY` 配置
   - 验证请求头 `X-API-Key` 格式

3. **测试数据库锁定**
   - 关闭所有使用数据库的进程
   - 删除 `chroma.sqlite3-wal` 文件
   - 重新运行测试

4. **端口占用**
   - 检查 8000 端口：`lsof -i :8000`
   - 终止占用进程或修改端口配置

## 性能测试

### 基准测试

使用 pytest-benchmark 进行性能测试：

```bash
pytest tests/ --benchmark-only
```

### 负载测试

使用 Apache Bench 或 wrk 进行负载测试：

```bash
# 使用 ab
ab -n 1000 -c 10 http://localhost:8000/health

# 使用 wrk
wrk -t4 -c100 -d30s http://localhost:8000/health
```

## 测试覆盖率

生成测试覆盖率报告：

```bash
# 生成终端报告
pytest tests/ --cov=src --cov-report=term-missing

# 生成 HTML 报告
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## 相关文档

- [API 文档](../docs/API.md)
- [API 测试示例](../docs/API_TESTING.md)
- [认证配置](../docs/AUTH.md)
- [部署指南](../docs/DEPLOYMENT.md)
