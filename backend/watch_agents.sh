#!/bin/bash
# Watch Agent Activity in Real-Time

echo "╔════════════════════════════════════════════╗"
echo "║   LIVE AGENT ACTIVITY MONITOR              ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Monitoring: /home/samarth/AIBlogs/backend/server.log"
echo "Press Ctrl+C to stop"
echo ""
echo "Legend:"
echo "  ✓ = Success"
echo "  → = Working"
echo "  ✗ = Error"
echo ""
echo "════════════════════════════════════════════"
echo ""

# Watch logs with color highlighting
tail -f server.log | grep --color=always -E "\[.*\].*forum|\[.*\].*post|\[.*\].*comment|✓|ERROR|Failed|Posted|Created|Commented"
