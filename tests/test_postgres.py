from concurrent.futures import ThreadPoolExecutor
import subprocess
import pytest
from pathlib import Path

def test_selected_reset_and_resubmission(request):
    container=request.config.getoption('--postgres-container')
    if not container:
        pytest.skip('Richiede container PostgreSQL di test esplicito')
    sql=(Path(__file__).resolve().parents[1]/'sql'/'verify_reset.sql').read_text(encoding='utf-8')
    result=subprocess.run(['docker','exec','-i',container,'psql','-U','postgres','-v','ON_ERROR_STOP=1'],
                          input=sql,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stderr

def test_concurrent_submit(request):
    container=request.config.getoption('--postgres-container')
    if not container:
        pytest.skip('Richiede container PostgreSQL di test esplicito')
    def sql(statement):
        return subprocess.run(['docker','exec',container,'psql','-U','postgres','-v','ON_ERROR_STOP=1','-At','-c',statement],capture_output=True,text=True)
    setup=sql("select public.manage_participant('add',null,'Concurrency check','RDM'); select id from public.participants where full_name='Concurrency check' order by created_at desc limit 1;")
    assert setup.returncode==0,setup.stderr
    pid=setup.stdout.strip().splitlines()[-1]
    statement=f"select public.submit_vote('{pid}','rdm_fc',(select id from public.sponsors where team='RDM' and slot_number=1),'rdm_world','rdm_internazionale');"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outputs=list(pool.map(sql,[statement,statement]))
    assert sum(o.returncode==0 for o in outputs)==1
    assert any('ALREADY_SUBMITTED' in o.stderr for o in outputs)
    check=sql(f"select count(*) from public.votes where participant_id='{pid}'; select submitted from public.participants where id='{pid}';")
    assert check.stdout.strip().splitlines()==['1','t']
