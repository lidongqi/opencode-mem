#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "================================"
echo "OpenCode mem0 Deployment"
echo "================================"
echo ""

echo "Step 1: Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "✗ Python3 is required but not installed."; exit 1; }
command -v bun >/dev/null 2>&1 || { echo "✗ Bun is required but not installed."; exit 1; }
echo "✓ All prerequisites met"
echo ""

echo "Step 2: Setting up backend..."
cd "$PROJECT_ROOT/backend"

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
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

# Legacy Ollama Configuration (backward compatibility)
OLLAMA_BASE_URL=http://localhost:11434

# Vector Store Configuration
VECTOR_STORE=chroma
CHROMA_PATH=./mem0_db

# User Configuration
DEFAULT_USER_ID=default_user

# Authentication
MEM0_API_KEY=
EOF
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "Step 3: Installing Python dependencies..."
pip3 install -e .. -q
echo "✓ Python dependencies installed"
echo ""

echo "Step 4: Building plugin..."
cd "$PROJECT_ROOT/plugin"
bun install -s
bun run build
echo "✓ Plugin built"
echo ""

echo "================================"
echo "✓ Deployment Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API Key (optional for production):"
echo "   cd backend && echo 'MEM0_API_KEY=your-secret-key' >> .env"
echo ""
echo "2. Start backend:"
echo "   cd backend && ./start.sh"
echo ""
echo "3. Install plugin locally:"
echo "   cd plugin && bun link"
echo ""
echo "4. Configure OpenCode (~/.config/opencode/opencode.json):"
echo ""
cat << 'JSONEOF'
{
  "plugin": [
    ["@opencode-ai/mem0-plugin", {
      "backendUrl": "http://localhost:8000",
      "apiKey": "your-secret-key"
    }]
  ]
}
JSONEOF
echo ""
echo "For production deployment, see docs/DEPLOYMENT.md"
echo ""