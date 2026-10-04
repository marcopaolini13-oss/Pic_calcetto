import json
import hashlib
from PIL import Image,ImageChops,ImageDraw
from src.config import ROOT
from src.assets import image_paths

def test_overlay_preserves_real_jersey_and_logo_sources():
    records=json.loads((ROOT/'assets'/'crest_previews.json').read_text())
    assert len(records)==6
    for concept,record in records.items():
        original=Image.open(ROOT/record['source']).convert('RGB')
        front=Image.open(ROOT/record['front']).convert('RGB')
        detail=Image.open(ROOT/record['detail']).convert('RGB')
        assert front.size==original.size==(1000,1000)
        assert detail.size==(560,560)
        # Exact photo pixels outside the actual crest patch rectangle.
        delta=ImageChops.difference(original,front)
        assert delta.getbbox() is not None
        ImageDraw.Draw(delta).rectangle(record['crest_box'],fill=(0,0,0))
        assert delta.getbbox() is None
        assert ImageChops.difference(detail,front.crop(record['detail_crop'])).getbbox() is None
        assert record['crest_box'][0]>500  # Wearer's left = viewer's right.
        assert hashlib.sha256((ROOT/record['source']).read_bytes()).hexdigest()==record['source_sha256']
        assert hashlib.sha256((ROOT/record['logo']).read_bytes()).hexdigest()==record['logo_sha256']
        paths=image_paths(concept,'kit')
        assert paths[0]==ROOT/record['detail']
        assert ROOT/record['front'] in paths
        assert ROOT/record['source'] in paths
