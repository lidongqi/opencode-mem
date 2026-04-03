#!/bin/bash

# Test script for intelligent memory API endpoints

BASE_URL="http://localhost:8000"
API_KEY="${MEM0_API_KEY:-}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Intelligent Memory API ===${NC}\n"

# Test 1: Health check
echo -e "${BLUE}Test 1: Health Check${NC}"
curl -s "$BASE_URL/health" | jq .
echo -e "\n"

# Test 2: Add a memory
echo -e "${BLUE}Test 2: Add Memory${NC}"
curl -s -X POST "$BASE_URL/api/memory/add" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "content": "用户名叫张三，是一名软件工程师",
    "user_id": "test_user_001"
  }' | jq .
echo -e "\n"

sleep 2

# Test 3: Intelligent memory query - personal
echo -e "${BLUE}Test 3: Intelligent Query - Personal${NC}"
curl -s -X POST "$BASE_URL/api/memory/intelligent" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_input": "我是谁",
    "user_id": "test_user_001",
    "session_id": "test_session_001",
    "conversation_history": []
  }' | jq .
echo -e "\n"

# Test 4: Intelligent memory query - not needed
echo -e "${BLUE}Test 4: Intelligent Query - Not Needed${NC}"
curl -s -X POST "$BASE_URL/api/memory/intelligent" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_input": "今天天气怎么样",
    "user_id": "test_user_001",
    "session_id": "test_session_002",
    "conversation_history": []
  }' | jq .
echo -e "\n"

# Test 5: Cache hit (same session)
echo -e "${BLUE}Test 5: Cache Hit Test${NC}"
curl -s -X POST "$BASE_URL/api/memory/intelligent" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_input": "我的名字是什么",
    "user_id": "test_user_001",
    "session_id": "test_session_001",
    "conversation_history": []
  }' | jq .
echo -e "\n"

# Test 6: Get metrics
echo -e "${BLUE}Test 6: Get Metrics${NC}"
curl -s "$BASE_URL/api/metrics" \
  -H "X-API-Key: $API_KEY" | jq .
echo -e "\n"

# Test 7: Get cache stats
echo -e "${BLUE}Test 7: Get Cache Stats${NC}"
curl -s "$BASE_URL/api/cache/stats" \
  -H "X-API-Key: $API_KEY" | jq .
echo -e "\n"

echo -e "${GREEN}=== All tests completed ===${NC}\n"
