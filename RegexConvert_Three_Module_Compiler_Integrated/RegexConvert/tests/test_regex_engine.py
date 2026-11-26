import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from regexconvert_core.regex_engine import compile_regex, validate_string, automaton_to_regex, equivalent_automata, minimize_dfa, RegexError

def test_basic_acceptance():
    c=compile_regex("(a|b)*abb")
    assert validate_string(c["dfa"],"abb")[0]
    assert validate_string(c["dfa"],"aabb")[0]
    assert validate_string(c["dfa"],"babb")[0]
    assert not validate_string(c["dfa"],"ab")[0]
    assert not validate_string(c["dfa"],"aba")[0]

def test_epsilon():
    c=compile_regex("ε")
    assert validate_string(c["dfa"],"")[0]
    assert not validate_string(c["dfa"],"a")[0]

def test_empty_language():
    c=compile_regex("∅")
    assert not validate_string(c["dfa"],"")[0]
    assert not validate_string(c["dfa"],"a")[0]

def test_plus_optional():
    assert validate_string(compile_regex("a+")["dfa"],"a")[0]
    assert validate_string(compile_regex("a+")["dfa"],"aaa")[0]
    assert not validate_string(compile_regex("a+")["dfa"],"")[0]
    assert validate_string(compile_regex("a?")["dfa"],"")[0]
    assert validate_string(compile_regex("a?")["dfa"],"a")[0]
    assert not validate_string(compile_regex("a?")["dfa"],"aa")[0]

def test_equivalence():
    a=compile_regex("a*b")["dfa"]
    b=compile_regex("(a|aa)*b")["dfa"]
    assert equivalent_automata(a,b)[0]
    c=compile_regex("ab")["dfa"]
    same,witness=equivalent_automata(a,c)
    assert not same
    assert witness is not None

def test_reverse_conversion_equivalent():
    d=compile_regex("(a|b)*abb")["dfa"]
    r=automaton_to_regex(d)
    rdfa=compile_regex(r)["dfa"]
    assert equivalent_automata(d,rdfa)[0]

def test_invalid_patterns():
    for p in ["", "a|", "*a", "(ab", "a)", "a||b", "()"]:
        try:
            compile_regex(p)
            assert False, f"Expected invalid pattern: {p}"
        except RegexError:
            pass

def test_minimized_dfa():
    d=compile_regex("(a|b)*abb")["dfa"]
    m=minimize_dfa(d)
    for s in ["","a","b","abb","aabb","babb","aba","abab"]:
        assert validate_string(d,s)[0] == validate_string(m,s)[0]
