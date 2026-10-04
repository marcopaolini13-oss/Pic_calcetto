"""UI-only preview; never imports the database or submits votes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import streamlit as st
from src.config import CONCEPTS,TEAMS
from src.ui import style,cards

st.set_page_config(page_title='Anteprima asset FAVERO',layout='wide')
style()
st.title('Anteprima asset · nessun voto viene registrato')
team=st.selectbox('Squadra',list(TEAMS),format_func=TEAMS.get)
kind=st.radio('Schermata',['Stemma','Maglia'],horizontal=True)
cards(CONCEPTS[team],'preview_'+team+'_'+kind,team,'logo' if kind=='Stemma' else 'kit')
