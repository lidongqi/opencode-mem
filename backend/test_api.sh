#!/bin/bash

# OpenCode Memory Backend API 测试脚本
# 使用方法: ./test_api.sh [BASE_URL] [API_KEY]

BASE_URL="${1:-http://localhost:8000}"
API_KEY="${2:-}"

# 设置 API Key（如果提供）
if [ -n "$API_KEY" ]; then
    AUTH_HEADER="-H 'X-API-Key: $API_KEY'"
else
    AUTH_HEADER=""
fi

echo "========================================="
echo "OpenCode Memory Backend API 测试"
echo "Base URL: $BASE_URL"
echo "API Key: ${API_KEY:-未设置（开发模式）}"
echo "========================================="
echo ""

# 1. 健康检查（无需认证）
echo "1. 健康检查"
echo "GET /health"
curl -s -X GET "$BASE_URL/health" | jq .
echo ""
echo "---"
echo ""

# 2. 根路径
echo "2. 根路径"
echo "GET /"
eval curl -s -X GET "$BASE_URL/" $AUTH_HEADER | jq .
echo ""
echo "---"
echo ""

# 3. 添加记忆
echo "3. 添加记忆"
echo "POST /api/memory/add"
MEMORY_ID=$(eval curl -s -X POST "$BASE_URL/api/memory/add" \
    $AUTH_HEADER \
    -H "Content-Type: application/json" \
    -d '{
        "content": "这是一条测试记忆，记录了用户喜欢编程和人工智能",
        "user_id": "test_user",
        "metadata": {
            "source": "test_script",
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
        }
    }' | jq -r '.memory_id')

echo "Memory ID: $MEMORY_ID"
echo ""
echo "---"
echo ""

# 等待队列处理
echo "等待队列处理..."
sleep 2
echo ""

# 4. 搜索记忆
echo "4. 搜索记忆"
echo "POST /api/memory/search"
eval curl -s -X POST "$BASE_URL/api/memory/search" \
    $AUTH_HEADER \
    -H "Content-Type: application/json" \
    -d '{
        "query": "编程",
        "user_id": "test_user",
        "limit": 5
    }' | jq .
echo ""
echo "---"
echo ""

# 5. 获取所有记忆
echo "5. 获取所有记忆"
echo "GET /api/memory/all"
eval curl -s -X GET "$BASE_URL/api/memory/all?user_id=test_user" $AUTH_HEADER | jq .
echo ""
echo "---"
echo ""

# 6. 获取队列状态
echo "6. 获取队列状态"
echo "GET /api/queue/status"
eval curl -s -X GET "$BASE_URL/api/queue/status" $AUTH_HEADER | jq .
echo ""
echo "---"
echo ""

# 7. 获取任务状态
if [ -n "$MEMORY_ID" ]; then
    echo "7. 获取任务状态"
    echo "GET /api/queue/task/{task_id}"
    eval curl -s -X GET "$BASE_URL/api/queue/task/$MEMORY_ID" $AUTH_HEADER | jq .
    echo ""
    echo "---"
    echo ""
fi

# 8. 获取上下文
echo "8. 获取上下文"
echo "GET /api/memory/context"
eval curl -s -X GET "$BASE_URL/api/memory/context?query=编程&user_id=test_user" $AUTH_HEADER | jq .
echo ""
echo "---"
echo ""

# 9. 更新记忆（需要先有记忆ID）
if [ -n "$MEMORY_ID" ]; then
    echo "9. 更新记忆"
    echo "PUT /api/memory/update"
    eval curl -s -X PUT "$BASE_URL/api/memory/update" \
        $AUTH_HEADER \
        -H "Content-Type: application/json" \
        -d '{
            "memory_id": "'$MEMORY_ID'",
            "content": "更新后的记忆：用户热爱编程，特别是人工智能和机器学习领域"
        }' | jq .
    echo ""
    echo "---"
    echo ""
fi

# 10. 获取记忆历史
if [ -n "$MEMORY_ID" ]; then
    echo "10. 获取记忆历史"
    echo "GET /api/memory/{memory_id}/history"
    eval curl -s -X GET "$BASE_URL/api/memory/$MEMORY_ID/history" $AUTH_HEADER | jq .
    echo ""
    echo "---"
    echo ""
fi

# 11. 删除记忆
if [ -n "$MEMORY_ID" ]; then
    echo "11. 删除记忆"
    echo "DELETE /api/memory/{memory_id}"
    read -p "是否删除测试记忆？(y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        eval curl -s -X DELETE "$BASE_URL/api/memory/$MEMORY_ID" $AUTH_HEADER | jq .
    else
        echo "跳过删除"
    fi
    echo ""
    echo "---"
    echo ""
fi

echo "========================================="
echo "测试完成"
echo "========================================="
