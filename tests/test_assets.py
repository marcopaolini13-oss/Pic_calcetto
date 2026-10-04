from pathlib import Path
from unittest.mock import patch
import hashlib
import json
import pytest
from streamlit.testing.v1 import AppTest
from src.config import CONCEPTS,ROOT
from src.assets import image_paths,load_image,manifest

def test_real_assets_and_unchanged_sources():
    data=manifest()
    for concepts in CONCEPTS.values():
        for concept in concepts:
            logo=image_paths(concept)
            kit=image_paths(concept,'kit')
            assert len(logo)==1 and len(kit)>=4
            assert kit[0].stem=='detail_with_crest'
            assert any(p.stem=='front' for p in kit)
            for p in logo+kit:
                picture=load_image(p)
                assert picture is not None
                assert min(picture.size)>=500
    records=list(data['logos'].values())+[v for kit in data['kits'].values() for v in kit]
    for record in records:
        assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256']
        assert hashlib.sha256((ROOT/record['source']).read_bytes()).hexdigest()==record['sha256']

@pytest.mark.parametrize('team',['ENERGETICI','RDM'])
@pytest.mark.parametrize('kind',['Stemma','Maglia'])
def test_preview_zoom_gallery(team,kind):
    at=AppTest.from_file('scripts/preview_assets.py').run(timeout=15)
    at.selectbox[0].select(team).run()
    at.radio[0].set_value(kind).run()
    assert not at.exception
    zoom=[b for b in at.button if str(b.key).startswith('asset_zoom_')]
    assert len(zoom)==3 and all(not b.disabled for b in zoom)
    if kind=='Maglia':
        thumbnails=[b for b in at.button if str(b.key).startswith('asset_thumb_')]
        back=next(b for b in thumbnails if '![Retro]' in b.label)
        back_index=int(back.key.rsplit('_',1)[1])
        back.click().run()
        assert not at.exception
        assert any(k.startswith('gallery_view_') and v==back_index for k,v in at.session_state.filtered_state.items())
        assert any(c.value=='Retro' for c in at.caption)
        zoom=[b for b in at.button if str(b.key).startswith('asset_zoom_')]
    zoom[0].click().run()
    assert not at.exception
    assert any(b.label=='Chiudi' for b in at.button)
    if kind=='Maglia':
        view=next(s for s in at.selectbox if s.label=='Vista')
        view.select(2).run()
        assert not at.exception
    next(b for b in at.button if b.label=='Chiudi').click().run()
    assert not at.exception
    # AppTest retains the previous fragment tree after an app rerun; the modal
    # lifecycle is asserted from application state instead of that stale tree.
    assert 'asset_open_lightbox' not in at.session_state.filtered_state
    assert all(not k.startswith('vote_') for k in at.session_state.filtered_state)

def test_missing_image_and_mockup_precedence(tmp_path,caplog):
    assert load_image(tmp_path/'missing.png') is None
    assert 'missing.png' in caplog.text
    directory=tmp_path/'assets'/'mockups'/'rdm_fc'
    directory.mkdir(parents=True)
    generic=directory/'front.jpg';generic.write_bytes(b'dummy')
    specific=directory/'rdm_world__sponsor-id'
    specific.mkdir();(specific/'front.jpg').write_bytes(b'dummy')
    with patch('src.assets.ROOT',tmp_path):
        assert image_paths('rdm_fc','kit')==[generic]
        assert image_paths('rdm_fc','kit','rdm_world','sponsor-id')==[specific/'front.jpg']
