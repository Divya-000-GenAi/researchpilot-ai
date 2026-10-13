from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from .models import AuditRequest, AuditResult
from .engine import audit
from .llm import summarize

app=FastAPI(title='ResearchPilot AI',version='1.0.0',description='Evidence-linked research reproducibility POC')

@app.get('/health')
def health(): return {'status':'ok','mode':'heuristic; optional LLM'}

@app.post('/audit',response_model=AuditResult)
def run_audit(req: AuditRequest, use_llm: bool=False):
    result=audit(req)
    if use_llm:
        try:
            result.llm_summary=summarize(result)
            if result.llm_summary is None:
                raise HTTPException(status_code=400,detail='Set OPENAI_API_KEY to enable LLM summarization')
        except HTTPException: raise
        except Exception as exc: raise HTTPException(status_code=502,detail=f'LLM gateway error: {type(exc).__name__}') from exc
    return result

@app.post('/audit/report',response_class=PlainTextResponse)
def report(req:AuditRequest):
    r=audit(req)
    lines=['# ResearchPilot AI — Research Audit','',f'**Question:** {r.question}','',r.executive_summary,'','## Evidence']
    for e in r.evidence: lines.append(f'- **{e.paper}** (lexical score {e.score}): {e.sentence}')
    lines+=['','## Reproducibility checklist']
    for a in r.paper_assessments:
        lines.append(f"### {a['paper']} — {a['coverage_score']}% coverage")
        lines.append('Missing mentions: '+(', '.join(a['missing_details']) or 'None detected'))
    lines+=['','## Critic findings']+[f'- {x}' for x in r.cross_paper_findings]
    lines+=['','## Proposed experiments']+[f"{x['step']}. **{x['name']}**: {x['action']}" for x in r.experiment_plan]
    lines+=['','_Scores measure keyword coverage, not scientific validity._']
    return '\n'.join(lines)

@app.get('/',response_class=HTMLResponse)
def home():
    return '''<!doctype html><html><head><meta charset="utf-8"><title>ResearchPilot AI</title><style>body{font:16px system-ui;max-width:950px;margin:35px auto;padding:0 18px;color:#15283b;background:#f7fafc}textarea,input,button{box-sizing:border-box;width:100%;padding:12px;margin:7px 0 15px;border:1px solid #b8c6d5;border-radius:8px}textarea{height:165px}button{background:#175cd3;color:white;font-weight:bold;cursor:pointer}pre{white-space:pre-wrap;background:white;padding:20px;border-radius:12px;border:1px solid #ddd}small{color:#586a7c}</style></head><body><h1>🔬 ResearchPilot AI</h1><p>Evidence-driven research auditing and experiment planning</p><small>POC: keyword-based checklist and lexical evidence ranking. Not a scientific validator.</small><label>Research question</label><input id="q" value="How reproducible is the proposed method and what experiment should come next?"><label>Paper title</label><input id="title" value="Demo Research Paper"><label>Paper text</label><textarea id="paper">We propose a novel classifier for a benchmark dataset. We evaluated accuracy of 92% on a test set. The method improved results over an existing approach. We did not provide implementation details.</textarea><button onclick="run()">Run research audit</button><pre id="out">Ready. You can also use /docs for multi-paper analysis.</pre><script>async function run(){const out=document.getElementById('out');out.textContent='Analyzing...';try{const r=await fetch('/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.getElementById('q').value,papers:[{title:document.getElementById('title').value,text:document.getElementById('paper').value}]})});const data=await r.json();out.textContent=JSON.stringify(data,null,2)}catch(e){out.textContent=String(e)}}</script></body></html>'''
