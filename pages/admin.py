import streamlit as st
from src.auth import require_admin
from src.config import TEAMS, CONCEPTS
from src.database import Database, DatabaseError
from src.ui import style
from src.utils import csv_bytes
from src.admin_results import ranking,vote_details
from src.admin_reset import reset_selected_votes

st.set_page_config(page_title='Admin · FAVERO',page_icon='🔐',layout='wide')
style()
require_admin()
st.title('Gestione contest · Paolo')
if notice:=st.session_state.pop('admin_reset_notice',None):
    st.success(notice)
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
    results_tab,participants_tab,sponsors_tab,export_tab,reset_tab=st.tabs(['Risultati','Partecipanti','Sponsor','Export','Reset prove'])
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
        st.caption('Risultati riservati all’organizzatore. Nome e logo sono una scelta unica; sponsor e maglia sono indipendenti.')
        for team,label in TEAMS.items():
            with st.container(border=True):
                st.header(label)
                team_votes=[v for v in votes if v['team']==team]
                team_people=[p for p in people if p['team']==team]
                a,b,c=st.columns(3)
                a.metric('Voti ricevuti',len(team_votes))
                b.metric('In attesa',max(0,len(team_people)-len(team_votes)))
                c.metric('Completamento',f'{len(team_votes)/len(team_people):.0%}' if team_people else '0%')
                for col,(field,title) in zip(st.columns(3),[('team_name_choice','Nome e logo'),('sponsor_id','Sponsor'),('kit_choice','Maglia')]):
                    with col:
                        st.subheader(title)
                        options={s['id']:s['sponsor_name'] for s in sponsors if s['team']==team} if field=='sponsor_id' else CONCEPTS[team]
                        rows=ranking(team_votes,options,field)
                        if team_votes and rows:
                            best=rows[0]['Voti']
                            winners=[r['Scelta'] for r in rows if r['Voti']==best]
                            st.write(('In testa: ' if len(winners)==1 else 'Pari merito: ')+' · '.join(winners))
                        st.dataframe(rows,hide_index=True,width='stretch')
        st.subheader('Dettaglio voti')
        filter_team=st.selectbox('Filtra squadra',['Tutte',*TEAMS],format_func=lambda t:TEAMS.get(t,t))
        filtered=votes if filter_team=='Tutte' else [v for v in votes if v['team']==filter_team]
        if filtered:
            st.dataframe(vote_details(filtered,people,sponsors),hide_index=True,width='stretch')
        else:
            st.info('Nessun voto registrato per questa selezione.')
    with export_tab:
        participant_map={p['id']:p['full_name'] for p in people}
        sponsor_map={s['id']:s['sponsor_name'] for s in sponsors}
        export=[{**v,'full_name':participant_map.get(v['participant_id'],''),
                 'sponsor_name':sponsor_map.get(v['sponsor_id'],'')} for v in votes]
        st.download_button('ESPORTA RISULTATI CSV',csv_bytes(export),file_name='favero_voti.csv',mime='text/csv',disabled=not votes)
        st.caption('Il CSV contiene voti definitivi e nominativi. Conservalo in un archivio aziendale riservato.')
    with reset_tab:
        st.subheader('Reset dei voti di prova')
        st.write('Seleziona soltanto i partecipanti delle prove: vengono eliminati i loro voti e potranno votare di nuovo. Gli altri voti e i partecipanti restano invariati.')
        st.caption('Per attivare questa funzione, esegui una volta la migrazione sql/migrations/001_admin_reset_votes.sql nel progetto Calcetto FAVERO. Non esegue alcun reset da sola.')
        submitted={p['id']:p for p in people if p['submitted']}
        if not submitted:
            st.info('Non ci sono voti da resettare.')
        else:
            with st.form('admin_reset_form',clear_on_submit=True):
                selected_ids=st.multiselect('Partecipanti di prova da resettare',list(submitted),
                    format_func=lambda pid:submitted[pid]['full_name']+' · '+TEAMS[submitted[pid]['team']],max_selections=50)
                st.warning('L’eliminazione dei voti selezionati è definitiva. Esporta prima il CSV se vuoi conservarne una copia.')
                confirmation=st.text_input('Scrivi RESET per confermare')
                password=st.text_input('Password Admin per autorizzare il reset',type='password')
                if st.form_submit_button('Resetta i voti selezionati',type='primary'):
                    removed=reset_selected_votes(db,selected_ids,password,confirmation)
                    st.session_state.admin_reset_notice=f'Reset completato: {removed} voti eliminati. I partecipanti selezionati possono votare di nuovo.'
                    st.rerun()
except DatabaseError as exc:
    st.error({'SPONSORS_LOCKED':'Sponsor bloccati: è arrivato un voto definitivo.',
              'RESET_NOT_AUTHORIZED':'Reset non autorizzato: verifica la password Admin o accedi nuovamente.',
              'INVALID_RESET':'Seleziona almeno un partecipante e scrivi esattamente RESET.',
              'PARTICIPANT_LOCKED':'Il partecipante ha già votato e non è modificabile.'}.get(str(exc),str(exc)))
