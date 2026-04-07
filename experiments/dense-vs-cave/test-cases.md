# Dense Mode vs Cave Talk — Side-by-Side Test Cases

**Method:** Same prompt answered in 4 styles, token counts measured via word count × 1.3
**Date:** 2026-04-07

---

## Task 1: React Re-render Explanation (Prose-Heavy)

**Prompt:** "Why does my React component re-render when I click a button in a completely different component?"

### Normal (Default Claude)

When you click a button in a completely different component and notice your component re-rendering, this is almost always caused by shared state being updated higher in the component tree. Here's what's happening:

The button click triggers a state update — either via `useState` in a parent component, a context value change, or a global state manager like Redux or Zustand. When state updates in a parent component, React re-renders that parent and all of its children by default, even if the child's props haven't changed.

The most common scenarios are:

1. **Shared parent state** — Both components are children of a parent that holds state. When the button updates parent state, both children re-render.
2. **Context consumers** — If both components consume the same React Context, any update to that context triggers a re-render in all consumers, regardless of which part of the context value they actually use.
3. **Global state** — Redux, Zustand, or similar. If your component subscribes to a store slice that gets updated by the button click, it re-renders.

To fix this:
- Use `React.memo()` to skip re-renders when props haven't changed
- Split your context into smaller, more focused contexts
- Use `useMemo` and `useCallback` to stabilize references
- In Redux, use granular selectors with `useSelector` to only subscribe to the specific slice your component needs

The key diagnostic tool is React DevTools Profiler — it shows you exactly which components re-rendered and why. Enable "Highlight updates when components render" to see re-renders in real-time.

**Word count: 228 | Est. tokens: ~296**

### Caveman Full

Component re-render because shared state updates higher in tree. Button click triggers state change in parent or context or global store. React re-renders parent and all children by default.

Common causes:
1. **Shared parent state** — both components children of stateful parent. Parent state change, both re-render.
2. **Context consumers** — both consume same Context. Any context update triggers all consumers.
3. **Global state** — Redux/Zustand. Component subscribes to store slice button modifies.

Fix:
- `React.memo()` — skip re-render when props same
- Split context into smaller contexts
- `useMemo`/`useCallback` — stabilize references
- Redux: granular selectors with `useSelector`

Use React DevTools Profiler to see exactly what re-rendered and why.

**Word count: 109 | Est. tokens: ~142**

### Caveman Ultra

Re-render = shared state update upstream. Button → parent/context/store state change → React re-renders all children.

Causes:
1. Parent state shared between components
2. Same Context consumed
3. Global store slice overlap

Fix: `React.memo()`, split contexts, `useMemo`/`useCallback`, granular selectors.

Diagnose: React DevTools Profiler.

**Word count: 44 | Est. tokens: ~57**

### Dense Mode

Re-render cause: shared state updated upstream in component tree. Button click → state change (parent/context/global store) → React re-renders parent + all children by default.

Three patterns:
1. Shared parent state — both components are children, parent state change triggers both
2. Context consumers — same Context, any value change re-renders all consumers
3. Global store — component subscribes to slice the button modifies

Fixes: `React.memo()` for prop-stable components, split contexts for granular updates, `useMemo`/`useCallback` for reference stability, granular `useSelector` in Redux.

Diagnostic: React DevTools Profiler → shows re-render reasons per component.

**Word count: 96 | Est. tokens: ~125**

---

## Task 2: Fix Auth Middleware Bug (Code-Heavy)

**Prompt:** "The JWT middleware is rejecting valid tokens. The error is 'token expired' but the token was just created 2 seconds ago."

### Normal (Default Claude)

This is a classic clock skew issue. The `exp` (expiration) claim in your JWT is being compared against the server's current time, and there's likely a mismatch between the clock on the machine that issued the token and the machine that's validating it.

Here's what's probably happening and how to fix it:

The most common cause is that your token issuer sets `exp` based on its system clock, but the validating server's clock is slightly ahead. Even a few seconds of drift can cause "token expired" errors for freshly minted tokens.

```javascript
// Problem: No clock tolerance
const decoded = jwt.verify(token, secret);

// Fix: Add clockTolerance to account for clock skew
const decoded = jwt.verify(token, secret, {
  clockTolerance: 30, // Allow 30 seconds of clock skew
});
```

Other possible causes:

1. **Timezone confusion** — If you're using `Date.now()` somewhere and comparing it with UTC-based `iat`/`exp` claims, you might be off by hours.
2. **Seconds vs milliseconds** — JWT `exp` is in seconds since epoch, but `Date.now()` returns milliseconds. If you accidentally set `exp` using milliseconds, the token "expired" billions of seconds in the "past."
3. **Token reuse across environments** — Token issued in staging (different clock) being validated in production.

```javascript
// Common mistake: using milliseconds instead of seconds
const token = jwt.sign({ userId }, secret, {
  expiresIn: Date.now() + 3600000, // WRONG: milliseconds
});

// Correct: use relative time string or seconds
const token = jwt.sign({ userId }, secret, {
  expiresIn: '1h', // Correct
});
```

To diagnose: decode the token at jwt.io and compare the `iat` and `exp` timestamps with your server's `Date.now() / 1000`. If they don't align, you've found your clock skew.

**Word count: 252 | Est. tokens: ~328**

### Caveman Full

Clock skew issue. Token issuer clock and validator clock not synced. Even few seconds drift cause "expired" on fresh tokens.

Fix — add clock tolerance:

```javascript
// Before: no tolerance
const decoded = jwt.verify(token, secret);

// After: allow 30s skew
const decoded = jwt.verify(token, secret, {
  clockTolerance: 30,
});
```

Other causes:
1. **Seconds vs milliseconds** — JWT `exp` in seconds, `Date.now()` in milliseconds. Using ms makes token "expire" instantly.
2. **Timezone confusion** — `Date.now()` compared against UTC-based claims.
3. **Cross-environment** — token from staging validated in production.

```javascript
// Wrong: milliseconds
expiresIn: Date.now() + 3600000

// Right: relative string
expiresIn: '1h'
```

Diagnose: decode at jwt.io, compare `exp` with server `Date.now() / 1000`.

**Word count: 118 | Est. tokens: ~153**

### Caveman Ultra

Clock skew. Issuer clock ≠ validator clock.

Fix:
```javascript
jwt.verify(token, secret, { clockTolerance: 30 });
```

Also check: `exp` in seconds not ms (`Date.now()` returns ms), timezone mismatch, cross-env tokens.

```javascript
// Wrong
expiresIn: Date.now() + 3600000
// Right
expiresIn: '1h'
```

Diagnose: jwt.io → compare `exp` vs `Date.now()/1000`.

**Word count: 49 | Est. tokens: ~64**

### Dense Mode

Cause: clock skew between token issuer and validator. Server clock slightly ahead → fresh tokens appear expired.

Fix — add tolerance:
```javascript
jwt.verify(token, secret, { clockTolerance: 30 }); // 30s skew allowance
```

Other causes:
- Seconds/milliseconds mismatch — JWT `exp` uses seconds, `Date.now()` returns ms. Using ms = instant "expiry"
- Timezone confusion — `Date.now()` vs UTC-based `iat`/`exp`
- Cross-environment — staging-issued token validated in production

```javascript
// Wrong: milliseconds
expiresIn: Date.now() + 3600000
// Right: relative time
expiresIn: '1h'
```

Diagnose: decode at jwt.io → compare `exp` against server's `Date.now() / 1000`.

**Word count: 95 | Est. tokens: ~124**

---

## Task 3: Microservices vs Monolith (Prose-Heavy)

**Prompt:** "We're a 5-person startup. Our Rails monolith is getting slow. Should we move to microservices?"

### Normal (Default Claude)

Almost certainly not. For a 5-person startup, microservices would be a significant step backward in velocity, and the slowness you're experiencing is almost certainly solvable within your monolith.

Here's why microservices are a bad fit right now:

**The operational overhead will crush you.** Microservices require: service discovery, API gateways, distributed tracing, container orchestration (Kubernetes or similar), CI/CD pipelines per service, inter-service auth, eventual consistency handling, and on-call rotation across services. Netflix has 1000+ engineers to manage this. You have 5.

**Your actual problem is probably solvable.** Common causes of a slow Rails monolith:
- **Missing database indexes** — Run `EXPLAIN ANALYZE` on your slow queries. Adding an index is a 5-minute fix.
- **N+1 queries** — Install the `bullet` gem. It catches these automatically.
- **No caching** — Add Redis caching for expensive queries and fragment caching for views.
- **Fat controllers / bloated Active Record callbacks** — Refactor to service objects.
- **Background jobs** — Move email sending, PDF generation, and API calls to Sidekiq.

**The right path for a 5-person team:**
1. **Profile first** — Use `rack-mini-profiler` and `pg_stat_statements` to find actual bottlenecks
2. **Optimize the hot paths** — Usually 3-5 queries cause 80% of the slowness
3. **Add caching** — Redis + fragment caching for read-heavy pages
4. **Extract modules, not services** — Use Rails engines or packwerk gems to enforce boundaries within the monolith
5. **Consider microservices only when** — You have 30+ engineers, deploy conflicts are weekly, and different parts of the system need to scale independently

The monolith is your competitive advantage right now. It lets 5 people ship features fast with shared models, one deploy pipeline, and simple debugging. Don't trade that for distributed systems complexity.

**Word count: 272 | Est. tokens: ~354**

### Caveman Full

No. Microservices wrong for 5-person startup. Slowness solvable in monolith.

**Why not microservices:**
Operational overhead crushes small teams. Need service discovery, API gateways, distributed tracing, K8s, per-service CI/CD, inter-service auth. Netflix has 1000+ engineers for this. You have 5.

**Actual problem — fix these first:**
- Missing DB indexes — `EXPLAIN ANALYZE` slow queries, add indexes
- N+1 queries — install `bullet` gem, catches automatically
- No caching — add Redis for expensive queries, fragment caching for views
- Background jobs — move email/PDF/API calls to Sidekiq

**Right path:**
1. Profile with `rack-mini-profiler` + `pg_stat_statements`
2. Optimize 3-5 hot queries (80% of slowness)
3. Add Redis caching
4. Extract modules not services — Rails engines or packwerk
5. Microservices only at 30+ engineers with deploy conflicts

Monolith is competitive advantage. One deploy, shared models, simple debugging. Don't trade for distributed complexity.

**Word count: 139 | Est. tokens: ~181**

### Caveman Ultra

No. 5 ppl = monolith. Microservices need infra team you don't have.

Fix monolith:
- DB indexes (`EXPLAIN ANALYZE`)
- N+1s (`bullet` gem)
- Redis caching
- Sidekiq for background jobs
- `rack-mini-profiler` to find bottlenecks

Microservices only at 30+ engineers. Monolith = your advantage now.

**Word count: 42 | Est. tokens: ~55**

### Dense Mode

No. Microservices wrong at 5-person scale — operational overhead (service discovery, K8s, distributed tracing, per-service CI/CD) requires dedicated infra team.

Monolith slowness → profile first, fix bottlenecks:
- Missing indexes → `EXPLAIN ANALYZE` on slow queries
- N+1 queries → `bullet` gem for detection
- No caching → Redis + fragment caching for read-heavy paths
- Sync work in request cycle → Sidekiq for email/PDF/API calls

Progression path: profile (`rack-mini-profiler` + `pg_stat_statements`) → optimize hot queries (3-5 cause 80% of slowness) → add caching → extract modules (Rails engines/packwerk) → microservices only at 30+ engineers with weekly deploy conflicts.

Monolith = competitive advantage at your size. One deploy pipeline, shared models, simple debugging.

**Word count: 113 | Est. tokens: ~147**

---

## Task 4: Security Review of a PR (Mixed Code+Prose)

**Prompt:** "Review this authentication endpoint for security issues:
```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = db.execute(f'SELECT * FROM users WHERE username = \"{username}\"').fetchone()
    if user and user['password'] == password:
        session['user_id'] = user['id']
        return redirect('/dashboard')
    return 'Invalid credentials', 401
```"

### Normal (Default Claude)

This endpoint has several critical security vulnerabilities that need to be addressed immediately:

**1. SQL Injection (Critical)**
The f-string query construction directly interpolates user input into the SQL query. An attacker can bypass authentication entirely:
```
username: " OR 1=1 --
```

Fix — use parameterized queries:
```python
user = db.execute(
    'SELECT * FROM users WHERE username = ?',
    (username,)
).fetchone()
```

**2. Plaintext Password Storage (Critical)**
The code compares `user['password'] == password`, which means passwords are stored in plaintext in the database. If the database is compromised, all user passwords are exposed.

Fix — use bcrypt or argon2:
```python
from werkzeug.security import check_password_hash

if user and check_password_hash(user['password'], password):
    session['user_id'] = user['id']
```

**3. Timing Attack on Password Comparison (Medium)**
String comparison with `==` short-circuits on the first different character, which leaks information about how many characters of the password are correct. This is a timing side-channel attack.

Fix — use constant-time comparison (already handled if you switch to bcrypt/argon2, which includes this internally).

**4. Username Enumeration (Low-Medium)**
The response doesn't distinguish between "user not found" and "wrong password," which is good. However, the response time might differ (database query vs no query), which could still leak whether a username exists.

**5. No Rate Limiting (Medium)**
There's no protection against brute force attacks. An attacker can try thousands of passwords per second.

Fix — add rate limiting with Flask-Limiter:
```python
from flask_limiter import Limiter
limiter = Limiter(app, default_limits=["5 per minute"])

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
```

**6. Missing CSRF Protection (Medium)**
If this is a form-based login, there's no CSRF token validation. An attacker could craft a page that submits a login form on behalf of a victim.

**7. No Input Validation (Low)**
No length limits or character validation on username/password. Could lead to denial of service with extremely large inputs.

**Word count: 302 | Est. tokens: ~393**

### Caveman Full

Multiple critical vulnerabilities:

**1. SQL Injection (Critical)**
f-string interpolation in query. Attacker bypasses auth with `" OR 1=1 --`.

Fix:
```python
user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
```

**2. Plaintext Passwords (Critical)**
`user['password'] == password` means passwords stored in plain text.

Fix:
```python
from werkzeug.security import check_password_hash
if user and check_password_hash(user['password'], password):
```

**3. Timing Attack (Medium)**
`==` comparison short-circuits, leaks character match info. Fixed by bcrypt/argon2 (constant-time internally).

**4. No Rate Limiting (Medium)**
No brute force protection. Add Flask-Limiter:
```python
@limiter.limit("5 per minute")
```

**5. Missing CSRF (Medium)**
No token validation on form submission.

**6. No Input Validation (Low)**
No length limits. Large inputs could DoS.

**Word count: 119 | Est. tokens: ~155**

### Caveman Ultra

Critical bugs:

1. **SQL injection** — f-string in query. Fix: parameterized `db.execute('...WHERE username = ?', (username,))`
2. **Plaintext passwords** — Fix: `check_password_hash()`
3. **Timing attack** — `==` leaks info. Fix: bcrypt (constant-time)
4. **No rate limit** — Fix: Flask-Limiter
5. **No CSRF** — add token
6. **No input validation** — add length limits

**Word count: 50 | Est. tokens: ~65**

### Dense Mode

Critical vulnerabilities:

**SQL Injection (Critical)** — f-string interpolation → attacker sends `" OR 1=1 --` → auth bypass.
Fix: parameterized queries:
```python
user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
```

**Plaintext Passwords (Critical)** — `==` comparison means passwords stored unhashed. DB compromise = all credentials exposed.
Fix:
```python
from werkzeug.security import check_password_hash
if user and check_password_hash(user['password'], password):
```

**Timing Attack (Medium)** — `==` short-circuits → leaks character match count. Resolved by bcrypt/argon2 (constant-time internally).

**No Rate Limiting (Medium)** — unlimited login attempts → brute force. Fix: Flask-Limiter, 5/min.

**Missing CSRF (Medium)** — form submission without token validation.

**No Input Validation (Low)** — no length limits → potential DoS with large payloads.

**Word count: 117 | Est. tokens: ~152**

---

## Task 5: Docker Multi-Stage Build (Code-Heavy)

**Prompt:** "Write a multi-stage Dockerfile for a Node.js API that minimizes the final image size."

### Normal (Default Claude)

Here's a multi-stage Dockerfile optimized for a Node.js API:

```dockerfile
# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build (if using TypeScript or a build step)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Production image
FROM node:20-alpine AS runner
WORKDIR /app

# Security: run as non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 appuser

# Copy only production dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy only built output from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json

USER appuser

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

Key decisions explained:

1. **Alpine base** — `node:20-alpine` is ~50MB vs ~350MB for the full `node:20` image. Use Alpine unless you need glibc-specific native modules.

2. **Separate dependency and build stages** — The `deps` stage installs only production dependencies (`--only=production`), while the `builder` stage installs everything (including devDependencies for compilation). The final image only gets the production `node_modules`.

3. **Non-root user** — Running as root in containers is a security risk. The `appuser` has minimal permissions.

4. **Layer ordering** — `package.json` is copied before source code. Docker caches layers, so if your source changes but dependencies don't, the `npm ci` layer is cached and doesn't re-run.

5. **`npm ci` over `npm install`** — `ci` is deterministic (uses lock file exactly), faster, and cleans `node_modules` first.

Typical result: final image around 80-120MB instead of 500MB+.

**Word count: 237 | Est. tokens: ~308**

### Caveman Full

```dockerfile
# Stage 1: Production deps only
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Minimal runtime
FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

Key points:
- Alpine base (~50MB vs ~350MB full)
- Separate deps/build stages — final image gets production `node_modules` only
- Non-root user for security
- `package.json` copied first for layer caching
- `npm ci` over `npm install` for deterministic builds
- Final image: ~80-120MB

**Word count: 126 | Est. tokens: ~164**

### Caveman Ultra

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

Alpine, 3-stage, prod deps only in final. ~80-120MB.

**Word count: 82 | Est. tokens: ~107**

### Dense Mode

```dockerfile
# Deps: production only
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Build: full deps + compile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime: minimal
FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json
USER appuser
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

Design: Alpine base (~50MB vs ~350MB), separate deps/build stages → final image has production node_modules only. Non-root user, layer caching via package.json-first copy, `npm ci` for determinism. Result: ~80-120MB.

**Word count: 114 | Est. tokens: ~148**

---

## Task 6: Refactor + Run Tests (Tool-Dominated)

**Prompt:** "Refactor the calculateDiscount function to handle percentage and fixed discounts separately, then run the tests."

### Normal (Default Claude)

Let me read the current implementation first.

I can see the `calculateDiscount` function handles both discount types in a single block with nested conditionals. I'll refactor it into two clear helper functions.

I've made the following changes to `src/pricing/discount.ts`:

```typescript
function applyPercentageDiscount(price: number, percentage: number): number {
  return price * (1 - percentage / 100);
}

function applyFixedDiscount(price: number, amount: number): number {
  return Math.max(0, price - amount);
}

export function calculateDiscount(
  price: number,
  discount: Discount
): number {
  if (discount.type === 'percentage') {
    return applyPercentageDiscount(price, discount.value);
  }
  return applyFixedDiscount(price, discount.value);
}
```

The key improvements are:
- Each discount type has its own function with clear responsibility
- The fixed discount includes a floor at 0 to prevent negative prices
- The main function is now a clean dispatcher based on discount type
- Both helpers are testable independently

Now let me run the tests:

```
$ npm test

PASS src/pricing/discount.test.ts
  ✓ applies percentage discount correctly (3ms)
  ✓ applies fixed discount correctly (1ms)
  ✓ fixed discount floors at zero (1ms)
  ✓ handles zero discount (1ms)

Tests: 4 passed, 4 total
```

All tests pass. The refactoring preserved the original behavior while making the logic clearer and easier to extend for new discount types.

**Word count: 196 | Est. tokens: ~255**

### Caveman Full

Read current function. Has nested conditionals mixing both discount types.

Refactored `src/pricing/discount.ts`:

```typescript
function applyPercentageDiscount(price: number, percentage: number): number {
  return price * (1 - percentage / 100);
}

function applyFixedDiscount(price: number, amount: number): number {
  return Math.max(0, price - amount);
}

export function calculateDiscount(price: number, discount: Discount): number {
  if (discount.type === 'percentage') {
    return applyPercentageDiscount(price, discount.value);
  }
  return applyFixedDiscount(price, discount.value);
}
```

Tests:
```
$ npm test
PASS src/pricing/discount.test.ts — 4 passed, 4 total
```

All passing.

**Word count: 78 | Est. tokens: ~101**

### Caveman Ultra

Refactored `src/pricing/discount.ts` — split into `applyPercentageDiscount` + `applyFixedDiscount`:

```typescript
function applyPercentageDiscount(price: number, pct: number): number {
  return price * (1 - pct / 100);
}
function applyFixedDiscount(price: number, amt: number): number {
  return Math.max(0, price - amt);
}
export function calculateDiscount(price: number, d: Discount): number {
  return d.type === 'percentage'
    ? applyPercentageDiscount(price, d.value)
    : applyFixedDiscount(price, d.value);
}
```

`npm test` — 4/4 pass.

**Word count: 59 | Est. tokens: ~77**

### Dense Mode

Read current function → nested conditionals mixing discount types. Refactored into two helpers:

```typescript
function applyPercentageDiscount(price: number, percentage: number): number {
  return price * (1 - percentage / 100);
}

function applyFixedDiscount(price: number, amount: number): number {
  return Math.max(0, price - amount);
}

export function calculateDiscount(price: number, discount: Discount): number {
  if (discount.type === 'percentage') {
    return applyPercentageDiscount(price, discount.value);
  }
  return applyFixedDiscount(price, discount.value);
}
```

Changes: separate responsibility per type, floor at 0 for fixed discounts, clean dispatch.

`npm test` → 4 passed, 4 total.

**Word count: 77 | Est. tokens: ~100**
