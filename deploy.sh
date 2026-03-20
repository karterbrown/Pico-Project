#!/bin/bash
# Deploy Python files to Raspberry Pi Pico

echo "🚀 Deploying to Pico..."

# Copy main.py to the Pico
mpremote fs cp main.py :main.py

echo "✅ Deployment complete!"
echo "Files deployed: main.py"
