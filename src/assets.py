"""Central asset catalog, independent of voting and database code."""
from pathlib import Path
import json
import logging
from io import BytesIO
from functools import lru_cache
from PIL import Image, ImageOps, UnidentifiedImageError
from src.config import ROOT

LOG=logging.getLogger(__name__)
EXTENSIONS={'.jpg','.jpeg','.png','.webp','.avif'}
VIEW_LABELS={'front_with_sponsor':'Frontale · logo e sponsor','detail_with_sponsor':'Dettaglio · logo e sponsor',
 'front':'Frontale','back':'Retro','three_quarter':'Vista 3/4','detail':'Dettaglio',
 'detail_02':'Dettaglio 2','detail_03':'Dettaglio 3','back_02':'Retro · altra vista',
 'detail_with_crest':'Dettaglio · stemma applicato','front_with_crest':'Frontale · stemma applicato'}
# Numbered source folders follow the six proposals in the user-specified order.
KIT_ASSIGNMENTS={c:c for c in ('energetici_fc','renewables','energentus','rdm_fc','rdm_world','rdm_internazionale')}

@lru_cache(maxsize=4)
def _manifest(path,stamp):
 return json.loads(Path(path).read_text(encoding='utf-8'))

def manifest():
 try:
  path=ROOT/'assets'/'manifest.json'
  return _manifest(str(path),path.stat().st_mtime_ns)
 except (OSError,ValueError):
  LOG.warning('Asset manifest missing or invalid: %s',ROOT/'assets'/'manifest.json')
  return {'logos':{},'kits':{}}

def configured_assets():
 data=manifest()
 return {concept:{'logo':ROOT/record['path'],
  'kit_images':[{'type':view['type'],'path':ROOT/view['path']}
   for view in data['kits'].get(KIT_ASSIGNMENTS.get(concept),[])]}
  for concept,record in data['logos'].items()}

def image_paths(concept,kind='logo',name=None,sponsor=None,sponsor_label=None):
 configured=configured_assets().get(concept,{})
 if kind=='logo':
  expected=configured.get('logo',ROOT/'assets'/'logos'/concept/'logo.jpeg')
  candidates=[expected]+[ROOT/'assets'/'logos'/(concept+ext) for ext in ('.jpeg','.jpg','.png')]
  files=[p for p in candidates if p.is_file()]
  if not files: LOG.warning('Logo missing: %s',expected)
  return files[:1]
 # A selected name is also the selected crest. Never show a generic kit crest
 # when a different logo was chosen in Step 1.
 if name in KIT_ASSIGNMENTS:
  from src.kit_preview import preview,with_sponsor
  logos=image_paths(name,'logo')
  priority={view:i for i,view in enumerate(VIEW_LABELS)}
  original=sorted((p for p in (ROOT/'assets'/'kits'/concept).glob('*') if p.suffix.lower() in EXTENSIONS and p.is_file()),key=lambda p:(priority.get(p.stem,99),p.name))
  if sponsor:
   directory=ROOT/'assets'/'mockups'/concept/f'{name}__{sponsor}'
   specific=sorted(p for p in directory.glob('*') if p.suffix.lower() in EXTENSIONS and p.is_file())
   if specific: return specific+original
  try:
   if not logos: raise OSError('Selected logo missing')
   rendered=preview(name,concept,logos[0])
   if sponsor_label:
    rendered=with_sponsor(rendered[0],sponsor_label)
   return rendered+original
  except (OSError,ValueError):
   LOG.warning('Dynamic preview unavailable: logo=%s kit=%s',name,concept)
   return original
 directories=[]
 if name and sponsor: directories.append(ROOT/'assets'/'mockups'/concept/f'{name}__{sponsor}')
 directories.append(ROOT/'assets'/'mockups'/concept)
 previews=[]
 for directory in directories:
  files=sorted((p for p in directory.glob('*') if p.suffix.lower() in EXTENSIONS and p.is_file()),
               key=lambda p:(0 if p.stem=='detail_with_crest' else 1 if p.stem=='front_with_crest' else 2,p.name))
  if files:
   previews=files
   break
 expected=[v['path'] for v in configured.get('kit_images',[])]
 for p in expected:
  if not p.is_file(): LOG.warning('Kit view missing: %s',p)
 priority={view:i for i,view in enumerate(VIEW_LABELS)}
 direct=sorted((p for p in (ROOT/'assets'/'kits'/concept).glob('*') if p.suffix.lower() in EXTENSIONS and p.is_file()),key=lambda p:(priority.get(p.stem,99),p.name))
 if direct: return previews+direct
 files=[p for p in expected if p.is_file()]
 if not files: LOG.warning('Kit missing or association pending: %s (directory %s)',concept,ROOT/'assets'/'kits'/concept)
 return previews+files

@lru_cache(maxsize=64)
def _decoded(token,content):
 with Image.open(BytesIO(content)) as original:
  rgba=ImageOps.exif_transpose(original).convert('RGBA')
  background=Image.new('RGBA',rgba.size,'#f4f6f8')
  background.alpha_composite(rgba)
  return background.convert('RGB')

@lru_cache(maxsize=128)
def file_bytes(path,stamp,size):
 return Path(path).read_bytes()

def load_image(path):
 try:
  if hasattr(path,'data'):
   return _decoded(None,path.data).copy()
  p=Path(path);info=p.stat()
  return _decoded((str(p),info.st_mtime_ns,info.st_size),file_bytes(str(p),info.st_mtime_ns,info.st_size)).copy()
 except (OSError,ValueError,UnidentifiedImageError):
  LOG.warning('Image missing or unreadable: %s',path)
  return None

def view_label(path):
 stem=path.stem if hasattr(path,'stem') else Path(path).stem
 return VIEW_LABELS.get(stem,stem.replace('_',' ').capitalize())
