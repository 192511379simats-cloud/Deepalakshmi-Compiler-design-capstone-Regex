# RegexConvert — Formal Language Processing Workbench

A local Flask application demonstrating regular-expression processing, finite-automata construction, reverse conversion, language equivalence, and string recognition.

## Three functional modules

1. **Expression Analysis & Automata Generation** — tokenization, syntax parsing, AST construction, Thompson epsilon-NFA construction, subset-construction DFA conversion, DFA minimization, automata statistics and SVG visualization.
2. **Reverse Conversion & Equivalence** — literal-string-to-regex derivation (singleton language), automaton-to-regex state elimination, and equivalence checking with a distinguishing witness when languages differ.
3. **String Recognition & Visualization** — single/batch string validation, acceptance/rejection, transition traces, and downloadable SVG automata.

## Compiler Design concepts implemented

- **Lexical analysis:** `tokenize()` recognizes literals, parentheses, union, postfix operators, epsilon and empty-language symbols; it inserts explicit concatenation tokens.
- **Syntax analysis:** `to_postfix()` checks operator placement and precedence; `postfix_ast()` builds an abstract syntax tree.
- **Syntax-directed translation:** `ast_to_nfa()` recursively translates AST nodes into Thompson fragments for literals, union, concatenation, star, plus, optional, epsilon and empty language.
- **Intermediate representation:** automata are represented as structured state, alphabet, transition, start-state and accepting-state data.
- **Code/representation transformation:** `nfa_to_dfa()` performs subset construction; `minimize_dfa()` reduces equivalent DFA states.
- **Semantic/language verification:** string recognition and product-automaton equivalence checking verify language behavior; reverse conversion uses state elimination and checks the generated expression against the imported automaton.
- **Diagnostics:** invalid syntax and malformed automaton input produce user-facing errors.

This is a Compiler Design learning workbench focused on the regular-expression and lexical-analysis front end; it is not a general-purpose programming-language compiler.

## Formal language descriptions

The workbench explicitly displays classroom descriptions for common patterns:

- `(a|b)*abb` — all strings over `Σ = {a,b}` that end with `abb`, i.e. `L = { w·abb | w ∈ {a,b}* }`.
- `(0|1)*011` — all binary strings over `Σ = {0,1}` that end with `011`, i.e. `L = { w·011 | w ∈ {0,1}* }`.
- `(0|1)*` — all finite binary strings, including epsilon.

For other expressions, the interface displays the formal membership definition `L(r) = {x ∈ Σ* | x is matched by r}`. The string-to-regex tool derives a regex for exactly one entered literal string, whose language is a singleton `{s}`; it does not infer a broader language from one sample.

## Requirements

- Python 3.10 or newer
- Flask (installed from `requirements.txt`)

## Run on Windows / VS Code

Open the folder containing `app.py` and `requirements.txt` in VS Code. In PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest .\tests -q
python app.py
```

Open `http://127.0.0.1:5000`.

If the virtual environment already exists, do not create another one; activate it and continue from the dependency-install command. Run pytest from this project folder only so unrelated test files elsewhere on the computer are not collected.

## Supported regular-expression syntax

- Union: `|`
- Implicit concatenation: `ab`
- Kleene star: `*`
- One or more: `+`
- Optional: `?`
- Epsilon: `ε`
- Empty language: `∅`
- Parentheses for grouping
- Backslash escapes a supported metacharacter as a literal

The parser intentionally uses formal regular-expression syntax rather than every feature of Python's `re` module.
