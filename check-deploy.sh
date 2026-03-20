#!/bin/bash
# Check repository status and files

echo "📋 Files in repository:"
echo ""
echo "Diagrams:"
ls -lh *.drawio 2>/dev/null || echo "  (none)"
echo ""
echo "Python files:"
ls -lh *.py 2>/dev/null || echo "  (none)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Git Status:"
git status -s
if [ -z "$(git status -s)" ]; then
    echo "  ✅ Working tree clean - ready to deploy"
else
    echo ""
    echo "  ⚠️  Uncommitted changes - run ./deploy.sh to commit & push"
fi
