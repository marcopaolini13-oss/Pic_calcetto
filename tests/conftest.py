def pytest_addoption(parser):
    parser.addoption('--postgres-container',default=None,help='Container PostgreSQL isolato con schema.sql già caricato')
