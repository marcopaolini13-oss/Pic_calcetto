"""Admin reset requires an active credential-bound session and reauthentication."""
import time
import streamlit as st
from src.auth import credential_signature,verify_password
from src.config import secret
from src.database import DatabaseError
from src import contest_reads

def reset_selected_votes(db,participant_ids,password,confirmation):
    if (st.session_state.get('admin_until',0)<=time.time()
            or st.session_state.get('admin_signature')!=credential_signature()
            or not verify_password(password,secret('ADMIN_PASSWORD_HASH'))):
        raise DatabaseError('RESET_NOT_AUTHORIZED')
    if confirmation!='RESET' or not 1<=len(participant_ids)<=50 or len(set(participant_ids))!=len(participant_ids):
        raise DatabaseError('INVALID_RESET')
    result=db.rpc('admin_reset_votes',p_participants=participant_ids,p_confirmation='RESET')
    contest_reads.clear()
    return result
