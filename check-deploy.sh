#!/bin/bash
# Check what files are in the repository

echo "📋 Files in repository:"
echo ""
echo "Diagrams:"
ls -lh *.drawio 2>/dev/null || echo "  (none)"
echo ""
echo "Python files:"
ls -lh *.py 2>/dev/null || echo "  (none)"
