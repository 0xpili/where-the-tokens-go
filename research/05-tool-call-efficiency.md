# Experiment 5: Tool Call Efficiency — What's Cheap vs Expensive

**Method:** Reasoning about tool mechanics from inside Claude Code
**Date:** 2026-04-06

## Tool Token Costs (From Claude's Perspective)

Every tool call has three costs:
1. **Call cost** — The JSON arguments I generate (output tokens)
2. **Result cost** — What comes back and enters context (input tokens on next turn)
3. **Persistence cost** — The result stays in context for all future turns

### Tool Cost Ranking (Cheapest to Most Expensive)

#### 1. Glob — Very Cheap (~50-200 tokens per call)
- Call: pattern string (~20 tokens)
- Result: list of file paths (~5-50 tokens per match)
- Good for: "Does this file exist?" "What files match this pattern?"
- **Use this instead of** `find` via Bash or Agent for file discovery

#### 2. Grep (files_with_matches mode) — Cheap (~50-300 tokens)
- Call: pattern + path (~30 tokens)
- Result: list of matching file paths (~5-50 tokens per match)
- Good for: "Which files contain this function name?"
- **Use this instead of** spawning an Agent to search

#### 3. Grep (content mode) — Moderate (~100-2000 tokens)
- Call: pattern + path + context lines (~40 tokens)
- Result: matching lines with context (~50-200 tokens per match)
- Cost depends heavily on: number of matches, context lines requested
- **Tip:** Use `head_limit` to cap results. Default is 250 lines — that's a lot of tokens.

#### 4. Edit — Moderate (~100-500 tokens)
- Call: file_path + old_string + new_string (~100-300 tokens depending on change size)
- Result: confirmation (~50 tokens)
- Very efficient! The result is tiny. The call scales with change size.

#### 5. Read — Moderate to Expensive (~200-10,000+ tokens)
- Call: file_path (~20 tokens)  
- Result: ENTIRE file content with line numbers
- **This is where people waste the most tokens**
- A 200-line file = ~2000 tokens that persist in context forever
- **Always use `offset` and `limit`** when you know which section you need

#### 6. Write — Moderate (~200-5000 tokens)
- Call: file_path + entire file content (~varies massively)
- Result: confirmation (~30 tokens)
- The cost is in the output tokens (I generate the full file content)
- **Prefer Edit over Write** for modifications — Edit sends only the diff

#### 7. Bash — Unpredictable (~100-10,000+ tokens)
- Call: command string (~20-100 tokens)
- Result: command output (could be 0 to 10,000+ tokens)
- Long build outputs, test results, or log dumps can be massive
- **Tip:** Pipe through `head` or `tail` to limit output

#### 8. Agent — VERY Expensive (~10,000-100,000+ tokens)
- Creates an entirely new Claude instance with its own context
- The agent reads files, runs tools, and does work — all consuming tokens
- The return summary is small (~200-500 tokens), but the agent's internal work is 10-100K
- **Only use for genuinely complex, multi-step research tasks**
- **Never use for:** simple searches, reading a file, running a test

### Real Examples of Waste

**Wasteful: Using Agent to find a file**
```
Agent: "Find where the login function is defined"
```
Agent cost: spawns, reads file tree, greps multiple patterns, reads several files → 15K-30K tokens

**Efficient: Using Grep directly**
```
Grep: pattern="def login|function login|login.*=.*function" 
```
Grep cost: ~200 tokens

**Savings: 99%**

---

**Wasteful: Reading an entire file when you need one function**
```
Read: src/utils.ts  (500 lines, ~5000 tokens)
```

**Efficient: Reading just the section you need**
```
Read: src/utils.ts, offset=40, limit=20  (~200 tokens)
```

**Savings: 96%**

---

**Wasteful: Running tests and capturing all output**
```
Bash: npm test  (could produce 500+ lines of output → 5000+ tokens)
```

**Efficient: Running tests with minimal output**
```
Bash: npm test -- --silent 2>&1 | tail -5  (~100 tokens)
```

**Savings: 98%**

## How To Make Claude Code More Efficient (User Tips)

### 1. Point to specific files
Instead of "fix the bug", say "fix the null check in src/auth.ts around line 45". This prevents search cascades.

### 2. Say "don't explain" when you don't need explanations
Claude defaults to explaining what it's doing. If you just want the code changed, say so. This saves output tokens AND context accumulation.

### 3. Use `/clear` between unrelated tasks
The accumulated tool results from Task A are dead weight when working on Task B.

### 4. For large codebases, use .claudeignore
```
# .claudeignore
node_modules/
dist/
build/
*.min.js
*.map
coverage/
.git/
```
This prevents Claude from accidentally reading or searching through irrelevant directories.

### 5. Prefer small, specific asks over large vague ones
"Refactor the entire auth module" → Claude reads 10 files, spawns agents, produces massive output
"Extract the password validation into a separate function in src/auth/validate.ts" → Claude reads 1 file, makes 1 edit

The small ask is 10-50x cheaper in tokens.
