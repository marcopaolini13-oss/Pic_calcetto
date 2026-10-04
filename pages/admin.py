import streamlit as st
from collections import Counter
from src.auth import require_admin
from src.config import TEAMS, CONCEPTS
from src.database import Database, DatabaseError
from src.ui import style
from src.utils import csv_bytes

st.set_page_config(page_title='Admin · FAVERO',page_icon='🔐',layout='wide')
style()
require_admin()
st.title('Gestione contest · Paolo')
try:
    db=Database()
    people=db.participants()
    votes=db.rows('votes',order='submitted_at.asc')
    sponsors=db.rows('sponsors',order='team.asc,slot_number.asc')
    total=len(people)
    received=len(votes)
    metrics=st.columns(4)
    for col,label,value in zip(metrics,['Partecipanti','Voti ricevuti','Voti mancanti','Completamento'],
                               [total,received,max(0,total-received),f'{received/total:.0%}' if total else '0%']):
        col.metric(label,value)
    opened=db.is_open()
    with st.expander('Configurazione contest'):
        active=st.toggle('Votazioni aperte',value=opened)
        if st.button('Salva configurazione'):
            db.rpc('set_contest_open',p_open=active)
            st.rerun()
    participants_tab,sponsors_tab,results_tab,export_tab=st.tabs(['Partecipanti','Sponsor','Risultati','Export'])
    with participants_tab:
        st.dataframe([{'Nome':p['full_name'],'Squadra':TEAMS[p['team']], 'Stato voto':'Registrato' if p['submitted'] else 'In attesa'} for p in people],hide_index=True,width='stretch')
        with st.form('add_person',clear_on_submit=True):
            name=st.text_input('Nome e cognome',max_chars=120)
            team=st.selectbox('Squadra assegnata',list(TEAMS),format_func=TEAMS.get)
            if st.form_submit_button('Aggiungi partecipante'):
                if not name.strip():
                    st.error('Inserisci nome e cognome.')
                else:
                    db.rpc('manage_participant',p_action='add',p_id=None,p_name=name,p_team=team)
                    st.rerun()
        editable={p['id']:p for p in people if not p['submitted']}
        if editable:
            pid=st.selectbox('Partecipante da gestire',list(editable),format_func=lambda p:editable[p]['full_name'])
            team=st.selectbox('Nuova squadra',list(TEAMS),index=list(TEAMS).index(editable[pid]['team']),format_func=TEAMS.get)
            if st.button('Aggiorna squadra'):
                db.rpc('manage_participant',p_action='update',p_id=pid,p_name=None,p_team=team)
                st.rerun()
            deletion=st.checkbox('Confermo di eliminare questo partecipante')
            if st.button('Elimina partecipante',disabled=not deletion):
                db.rpc('manage_participant',p_action='delete',p_id=pid,p_name=None,p_team=None)
                st.rerun()
    with sponsors_tab:
        for team,label in TEAMS.items():
            st.subheader(label)
            locked=any(v['team']==team for v in votes)
            if locked:
                st.warning('Sponsor bloccati: questa squadra ha almeno un voto definitivo. Cambiarli altererebbe il significato dei voti.')
            with st.form('sponsors_'+team):
                names=[st.text_input(f'Sponsor {s["slot_number"]}',value=s['sponsor_name'],disabled=locked,max_chars=120)
                       for s in sponsors if s['team']==team]
                if st.form_submit_button('Salva sponsor',disabled=locked):
                    if len(names)!=3 or not all(n.strip() for n in names):
                        st.error('Servono tre sponsor con testo non vuoto.')
                    else:
                        db.rpc('update_sponsors',p_team=team,p_names=names)
                        st.rerun()
    with results_tab:
        for team,label in TEAMS.items():
            st.header(label)
            team_votes=[v for v in votes if v['team']==team]
            st.caption(f'{len(team_votes)} voti definitivi')
            for field,title in [('team_name_choice','Nome squadra'),('sponsor_id','Sponsor'),('crest_choice','Stemma'),('kit_choice','Maglia')]:
                st.subheader(title)
                options={s['id']:s['sponsor_name'] for s in sponsors if s['team']==team} if field=='sponsor_id' else CONCEPTS[team]
                counts=Counter(v[field] for v in team_votes)
                for value,text in options.items():
                    count=counts[value]
                    fraction=count/len(team_votes) if team_votes else 0
                    st.progress(fraction,text=f'{text} · {count} voti · {fraction:.1%}')
    with export_tab:
        participant_map={p['id']:p['full_name'] for p in people}
        sponsor_map={s['id']:s['sponsor_name'] for s in sponsors}
        export=[{**v,'full_name':participant_map.get(v['participant_id'],''),
                 'sponsor_name':sponsor_map.get(v['sponsor_id'],'')} for v in votes]
        st.download_button('ESPORTA RISULTATI CSV',csv_bytes(export),file_name='favero_voti.csv',mime='text/csv',disabled=not votes)
        st.caption('Il CSV contiene voti definitivi e nominativi. Conservalo in un archivio aziendale riservato.')
except DatabaseError as exc:
    st.error({'SPONSORS_LOCKED':'Sponsor bloccati: è arrivato un voto definitivo.',
              'PARTICIPANT_LOCKED':'Il partecipante ha già votato e non è modificabile.'}.get(str(exc),str(exc)))
