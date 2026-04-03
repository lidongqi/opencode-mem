# API 文档

## 基础信息

**Base URL**: `http://localhost:8000`

**Content-Type**: `application/json`

## 端点列表

### 1. 健康检查

**GET** `/health`

**响应**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "backend": "python-fastapi"
}
```

### 2. 添加记忆

**POST** `/api/memory/add`

**请求体**:
```json
{
  "content": "我喜欢用 Python 进行数据分析",
  "user_id": "user_123",
  "metadata": {
    "category": "preference"
  }
}
```

**响应**:
```json
{
  "success": true,
  "memory_id": "mem-abc123",
  "message": "Memory added successfully"
}
```

### 3. 搜索记忆

**POST** `/api/memory/search`

**请求体**:
```json
{
  "query": "编程语言偏好",
  "user_id": "user_123",
  "limit": 5
}
```

**响应**:
```json
{
  "success": true,
  "memories": [
    {
      "id": "mem-abc123",
      "content": "我喜欢用 Python 进行数据分析",
      "score": 0.92,
      "metadata": {
        "category": "preference"
      }
    }
  ],
  "count": 1
}
```

### 4. 获取所有记忆

**GET** `/api/memory/all?user_id=user_123`

**响应**:
```json
{
  "success": true,
  "memories": [
    {
      "id": "mem-abc123",
      "content": "我喜欢用 Python 进行数据分析",
      "metadata": {},
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-01T10:00:00"
    }
  ],
  "count": 1
}
```

### 5. 更新记忆

**PUT** `/api/memory/update`

**请求体**:
```json
{
  "memory_id": "mem-abc123",
  "content": "我喜欢用 Python 和 R 进行数据分析"
}
```

**响应**:
```json
{
  "success": true,
  "memory_id": "mem-abc123",
  "message": "Memory updated successfully"
}
```

### 6. 删除记忆

**DELETE** `/api/memory/{memory_id}`

**响应**:
```json
{
  "success": true,
  "message": "Memory mem-abc123 deleted successfully"
}
```

### 7. 获取记忆历史

**GET** `/api/memory/{memory_id}/history`

**响应**:
```json
{
  "success": true,
  "history": [
    {
      "old_memory": "我喜欢用 Python 进行数据分析",
      "new_memory": "我喜欢用 Python 和 R 进行数据分析",
      "timestamp": "2025-01-01T10:30:00"
    }
  ]
}
```

### 8. 获取上下文

**GET** `/api/memory/context?query=数据分析&user_id=user_123`

**响应**:
```json
{
  "context": "## Relevant Memories\n1. 我喜欢用 Python 进行数据分析 (relevance: 0.92)"
}
```

## 错误响应

所有错误遵循统一格式：

```json
{
  "success": false,
  "error": "Error message"
}
```

## HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |