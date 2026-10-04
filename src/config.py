from pathlib import Path
import os
from dotenv import load_dotenv
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
TEAMS = {'ENERGETICI': 'ENERGETICI', 'RDM': 'RESTO DEL MONDO'}
CONCEPTS = {
    'ENERGETICI': {'energetici_fc': 'ENERGETICI F.C.', 'renewables': 'RENEWABLES', 'energentus': 'ENERGENTUS'},
    'RDM': {'rdm_fc': 'RDM F.C.', 'rdm_world': 'RDM WORLD', 'rdm_internazionale': 'RDM INTERNAZIONALE'},
}

KIT_NAMES = {
    'energetici_fc': 'CHARON', 'renewables': 'ELVES', 'energentus': 'SPECTRUM',
    'rdm_fc': 'CHARON', 'rdm_world': 'ELVES', 'rdm_internazionale': 'SPECTRUM',
}

def secret(name, default=''):
    try:
        return str(st.secrets.get(name, os.getenv(name, default)))
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.getenv(name, default)
