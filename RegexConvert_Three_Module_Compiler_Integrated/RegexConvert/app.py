from flask import Flask, render_template, request, jsonify, send_file
from regexconvert_core.regex_engine import RegexError, compile_regex, automaton_to_regex, minimize_dfa, validate_string, equivalent_automata, automaton_from_json
from regexconvert_core.visualize import automaton_svg
from regexconvert_core.reporting import build_report
import json, io, time
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "app": "RegexConvert", "version": "1.0.0"})

@app.post("/api/compile")
def compile_api():
    started = time.perf_counter()
    data = request.get_json(silent=True) or {}
    pattern = str(data.get("regex", ""))
    try:
        result = compile_regex(pattern)
        nfa, dfa = result["nfa"], result["dfa"]
        minimized = minimize_dfa(dfa)
        elapsed = (time.perf_counter() - started) * 1000
        return jsonify({
            "ok": True, "regex": pattern, "tokens": result["tokens"], "ast": result["ast"],
            "nfa": nfa, "dfa": dfa, "minimized_dfa": minimized,
            "stats": {"nfa_states": len(nfa["states"]), "dfa_states": len(dfa["states"]),
                      "minimized_states": len(minimized["states"]),
                      "nfa_transitions": sum(len(v) for v in nfa["transitions"].values()),
                      "dfa_transitions": sum(len(v) for v in dfa["transitions"].values()),
                      "compile_ms": round(elapsed, 3)},
            "svg": {"nfa": automaton_svg(nfa), "dfa": automaton_svg(dfa), "minimized_dfa": automaton_svg(minimized)}
        })
    except (RegexError, ValueError, KeyError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.post("/api/validate")
def validate_api():
    data = request.get_json(silent=True) or {}
    try:
        pattern = str(data.get("regex", ""))
        strings = data.get("strings", [])
        if isinstance(strings, str):
            strings = strings.splitlines()
        if not isinstance(strings, list):
            raise ValueError("Strings must be a list or newline-separated text.")
        if len(strings) > 500:
            raise ValueError("Please validate at most 500 strings per batch.")
        compiled = compile_regex(pattern)
        rows = []
        for item in strings:
            s = str(item)
            accepted, trace = validate_string(compiled["dfa"], s)
            rows.append({"string": s, "accepted": accepted, "trace": trace})
        return jsonify({"ok": True, "results": rows, "count": len(rows),
                        "accepted": sum(r["accepted"] for r in rows),
                        "rejected": sum(not r["accepted"] for r in rows)})
    except (RegexError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.post("/api/reverse")
def reverse_api():
    data = request.get_json(silent=True) or {}
    try:
        automaton = data.get("automaton")
        if not isinstance(automaton, dict):
            raise ValueError("Provide an automaton JSON object.")
        a = automaton_from_json(automaton)
        regex = automaton_to_regex(a)
        # Verify the generated expression can be parsed and has same language.
        generated = compile_regex(regex)
        equivalent, witness = equivalent_automata(a, generated["dfa"])
        return jsonify({"ok": True, "regex": regex, "verified": equivalent, "counterexample": witness,
                        "svg": automaton_svg(a)})
    except (RegexError, ValueError, KeyError, TypeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.post("/api/equivalence")
def equivalence_api():
    data = request.get_json(silent=True) or {}
    try:
        left = compile_regex(str(data.get("left", "")))["dfa"]
        right = compile_regex(str(data.get("right", "")))["dfa"]
        same, witness = equivalent_automata(left, right)
        return jsonify({"ok": True, "equivalent": same, "counterexample": witness})
    except (RegexError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.post("/api/import-automaton")
def import_automaton_api():
    data = request.get_json(silent=True) or {}
    try:
        a = automaton_from_json(data)
        regex = automaton_to_regex(a)
        return jsonify({"ok": True, "automaton": a, "regex": regex, "svg": automaton_svg(a)})
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.post("/api/export-report")
def export_report():
    data = request.get_json(silent=True) or {}
    try:
        report = build_report(data)
        return send_file(io.BytesIO(report), mimetype="text/html", as_attachment=True,
                         download_name="RegexConvert-report.html")
    except Exception as e:
        return jsonify({"ok": False, "error": f"Could not create report: {e}"}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
