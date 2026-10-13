from app.models import AuditRequest,Paper
from app.engine import audit

def test_audit():
    req=AuditRequest(question='How reproducible is the model?',papers=[Paper(title='Test Paper',text='We evaluated a model on a dataset. Accuracy was 92 percent. Results improved compared with a baseline.')])
    result=audit(req)
    assert len(result.paper_assessments)==1
    assert result.paper_assessments[0]['checklist']['dataset']
    assert not result.paper_assessments[0]['checklist']['reproducibility']
    assert result.experiment_plan

def test_no_false_verification():
    req=AuditRequest(question='Is this scientific claim valid?',papers=[Paper(title='Test Paper',text='We present a novel method. Our results appear promising, but there are important unknowns.')])
    assert 'not verification' in audit(req).executive_summary
