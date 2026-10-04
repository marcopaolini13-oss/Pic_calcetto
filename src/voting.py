import streamlit as st
from src.config import CONCEPTS, TEAMS, KIT_NAMES
from src.ui import cards, show_image
from src.database import DatabaseError
from src import contest_reads

def reset_vote():
    for key in list(st.session_state):
        if key.startswith(('vote_','gallery_')):
            del st.session_state[key]

def submit(db, participant, name, sponsor, kit):
    try:
        db.rpc('submit_vote',p_participant=participant,p_name=name,p_sponsor=sponsor,p_crest=name,p_kit=kit)
        contest_reads.clear()
        st.session_state.vote_success=True
        st.session_state.pop('vote_error',None)
    except DatabaseError as exc:
        if str(exc)=='ALREADY_SUBMITTED':
            contest_reads.clear()
            st.session_state.vote_success=True
        else:
            st.session_state.vote_error={'CONTEST_CLOSED':'Il contest è stato chiuso.',
                'INVALID_CHOICE':'Le opzioni sono cambiate. Controlla le scelte.'}.get(str(exc),str(exc))

def modify_choices():
    st.session_state.vote_step=1
    st.session_state.vote_confirm=False
    st.session_state.pop('vote_error',None)

def navigate(step):
    st.session_state.vote_step=step
    st.session_state.pop('asset_open_lightbox',None)

def wizard(db, person):
    team = person['team']
    concepts = CONCEPTS[team]
    if person['submitted']:
        st.success('Il tuo voto è già stato registrato.')
        st.info('Grazie. Il tuo voto è stato salvato e non può più essere modificato.')
        return
    opened,sponsor_rows=contest_reads.options(contest_reads.identity(db),team,db)
    if not opened:
        st.warning('Il contest è chiuso. Non è possibile inviare voti.')
        return
    sponsors = {s['id']:s['sponsor_name'] for s in sponsor_rows}
    if len(sponsors)!=3:
        st.error('Paolo deve configurare tre sponsor attivi per questa squadra.')
        return
    # Upgrade an existing draft from the previous combined-concept flow.
    if st.session_state.get('vote_flow_version')!=4:
        previous=st.session_state.pop('vote_concept',None)
        if previous in concepts:
            st.session_state.vote_kit=previous
        st.session_state.pop('vote_crest',None)
        st.session_state.vote_step=1
        st.session_state.vote_confirm=False
        st.session_state.vote_flow_version=4
    step = min(4,max(1,st.session_state.get('vote_step',1)))
    st.subheader('Stai votando per ' + TEAMS[team])
    st.progress(step/4, text=f'Step {step} di 4')
    labels = ['Nome + logo','Sponsor','Maglia','Riepilogo e conferma']
    st.header(labels[step-1])
    keys = ['vote_name','vote_sponsor','vote_kit']
    if step<=3:
        if step==1:
            st.caption('Scegli nome e logo insieme, poi lo sponsor e infine la maglia.')
        if step==3:
            if st.session_state.get('vote_name') not in concepts or st.session_state.get('vote_sponsor') not in sponsors:
                navigate(2);st.rerun()
            st.caption('Tutte le maglie mostrano il logo '+concepts[st.session_state['vote_name']]
                       +' e lo sponsor '+sponsors[st.session_state['vote_sponsor']]+'.')
        options=sponsors if step==2 else {key:KIT_NAMES[key] for key in concepts} if step==3 else concepts
        cards(options,keys[step-1],team,
              None if step==2 else 'kit' if step==3 else 'logo',
              st.session_state.get('vote_name'),st.session_state.get('vote_sponsor'),
              sponsors.get(st.session_state.get('vote_sponsor')))
        left,right = st.columns(2)
        left.button('← Indietro',disabled=step==1,key=f'back_{step}',on_click=navigate,args=(step-1,))
        right.button('Avanti →', type='primary',disabled=not st.session_state.get(keys[step-1]),
                     key=f'next_{step}',on_click=navigate,args=(step+1,))
        return
    if not all(st.session_state.get(k) for k in keys):
        st.session_state.vote_step=1
        st.rerun()
    name,sponsor,kit = [st.session_state[k] for k in keys]
    if name not in concepts or kit not in concepts:
        st.session_state.vote_step=1
        st.rerun()
    if sponsor not in sponsors:
        st.warning('Lo sponsor non è più disponibile. Selezionalo nuovamente.')
        st.session_state.vote_step=2
        st.session_state.pop('vote_sponsor',None)
        st.rerun()
    st.write('**Squadra:** ' + TEAMS[team])
    with st.container(border=True):
        st.subheader('La tua combinazione')
        a,b=st.columns(2)
        with a:
            st.write('**Nome/logo scelto:** '+concepts[name])
            show_image(name,concepts[name],team)
        with b:
            st.write('**Maglia scelta:** '+KIT_NAMES[kit])
            show_image(kit,KIT_NAMES[kit],team,'kit',name,sponsor,True,sponsors[sponsor])
            st.write('**Sponsor scelto:** '+sponsors[sponsor])
    st.warning('ATTENZIONE: dopo la conferma non sarà più possibile modificare il voto.')
    confirm=st.checkbox('Confermo di voler inviare definitivamente il mio voto.',key='vote_confirm')
    st.button('← MODIFICA LE SCELTE',on_click=modify_choices)
    st.button('CONFERMA DEFINITIVAMENTE',type='primary',disabled=not confirm,
              on_click=submit,args=(db,person['id'],name,sponsor,kit))
    if st.session_state.get('vote_error'):
        st.error(st.session_state.vote_error)
