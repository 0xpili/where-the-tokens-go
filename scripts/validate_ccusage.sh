#!/bin/bash
# Validate ccusage installation and document accuracy caveats
# Per D-03: ccusage used for session-level aggregation with documented accuracy caveats

set -euo pipefail

echo "=== ccusage Validation ==="
echo ""

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo "FAIL: npx not found. Install Node.js first."
    exit 1
fi
echo "PASS: npx available ($(npx --version))"

# Run ccusage session report (limited output)
echo ""
echo "--- Running: npx ccusage@latest session --limit 3 ---"
npx ccusage@latest session --limit 3 2>&1 || echo "NOTE: ccusage may need session data to display"

echo ""
echo "=== ACCURACY CAVEATS (per research findings) ==="
echo "1. ccusage reads JSONL session logs which undercount input tokens by 100-174x"
echo "2. JSONL input_tokens field is a streaming placeholder (75% are 0 or 1)"
echo "3. Thinking tokens are excluded from JSONL entirely"
echo "4. USE FOR: Relative session comparisons (session A vs session B)"
echo "5. DO NOT USE FOR: Absolute token count claims"
echo "6. CROSS-REFERENCE WITH: statusbar JSON capture or /cost command"
echo ""
echo "=== Validation Complete ==="
