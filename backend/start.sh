#!/bin/bash

set -e

echo "================================"
echo "OpenCode mem0 Backend Starter"
echo "================================"

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
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
    echo "✓ Created .env file. Please edit it to configure your settings."
    echo ""
fi

echo "Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

echo ""
echo "Configuration:"
echo "  LLM Provider: $LLM_PROVIDER"
echo "  LLM Model: $LLM_MODEL"
echo "  Embedding Provider: $EMBEDDING_PROVIDER"
echo "  Embedding Model: $EMBEDDING_MODEL"
echo "  Vector Store: $VECTOR_STORE"
echo "  Backend Port: 8000"
echo "  Auth Enabled: $([ -n "$MEM0_API_KEY" ] && echo "Yes" || echo "No (dev mode)")"
echo ""

echo "Starting backend server..."
python3 -m backend.src.main