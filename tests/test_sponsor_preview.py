from io import BytesIO
from itertools import product
from PIL import Image,ImageChops,ImageDraw
import pytest
from src.assets import image_paths,load_image
from src.kit_preview import preview,with_sponsor
from src.config import CONCEPTS

@pytest.mark.parametrize('name,kit',[pair for choices in CONCEPTS.values() for pair in product(choices,repeat=2)])
def test_sponsor_overlay_preserves_crest_and_original_photo(name,kit):
    original=preview(name,kit,image_paths(name)[0])[0]
    rendered=with_sponsor(original,'Sponsor di prova')
    assert load_image(rendered[0]).size==(1000,1000)
    assert load_image(rendered[1]).size==(560,560)
    delta=ImageChops.difference(load_image(original),load_image(rendered[0]))
    assert delta.getbbox() is not None
    ImageDraw.Draw(delta).rectangle((310,305,690,375),fill=(0,0,0))
    assert delta.getbbox() is None
    assert with_sponsor(original,'Altro sponsor')[0].data!=rendered[0].data
    files=image_paths(kit,'kit',name,'sponsor-id','Sponsor di prova')
    assert files[0].data==rendered[0].data
    assert any(p.stem=='front' for p in files)
