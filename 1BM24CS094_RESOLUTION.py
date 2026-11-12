import re
from collections import namedtuple

# ============================================================
#  1. PARSER   (ASCII or unicode input)
#     ~ not | & and | | or | -> implies | <-> iff
#     forall x (...)   exists y (...)   (forall x)(...)
#     forall x: body   <- colon/dot = quantifier covers EVERYTHING after it
#     Quantifier WITHOUT colon covers only the next unit, so use brackets.
#     Variables = names bound by a quantifier. Everything else = constant.
# ============================================================
_SYM = {'∀': ' forall ', '∃': ' exists ', '¬': '~', '∧': '&', '∨': '|',
        '→': '->', '⇒': '->', '↔': '<->', '⇔': '<->', '[': '(', ']': ')'}
_TOK = re.compile(r'\s*(<->|<=>|->|=>|[A-Za-z_][A-Za-z0-9_]*|[()~!&|,:.])')

def tokenize(s):
    for k, v in _SYM.items():
        s = s.replace(k, v)
    toks, pos = [], 0
    while pos < len(s):
        if s[pos:].strip() == '':
            break
        m = _TOK.match(s, pos)
        if not m:
            raise ValueError(f"Unexpected character near: {s[pos:pos+10]!r}")
        toks.append(m.group(1)); pos = m.end()
    return toks

_QUANT = {'forall': 'all', 'exists': 'ex'}
def _isq(t): return t is not None and t.lower() in _QUANT
def _isid(t): return t is not None and re.match(r'[A-Za-z_]', t) is not None

class _Parser:
    def __init__(s, text): s.t = tokenize(text); s.i = 0
    def peek(s, k=0): return s.t[s.i + k] if s.i + k < len(s.t) else None
    def nxt(s): t = s.peek(); s.i += 1; return t
    def expect(s, x):
        if s.nxt() != x: raise ValueError(f"Expected '{x}'")
    def parse(s):
        f = s.iff(frozenset())
        if s.peek() is not None: raise ValueError(f"Unexpected token '{s.peek()}'")
        return f
    def iff(s, b):
        l = s.imp(b)
        while s.peek() in ('<->', '<=>'):
            s.nxt(); l = ('iff', l, s.imp(b))
        return l
    def imp(s, b):
        l = s.or_(b)
        if s.peek() in ('->', '=>'):
            s.nxt(); return ('imp', l, s.imp(b))
        return l
    def or_(s, b):
        l = s.and_(b)
        while s.peek() == '|':
            s.nxt(); l = ('or', l, s.and_(b))
        return l
    def and_(s, b):
        l = s.un(b)
        while s.peek() == '&':
            s.nxt(); l = ('and', l, s.un(b))
        return l
    def un(s, b):
        t = s.peek()
        if t is None: raise ValueError("Formula ended unexpectedly")
        if t in ('~', '!'):
            s.nxt(); return ('not', s.un(b))
        if _isq(t): return s.quant(b, False)
        if t == '(' and _isq(s.peek(1)) and s._qparen(): return s.quant(b, True)
        if t == '(':
            s.nxt(); f = s.iff(b); s.expect(')'); return f
        if _isid(t): return s.atom(b)
        raise ValueError(f"Unexpected token '{t}'")
    def _qparen(s):
        # is this '(forall x)' / '(exists x, y)' (quantifier alone in brackets)?
        j = s.i + 2
        while j < len(s.t) and _isid(s.t[j]):
            j += 1
            if j < len(s.t) and s.t[j] == ',': j += 1
            else: break
        return j < len(s.t) and s.t[j] == ')'
    def quant(s, b, paren):
        if paren: s.nxt()
        kind = _QUANT[s.nxt().lower()]
        vs = []
        while True:
            v = s.nxt()
            if not _isid(v): raise ValueError("Expected a variable name after quantifier")
            vs.append(v)
            if s.peek() == ',': s.nxt()
            else: break
        if paren: s.expect(')')
        b2 = b | set(vs)
        if s.peek() in (':', '.'):
            s.nxt(); body = s.iff(b2)
        else:
            body = s.un(b2)
        for v in reversed(vs): body = (kind, v, body)
        return body
    def atom(s, b):
        name = s.nxt(); args = []
        if s.peek() == '(':
            s.nxt()
            args.append(s.term(b))
            while s.peek() == ',': s.nxt(); args.append(s.term(b))
            s.expect(')')
        return ('atom', name, tuple(args))
    def term(s, b):
        name = s.nxt()
        if not _isid(name): raise ValueError(f"Bad term '{name}'")
        if s.peek() == '(':
            s.nxt(); args = [s.term(b)]
            while s.peek() == ',': s.nxt(); args.append(s.term(b))
            s.expect(')')
            return ('func', name, tuple(args))
        return ('var', name) if name in b else ('const', name)

def parse(text): return _Parser(text).parse()

# ============================================================
#  2. PRINTING
# ============================================================
def term_str(t):
    if t[0] in ('var', 'const'): return t[1]
    return f"{t[1]}({','.join(term_str(a) for a in t[2])})"

_P = {'iff': 1, 'imp': 2, 'or': 3, 'and': 4}
_OP = {'iff': '↔', 'imp': '→', 'or': '∨', 'and': '∧'}
def f_str(f, outer=0):
    k = f[0]
    if k == 'atom':
        return f[1] + (f"({','.join(term_str(a) for a in f[2])})" if f[2] else '')
    if k == 'not': return '¬' + f_str(f[1], 5)
    if k in ('all', 'ex'):
        s = ('∀' if k == 'all' else '∃') + f[1] + ' ' + f_str(f[2], 5)
        return f"({s})" if outer > 0 else s
    p = _P[k]
    if k == 'imp': lo, ro = p + 1, p
    elif k == 'iff': lo, ro = p + 1, p + 1
    else: lo = p if f[1][0] == k else p + 1; ro = p if f[2][0] == k else p + 1
    s = f"{f_str(f[1], lo)} {_OP[k]} {f_str(f[2], ro)}"
    return f"({s})" if p < outer else s

# ============================================================
#  3. CNF CONVERSION  (the 6 steps from the slides)
# ============================================================
Lit = namedtuple('Lit', 'neg pred args')
def lit_str(l):
    return ('¬' if l.neg else '') + l.pred + (f"({','.join(term_str(a) for a in l.args)})" if l.args else '')
def clause_str(c): return ' ∨ '.join(lit_str(l) for l in c) if c else '{ }'

_POOL = list('xyzwuvstrqpnmkjihgfedcba')
def _fresh(avoid):
    for n in _POOL:
        if n not in avoid: return n
    i = 1
    while True:
        for n in _POOL:
            if f"{n}{i}" not in avoid: return f"{n}{i}"
        i += 1

class Ctx:
    """Shared across all sentences so variables / Skolem symbols never clash."""
    def __init__(s): s.used = set(); s.symbols = set(); s.nc = 0; s.nf = 0
    def skolem(s, is_func):
        pool = list('FGHKLMNPQR') if is_func else list('ABCDEJ')
        for n in pool:
            if n not in s.symbols: s.symbols.add(n); return n
        while True:
            if is_func: s.nf += 1; n = f"F{s.nf}"
            else: s.nc += 1; n = f"C{s.nc}"
            if n not in s.symbols: s.symbols.add(n); return n

def _symbols(f, acc=None):
    acc = set() if acc is None else acc
    def tm(t):
        if t[0] in ('const', 'func'): acc.add(t[1])
        if t[0] == 'func': [tm(a) for a in t[2]]
    k = f[0]
    if k == 'atom': acc.add(f[1]); [tm(a) for a in f[2]]
    elif k == 'not': _symbols(f[1], acc)
    elif k in ('all', 'ex'): _symbols(f[2], acc)
    else: _symbols(f[1], acc); _symbols(f[2], acc)
    return acc

def _boundvars(f, acc=None):
    acc = set() if acc is None else acc
    k = f[0]
    if k == 'not': _boundvars(f[1], acc)
    elif k in ('all', 'ex'): acc.add(f[1]); _boundvars(f[2], acc)
    elif k != 'atom': _boundvars(f[1], acc); _boundvars(f[2], acc)
    return acc

def elim_imp(f):
    k = f[0]
    if k == 'atom': return f
    if k == 'not': return ('not', elim_imp(f[1]))
    if k in ('all', 'ex'): return (k, f[1], elim_imp(f[2]))
    a, b = elim_imp(f[1]), elim_imp(f[2])
    if k == 'imp': return ('or', ('not', a), b)
    if k == 'iff': return ('and', ('or', ('not', a), b), ('or', ('not', b), a))
    return (k, a, b)

def nnf(f, neg=False):
    k = f[0]
    if k == 'atom': return ('not', f) if neg else f
    if k == 'not': return nnf(f[1], not neg)
    if k in ('and', 'or'):
        kk = k if not neg else ('or' if k == 'and' else 'and')
        return (kk, nnf(f[1], neg), nnf(f[2], neg))
    kk = k if not neg else ('ex' if k == 'all' else 'all')
    return (kk, f[1], nnf(f[2], neg))

def _sub_term(t, m):
    if t[0] == 'var': return m.get(t[1], t)
    if t[0] == 'func': return ('func', t[1], tuple(_sub_term(a, m) for a in t[2]))
    return t

def _sub(f, m):
    k = f[0]
    if k == 'atom': return ('atom', f[1], tuple(_sub_term(a, m) for a in f[2]))
    if k == 'not': return ('not', _sub(f[1], m))
    if k in ('all', 'ex'): return (k, f[1], _sub(f[2], m))
    return (k, _sub(f[1], m), _sub(f[2], m))

def standardize(f, ctx, env=None, reserved=None):
    env = env or {}
    reserved = _boundvars(f) if reserved is None else reserved
    k = f[0]
    if k == 'atom': return _sub(f, {a: ('var', b) for a, b in env.items()})
    if k == 'not': return ('not', standardize(f[1], ctx, env, reserved))
    if k in ('all', 'ex'):
        v = f[1]
        new = v if v not in ctx.used and v not in ctx.symbols else _fresh(ctx.used | reserved | ctx.symbols)
        ctx.used.add(new)
        return (k, new, standardize(f[2], ctx, {**env, v: new}, reserved))
    return (k, standardize(f[1], ctx, env, reserved), standardize(f[2], ctx, env, reserved))

def skolemize(f, ctx, univ=()):
    k = f[0]
    if k == 'atom': return f
    if k == 'not': return ('not', skolemize(f[1], ctx, univ))
    if k == 'all': return ('all', f[1], skolemize(f[2], ctx, univ + (f[1],)))
    if k == 'ex':
        if univ: t = ('func', ctx.skolem(True), tuple(('var', u) for u in univ))
        else: t = ('const', ctx.skolem(False))
        return skolemize(_sub(f[2], {f[1]: t}), ctx, univ)
    return (k, skolemize(f[1], ctx, univ), skolemize(f[2], ctx, univ))

def drop_all(f):
    k = f[0]
    if k == 'atom': return f
    if k == 'not': return ('not', drop_all(f[1]))
    if k == 'all': return drop_all(f[2])
    return (k, drop_all(f[1]), drop_all(f[2]))

def _lit(f):
    return Lit(False, f[1], f[2]) if f[0] == 'atom' else Lit(True, f[1][1], f[1][2])

def _dedupe(lits):
    out = []
    for l in lits:
        if l not in out: out.append(l)
    return tuple(out)

def to_clauses(f):
    k = f[0]
    if k == 'and': return to_clauses(f[1]) + to_clauses(f[2])
    if k == 'or':
        return [_dedupe(a + b) for a in to_clauses(f[1]) for b in to_clauses(f[2])]
    return [(_lit(f),)]

def cnf_str(cl):
    parts = [(' ∨ '.join(lit_str(l) for l in c)) for c in cl]
    return ' ∧ '.join(p if len(c) == 1 else f"({p})" for p, c in zip(parts, cl))

def to_cnf(src, ctx=None, verbose=True, title=None):
    """Print the 6 CNF steps and return the list of clauses."""
    ctx = ctx or Ctx()
    f = parse(src) if isinstance(src, str) else src
    ctx.symbols |= _symbols(f)
    if title and verbose: print(f"\n=== {title} ===")
    steps = []
    s1 = elim_imp(f);            steps.append(("1. Eliminate ↔ and →", s1))
    s2 = nnf(s1);                steps.append(("2. Move ¬ inwards", s2))
    s3 = standardize(s2, ctx);   steps.append(("3. Standardize variables", s3))
    s4 = skolemize(s3, ctx);     steps.append(("4. Skolemize (remove ∃)", s4))
    s5 = drop_all(s4);           steps.append(("5. Drop ∀", s5))
    cl = to_clauses(s5)
    if verbose:
        print(f"Original                     : {f_str(f)}")
        prev = f
        for name, g in steps:
            note = "   (no change)" if g == prev else ""
            print(f"{name:<29}: {f_str(g)}{note}")
            prev = g
        print(f"{'6. Distribute ∨ over ∧':<29}: {cnf_str(cl)}")
        print("Clauses:")
        for i, c in enumerate(cl, 1): print(f"   {i}. {clause_str(c)}")
    return cl

def cnf_steps(sentence, steps=False):
    """Convert one FOL sentence to CNF. Prints only the final CNF unless steps=True."""
    try: cl = to_cnf(sentence, verbose=steps)
    except ValueError as e: print("Parse error:", e); return
    print("CNF:", cnf_str(cl))
    for i, c in enumerate(cl, 1): print(f"  clause {i}: {clause_str(c)}")

# ============================================================
#  4. UNIFICATION + RESOLUTION
# ============================================================
def _walk(t, s):
    while t[0] == 'var' and t[1] in s: t = s[t[1]]
    return t

def _occurs(v, t, s):
    t = _walk(t, s)
    if t[0] == 'var': return t[1] == v
    if t[0] == 'func': return any(_occurs(v, a, s) for a in t[2])
    return False

def unify_terms(a, b, s):
    a, b = _walk(a, s), _walk(b, s)
    if a == b: return s
    if a[0] == 'var': return None if _occurs(a[1], b, s) else {**s, a[1]: b}
    if b[0] == 'var': return None if _occurs(b[1], a, s) else {**s, b[1]: a}
    if a[0] == 'func' and b[0] == 'func' and a[1] == b[1] and len(a[2]) == len(b[2]):
        for x, y in zip(a[2], b[2]):
            s = unify_terms(x, y, s)
            if s is None: return None
        return s
    return None

def _apply(t, s):
    t = _walk(t, s)
    if t[0] == 'func': return ('func', t[1], tuple(_apply(a, s) for a in t[2]))
    return t

def _vars_t(t, acc):
    if t[0] == 'var': acc.add(t[1])
    elif t[0] == 'func': [_vars_t(a, acc) for a in t[2]]

def _vars(c):
    acc = set()
    for l in c: [_vars_t(a, acc) for a in l.args]
    return acc

def _depth(t):
    return 1 + max((_depth(a) for a in t[2]), default=0) if t[0] == 'func' else 0

def _rename(c, m):
    return tuple(Lit(l.neg, l.pred, tuple(_sub_term(a, m) for a in l.args)) for l in c)

def _apply_clause(c, s):
    return _dedupe([Lit(l.neg, l.pred, tuple(_apply(a, s) for a in l.args)) for l in c])

def _unify_lits(l1, l2):
    if l1.pred != l2.pred or len(l1.args) != len(l2.args): return None
    s = {}
    for a, b in zip(l1.args, l2.args):
        s = unify_terms(a, b, s)
        if s is None: return None
    return s

def _theta_str(s, vars_):
    items = []
    for v in sorted(vars_):
        if v in s:
            val = _apply(('var', v), s)
            if val != ('var', v): items.append(f"{term_str(val)}/{v}")
    return '{' + ', '.join(items) + '}' if items else ''

def _is_taut(c):
    return any(a.neg != b.neg and a.pred == b.pred and a.args == b.args for a in c for b in c)

def _canon(c):
    blind = lambda l: ('~' if l.neg else '') + l.pred + re.sub(r'\b[a-z]\w*\b(?!\()', '_', ','.join(term_str(a) for a in l.args))
    seen = {}
    def rn(t):
        if t[0] == 'var':
            seen.setdefault(t[1], f"v{len(seen)}"); return ('var', seen[t[1]])
        if t[0] == 'func': return ('func', t[1], tuple(rn(a) for a in t[2]))
        return t
    return tuple(sorted((l.neg, l.pred, tuple(term_str(rn(a)) for a in l.args)) for l in sorted(c, key=blind)))

def resolvents(c1, c2):
    clash = _vars(c1) & _vars(c2)
    avoid = _vars(c1) | _vars(c2); m = {}
    for v in sorted(clash):
        n = _fresh(avoid); avoid.add(n); m[v] = ('var', n)
    c2r = _rename(c2, m) if m else c2
    for i, a in enumerate(c1):
        for j, b in enumerate(c2r):
            if a.neg != b.neg:
                s = _unify_lits(a, b)
                if s is not None:
                    rest = [l for k, l in enumerate(c1) if k != i] + [l for k, l in enumerate(c2r) if k != j]
                    yield _apply_clause(rest, s), _theta_str(s, _vars(c1) | _vars(c2r)), c2r

def factors(c):
    for i in range(len(c)):
        for j in range(i + 1, len(c)):
            if c[i].neg == c[j].neg:
                s = _unify_lits(c[i], c[j])
                if s is not None and s:
                    yield _apply_clause(c, s), _theta_str(s, _vars(c))

class Node:
    def __init__(s, id, lits, kind, parents=(), theta='', pa=None, pb=None):
        s.id, s.lits, s.kind, s.parents, s.theta, s.pa, s.pb = id, lits, kind, list(parents), theta, pa, pb

def draw_tree(root, nodes, save=None):
    import matplotlib.pyplot as plt
    def build(nid):
        n = nodes[nid]
        ch = [build(p) for p in n.parents]
        ch.sort(key=lambda c: -c['size'])
        return dict(text=clause_str(n.lits), theta=n.theta, ch=ch, size=1 + sum(c['size'] for c in ch))
    tree = build(root)
    cnt = [0]; maxd = [0]
    def place(n, d):
        n['y'] = d; maxd[0] = max(maxd[0], d)
        if not n['ch']: n['x'] = cnt[0]; cnt[0] += 1
        else:
            for c in n['ch']: place(c, d + 1)
            n['x'] = sum(c['x'] for c in n['ch']) / len(n['ch'])
    place(tree, 0)
    W = max(8, cnt[0] * 3.3); H = max(4, (maxd[0] + 1) * 1.15)
    fig, ax = plt.subplots(figsize=(W, H)); ax.axis('off')
    def draw(n):
        for c in n['ch']:
            ax.plot([n['x'], c['x']], [n['y'], c['y']], color='gray', lw=1, zorder=1)
            draw(c)
        if n['ch'] and n['theta']:
            c = n['ch'][-1]
            ax.text((n['x'] + c['x']) / 2 + .05, (n['y'] + c['y']) / 2, n['theta'], color='tab:blue',
                    fontsize=9, ha='left', va='center', zorder=3,
                    bbox=dict(fc='white', ec='none', alpha=.85, pad=1))
        ax.text(n['x'], n['y'], n['text'] if n['text'] != '{ }' else '{ }   Hence proved',
                ha='center', va='center', fontsize=10, zorder=2,
                bbox=dict(boxstyle='round,pad=0.3', fc='#fff8dc' if not n['ch'] else 'white', ec='gray'))
    draw(tree)
    ax.set_xlim(-0.8, cnt[0] - 0.2); ax.set_ylim(-0.6, maxd[0] + 0.6)
    ax.set_title("Resolution proof tree (leaves = clauses, bottom = empty clause)", fontsize=11)
    plt.tight_layout()
    if save: plt.savefig(save, dpi=150)
    plt.show()

def prove(premises, goal, show_cnf_steps=True, max_nodes=5000, max_lits=8, plot=True, save=None):
    """premises: list of FOL strings.  goal: FOL string.  Proves by resolution refutation."""
    ctx = Ctx()
    try:
        pf = [parse(p) for p in premises]; gf = parse(goal)
    except ValueError as e:
        print("Parse error:", e); return False
    for f in pf + [gf]: ctx.symbols |= _symbols(f)

    print("KNOWLEDGE BASE")
    for i, f in enumerate(pf, 1): print(f"  {i}. {f_str(f)}")
    print(f"GOAL: {f_str(gf)}")

    nodes, kb, sos, seen = {}, [], [], set()
    def add(lits, kind, **kw):
        n = Node(len(nodes) + 1, lits, kind, **kw); nodes[n.id] = n; return n

    for i, f in enumerate(pf, 1):
        for c in to_cnf(f, ctx, verbose=show_cnf_steps, title=f"Premise {i} to CNF"):
            if _is_taut(c) or _canon(c) in seen: continue
            seen.add(_canon(c)); kb.append(add(c, 'kb'))
    goal_cl = to_cnf(('not', gf), ctx, verbose=show_cnf_steps, title="NEGATED GOAL to CNF")
    for c in goal_cl:
        if _canon(c) in seen: continue
        seen.add(_canon(c)); sos.append(add(c, 'goal'))

    print("\nCLAUSE LIST (CNF)")
    for n in kb: print(f"  {n.id:>2}. {clause_str(n.lits)}")
    for n in nodes.values():
        if n.kind == 'goal': print(f"  {n.id:>2}. {clause_str(n.lits)}      <-- negated goal")

    usable, processed, found = list(kb), [], None
    def consider(lits, kind, parents, theta, pa=None, pb=None):
        nonlocal found
        if _is_taut(lits) or len(lits) > max_lits: return
        if any(_depth(a) > 6 for l in lits for a in l.args): return
        key = _canon(lits)
        if key in seen: return
        seen.add(key)
        n = add(lits, kind, parents=parents, theta=theta, pa=pa, pb=pb)
        if not lits: found = n
        else: sos.append(n)

    while sos and not found and len(nodes) < max_nodes:
        sos.sort(key=lambda n: (len(n.lits), n.id))
        g = sos.pop(0)
        for lits, th in factors(g.lits):
            consider(lits, 'factor', [g.id], th, pa=g.lits)
            if found: break
        for o in usable + processed + [g]:
            if found: break
            for lits, th, c2r in resolvents(g.lits, o.lits):
                consider(lits, 'res', [g.id, o.id], th, pa=g.lits, pb=c2r)
                if found: break
        processed.append(g)

    if not found:
        print(f"\n✗ No contradiction found ({len(nodes)} clauses generated). "
              "Either the goal does not follow, or the search limit was hit.")
        return False

    used, seen_ids = [], set()
    def visit(i):
        if i in seen_ids: return
        seen_ids.add(i)
        for p in nodes[i].parents: visit(p)
        used.append(i)
    visit(found.id)
    label, r = {}, 0
    for i in used:
        if nodes[i].kind in ('kb', 'goal'): label[i] = str(i)
        else: r += 1; label[i] = f"R{r}"

    print("\nRESOLUTION STEPS")
    for i in used:
        n = nodes[i]
        if n.kind == 'res':
            a, b = n.parents
            print(f"  {label[i]}: resolve {label[a]} [{clause_str(n.pa)}]")
            print(f"{'':>6}with    {label[b]} [{clause_str(n.pb)}]")
            print(f"{'':>6}unifier {n.theta or '(none needed)'}   =>   {clause_str(n.lits)}")
        elif n.kind == 'factor':
            print(f"  {label[i]}: factor {label[n.parents[0]]} [{clause_str(n.pa)}]  unifier {n.theta}  =>  {clause_str(n.lits)}")
    print("\n✓ Empty clause { } derived: the negated goal contradicts the KB, so the goal is PROVED.")
    if plot:
        try: draw_tree(found.id, nodes, save)
        except Exception as e: print("(could not draw tree:", e, ")")
    return True


# ============================================================
#  MAIN: type your input
# ============================================================
mode = input("1 = convert to CNF, 2 = prove by resolution: ").strip()
if mode == "1":
    cnf_steps(input("FOL sentence: "))
else:
    prem = []
    print("Enter premises one per line, blank line to finish:")
    while True:
        p = input(f"  premise {len(prem)+1}: ").strip()
        if not p: break
        prem.append(p)
    prove(prem, input("Goal to prove: "))