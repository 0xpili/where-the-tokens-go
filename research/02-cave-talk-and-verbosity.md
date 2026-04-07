# Experiment 2: Cave Talk & Verbosity Reduction — Does It Actually Matter?

**Method:** Direct observation and reasoning from inside Claude Code
**Date:** 2026-04-06

## The Claim

A viral tweet suggested asking Claude to "talk like a caveman" to reduce token consumption. The premise: shorter responses = fewer output tokens = slower usage limit consumption.

## Analysis From Inside Claude Code

### Where Tokens Actually Go In A Typical Session

Let me trace a typical Claude Code interaction:

**User asks:** "Add error handling to the login function"

**What happens (token flow):**
1. **Input (re-sent every turn):**
   - System prompt: ~4K tokens (cached)
   - Tool schemas: ~12K tokens (cached)
   - CLAUDE.md + memory: ~2K tokens (cached)
   - Full conversation history: 5K-500K+ tokens (partially cached)
   - User's new message: ~20 tokens
   
2. **Output (Claude's response):**
   - Thinking/reasoning (extended thinking): potentially ~10-30K tokens (INVISIBLE to user but billed)
   - Text response to user: ~100-500 tokens
   - Tool calls (Read, Edit, Bash): ~200-2000 tokens per tool call
   
3. **Tool results (added to context):**
   - Read file result: ~500-5000 tokens per file
   - Edit confirmation: ~50 tokens
   - Bash output: varies wildly

### The Math On Cave Talk

**Normal response:** "I've added try-except error handling to the login function. The function now catches AuthenticationError and DatabaseError separately, logs the error details, and returns appropriate HTTP status codes." (~40 tokens)

**Cave talk:** "Me add error catch. Login safe now." (~10 tokens)

**Savings:** ~30 tokens per response.

**But the REAL cost of that turn was:**
- Input context resend: 20,000-200,000 tokens
- Extended thinking: 10,000-30,000 tokens  
- Tool calls (Read + Edit + maybe Bash): 5,000-15,000 tokens
- The text response: 40 tokens

**Per-turn, cave talk saves 30 tokens out of 35,000-245,000 total. That's 0.01% to 0.08%.** But this per-turn framing is misleading — see the Conclusion for why compounding changes the math significantly.

### When Cave Talk DOES Matter

Cave talk (or any verbosity reduction) matters more when:

1. **Claude is writing long explanations without tool calls** — Pure Q&A, no code. If the response IS the main output (not tool calls), then shorter responses = real savings.

2. **The response text persists in context** — Because text responses stay in conversation history, a 500-token explanation adds 500 tokens to EVERY future turn. Over 30 turns, that's 15,000 extra input tokens from one verbose response.

3. **You're asking for summaries/analysis** — Research tasks where Claude writes paragraphs. Here, "be concise" genuinely helps.

### When Cave Talk Has Minimal Per-Turn Impact

- **Code editing tasks** — The tool calls (Read, Edit) dominate. The text is a minor footnote per turn (but compounds — see Conclusion).
- **Multi-file operations** — Agent spawning, file searching, grepping. Text output is tiny compared to tool overhead.
- **Long sessions** — Context re-sending dwarfs output tokens per turn, but compressed responses compound savings across all turns.

## The Real Verbosity Problem

The bigger waste isn't the final response — it's **Claude's tendency to:**

1. **Re-read files it already read** — Each Read adds thousands of tokens
2. **Explain what it's about to do before doing it** — "Let me first check..." "I'll now..." 
3. **Summarize what it just did after doing it** — "I've successfully updated the file to..."
4. **Use Agent tool for simple searches** — An Agent spawn costs 10K-50K tokens when a Grep would cost 200

## What Actually Works (Ranked by Impact)

### Tier 1: Context Management (saves 30-60%)
- **`/clear` between unrelated tasks** — Prevents context compounding. The single highest-impact habit.
- **`/compact` at ~60% utilization** — Better summaries than auto-compaction at 95%.
- **Disable unused MCP servers** — Each one taxes every request.

### Tier 2: Reducing Tool Overhead (saves 15-30%)
- **Be specific about files** — "Edit src/auth/login.ts" vs "fix the login function" (avoids search overhead)
- **Batch requests** — "Do X, Y, and Z" instead of three separate messages (avoids 3x context resend)
- **Use Glob/Grep over Agent** — Direct search is 50-100x cheaper than spawning an agent to search

### Tier 3: Output Reduction (saves 5-15%)
- **"No explanations, just do it" in CLAUDE.md** — Eliminates preambles and summaries
- **"Be terse" / "Skip the walkthrough"** — Reduces conversational padding
- **Cave talk** — Works but only matters for text-heavy interactions

### Tier 4: Almost No Impact
- **Shorter prompts** — Your prompt is 20 tokens vs 15K+ of system overhead. Doesn't matter.
- **Abbreviations in code comments** — Tokenizer handles them similarly
- **Removing "please" and "thanks"** — 2 tokens. Literally noise.

## Conclusion

**Cave talk isn't a meme — but it's Tier 4, not Tier 1.**

My original analysis here underestimated cave talk by measuring only per-turn savings (~30 tokens). [Experiment 13](13-dense-vs-cave-talk.md) ran an empirical test: 6 tasks × 4 styles. Caveman full achieves 54% output reduction, and that compounds — ~80K tokens saved over a 30-turn session (4-18% of total session cost). That's not a rounding error.

But the core thesis holds: context management and tool overhead still dwarf output reduction. And **dense mode** (arrow notation, key:value, no articles/filler) beats caveman — 59% reduction, zero information loss, professional readability vs broken English. Dense mode compresses at the *structural* level (arrow notation replaces sentences), while cave talk compresses at the *word* level (dropping articles).

The hierarchy remains:
1. Managing your context window (/clear, /compact) — 30-60%
2. Being specific to avoid search overhead — 15-30%
3. Batching work to reduce round-trips — 20-40%
4. Dense mode responses — 4-18% via compounding
