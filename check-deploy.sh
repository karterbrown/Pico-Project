#!/bin/bash

# Check-Deploy script for Pico-Project
# Shows detailed status and confirms before deploying
# Usage: ./check-deploy.sh "Your commit message"

# Check if commit message provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a commit message"
    echo "Usage: ./check-deploy.sh \"Your commit message\""
    exit 1
fi

# Show current branch
echo "🌿 Current branch: $(git branch --show-current)"
echo ""

# Show detailed status
echo "📊 Repository status:"
git status
echo ""

# Show what will be committed
echo "📝 Changes to be committed:"
git diff --stat
echo ""

# Show actual diff
echo "🔍 Detailed changes:"
git diff
echo ""

# Ask for confirmation
read -p "🤔 Deploy these changes? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Adding changes..."
    git add .
    
    echo "💾 Committing with message: '$1'"
    git commit -m "$1"
    
    echo "🚀 Pushing to GitHub..."
    git push
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deployed to GitHub!"
        echo "🔗 View at: https://github.com/karterbrown/Pico-Project"
    else
        echo "❌ Push failed. Check your connection and try again."
        exit 1
    fi
else
    echo "❌ Deployment cancelled."
    exit 0
fi
