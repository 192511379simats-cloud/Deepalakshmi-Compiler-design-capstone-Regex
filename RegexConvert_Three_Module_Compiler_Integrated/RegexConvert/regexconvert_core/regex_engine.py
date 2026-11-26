"""Regex parsing, Thompson NFA, subset DFA, minimization and language algorithms."""
from collections import deque
import json

EPS = "ε"
class RegexError(ValueError):
    pass

def tokenize(pattern):
    if not isinstance(pattern, str) or not pattern.strip():
        raise RegexError("Enter a regular expression. Empty input is not treated as epsilon; use ε.")
    tokens, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c.isspace():
            i += 1; continue
        if c in "()|*+?":
            tokens.append(c)
        elif c == "ε":
            tokens.append("ε")
        elif c == "∅":
            tokens.append("∅")
        elif c == "\\":
            i += 1
            if i >= len(pattern):
                raise RegexError("A trailing escape (\\\\) has no character to escape.")
            tokens.append(("LITERAL", pattern[i]))
        elif c in ".[]{}^$":
            raise RegexError(f"Unsupported regex operator '{c}'. This project uses formal regular-expression syntax; escape it to treat it as a literal.")
        else:
            tokens.append(("LITERAL", c))
        i += 1
    # Insert explicit concatenation operator ·
    out = []
    def can_end(t):
        return t == ")" or t in ("*", "+", "?") or t == "ε" or t == "∅" or (isinstance(t, tuple) and t[0] == "LITERAL")
    def can_start(t):
        return t == "(" or t == "ε" or t == "∅" or (isinstance(t, tuple) and t[0] == "LITERAL")
    for idx, t in enumerate(tokens):
        if idx and can_end(tokens[idx-1]) and can_start(t):
            out.append("·")
        out.append(t)
    return out

def token_label(t):
    if isinstance(t, tuple): return t[1]
    return t

def to_postfix(tokens):
    prec = {"|":1, "·":2}
    out, stack = [], []
    expect_operand = True
    for t in tokens:
        if isinstance(t, tuple) or t in ("ε", "∅"):
            if not expect_operand: raise RegexError("Missing operator between expression terms.")
            out.append(t); expect_operand = False
        elif t == "(":
            if not expect_operand: raise RegexError("Missing concatenation operator before '('.")
            stack.append(t)
        elif t == ")":
            if expect_operand: raise RegexError("Unexpected ')' or empty group.")
            while stack and stack[-1] != "(": out.append(stack.pop())
            if not stack: raise RegexError("Unmatched closing parenthesis ')'.")
            stack.pop()
            expect_operand = False
        elif t in ("*", "+", "?"):
            if expect_operand: raise RegexError(f"Operator '{t}' has no operand.")
            out.append(t); expect_operand = False
        elif t in ("|", "·"):
            if expect_operand: raise RegexError(f"Operator '{t}' is missing its left operand.")
            while stack and stack[-1] != "(" and prec.get(stack[-1], 0) >= prec[t]:
                out.append(stack.pop())
            stack.append(t); expect_operand = True
        else:
            raise RegexError(f"Unknown token: {t}")
    if expect_operand: raise RegexError("Expression ends with an operator or has no operand.")
    while stack:
        t = stack.pop()
        if t == "(": raise RegexError("Unmatched opening parenthesis '('.")
        out.append(t)
    return out

def postfix_ast(postfix):
    stack=[]
    for t in postfix:
        if isinstance(t, tuple):
            stack.append({"type":"literal","value":t[1]})
        elif t in ("ε","∅"):
            stack.append({"type":"epsilon" if t=="ε" else "empty"})
        elif t in ("*","+","?"):
            if not stack: raise RegexError(f"Operator '{t}' has no operand.")
            stack.append({"type":{"*":"star","+":"plus","?":"optional"}[t],"child":stack.pop()})
        elif t in ("|","·"):
            if len(stack)<2: raise RegexError(f"Operator '{t}' requires two operands.")
            right,left=stack.pop(),stack.pop()
            stack.append({"type":"union" if t=="|" else "concat","left":left,"right":right})
        else: raise RegexError("Could not construct expression tree.")
    if len(stack)!=1: raise RegexError("Malformed regular expression.")
    return stack[0]

def ast_to_text(ast):
    typ=ast["type"]
    if typ=="literal":
        v=ast["value"]
        return ("\\"+v) if v in r"\()|*+?ε∅" else v
    if typ=="epsilon": return "ε"
    if typ=="empty": return "∅"
    if typ in ("star","plus","optional"):
        sym={"star":"*","plus":"+","optional":"?"}[typ]
        c=ast_to_text(ast["child"])
        if ast["child"]["type"] in ("union","concat"): c="("+c+")"
        return c+sym
    l,r=ast_to_text(ast["left"]),ast_to_text(ast["right"])
    if typ=="concat":
        if ast["left"]["type"]=="union": l="("+l+")"
        if ast["right"]["type"]=="union": r="("+r+")"
        return l+r
    return "("+l+"|"+r+")"

def compile_regex(pattern):
    tokens=tokenize(pattern)
    postfix=to_postfix(tokens)
    ast=postfix_ast(postfix)
    nfa=ast_to_nfa(ast)
    dfa=nfa_to_dfa(nfa)
    return {"tokens":[token_label(t) if not (isinstance(t,str) and t=="·") else "CONCAT" for t in tokens],
            "postfix":[token_label(t) for t in postfix], "ast":ast, "nfa":nfa, "dfa":dfa}

def ast_to_nfa(ast):
    states=[]; trans={}; counter=[0]
    def new():
        s=f"q{counter[0]}"; counter[0]+=1; states.append(s); trans[s]={}; return s
    def edge(a,sym,b):
        trans[a].setdefault(sym,[]).append(b)
    def build(node):
        typ=node["type"]
        if typ in ("literal","epsilon","empty"):
            a,b=new(),new()
            if typ=="literal": edge(a,node["value"],b)
            elif typ=="epsilon": edge(a,EPS,b)
            return a,b
        if typ=="concat":
            a,x=build(node["left"]); y,b=build(node["right"]); edge(x,EPS,y); return a,b
        if typ=="union":
            a,b=new(),new(); x,y=build(node["left"]); u,v=build(node["right"])
            edge(a,EPS,x); edge(a,EPS,u); edge(y,EPS,b); edge(v,EPS,b); return a,b
        if typ=="star":
            a,b=new(),new(); x,y=build(node["child"])
            edge(a,EPS,b); edge(a,EPS,x); edge(y,EPS,x); edge(y,EPS,b); return a,b
        if typ=="plus":
            x,y=build(node["child"]); a,b=new(),new()
            edge(a,EPS,x); edge(y,EPS,x); edge(y,EPS,b); return a,b
        if typ=="optional":
            a,b=new(),new(); x,y=build(node["child"])
            edge(a,EPS,b); edge(a,EPS,x); edge(y,EPS,b); return a,b
        raise RegexError("Unsupported syntax tree node.")
    start,final=build(ast)
    return {"kind":"NFA","states":states,"alphabet":sorted({s for row in trans.values() for s in row if s!=EPS}),
            "transitions":trans,"start":start,"accepting":[final]}

def epsilon_closure(nfa, seeds):
    seen=set(seeds); stack=list(seeds)
    while stack:
        s=stack.pop()
        for t in nfa["transitions"].get(s,{}).get(EPS,[]):
            if t not in seen: seen.add(t); stack.append(t)
    return frozenset(seen)

def nfa_move(nfa, states, symbol):
    return {t for s in states for t in nfa["transitions"].get(s,{}).get(symbol,[])}

def nfa_to_dfa(nfa):
    alphabet=sorted(nfa["alphabet"])
    startset=epsilon_closure(nfa,[nfa["start"]])
    subsets=[startset]; ids={startset:"D0"}; queue=deque([startset]); trans={}
    accepting=set(nfa["accepting"])
    while queue:
        subset=queue.popleft(); sid=ids[subset]; trans[sid]={}
        for sym in alphabet:
            dest=epsilon_closure(nfa,nfa_move(nfa,subset,sym))
            if not dest: continue
            if dest not in ids:
                ids[dest]=f"D{len(ids)}"; subsets.append(dest); queue.append(dest)
            trans[sid][sym]=ids[dest]
    states=list(ids.values())
    return {"kind":"DFA","states":states,"alphabet":alphabet,"transitions":trans,"start":"D0",
            "accepting":[ids[s] for s in subsets if set(s)&accepting],
            "subsets":{ids[s]:sorted(s) for s in subsets}}

def complete_dfa(dfa):
    states=list(dfa["states"])
    raw_trans=dfa.get("transitions", {})
    # Defensive normalization for imported/externally supplied representations.
    if not isinstance(raw_trans, dict):
        raise ValueError("DFA transitions must be an object keyed by source state.")
    trans={s:dict(raw_trans.get(s,{})) for s in states}
    a=dict(dfa)
    sink="__DEAD__"
    missing=any(sym not in trans[s] for s in states for sym in a["alphabet"])
    if missing:
        while sink in states: sink+="_"
        states.append(sink); trans[sink]={sym:sink for sym in a["alphabet"]}
        for s in states:
            if s==sink: continue
            for sym in a["alphabet"]:
                trans[s].setdefault(sym,sink)
    a.update(states=states,transitions=trans)
    return a

def minimize_dfa(dfa):
    if not dfa["alphabet"]:
        # Empty alphabet: one state suffices for the only possible string, epsilon.
        accepted=dfa["start"] in dfa["accepting"]
        return {"kind":"DFA","states":["M0"],"alphabet":[],"transitions":{"M0":{}},
                "start":"M0","accepting":["M0"] if accepted else [],"subsets":{"M0":[dfa["start"]]}}
    a=complete_dfa(dfa); states=a["states"]; alpha=a["alphabet"]; finals=set(a["accepting"])
    P=[set(finals),set(states)-set(finals)]; P=[x for x in P if x]
    changed=True
    while changed:
        changed=False; newP=[]
        for group in P:
            buckets={}
            for s in group:
                sig=tuple(next(i for i,g in enumerate(P) if a["transitions"][s][c] in g) for c in alpha)
                buckets.setdefault(sig,set()).add(s)
            newP.extend(buckets.values())
            if len(buckets)>1: changed=True
        P=newP
    # Remove unreachable partition groups
    group_of={s:i for i,g in enumerate(P) for s in g}
    start_group=group_of[a["start"]]; reachable={start_group}; q=deque([start_group])
    while q:
        gi=q.popleft(); rep=next(iter(P[gi]))
        for c in alpha:
            gj=group_of[a["transitions"][rep][c]]
            if gj not in reachable: reachable.add(gj); q.append(gj)
    ordered=[start_group]+sorted(reachable-{start_group})
    names={gi:f"M{i}" for i,gi in enumerate(ordered)}
    trans={}; subsets={}
    for gi in ordered:
        name=names[gi]; rep=next(iter(P[gi])); trans[name]={}
        subsets[name]=sorted(P[gi])
        for c in alpha:
            gj=group_of[a["transitions"][rep][c]]
            if gj in names: trans[name][c]=names[gj]
    return {"kind":"DFA","states":[names[i] for i in ordered],"alphabet":alpha,"transitions":trans,
            "start":"M0","accepting":[names[gi] for gi in ordered if P[gi]&finals],"subsets":subsets}

def validate_string(automaton, string):
    if not isinstance(string,str): string=str(string)
    state=automaton["start"]; trace=[{"index":0,"symbol":"START","state":state,"status":"start"}]
    if automaton["kind"]=="DFA":
        for i,ch in enumerate(string,1):
            nxt=automaton["transitions"].get(state,{}).get(ch)
            if nxt is None:
                trace.append({"index":i,"symbol":ch,"state":None,"status":"no-transition"})
                return False,trace
            state=nxt; trace.append({"index":i,"symbol":ch,"state":state,"status":"transition"})
        ok=state in automaton["accepting"]
        trace.append({"index":len(string),"symbol":"END","state":state,"status":"accepted" if ok else "non-accepting"})
        return ok,trace
    current=epsilon_closure(automaton,[state])
    trace[0]["state"]=sorted(current)
    for i,ch in enumerate(string,1):
        current=epsilon_closure(automaton,nfa_move(automaton,current,ch))
        trace.append({"index":i,"symbol":ch,"state":sorted(current),"status":"transition" if current else "no-transition"})
        if not current: return False,trace
    ok=bool(current & set(automaton["accepting"]))
    trace.append({"index":len(string),"symbol":"END","state":sorted(current),"status":"accepted" if ok else "non-accepting"})
    return ok,trace

def automaton_from_json(obj):
    if "automaton" in obj and isinstance(obj["automaton"],dict): obj=obj["automaton"]
    kind=str(obj.get("kind",obj.get("type","DFA"))).upper()
    if kind not in ("DFA","NFA"): raise ValueError("Automaton kind must be DFA or NFA.")
    states=obj.get("states"); alphabet=obj.get("alphabet"); transitions=obj.get("transitions")
    start=obj.get("start",obj.get("start_state")); accepting=obj.get("accepting",obj.get("final_states"))
    if not isinstance(states,list) or not states or not all(isinstance(s,str) and s for s in states):
        raise ValueError("'states' must be a non-empty list of state names.")
    if len(set(states))!=len(states): raise ValueError("State names must be unique.")
    if not isinstance(alphabet,list) or not all(isinstance(x,str) and len(x)==1 and x!=EPS for x in alphabet):
        raise ValueError("'alphabet' must be a list of single-character symbols (excluding ε).")
    if not isinstance(transitions,dict): raise ValueError("'transitions' must be an object keyed by source state.")
    if start not in states: raise ValueError("The start state must be one of the declared states.")
    if not isinstance(accepting,list) or any(s not in states for s in accepting):
        raise ValueError("'accepting' must list declared states.")
    norm={s:{} for s in states}
    for src, row in transitions.items():
        if src not in states or not isinstance(row,dict): raise ValueError(f"Invalid transition row for state {src}.")
        for sym,dest in row.items():
            if sym!=EPS and sym not in alphabet: raise ValueError(f"Transition symbol '{sym}' is not in the alphabet.")
            dests=dest if isinstance(dest,list) else [dest]
            if kind=="DFA" and len(dests)!=1: raise ValueError("DFA transitions must have exactly one destination.")
            if any(d not in states for d in dests): raise ValueError(f"Transition from {src} references an unknown state.")
            norm[src][sym]=dests if kind=="NFA" else dests[0]
    return {"kind":kind,"states":states,"alphabet":sorted(alphabet),"transitions":norm,"start":start,"accepting":accepting}

def to_dfa(automaton):
    if automaton["kind"]=="DFA": return automaton
    return nfa_to_dfa(automaton)

def equivalent_automata(left, right):
    a=to_dfa(left); b=to_dfa(right)
    alphabet=sorted(set(a["alphabet"])|set(b["alphabet"]))
    # complete over union alphabet
    def norm(d):
        states=list(d["states"]); trans={s:dict(d["transitions"].get(s,{})) for s in states}
        sink="__sink__"
        while sink in states: sink+="_"
        needs=any(c not in trans[s] for s in states for c in alphabet)
        if needs: states.append(sink); trans[sink]={c:sink for c in alphabet}
        for s in states:
            for c in alphabet: trans[s].setdefault(c,sink if needs else s)
        return states,trans,sink if needs else None
    sa,ta,sinka=norm(a); sb,tb,sinkb=norm(b)
    q=deque([(a["start"],b["start"],"")]); seen={(a["start"],b["start"])}
    fa,fb=set(a["accepting"]),set(b["accepting"])
    while q:
        x,y,w=q.popleft()
        if (x in fa)!=(y in fb): return False,w
        for c in alphabet:
            nx=ta[x][c]; ny=tb[y][c]
            if (nx,ny) not in seen:
                seen.add((nx,ny)); q.append((nx,ny,w+c))
    return True,None

def automaton_to_regex(automaton):
    d=to_dfa(automaton)
    states=list(d["states"]); start=d["start"]; finals=set(d["accepting"])
    # GNFA adds new start/final, labels represented as regex strings or None (empty language)
    allstates=["__S__"]+states+["__F__"]
    R={(i,j):None for i in allstates for j in allstates}
    R["__S__",start]="ε"
    for f in finals: R[f,"__F__"]="ε"
    for src,row in d["transitions"].items():
        for sym,dest in row.items():
            R[src,dest]=regex_union(R[src,dest],regex_escape(sym))
    remaining=set(states)
    while remaining:
        # Heuristic: eliminate low-degree/simple states first
        def score(k):
            incoming=sum(1 for i in allstates if i!=k and R.get((i,k)) is not None)
            outgoing=sum(1 for j in allstates if j!=k and R.get((k,j)) is not None)
            loop=1 if R.get((k,k)) is not None else 0
            return incoming*outgoing + loop*10
        k=min(remaining,key=score)
        others=[x for x in allstates if x!=k and x in ({"__S__","__F__"}|remaining)]
        loop=regex_star(R[(k,k)])
        for i in others:
            if R[(i,k)] is None: continue
            for j in others:
                if R[(k,j)] is None: continue
                via=regex_concat(R[(i,k)],loop,R[(k,j)])
                R[(i,j)]=regex_union(R[(i,j)],via)
        for i in allstates: R[(i,k)]=None; R[(k,i)]=None
        remaining.remove(k)
    return R[("__S__","__F__")] or "∅"

def regex_escape(c):
    if c in r"\()|*+?·": return "\\"+c
    return c

def regex_union(a,b):
    if a is None: return b
    if b is None or a==b: return a
    if a=="∅": return b
    if b=="∅": return a
    return f"({a}|{b})"

def regex_concat(*parts):
    p=[x for x in parts if x is not None and x!="ε"]
    if any(x=="∅" for x in p): return "∅"
    if not p: return "ε"
    def wrap(x):
        if x in ("ε","∅"): return x
        # Parenthesize union and any compound expression conservatively.
        if "|" in x: return "("+x+")"
        return x
    return "".join(wrap(x) for x in p)

def regex_star(a):
    if a is None or a=="∅" or a=="ε": return "ε"
    if len(a)==1 or (a.startswith("(") and a.endswith(")")): return a+"*"
    return "("+a+")*"
