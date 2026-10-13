"""Deterministic, inspectable research-audit agents. Not a scientific fact checker."""
import math
import re
from collections import Counter
from .models import AuditRequest, AuditResult, Evidence

STOP = set('the a an and or of in to for with on by is are was were from as at that this we our their be can using used study paper results model'.split())
CHECKS = {
    'dataset': r'\b(dataset|data source|corpus|benchmark|sample size)\b',
    'baseline': r'\b(baseline|compared with|comparison|control group)\b',
    'metrics': r'\b(accuracy|f1|precision|recall|auc|rmse|mae|metric|confidence interval)\b',
    'reproducibility': r'\b(seed|code available|github|hyperparameter|implementation details|reproducib|random state)\w*',
    'limitations': r'\b(limitation|failure case|threat to validity|bias|uncertainty)\b',
    'evaluation protocol': r'\b(train.test|cross.validation|holdout|evaluation protocol|test set|validation set)\b',
}

def tokenize(text):
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if len(t)>2 and t not in STOP]

def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if len(s.strip()) > 12]

def evidence_agent(req):
    """Rank sentences by overlap with query and research-significance terms."""
    q = set(tokenize(req.question))
    candidates=[]
    for paper in req.papers:
        for s in sentences(paper.text):
            tokens=set(tokenize(s))
            overlap=len(q & tokens)/max(1,len(q))
            research_bonus=0.12 if re.search(r'\b(achieved|improved|outperform|evaluat|experiment|result|propos|compare)\w*',s,re.I) else 0
            score=round(overlap+research_bonus,3)
            candidates.append(Evidence(paper=paper.title,sentence=s,score=score))
    return sorted(candidates,key=lambda x:x.score,reverse=True)[:12]

def reproducibility_agent(req):
    assessments=[]
    for paper in req.papers:
        checks={key:bool(re.search(pattern,paper.text,re.I)) for key,pattern in CHECKS.items()}
        missing=[k for k,v in checks.items() if not v]
        assessments.append({
            'paper':paper.title,'checklist':checks,'coverage_score':round(100*sum(checks.values())/len(checks)),
            'missing_details':missing,
            'caveat':'Keyword-based reporting completeness, not proof of correctness or reproducibility.'
        })
    return assessments

def critic_agent(assessments, evidence):
    findings=[]
    for a in assessments:
        if a['missing_details']:
            findings.append(f"{a['paper']}: no explicit mention detected for {', '.join(a['missing_details'])}.")
        else:
            findings.append(f"{a['paper']}: all checklist topics mentioned; verify their adequacy manually.")
    if len(assessments)>1:
        findings.append('Compare reported metrics only after confirming equivalent datasets, splits, and evaluation protocols.')
    if not evidence or max(e.score for e in evidence)<0.2:
        findings.append('Low query-to-text lexical overlap; evidence may be insufficient to answer the research question.')
    return findings

def experiment_agent(assessments):
    missing=set(k for a in assessments for k in a['missing_details'])
    plan=[{'step':1,'name':'Define falsifiable hypothesis','action':'Specify expected improvement and a measurable null hypothesis.', 'deliverable':'Pre-registered hypothesis'}]
    if 'dataset' in missing or 'evaluation protocol' in missing:
        plan.append({'step':len(plan)+1,'name':'Standardize evaluation','action':'Use a documented dataset, fixed train/validation/test splits, and leakage checks.','deliverable':'Dataset card and evaluation protocol'})
    if 'baseline' in missing:
        plan.append({'step':len(plan)+1,'name':'Build baselines','action':'Compare against a simple baseline under identical conditions.','deliverable':'Baseline results table'})
    if 'reproducibility' in missing:
        plan.append({'step':len(plan)+1,'name':'Reproduce runs','action':'Record code revision, environment, hyperparameters, and multiple random seeds.','deliverable':'Reproduction manifest'})
    plan.append({'step':len(plan)+1,'name':'Measure uncertainty','action':'Report task-appropriate metrics, error analysis, confidence intervals, and limitations.','deliverable':'Evaluation report'})
    return plan

def audit(req: AuditRequest) -> AuditResult:
    evidence=evidence_agent(req)
    assessments=reproducibility_agent(req)
    findings=critic_agent(assessments,evidence)
    plan=experiment_agent(assessments)
    avg=sum(a['coverage_score'] for a in assessments)/len(assessments)
    summary=(f"Audited {len(req.papers)} supplied research document(s). "
             f"Average reporting-checklist coverage: {avg:.0f}%. "
             f"Found {sum(len(a['missing_details']) for a in assessments)} unmentioned checklist topics. "
             "This is a heuristic audit, not verification of research claims.")
    return AuditResult(question=req.question,evidence=evidence,paper_assessments=assessments,
                       cross_paper_findings=findings,experiment_plan=plan,executive_summary=summary)
