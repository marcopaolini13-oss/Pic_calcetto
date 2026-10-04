from unittest.mock import patch
import pytest
from streamlit.testing.v1 import AppTest
from src.auth import hash_password, verify_password
from src.database import DatabaseError
from src.utils import csv_bytes
from src.config import CONCEPTS

class FakeDatabase:
    def __init__(self, team='ENERGETICI'):
        self.person={'id':'person-1','full_name':'Collega Test','team':team,'submitted':False}
        self.sent=[]
        self.fail=False
    def participants(self): return [self.person.copy()]
    def is_open(self): return True
    def rows(self,table,**filters):
        if table=='votes': return []
        if table=='sponsors': return self.sponsors('ENERGETICI')+self.sponsors('RDM')
        return []
    def sponsors(self,team):
        return [{'id':f'sponsor-{n}','sponsor_name':f'Sponsor {n}','slot_number':n,'team':team} for n in range(1,4)]
    def rpc(self,fn,**params):
        if self.fail: raise DatabaseError('Connessione al database non disponibile.')
        if self.person['submitted']: raise DatabaseError('ALREADY_SUBMITTED')
        self.sent.append(params)
        self.person['submitted']=True

def button(at,label):
    return next(b for b in at.button if b.label==label)

@pytest.mark.parametrize('team',['ENERGETICI','RDM'])
def test_wizard_back_summary_submit_and_second_vote(team):
    db=FakeDatabase(team)
    with patch('src.database.Database',return_value=db):
        at=AppTest.from_file('app.py',default_timeout=30).run()
        assert not at.exception
        at.selectbox[0].select('person-1').run()
        at.button(key='vote_name_'+list(CONCEPTS[team])[2]).click().run()
        chosen=at.session_state['vote_name']
        button(at,'Avanti →').click().run()
        assert at.session_state['vote_step']==2
        at.button(key='vote_sponsor_sponsor-1').click().run()
        button(at,'Avanti →').click().run()
        assert len([b for b in at.button if b.label=='Scegli questa maglia'])==3
        kit=list(CONCEPTS[team])[1]
        at.button(key='vote_kit_'+kit).click().run()
        button(at,'← Indietro').click().run()
        assert at.session_state['vote_name']==chosen
        assert at.session_state['vote_sponsor']=='sponsor-1'
        button(at,'Avanti →').click().run()
        assert at.session_state['vote_step']==3
        assert not at.session_state.filtered_state.get('asset_open_lightbox'), at.session_state.filtered_state
        assert at.session_state['vote_kit']!=chosen
        assert 'vote_crest' not in at.session_state.filtered_state
        assert 'vote_concept' not in at.session_state.filtered_state
        button(at,'← Indietro').click().run()
        button(at,'Avanti →').click().run()
        assert at.session_state['vote_kit']==kit
        button(at,'Avanti →').click().run()
        assert at.session_state['vote_step']==4
        assert any('**Nome/logo scelto:** '+CONCEPTS[team][chosen] in m.value for m in at.markdown)
        assert any('**Maglia scelta:** '+CONCEPTS[team][kit] in m.value for m in at.markdown)
        assert button(at,'CONFERMA DEFINITIVAMENTE').disabled
        at.checkbox[0].check().run()
        button(at,'← MODIFICA LE SCELTE').click().run()
        assert not at.exception
        assert at.session_state['vote_name']==chosen
        for _ in range(3):
            button(at,'Avanti →').click().run()
        assert button(at,'CONFERMA DEFINITIVAMENTE').disabled
        at.checkbox[0].check().run()
        db.fail=True
        button(at,'CONFERMA DEFINITIVAMENTE').click().run()
        assert at.error and not db.sent
        db.fail=False
        button(at,'CONFERMA DEFINITIVAMENTE').click().run()
        assert len(db.sent)==1
        assert db.sent[0]['p_name']==db.sent[0]['p_crest']==chosen
        assert db.sent[0]['p_kit']==kit
        assert db.sent[0]['p_kit']!=db.sent[0]['p_crest']
        assert any('déjà' in s.value or 'già' in s.value for s in at.success)
        at.run()
        assert not any(b.label=='CONFERMA DEFINITIVAMENTE' for b in at.button)
        assert not at.exception

def test_admin_requires_login(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('long-password-123'))
    with patch('src.database.Database') as db:
        at=AppTest.from_file('pages/admin.py').run()
        assert not at.exception
        assert not at.tabs
        db.assert_not_called()

def test_hash_and_csv():
    encoded=hash_password('secret-password')
    assert verify_password('secret-password',encoded)
    assert not verify_password('wrong',encoded)
    assert not verify_password('anything','malformed')
    assert "'=HYPERLINK" in csv_bytes([{'name':'=HYPERLINK(test)'}]).decode('utf-8-sig')

def test_admin_login_dashboard(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('long-password-123'))
    monkeypatch.setenv('ADMIN_USERNAME','Paolo')
    with patch('src.database.Database',return_value=FakeDatabase()):
        at=AppTest.from_file('pages/admin.py').run()
        at.text_input[0].input('Paolo')
        at.text_input[1].input('long-password-123')
        button(at,'Accedi').click().run(timeout=15)
        assert not at.exception
        assert len(at.tabs)==5
        assert at.metric[0].value=='1'
        button(at,'Esci da Admin').click().run()
        assert not at.tabs and not at.exception

def test_missing_config(monkeypatch):
    monkeypatch.delenv('SUPABASE_URL',raising=False)
    monkeypatch.delenv('SUPABASE_KEY',raising=False)
    with patch('src.database.secret',return_value=''):
        at=AppTest.from_file('app.py').run()
    assert not at.exception
    assert at.error
