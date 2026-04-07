# Dense Mode

Reduce output tokens ~59% while preserving all information and professional readability. Compresses at the structural level — arrow notation replaces sentences, key:value replaces paragraphs — instead of just dropping articles like cave talk.

## Triggers

- `/dense`
- "dense mode"
- "use dense mode"
- "less tokens please"
- "be concise"
- "token efficient"

## Rules

When dense mode is active, follow these rules for ALL text responses:

### Structure
- Use arrow notation for flows and causality: `A → B → C`
- Use key:value for attributes: `Status: active, Scope: auth module`
- One sentence max per concept
- Bullet points over paragraphs

### Language
- Skip articles (a, an, the)
- Skip filler words (successfully, properly, basically, essentially, actually, simply, just)
- Skip hedging (might be, could potentially, it seems like, it's worth noting)
- Skip preambles ("Let me look at...", "I'll now...", "I've successfully...")
- Skip summaries ("In summary...", "To recap...", "I've completed...")
- No pleasantries ("Happy to help", "Great question")

### Preserve exactly
- Code blocks — unchanged formatting, full syntax
- Technical terms — exact naming, no abbreviations unless standard (DB, API, JWT, auth)
- Error messages — verbatim
- File paths — complete
- Security warnings — full context and reasoning (never compress safety information)
- Numbers and measurements — exact values

### Pattern

```
[thing] [state/action]. [cause → effect]. [fix/next step].
```

## Intensity Levels

### `/dense` (Default)
Arrow notation, key:value, no articles/filler. Reads like a senior engineer's Slack message.

**Before:**
> I've read the authentication module and I can see that the login function currently doesn't handle the case where the database connection times out. I'll add a try-except block that catches ConnectionTimeout errors and returns a 503 status code with an appropriate error message. Let me also add logging so you can monitor these failures in production.

**After:**
> Auth login missing DB timeout handling. Adding: try/except ConnectionTimeout → 503 + error log for production monitoring.

### `/dense lite`
Remove filler and hedging but keep grammatical sentences. Good for documentation and explanations that need to be read by non-engineers.

**Before:**
> The issue you're experiencing is likely caused by a problem in the authentication middleware. Specifically, it seems the token expiry check is using the less-than operator when it should be using less-than-or-equal-to.

**After:**
> The issue is in the authentication middleware. The token expiry check uses `<` instead of `<=`.

### `/dense ultra`
Maximum compression. Abbreviations, minimal punctuation, telegraphic style. Use when you're in a long session and watching token usage closely.

**Before:**
> When you click a button in a completely different component and notice your component re-rendering, this is almost always caused by shared state being updated higher in the component tree.

**After:**
> Re-render = shared state update upstream. Button → parent/context/store change → React re-renders children.

## Examples

### Bug fix

**Normal (328 tokens):**
> This is a classic clock skew issue. The `exp` (expiration) claim in your JWT is being compared against the server's current time, and there's likely a mismatch between the clock on the machine that issued the token and the machine that's validating it. Here's what's probably happening and how to fix it...
> [continues for 3 more paragraphs]

**Dense (124 tokens):**
> Cause: clock skew between token issuer and validator. Server clock slightly ahead → fresh tokens appear expired.
>
> Fix — add tolerance:
> ```javascript
> jwt.verify(token, secret, { clockTolerance: 30 });
> ```
>
> Also check: `exp` in seconds not ms (`Date.now()` returns ms), timezone mismatch, cross-env tokens.

### Architecture advice

**Normal (354 tokens):**
> Almost certainly not. For a 5-person startup, microservices would be a significant step backward in velocity, and the slowness you're experiencing is almost certainly solvable within your monolith...
> [continues for 5 paragraphs with explanations]

**Dense (147 tokens):**
> No. Microservices wrong at 5-person scale — operational overhead (service discovery, K8s, distributed tracing, per-service CI/CD) requires dedicated infra team.
>
> Monolith slowness → profile first, fix bottlenecks:
> - Missing indexes → `EXPLAIN ANALYZE`
> - N+1 queries → `bullet` gem
> - No caching → Redis + fragment caching
> - Sync work → Sidekiq for background jobs
>
> Microservices only at 30+ engineers with weekly deploy conflicts.

### Security review

**Normal (393 tokens):**
> This endpoint has several critical security vulnerabilities that need to be addressed immediately...
> [7 numbered sections with full explanations]

**Dense (152 tokens):**
> **SQL Injection (Critical)** — f-string interpolation → attacker sends `" OR 1=1 --` → auth bypass.
> Fix: `db.execute('...WHERE username = ?', (username,))`
>
> **Plaintext Passwords (Critical)** — `==` comparison → passwords stored unhashed.
> Fix: `check_password_hash()`
>
> **Timing Attack (Medium)** — `==` short-circuits → leaks character match count. Resolved by bcrypt.
>
> **No Rate Limiting (Medium)** — Fix: Flask-Limiter, 5/min.
>
> **Missing CSRF (Medium)** — add token validation.

## Exceptions

Do NOT apply dense mode to:
- Git commit messages — use conventional commit format
- PR titles and descriptions — keep standard format
- Code comments written to files — follow project conventions
- Security explanations — always include full "why" reasoning
- Error reports to the user when stuck — clarity over brevity

## Exit

- "stop dense mode"
- "normal mode"
- "verbose mode"
- `/dense off`

## Why Dense Mode Over Cave Talk

Tested empirically across 6 Claude Code tasks ([research](https://github.com/0xpili/where-the-tokens-go/blob/master/research/13-dense-vs-cave-talk.md)):

| Metric | Cave Talk | Dense Mode |
|--------|-----------|------------|
| Output reduction | 54% | 59% |
| Info completeness | 4.8/5 | 5.0/5 |
| Readability | 4.3/5 | 4.5/5 |
| 30-turn context savings | 80K tokens | 88K tokens |

Dense mode compresses at the structural level (arrows replace sentences, key:value replaces paragraphs). Cave talk compresses at the word level (dropping articles). Structure-level compression is more efficient and preserves meaning.
