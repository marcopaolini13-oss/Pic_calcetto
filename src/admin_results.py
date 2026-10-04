"""Readable result data; no database writes."""
from collections import Counter
from src.config import TEAMS,CONCEPTS,KIT_NAMES

def ranking(votes,options,field):
    counts=Counter(v[field] for v in votes)
    total=len(votes)
    return sorted([{'Scelta':label,'Voti':counts[value],
                    'Percentuale':f'{counts[value]/total:.1%}' if total else '0.0%'}
                   for value,label in options.items()],key=lambda row:-row['Voti'])

def vote_details(votes,people,sponsors):
    participants={p['id']:p['full_name'] for p in people}
    sponsor_names={s['id']:s['sponsor_name'] for s in sponsors}
    return [{'Partecipante':participants.get(v['participant_id'],'Partecipante non disponibile'),
             'Squadra':TEAMS[v['team']],
             'Nome e logo':CONCEPTS[v['team']].get(v['team_name_choice'],v['team_name_choice']),
             'Sponsor':sponsor_names.get(v['sponsor_id'],'Sponsor non disponibile'),
             'Maglia':KIT_NAMES.get(v['kit_choice'],v['kit_choice']),
             'Data voto (UTC)':v.get('submitted_at','')} for v in votes]
