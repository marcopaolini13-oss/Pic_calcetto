import streamlit as st
from src.database import Database, DatabaseError
from src.ui import style
from src.voting import wizard, reset_vote
from src.config import TEAMS
from src import contest_reads

st.set_page_config(page_title='FAVERO FOOTBALL KIT CONTEST',page_icon='⚽',layout='wide')
style()
st.caption('FAVERO')
st.title('FOOTBALL KIT CONTEST')
st.subheader('ENERGETICI  VS  RESTO DEL MONDO')
st.page_link('pages/admin.py',label='Area Admin · Paolo',icon='🔐')
try:
    db=Database()
    people=contest_reads.participants(contest_reads.identity(db),db)
    if not people:
        st.info('Il contest è in preparazione. Paolo deve aggiungere i partecipanti in Admin.')
        st.stop()
    lookup={p['id']:p for p in people}
    selected=st.selectbox('Seleziona il tuo nome',list(lookup),index=None,
        placeholder='Chi sei?',format_func=lambda pid:lookup[pid]['full_name']+' · '+TEAMS[lookup[pid]['team']],key='participant_select')
    if selected:
        signature=(selected,lookup[selected]['team'])
        if st.session_state.get('participant_signature')!=signature:
            reset_vote()
            st.session_state.participant_signature=signature
        if st.session_state.get('vote_success') and lookup[selected]['submitted']:
            st.success('VOTO REGISTRATO ✓')
        wizard(db,lookup[selected])
except DatabaseError as exc:
    st.error(str(exc))
