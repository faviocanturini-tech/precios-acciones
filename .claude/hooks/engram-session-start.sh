#!/bin/bash
# Engram: Load memory context at session start
cd "C:/Users/favio/Desktop/TRADING"
CONTEXT=$(./engram.exe context TRADING 2>/dev/null)
if [ -n "$CONTEXT" ]; then
    echo "<engram-context>"
    echo "$CONTEXT"
    echo "</engram-context>"
fi
