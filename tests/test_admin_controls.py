import time
from unittest.mock import Mock,patch
import pytest
from streamlit.testing.v1 import AppTest
from src.auth import hash_password,credential_signature
from src.admin_reset import reset_selected_votes
from src.admin_results import ranking,vote_details
from src.database import DatabaseError


def test_reset_requires_login_password_and_explicit_selection(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('private-test-password'))
    monkeypatch.setenv('ADMIN_USERNAME','Owner')
    db=Mock()
    session={'admin_until':time.time()+60,'admin_signature':credential_signature()}
    with patch('src.admin_reset.st.session_state',session):
        for ids,password,confirmation in [(['test-id'],'wrong','RESET'),([], 'private-test-password','RESET'),
                                          (['test-id'],'private-test-password','reset')]:
            with pytest.raises(DatabaseError):
                reset_selected_votes(db,ids,password,confirmation)
        db.rpc.assert_not_called()
        reset_selected_votes(db,['test-id'],'private-test-password','RESET')
        db.rpc.assert_called_once_with('admin_reset_votes',p_participants=['test-id'],p_confirmation='RESET')
        db.reset_mock()
        monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('changed-password'))
        with pytest.raises(DatabaseError):
            reset_selected_votes(db,['test-id'],'changed-password','RESET')
        db.rpc.assert_not_called()


def test_rankings_include_zero_choices_ties_and_details():
    votes=[{'participant_id':'p1','team':'ENERGETICI','team_name_choice':'energentus','crest_choice':'energentus',
            'sponsor_id':'s1','kit_choice':'renewables','submitted_at':'2026-10-04T10:00:00Z'}]
    results=ranking(votes,{'energentus':'ENERGENTUS','renewables':'RENEWABLES'},'team_name_choice')
    assert results==[{'Scelta':'ENERGENTUS','Voti':1,'Percentuale':'100.0%'},
                     {'Scelta':'RENEWABLES','Voti':0,'Percentuale':'0.0%'}]
    detail=vote_details(votes,[{'id':'p1','full_name':'Test'}],[{'id':'s1','sponsor_name':'Sponsor Test'}])[0]
    assert detail['Nome e logo']=='ENERGENTUS' and detail['Maglia']=='ELVES'
    assert detail['Sponsor']=='Sponsor Test'
    assert ranking([],{'a':'A'},'kit_choice')[0]['Percentuale']=='0.0%'


def test_wrong_login_does_not_read_database(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('private-test-password'))
    monkeypatch.setenv('ADMIN_USERNAME','Owner')
    with patch('src.database.Database') as db:
        app=AppTest.from_file('pages/admin.py').run()
        app.text_input[0].input('Owner')
        app.text_input[1].input('wrong')
        next(b for b in app.button if b.label=='Accedi').click().run()
        assert app.error and not app.tabs and not app.exception
        db.assert_not_called()


def test_changing_admin_credentials_invalidates_existing_session(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('private-test-password'))
    monkeypatch.setenv('ADMIN_USERNAME','Owner')
    class Db:
        def participants(self):return []
        def rows(self,*args,**kwargs):return []
        def is_open(self):return True
    with patch('src.database.Database',return_value=Db()) as db:
        app=AppTest.from_file('pages/admin.py').run()
        app.text_input[0].input('Owner');app.text_input[1].input('private-test-password')
        next(b for b in app.button if b.label=='Accedi').click().run()
        assert len(app.tabs)==5 and not app.exception
        db.reset_mock()
        monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('changed-password'))
        app.run()
        assert not app.tabs and not app.exception
        db.assert_not_called()


def test_admin_can_reset_only_selected_trial_vote(monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD_HASH',hash_password('private-test-password'))
    monkeypatch.setenv('ADMIN_USERNAME','Owner')
    class Db:
        def __init__(self):
            self.people=[{'id':p,'full_name':p,'team':'RDM','submitted':True} for p in ('trial','other')]
            self.votes=[{'id':p,'participant_id':p,'team':'RDM','team_name_choice':'rdm_fc',
                         'crest_choice':'rdm_fc','kit_choice':'rdm_world','sponsor_id':'s1','submitted_at':'2026-10-04T10:00:00Z'}
                        for p in ('trial','other')]
            self.calls=[]
        def participants(self):return [p.copy() for p in self.people]
        def is_open(self):return True
        def rows(self,table,**kwargs):
            if table=='votes':return self.votes
            return [{'id':f's{n}','team':'RDM','slot_number':n,'sponsor_name':f'Sponsor {n}'} for n in range(1,4)]
        def rpc(self,function,**params):
            self.calls.append((function,params))
            selected=params['p_participants']
            self.votes=[v for v in self.votes if v['participant_id'] not in selected]
            for p in self.people:
                if p['id'] in selected:p['submitted']=False
            return len(selected)
    db=Db()
    with patch('src.database.Database',return_value=db):
        app=AppTest.from_file('pages/admin.py').run()
        app.text_input[0].input('Owner');app.text_input[1].input('private-test-password')
        next(b for b in app.button if b.label=='Accedi').click().run()
        app.multiselect[0].select('trial')
        next(t for t in app.text_input if t.label=='Scrivi RESET per confermare').input('RESET')
        next(t for t in app.text_input if t.label=='Password Admin per autorizzare il reset').input('private-test-password')
        next(b for b in app.button if b.label=='Resetta i voti selezionati').click().run()
        assert not app.exception and app.success
        assert db.calls==[('admin_reset_votes',{'p_participants':['trial'],'p_confirmation':'RESET'})]
        assert len(db.votes)==1 and db.votes[0]['participant_id']=='other'
        assert not db.people[0]['submitted'] and db.people[1]['submitted']
