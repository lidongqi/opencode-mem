#!/bin/bash

# 测试 user_id 修复后的记忆查询

BASE_URL="http://localhost:8000"

echo "========================================="
echo "测试 user_id 修复后的记忆查询"
echo "========================================="
echo ""

echo "1. 查询所有记忆 (user_id=default)"
curl -s -X GET "$BASE_URL/api/memory/all?user_id=default" | jq .
echo ""
echo "---"
echo ""

echo "2. 搜索记忆: '李二'"
curl -s -X POST "$BASE_URL/api/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "李二",
    "user_id": "default",
    "limit": 5
  }' | jq .
echo ""
echo "---"
echo ""

echo "3. 智能记忆查询: '我是谁'"
curl -s -X POST "$BASE_URL/api/memory/intelligent" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "我是谁",
    "user_id": "default",
    "session_id": "test_session",
    "conversation_history": []
  }' | jq .
echo ""
echo "---"
echo ""

echo "========================================="
echo "测试完成"
echo "========================================="
