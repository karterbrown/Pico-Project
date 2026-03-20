#!/bin/bash

# Deploy script for Pico-Project
# Usage: ./deploy.sh "Your commit message"

# Check if commit message provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a commit message"
    echo "Usage: ./deploy.sh \"Your commit message\""
    exit 1
fi

# Show what files changed
echo "📝 Files to be committed:"
git status --short

# Add all changes
echo ""
echo "📦 Adding changes..."
git add .

# Commit with provided message
echo "💾 Committing changes..."
git commit -m "$1"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push

# Check if push was successful
if [ $? -eq 0 ]; then
    echo "✅ Successfully deployed to GitHub!"
    echo "🔗 View at: https://github.com/karterbrown/Pico-Project"
else
    echo "❌ Push failed. Check your connection and try again."
    exit 1
fi
