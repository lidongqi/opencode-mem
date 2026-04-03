#!/bin/bash

set -e

echo "================================"
echo "OpenCode mem0 Plugin Builder"
echo "================================"

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PLUGIN_DIR"

echo "Installing dependencies..."
bun install

echo ""
echo "Building plugin..."
bun run build

echo ""
if [ -d "dist" ]; then
    echo "✓ Build successful!"
    echo ""
    echo "Built files:"
    ls -lh dist/
    echo ""
    echo "To test locally:"
    echo "  bun link"
    echo ""
    echo "To publish to npm:"
    echo "  bun publish --access public"
else
    echo "✗ Build failed!"
    exit 1
fi