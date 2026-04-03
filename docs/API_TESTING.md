# OpenCode Memory Backend API 测试命令

## 环境变量设置

```bash
BASE_URL="http://localhost:8000"
API_KEY="your-api-key-here"  # 如果设置了认证
```

## 1. 健康检查（无需认证）

```bash
curl -X GET "$BASE_URL/health"
```

## 2. 根路径

```bash
# 无认证
curl -X GET "$BASE_URL/"

# 有认证
curl -X GET "$BASE_URL/" \
  -H "X-API-Key: $API_KEY"
```

## 3. 添加记忆

```bash
# 无认证
curl -X POST "$BASE_URL/api/memory/add" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一条测试记忆",
    "user_id": "test_user",
    "metadata": {
      "source": "test",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'

# 有认证
curl -X POST "$BASE_URL/api/memory/add" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "这是一条测试记忆",
    "user_id": "test_user",
    "metadata": {
      "source": "test",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'
```

## 4. 搜索记忆

```bash
# 无认证
curl -X POST "$BASE_URL/api/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试",
    "user_id": "test_user",
    "limit": 5
  }'

# 有认证
curl -X POST "$BASE_URL/api/memory/search" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试",
    "user_id": "test_user",
    "limit": 5
  }'
```

## 5. 获取所有记忆

```bash
# 无认证
curl -X GET "$BASE_URL/api/memory/all?user_id=test_user"

# 有认证
curl -X GET "$BASE_URL/api/memory/all?user_id=test_user" \
  -H "X-API-Key: $API_KEY"
```

## 6. 更新记忆

```bash
# 无认证
curl -X PUT "$BASE_URL/api/memory/update" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "your-memory-id",
    "content": "更新后的记忆内容"
  }'

# 有认证
curl -X PUT "$BASE_URL/api/memory/update" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_id": "your-memory-id",
    "content": "更新后的记忆内容"
  }'
```

## 7. 删除记忆

```bash
# 无认证
curl -X DELETE "$BASE_URL/api/memory/your-memory-id"

# 有认证
curl -X DELETE "$BASE_URL/api/memory/your-memory-id" \
  -H "X-API-Key: $API_KEY"
```

## 8. 获取记忆历史

```bash
# 无认证
curl -X GET "$BASE_URL/api/memory/your-memory-id/history"

# 有认证
curl -X GET "$BASE_URL/api/memory/your-memory-id/history" \
  -H "X-API-Key: $API_KEY"
```

## 9. 获取上下文

```bash
# 无认证
curl -X GET "$BASE_URL/api/memory/context?query=测试&user_id=test_user"

# 有认证
curl -X GET "$BASE_URL/api/memory/context?query=测试&user_id=test_user" \
  -H "X-API-Key: $API_KEY"
```

## 10. 获取队列状态

```bash
# 无认证
curl -X GET "$BASE_URL/api/queue/status"

# 有认证
curl -X GET "$BASE_URL/api/queue/status" \
  -H "X-API-Key: $API_KEY"
```

## 11. 获取任务状态

```bash
# 无认证
curl -X GET "$BASE_URL/api/queue/task/your-task-id"

# 有认证
curl -X GET "$BASE_URL/api/queue/task/your-task-id" \
  -H "X-API-Key: $API_KEY"
```

## 使用说明

1. **开发模式**：如果 `.env` 文件中 `MEM0_API_KEY` 为空，后端运行在开发模式，无需认证
2. **生产模式**：如果设置了 `MEM0_API_KEY`，所有接口（除健康检查外）都需要提供正确的 API Key
3. **运行测试脚本**：
   ```bash
   # 无认证模式
   ./test_api.sh
   
   # 有认证模式
   ./test_api.sh http://localhost:8000 your-api-key
   ```
