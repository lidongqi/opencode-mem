# API Key 认证配置指南

## 概述

OpenCode mem0 插件支持 API Key 认证，保护后端 API 不被未授权访问。

## 认证模式

### 开发模式（无需认证）

如果未配置 `MEM0_API_KEY`，后端将跳过认证，适合本地开发。

### 生产模式（启用认证）

配置 `MEM0_API_KEY` 后，所有 API 请求都需要提供有效的 API Key。

## 快速开始

### 1. 生成 API Key

运行脚本生成安全的 API Key：

```bash
./generate-api-key.sh
```

输出示例：
```
Generated API Key:
  3a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f
```

### 2. 配置后端

编辑 `backend/.env` 文件：

```bash
cd backend
echo 'MEM0_API_KEY=3a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f' >> .env
```

### 3. 配置插件

编辑 `~/.config/opencode/opencode.json`：

```json
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "3a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z2a3b4c5d6e7f"
    }]
  ]
}
```

### 4. 启动服务

```bash
cd backend
./start.sh
```

检查认证状态：

```bash
curl http://localhost:8000/
```

响应：
```json
{
  "name": "OpenCode mem0 Memory Backend",
  "version": "0.1.0",
  "status": "running",
  "auth_enabled": true
}
```

## API 请求方式

### 使用 HTTP Header

所有 API 请求需在 Header 中包含 `X-API-Key`：

```bash
curl -X POST http://localhost:8000/api/memory/add \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"content": "test memory"}'
```

### 使用插件

插件会自动在请求中添加 API Key，无需手动处理。

## 环境变量配置

### 后端环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MEM0_API_KEY` | API Key（可选） | `3a7b8c9d...` |

### 插件环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MEM0_BACKEND_URL` | 后端地址 | `http://localhost:8000` |
| `MEM0_API_KEY` | API Key | `3a7b8c9d...` |

## 安全最佳实践

### 1. 使用强密钥

- 至少 32 字节（64 个十六进制字符）
- 使用加密安全的随机数生成器
- 定期轮换密钥

### 2. 保护密钥安全

- 不要将密钥提交到版本控制
- 使用环境变量或密钥管理服务
- 限制密钥的访问权限

### 3. 传输安全

- 生产环境使用 HTTPS
- 使用反向代理（nginx/Caddy）添加 SSL/TLS

### 4. 密钥轮换

定期更换 API Key：

1. 生成新密钥
2. 更新后端配置并重启
3. 更新所有客户端配置
4. 删除旧密钥

## 生产部署示例

### Docker Compose

```yaml
version: '3.8'

services:
  mem0-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MEM0_API_KEY=${MEM0_API_KEY}
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.1:latest
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
```

启动：

```bash
export MEM0_API_KEY=$(openssl rand -hex 32)
docker-compose up -d
```

### Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mem0-api-key
type: Opaque
stringData:
  api-key: "3a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p..."
```

Deployment：

```yaml
env:
  - name: MEM0_API_KEY
    valueFrom:
      secretKeyRef:
        name: mem0-api-key
        key: api-key
```

## 故障排查

### 问题：401 Unauthorized

**原因**：未提供 API Key 或密钥无效

**检查**：
1. 后端 `.env` 中是否配置了 `MEM0_API_KEY`
2. 请求 Header 是否包含 `X-API-Key`
3. API Key 是否正确

### 问题：开发模式下仍需要认证

**原因**：可能配置了环境变量

**检查**：
```bash
echo $MEM0_API_KEY
```

取消设置：
```bash
unset MEM0_API_KEY
```

## 监控和日志

### 查看认证日志

后端会记录认证失败：

```
INFO: 401 Unauthorized - Invalid API Key
```

### 监控建议

- 记录所有认证失败事件
- 设置异常访问频率告警
- 定期审计 API Key 使用情况

## 多租户支持（未来）

当前版本仅支持单一 API Key。未来版本可能支持：

- 多 API Key 管理
- 按用户/角色的权限控制
- API Key 过期时间
- 访问频率限制

---

**相关文档**：
- [部署指南](./DEPLOYMENT.md)
- [API 文档](./API.md)