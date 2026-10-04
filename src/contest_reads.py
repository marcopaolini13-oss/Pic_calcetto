"""Short-lived read cache for the public wizard; submit stays authoritative."""
import hashlib
import streamlit as st

def identity(db):
    if hasattr(db,'url') and hasattr(db,'key'):
        return hashlib.sha256((db.url+'|'+db.key).encode()).hexdigest()
    return str(id(db))

@st.cache_data(ttl=10,max_entries=16,show_spinner=False)
def participants(identity_key,_db):
    return _db.participants()

@st.cache_data(ttl=10,max_entries=32,show_spinner=False)
def options(identity_key,team,_db):
    return _db.is_open(),_db.sponsors(team)

def clear():
    participants.clear()
    options.clear()
