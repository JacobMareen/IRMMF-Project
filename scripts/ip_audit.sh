#!/bin/bash

echo "Starting IP & License Audit..."
echo "----------------------------------------"

echo "[1] Scanning for Third-Party Copyright Headers..."
grep -r "Copyright" . | grep -v "IRMMF Project" | grep -v "node_modules" | grep -v ".git" | head -n 20
if [ $? -ne 0 ]; then
    echo "  > CLEAN: No obvious third-party copyright headers found in source."
else
    echo "  > NOTE: Check the above lines for potential third-party code."
fi
echo ""

echo "[2] Scanning for Viral Licenses (GPL/AGPL)..."
grep -r "GPL" . | grep -v "node_modules" | grep -v ".git" | grep -v "LGPL" | head -n 20
if [ $? -ne 0 ]; then
    echo "  > CLEAN: No GPL/AGPL headers found in source."
else
    echo "  > WARNING: Potential GPL code found. Verify compatibility."
fi
echo ""

echo "[3] Auditing Asset Directories..."
if [ -d "frontend/public" ]; then
    echo "  > frontend/public contents:"
    ls -R frontend/public
else
    echo "  > frontend/public does not exist (Clean)."
fi

if [ -d "app/static" ]; then
    echo "  > app/static contents:"
    ls -R app/static
else
    echo "  > app/static does not exist (Clean)."
fi
echo ""

echo "----------------------------------------"
echo "Audit Complete. Review findings above."
