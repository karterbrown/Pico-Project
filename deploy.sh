#!/bin/bash
# Commit and push changes to git repository

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Committing changes..."
    git add -A
    
    # Use provided message or default
    if [ -z "$1" ]; then
        git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
    else
        git commit -m "$1"
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Changes committed"
    else
        echo "⚠️  Commit failed"
        exit 1
    fi
else
    echo "✅ No changes to commit"
fi

echo "🚀 Pushing to repository..."
git push

if [ $? -eq 0 ]; then
    echo "✅ Deploy complete!"
else
    echo "❌ Push failed"
    exit 1
fi
