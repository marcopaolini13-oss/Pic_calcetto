import base64
import hashlib
import hmac
import secrets
import time
import streamlit as st
from src.config import secret

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600_000)
    return 'pbkdf2_sha256$600000$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(digest).decode()

def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256' or not 100_000 <= int(rounds) <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(actual, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False

def credential_signature():
    return hashlib.sha256((secret('ADMIN_USERNAME','Paolo')+'|'+secret('ADMIN_PASSWORD_HASH')).encode()).hexdigest()

def require_admin():
    if (st.session_state.get('admin_until', 0) > time.time()
            and st.session_state.get('admin_signature')==credential_signature()
            and secret('ADMIN_PASSWORD_HASH')):
        if st.sidebar.button('Esci da Admin'):
            st.session_state.pop('admin_until', None)
            st.session_state.pop('admin_signature', None)
            st.rerun()
            st.rerun()
        return
    st.title('Admin · Paolo')
    if not secret('ADMIN_PASSWORD_HASH'):
        st.warning('Configura ADMIN_PASSWORD_HASH per attivare Admin.')
        st.stop()
    with st.form('login'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submit = st.form_submit_button('Accedi')
    if submit:
        if time.time() < st.session_state.get('login_retry_at', 0):
            st.error('Attendi qualche secondo prima di riprovare.')
        elif hmac.compare_digest(username, secret('ADMIN_USERNAME', 'Paolo')) and verify_password(password, secret('ADMIN_PASSWORD_HASH')):
            st.session_state.admin_until = time.time() + 3600
            st.session_state.admin_signature = credential_signature()
            st.rerun()
        else:
            st.session_state.login_retry_at = time.time() + 5
            st.error('Credenziali non valide.')
    st.stop()
