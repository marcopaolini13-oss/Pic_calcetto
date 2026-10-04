"""Build all 18 genuine logo/kit combinations before serving the app."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import hashlib
from src.config import ROOT,CONCEPTS
from src.assets import image_paths
from src.kit_preview import compose,asset_bytes

if __name__=='__main__':
    for choices in CONCEPTS.values():
        for logo in choices:
            logo_bytes=asset_bytes(image_paths(logo)[0])
            for kit in choices:
                front=asset_bytes(ROOT/'assets'/'kits'/kit/'front.jpg')
                output=ROOT/'assets'/'mockups'/'combinations'/logo/kit
                output.mkdir(parents=True,exist_ok=True)
                for picture in compose(front,logo_bytes,logo,kit):
                    (output/(picture.stem+'.png')).write_bytes(picture.data)
                (output/'sources.json').write_text(json.dumps({'front':hashlib.sha256(front).hexdigest(),
                    'logo':hashlib.sha256(logo_bytes).hexdigest()}),encoding='utf-8')
    print('Prepared all 18 combinations. Original sources unchanged.')
