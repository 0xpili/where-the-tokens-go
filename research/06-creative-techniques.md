# Experiment 6: Creative & Unconventional Token-Saving Techniques

**Method:** Direct analysis from inside Claude Code + community findings
**Date:** 2026-04-06

## Technique 1: The /clear Habit (Most Impactful)

Not creative but criminally underused. Most users never type `/clear`.

**The pattern:**
```
> Fix bug in auth.ts
[Claude fixes it]
> /clear
> Now add the new API endpoint for users
[Fresh context, no auth.ts baggage]
```

**Why it works:** You trade 20K tokens of system reload for potentially 100K+ of stale context removal.

**When NOT to clear:** When the next task builds on the current one ("now add tests for what you just wrote").

## Technique 2: The Focused /compact

Most people use `/compact` naked. But you can tell it what to keep:

```
/compact Keep the database schema decisions and the API response format. Drop everything about file searching and setup.
```

This produces dramatically better summaries than blind compaction. The model knows what to prioritize.

## Technique 3: The One-Shot Batch

Instead of an interactive back-and-forth:
```
> Add error handling
[response]
> Also add logging  
[response]  
> And input validation
[response]
> Run the tests
[response]
```

Write a single comprehensive prompt:
```
> In src/auth/login.ts:
> 1. Add try-catch error handling around the DB call
> 2. Add structured logging with user ID context  
> 3. Add Zod validation for email and password inputs
> 4. Run tests after all changes
> 
> Don't explain each step, just do it.
```

**4 round trips → 1 round trip.** Each round trip resends the entire conversation, so this saves 3x the context resend cost.

## Technique 4: The .claudeignore Diet

Create `.claudeignore` to prevent Claude from reading irrelevant files:

```
# Heavy directories
node_modules/
.next/
dist/
build/
coverage/

# Large generated files
*.min.js
*.min.css
*.map
package-lock.json
yarn.lock
pnpm-lock.yaml

# Binary files
*.png
*.jpg
*.gif
*.ico
*.woff
*.woff2

# Test fixtures with large data
**/__fixtures__/
**/testdata/
```

Without this, a single `Grep` could match inside `node_modules/` and Claude reads those matches into context. Thousands of wasted tokens.

## Technique 5: Strategic CLAUDE.md

**Minimal high-impact CLAUDE.md:**
```markdown
# ProjectName
Stack: [language, framework, key libs]
Tests: [how to run them]
Don't explain your changes — just make them.
Keep responses under 3 sentences unless asked for detail.
```

That last line alone — "keep responses under 3 sentences" — reduces output tokens by 50-70% for routine tasks. And since responses persist in context, this compounds.

## Technique 6: The "Just Do It" Instruction

Adding this to CLAUDE.md or your prompt:

```
When making code changes:
- Don't describe what you're about to do
- Don't explain what you just did
- Don't suggest next steps unless asked
- Just make the change and show the diff
```

This eliminates the "Let me first read the file... Now I'll make the change... I've successfully updated..." pattern that can add 200-500 unnecessary output tokens per interaction.

## Technique 7: File Reference Precision

**Vague (triggers multi-file search):**
```
> Where is the user model defined?
```
Claude: Grep → Glob → Read 3 files → narrow down → answer. 5+ tool calls, 3000+ tokens of file content in context.

**Precise (direct hit):**
```
> Read src/models/user.ts lines 1-30
```
Claude: Read (30 lines). 1 tool call, ~300 tokens.

## Technique 8: Output Format Control

**Default (verbose):**
```
> What environment variables does this project need?
```
Claude writes a 500-token explanation with context and recommendations.

**Controlled:**
```
> List environment variables from .env.example. Just names and one-word descriptions. No prose.
```
Claude writes a 50-token list.

## Technique 9: Avoid the Exploration Spiral

When Claude doesn't find what it expects, it enters "exploration mode" — reading more files, trying different search patterns, sometimes spawning agents. This can burn 10K-50K tokens on a search that goes nowhere.

**Prevention:** If Claude is searching for something and not finding it, interrupt:
```
> Stop searching. It's in src/lib/auth.ts
```

One message saves potentially thousands of tokens of fruitless exploration.

## Technique 10: Session Segmentation for Large Tasks

**Bad:** One continuous session for a major refactor (100+ turns, 500K+ context)

**Good:** Break it into focused sessions:
```
Session 1: Plan the refactor (discuss, outline steps)
/clear
Session 2: Refactor file A
/clear
Session 3: Refactor file B  
/clear
Session 4: Update tests
/clear
Session 5: Integration check
```

Each session starts fresh at 20K instead of carrying 200K+ of accumulated context.

## Summary: Impact Ranking

| Technique | Token Savings | Effort |
|-----------|--------------|--------|
| /clear between tasks | 30-50% | Zero |
| Batch requests | 20-40% | Low |
| .claudeignore | 15-30% | One-time setup |
| "Don't explain" in CLAUDE.md | 10-20% | One-time setup |
| Focused /compact | 10-20% | Low |
| File precision | 10-25% | Medium (habit) |
| Interrupt exploration spirals | 5-20% per incident | Medium (awareness) |
| Session segmentation | 20-40% for large tasks | Medium |
| Output format control | 5-15% | Low |
| MCP server cleanup | 5-15% | One-time setup |
