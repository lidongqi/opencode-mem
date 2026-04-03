# 部署指南

## 本地开发部署

### 1. 后端部署

```bash
# 安装依赖
cd backend
pip install -e ..

# 配置环境变量
cat > .env << EOF
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=glm-4.7-flash:latest
LLM_BASE_URL=
LLM_API_KEY=

# Embedding Configuration
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
EMBEDDING_BASE_URL=
EMBEDDING_API_KEY=

# Legacy Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Vector Store Configuration
VECTOR_STORE=chroma
CHROMA_PATH=./mem0_db

# User Configuration
DEFAULT_USER_ID=default_user
EOF

# 启动服务
python -m backend.src.main
```

### 2. 插件安装

```bash
cd plugin
bun install
bun run build
bun link  # 本地链接
```

### 3. OpenCode 配置

编辑 `~/.config/opencode/opencode.json`：

```json
{
  "plugin": [
    "@opencode-ai/mem0-plugin"
  ]
}
```

## Docker 部署

### 后端 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "backend.src.main"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mem0-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama3.1:latest
      - LLM_BASE_URL=
      - LLM_API_KEY=
      - EMBEDDING_PROVIDER=ollama
      - EMBEDDING_MODEL=nomic-embed-text-v2-moe:latest
      - EMBEDDING_BASE_URL=
      - EMBEDDING_API_KEY=
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./mem0_db:/app/mem0_db
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

### 启动

```bash
docker-compose up -d
```

## 生产部署

### 使用 HTTPS

```bash
# 使用 nginx 反向代理
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 环境变量管理

使用 `.env` 文件或 Kubernetes Secrets：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mem0-backend-secrets
type: Opaque
stringData:
  LLM_PROVIDER: "openai"
  OPENAI_API_KEY: "your-key"
  VECTOR_STORE: "qdrant"
  QDRANT_HOST: "qdrant.example.com"
```

### 高可用部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mem0-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mem0-backend
  template:
    metadata:
      labels:
        app: mem0-backend
    spec:
      containers:
      - name: backend
        image: your-registry/mem0-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_PROVIDER
          value: "openai"
        envFrom:
        - secretRef:
            name: mem0-backend-secrets
```

## 监控和日志

### 健康检查

```bash
curl http://localhost:8000/health
```

### 日志管理

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mem0_backend.log'),
        logging.StreamHandler()
    ]
)
```