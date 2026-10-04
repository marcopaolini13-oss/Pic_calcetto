from io import BytesIO
from unittest.mock import patch,MagicMock
from itertools import product
import hashlib
import pytest
from PIL import Image,ImageChops,ImageDraw
from src.config import CONCEPTS,ROOT
from src.assets import image_paths,load_image
from src.kit_preview import preview,PLACEMENTS
from src.voting import submit

COMBINATIONS=[(name,kit) for choices in CONCEPTS.values() for name,kit in product(choices,repeat=2)]

@pytest.mark.parametrize('name,kit',COMBINATIONS)
def test_all_combinations_preview_and_submit(name,kit):
    logo=image_paths(name)[0]
    front=ROOT/'assets'/'kits'/kit/'front.jpg'
    before=hashlib.sha256(front.read_bytes()).hexdigest()
    result=preview(name,kit,logo)
    assert result[0].selected_logo==name and result[0].selected_kit==kit
    rendered=load_image(result[0])
    assert rendered.size==(1000,1000)
    assert load_image(result[1]).size==(560,560)
    # Every pixel outside the selected kit's left-chest patch remains real.
    delta=ImageChops.difference(rendered,Image.open(front).convert('RGB'))
    assert delta.getbbox() is not None
    cx,cy,w,h=PLACEMENTS[kit]
    ImageDraw.Draw(delta).rectangle((cx-w,cy-h,cx+w,cy+h),fill=(0,0,0))
    assert delta.getbbox() is None
    assert hashlib.sha256(front.read_bytes()).hexdigest()==before
    paths=image_paths(kit,'kit',name)
    assert paths[0].data==result[0].data
    assert all(getattr(p,'selected_logo',name)==name for p in paths)
    # Public submit contract: names/crests match while all independent kits work.
    db=MagicMock()
    with patch('src.voting.st'):
        submit(db,'participant',name,'sponsor',kit)
    db.rpc.assert_called_once_with('submit_vote',p_participant='participant',p_name=name,
                                   p_sponsor='sponsor',p_crest=name,p_kit=kit)

def test_selected_logo_changes_preview_and_other_team_rejected():
    kit='renewables'
    same=preview('renewables',kit,image_paths('renewables')[0])
    crossed=preview('energentus',kit,image_paths('energentus')[0])
    assert same[0].data!=crossed[0].data
    with pytest.raises(ValueError):
        preview('rdm_fc',kit,image_paths('rdm_fc')[0])
