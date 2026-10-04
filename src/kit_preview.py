"""Cached, deterministic previews from the real selected logo and jersey."""
from dataclasses import dataclass,field
from pathlib import Path
from io import BytesIO
import streamlit as st
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from src.config import ROOT,CONCEPTS
from scripts.apply_crests import cutout,PLACEMENTS
from functools import lru_cache
import hashlib
import json

@lru_cache(maxsize=12)
def prepared_crest(logo_bytes):
    with Image.open(BytesIO(logo_bytes)) as im:
        return cutout(im)

@lru_cache(maxsize=128)
def read_asset(path,stamp,size):
    return Path(path).read_bytes()

def asset_bytes(path):
    path=Path(path);info=path.stat()
    return read_asset(str(path),info.st_mtime_ns,info.st_size)

@dataclass(frozen=True)
class PreviewImage:
    stem:str
    data:bytes=field(repr=False)
    selected_logo:str=''
    selected_kit:str=''

@st.cache_data(show_spinner=False,max_entries=36)
def compose(front_bytes,logo_bytes,selected_logo,selected_kit):
    with Image.open(BytesIO(front_bytes)) as im: base=im.convert('RGB')
    crest=prepared_crest(logo_bytes).copy()
    cx,cy,max_width,max_height=PLACEMENTS[selected_kit]
    crest.thumbnail((max_width,max_height),Image.Resampling.LANCZOS)
    edge=crest.getchannel('A').filter(ImageFilter.MaxFilter(3))
    patch=Image.new('RGBA',crest.size,(245,245,245,255));patch.putalpha(edge)
    patch.alpha_composite(crest)
    x,y=cx-crest.width//2,cy-crest.height//2
    base.paste(patch,(x,y),patch)
    full=BytesIO();base.save(full,format='PNG')
    detail=BytesIO();base.crop((380,50,940,610)).save(detail,format='PNG')
    return [PreviewImage('front_with_crest',full.getvalue(),selected_logo,selected_kit),
            PreviewImage('detail_with_crest',detail.getvalue(),selected_logo,selected_kit)]

def preview(selected_logo,selected_kit,logo_path):
    if not any(selected_logo in choices and selected_kit in choices for choices in CONCEPTS.values()):
        raise ValueError('Logo and kit must belong to the same team')
    front=ROOT/'assets'/'kits'/selected_kit/'front.jpg'
    front_bytes=asset_bytes(front);logo_bytes=asset_bytes(logo_path)
    directory=ROOT/'assets'/'mockups'/'combinations'/selected_logo/selected_kit
    try:
        metadata=json.loads(asset_bytes(directory/'sources.json'))
        if metadata=={'front':hashlib.sha256(front_bytes).hexdigest(),'logo':hashlib.sha256(logo_bytes).hexdigest()}:
            return [PreviewImage(stem,asset_bytes(directory/(stem+'.png')),selected_logo,selected_kit)
                    for stem in ('front_with_crest','detail_with_crest')]
    except (OSError,ValueError):
        pass
    return compose(front_bytes,logo_bytes,selected_logo,selected_kit)

@st.cache_data(show_spinner=False,max_entries=64)
def with_sponsor(front_preview,sponsor_label):
    """Apply the actual sponsor name to the real chest; keep source photos intact."""
    text=sponsor_label.strip()
    if not text or len(text)>120:
        raise ValueError('Invalid sponsor label')
    with Image.open(BytesIO(front_preview.data)) as im:
        base=im.convert('RGB')
    draw=ImageDraw.Draw(base)
    def font_at(size):
        for font in ('DejaVuSans-Bold.ttf','arialbd.ttf'):
            try: return ImageFont.truetype(font,size)
            except OSError: pass
        return ImageFont.load_default(size=size)
    # Fit lettering inside the torso, below both chest badges. Outlined white
    # printing remains readable on solid and striped fabrics without a panel.
    for size in range(34,9,-1):
        font=font_at(size)
        if draw.textbbox((0,0),text,font=font,stroke_width=2)[2]<=350:
            break
    draw.text((500,340),text,font=font,anchor='mm',fill='white',stroke_width=2,stroke_fill='#18202b')
    full=BytesIO();base.save(full,format='PNG')
    detail=BytesIO();base.crop((220,70,780,630)).save(detail,format='PNG')
    return [PreviewImage('front_with_sponsor',full.getvalue(),front_preview.selected_logo,front_preview.selected_kit),
            PreviewImage('detail_with_sponsor',detail.getvalue(),front_preview.selected_logo,front_preview.selected_kit)]
