let lastCompile=null, currentAuto="nfa", lastResults=[];
const $=id=>document.getElementById(id);
async function api(path,payload){const r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const d=await r.json().catch(()=>({ok:false,error:"Invalid server response."}));if(!r.ok||!d.ok)throw new Error(d.error||"Request failed.");return d}
let toastTimer;
function toast(message,error=false){const t=$("toast");t.textContent=message;t.className="toast show"+(error?" error":"");clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.className="toast",3500)}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function setStageDone(){document.querySelectorAll(".stage").forEach(x=>{x.classList.add("done");x.querySelector("em").textContent="Complete"})}
function setStageWaiting(){document.querySelectorAll(".stage").forEach(x=>{x.classList.remove("done");x.querySelector("em").textContent="Waiting"})}
function showGraph(which){currentAuto=which;document.querySelectorAll(".seg").forEach(b=>b.classList.toggle("active",b.dataset.auto===which));if(!lastCompile)return;const svg=lastCompile.svg[which];$("graphWrap").innerHTML=svg||'<div class="empty-state">No diagram available.</div>';$("graphLabel").textContent=({nfa:"Nondeterministic finite automaton",dfa:"Deterministic finite automaton",minimized_dfa:"Minimized deterministic finite automaton"})[which]}
async function compilePattern(pattern, updateMain=true){
  try{
    if(updateMain){$("compileBtn").disabled=true;$("compileBtn").textContent="Compiling…"}
    const d=await api("/api/compile",{regex:pattern});lastCompile=d;
    setStageDone();$("compileTime").textContent=d.stats.compile_ms+" ms";
    $("stats").innerHTML=`<div><small>NFA states</small><strong>${d.stats.nfa_states}</strong></div><div><small>DFA states</small><strong>${d.stats.dfa_states}</strong></div><div><small>Minimized</small><strong>${d.stats.minimized_states}</strong></div><div><small>Compile time</small><strong>${d.stats.compile_ms}<small style="display:inline"> ms</small></strong></div>`;
    $("tokenList").innerHTML=d.tokens.map(t=>`<span class="token ${["|","*","+","?","(",")","CONCAT"].includes(t)?"operator":""}">${esc(t==="CONCAT"?"·":t)}</span>`).join("");
    $("astOutput").textContent=JSON.stringify(d.ast,null,2);showGraph(currentAuto);
    if(updateMain){$("validatorPattern").value=pattern;toast("Compilation completed successfully.");}
    return d;
  }catch(e){setStageWaiting();toast(e.message,true);if(updateMain){$("graphWrap").innerHTML=`<div class="empty-state"><div class="empty-icon">!</div><b>Compilation failed</b><p>${esc(e.message)}</p></div>`;$("graphLabel").textContent="Input error"}throw e}
  finally{if(updateMain){$("compileBtn").disabled=false;$("compileBtn").innerHTML='Compile pattern <span>→</span>'}}
}
async function runValidation(pattern, strings, targetBody, summaryTarget){
  const d=await api("/api/validate",{regex:pattern,strings});
  lastResults=d.results;
  const body=$(targetBody);
  body.innerHTML=d.results.length?d.results.map((r,i)=>`<tr><td><code>${esc(r.string===""?"ε (empty string)":r.string)}</code></td><td><span class="result-badge ${r.accepted?"accepted":"rejected"}">${r.accepted?"Accepted":"Rejected"}</span></td><td><button class="btn btn-small btn-quiet trace-btn" data-index="${i}">View trace ↗</button><div class="trace-content" id="trace-${targetBody}-${i}" hidden>${r.trace.map(t=>`${t.index}. ${t.symbol}: ${Array.isArray(t.state)?t.state.join(", "):t.state??"no transition"} (${t.status})`).map(esc).join("<br>")}</div></td></tr>`).join(""):'<tr><td colspan="3" class="muted">No strings supplied.</td></tr>';
  body.querySelectorAll(".trace-btn").forEach(b=>b.addEventListener("click",()=>{const el=$(`trace-${targetBody}-${b.dataset.index}`);el.hidden=!el.hidden;b.textContent=el.hidden?"View trace ↗":"Hide trace ↑"}));
  if(summaryTarget)$(summaryTarget).innerHTML=`<span class="summary-chip"><strong>${d.count}</strong> tested</span><span class="summary-chip"><strong>${d.accepted}</strong> accepted</span><span class="summary-chip"><strong>${d.rejected}</strong> rejected</span>`;
  return d;
}
$("compileBtn").addEventListener("click",async()=>{try{await compilePattern($("regexInput").value);await runValidation($("regexInput").value,$("stringsInput").value.split(/\r?\n/),"resultsBody","resultsSummary")}catch(e){}});
document.querySelectorAll(".example").forEach(b=>b.addEventListener("click",()=>{$("regexInput").value=b.dataset.value;compilePattern(b.dataset.value).catch(()=>{})}));
document.querySelectorAll(".seg").forEach(b=>b.addEventListener("click",()=>showGraph(b.dataset.auto)));
$("validateBtn").addEventListener("click",async()=>{try{if(!lastCompile||lastCompile.regex!==$("regexInput").value)await compilePattern($("regexInput").value);await runValidation($("regexInput").value,$("stringsInput").value.split(/\r?\n/),"resultsBody","resultsSummary");toast("Batch validation complete.")}catch(e){}});
$("downloadSvg").addEventListener("click",()=>{if(!lastCompile){toast("Compile a pattern first.",true);return}const blob=new Blob([lastCompile.svg[currentAuto]],{type:"image/svg+xml"});downloadBlob(blob,`regexconvert-${currentAuto}.svg`)});
function downloadBlob(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(".nav-item").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".view").forEach(x=>x.classList.toggle("active",x.id==="view-"+b.dataset.view));$("pageTitle").textContent=b.textContent.trim().replace(/^[⌘✓⇄↶i]\s*/,"");}));
$("validatorCompile").addEventListener("click",async()=>{try{await compilePattern($("validatorPattern").value,false);$("validatorResults").innerHTML=`<div class="results-summary" id="validatorSummary"></div><div class="table-wrap"><table><thead><tr><th>String</th><th>Result</th><th>Trace</th></tr></thead><tbody id="validatorResultsBody"></tbody></table></div>`;await runValidation($("validatorPattern").value,$("validatorStrings").value.split(/\\r?\\n/),"validatorResultsBody","validatorSummary");toast("Validation complete.")}catch(e){toast(e.message,true)}});
$("equivBtn").addEventListener("click",async()=>{const out=$("equivResult");out.className="notice";out.textContent="Comparing…";try{const d=await api("/api/equivalence",{left:$("leftRegex").value,right:$("rightRegex").value});out.className="notice "+(d.equivalent?"success":"error");out.innerHTML=d.equivalent?"<b>Equivalent languages.</b><br>Both expressions recognize the same set of strings.":`<b>Languages differ.</b><br>Distinguishing string: <code>${esc(d.counterexample===""?"ε (empty string)":d.counterexample)}</code><br>This string is accepted by one expression and rejected by the other.`}catch(e){out.className="notice error";out.textContent=e.message}});
const sample={kind:"DFA",states:["q0","q1"],alphabet:["a","b"],transitions:{q0:{a:"q1",b:"q0"},q1:{a:"q1",b:"q0"}},start:"q0",accepting:["q1"]};
$("loadSampleAutomaton").addEventListener("click",()=>$("automatonJson").value=JSON.stringify(sample,null,2));
$("automatonFile").addEventListener("change",async e=>{const f=e.target.files[0];if(!f)return;try{const text=await f.text();JSON.parse(text);$("automatonJson").value=text;toast("Automaton JSON loaded. Click Generate to convert it.")}catch(err){toast("The selected file is not valid JSON.",true)}});
$("reverseBtn").addEventListener("click",async()=>{const out=$("reverseResult");try{const a=JSON.parse($("automatonJson").value);const d=await api("/api/reverse",{automaton:a});out.innerHTML=`<div class="notice ${d.verified?"success":"error"}"><b>Equivalent regular expression</b><p><code>${esc(d.regex)}</code></p><p>Equivalence verified: <b>${d.verified?"Yes":"No"}</b></p></div><div class="graph-wrap">${d.svg}</div>`;toast("Reverse conversion completed.")}catch(e){out.innerHTML=`<div class="notice error">${esc(e.message)}</div>`;toast(e.message,true)}});
$("exportBtn").addEventListener("click",async()=>{if(!lastCompile){toast("Compile a pattern before exporting a report.",true);return}try{const res=await fetch("/api/export-report",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({regex:lastCompile.regex,results:lastResults,title:"RegexConvert Compilation Report"})});if(!res.ok)throw new Error("Report generation failed.");downloadBlob(await res.blob(),"RegexConvert-report.html");toast("Report exported.")}catch(e){toast(e.message,true)}});
fetch("/api/health").then(r=>r.json()).then(d=>{$("healthText").textContent=d.ok?"Connected · v1.0.0":"Unavailable"}).catch(()=>$("healthText").textContent="Not connected");
$("automatonJson").value=JSON.stringify(sample,null,2);
compilePattern($("regexInput").value).then(()=>runValidation($("regexInput").value,$("stringsInput").value.split(/\r?\n/),"resultsBody","resultsSummary")).catch(()=>{});

// Semantic language descriptions: explicit set notation for teaching/demo patterns.
function updateLanguageDescription(pattern){
  const title=$("languageTitle"), desc=$("languageDescription"); if(!title||!desc)return;
  const p=pattern.replace(/\s+/g,"");
  if(p==="(a|b)*abb" || p==="(b|a)*abb"){
    title.textContent="Language of all strings over Σ = {a, b} that end with abb";
    desc.innerHTML='The language is <strong>L = { w·abb | w ∈ {a,b}* }</strong>, where <code>w</code> can be any (possibly empty) sequence of <code>a</code> and <code>b</code>. Therefore every accepted string ends in <code>abb</code>.';
  } else if(p==="(0|1)*011" || p==="(1|0)*011"){
    title.textContent="Language of all binary strings over Σ = {0, 1} that end with 011";
    desc.innerHTML='The language is <strong>L = { w·011 | w ∈ {0,1}* }</strong>. Here <code>w</code> is any binary prefix, so the final three symbols must be <code>011</code>.';
  } else if(p==="(0|1)*"){
    title.textContent="Language of all binary strings over Σ = {0, 1}";
    desc.innerHTML='The language is <strong>L = {0,1}*</strong>: every finite sequence of zeroes and ones, including the empty string <code>ε</code>.';
  } else if(p==="(a|b)*"){
    title.textContent="Language of all strings over Σ = {a, b}";
    desc.innerHTML='The language is <strong>L = {a,b}*</strong>: every finite sequence formed using <code>a</code> and <code>b</code>, including <code>ε</code>.';
  } else {
    title.textContent="Formal language defined by the entered expression";
    desc.innerHTML='The expression defines <strong>L(r) = { x ∈ Σ* | x is matched by r }</strong>. The alphabet <code>Σ</code> is the set of literal symbols used in the expression. Use the validation lab below to inspect members and non-members of this language.';
  }
}
const originalCompilePattern=compilePattern;
compilePattern=async function(pattern, updateMain=true){
  const result=await originalCompilePattern(pattern,updateMain);
  updateLanguageDescription(pattern);
  return result;
};
const literalBtn=$("literalToRegexBtn");
if(literalBtn)literalBtn.addEventListener("click",()=>{
  const raw=$("literalString").value;
  if(raw.length===0){$("literalRegexResult").innerHTML='<div class="notice success"><b>Generated regular expression</b><p><code class="large-code">ε</code></p><p><b>Language represented:</b> <strong>L = { ε }</strong>, containing only the empty string.</p></div>';return;}
  // Escape formal-regex metacharacters so every input character is treated literally.
  const regex=raw.replace(/[\\|()*+?.]/g,"\\$&");
  const concatenation=[...raw].map(ch=>`<code>${esc(ch)}</code>`).join(' <span class="muted">·</span> ');
  $("literalRegexResult").innerHTML=`<div class="notice success"><b>Generated regular expression for the exact input string</b><p><code class="large-code">${esc(regex)}</code></p><p><b>Concatenation structure:</b> ${concatenation}</p><p><b>Language represented:</b> <strong>L = { ${esc(raw)} }</strong>. This is a singleton language: it contains exactly the entered string and no other string.</p><p class="hint"><b>Important distinction:</b> a literal string converts to a regex for one exact string. A language rule such as “all binary strings ending in 011” is represented by <code>(0|1)*011</code>; it is not inferred from one sample string.</p></div>`;
});
