import requests
from src.config import secret

class DatabaseError(Exception):
    pass

class Database:
    def __init__(self):
        self.url = secret('SUPABASE_URL').rstrip('/')
        self.key = secret('SUPABASE_KEY')
        if not self.url or not self.key:
            raise DatabaseError('Configura SUPABASE_URL e SUPABASE_KEY in .env o Streamlit Secrets.')

    def request(self, method, path, params=None, body=None):
        try:
            response = requests.request(method, self.url + '/rest/v1/' + path,
                headers={'apikey': self.key, 'Authorization': 'Bearer ' + self.key,
                         'Prefer': 'return=representation'},
                params=params, json=body, timeout=20)
        except requests.RequestException:
            raise DatabaseError('Connessione al database non disponibile. Riprova: le scelte restano in questa sessione.') from None
        if not response.ok:
            try:
                message = response.json().get('message', '')
            except ValueError:
                message = ''
            known = ['ALREADY_SUBMITTED', 'CONTEST_CLOSED', 'INVALID_CHOICE', 'PARTICIPANT_LOCKED', 'SPONSORS_LOCKED']
            error = next((x for x in known if x in message), None)
            raise DatabaseError(error or 'Operazione database non riuscita. Verifica schema, chiave e connessione.')
        return response.json() if response.content else []

    def rows(self, table, **filters):
        return self.request('GET', table, params={'select': '*', **filters})

    def rpc(self, function, **params):
        return self.request('POST', 'rpc/' + function, body=params)

    def participants(self):
        return self.rows('participants', order='full_name.asc')

    def sponsors(self, team):
        return self.rows('sponsors', team='eq.' + team, active='eq.true', order='slot_number.asc')

    def is_open(self):
        rows = self.rows('contest_settings', key='eq.contest_open')
        return bool(rows and rows[0]['value'] == 'true')
