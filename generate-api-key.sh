#!/bin/bash

set -e

echo "================================"
echo "Generate API Key"
echo "================================"
echo ""

API_KEY=$(openssl rand -hex 32)

echo "Generated API Key:"
echo ""
echo "  $API_KEY"
echo ""
echo "Add this to your backend/.env file:"
echo ""
echo "  MEM0_API_KEY=$API_KEY"
echo ""
echo "And configure your OpenCode plugin:"
echo ""
cat << JSONEOF
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "$API_KEY"
    }]
  ]
}
JSONEOF
echo ""