"""Local UI benchmark with fake reads; never contacts or writes Supabase."""
import sys
from pathlib import Path
from time import perf_counter
from statistics import median
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest
from src import contest_reads


class BenchmarkDatabase:
    def __init__(self):
        self.reads = 0

    def participants(self):
        self.reads += 1
        return [{'id': 'benchmark', 'full_name': 'Test locale', 'team': 'ENERGETICI', 'submitted': False}]

    def is_open(self):
        self.reads += 1
        return True

    def sponsors(self, team):
        self.reads += 1
        return [{'id': str(n), 'sponsor_name': f'Test {n}', 'slot_number': n, 'team': team} for n in range(1, 4)]


if __name__ == '__main__':
    contest_reads.clear()
    db = BenchmarkDatabase()
    with patch('src.database.Database', return_value=db):
        app = AppTest.from_file('app.py', default_timeout=30).run()
        app.selectbox[0].select('benchmark').run()
        app.button(key='vote_name_energentus').click().run()
        app.button(key='next_1').click().run()
        app.button(key='vote_sponsor_1').click().run()
        app.button(key='next_2').click().run()
        durations = []
        for kit in ('renewables', 'energentus', 'energetici_fc') * 2:
            start = perf_counter()
            app.button(key='vote_kit_' + kit).click().run()
            durations.append((perf_counter() - start) * 1000)
            assert not app.exception
        print(f'Local kit selection: median={median(durations):.0f} ms, max={max(durations):.0f} ms')
        print(f'Database reads across initial load and all selections: {db.reads}')
        print('Fake database; browser transfer and live network latency excluded. No votes submitted.')
