import sys
from pathlib import Path
from getpass import getpass
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.auth import hash_password

if __name__ == '__main__':
    password = getpass('Password Admin: ')
    if len(password) < 12:
        raise SystemExit('Usa almeno 12 caratteri.')
    if password != getpass('Ripeti password: '):
        raise SystemExit('Le password non coincidono.')
    print(hash_password(password))
