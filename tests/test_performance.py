from unittest.mock import Mock, patch
from PIL import Image
from src import contest_reads
from src.assets import load_image
from src.voting import submit


def test_reads_reused_and_refreshed_after_submit():
    contest_reads.clear()
    db = Mock()
    db.url, db.key = 'test-url', 'test-key'
    db.participants.return_value = [{'id': 'test', 'submitted': False}]
    db.is_open.return_value = True
    db.sponsors.return_value = [{'id': 'sponsor'}]
    key = contest_reads.identity(db)
    for _ in range(3):
        assert not contest_reads.participants(key, db)[0]['submitted']
        assert contest_reads.options(key, 'ENERGETICI', db)[0]
    assert db.participants.call_count == db.is_open.call_count == db.sponsors.call_count == 1
    db.participants.return_value = [{'id': 'test', 'submitted': True}]
    db.is_open.return_value = False
    with patch('src.voting.st.session_state'):
        submit(db, 'test', 'energentus', 'sponsor', 'renewables')
    db.rpc.assert_called_once_with('submit_vote', p_participant='test', p_name='energentus',
                                  p_sponsor='sponsor', p_crest='energentus', p_kit='renewables')
    assert contest_reads.participants(key, db)[0]['submitted']
    assert not contest_reads.options(key, 'ENERGETICI', db)[0]
    contest_reads.clear()


def test_image_cache_does_not_hide_replaced_files_or_share_mutable_images(tmp_path):
    path = tmp_path / 'kit.png'
    Image.new('RGB', (20, 30), 'red').save(path)
    first = load_image(path)
    first.putpixel((0, 0), (0, 0, 0))
    assert load_image(path).getpixel((0, 0)) == (255, 0, 0)
    Image.new('RGB', (40, 50), 'blue').save(path)
    updated = load_image(path)
    assert updated.size == (40, 50)
    assert updated.getpixel((0, 0)) == (0, 0, 255)
