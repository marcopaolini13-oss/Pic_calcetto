"""Deterministic overlays of the supplied logos; no generated jersey pixels."""
from pathlib import Path
from collections import deque
import json
import hashlib
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
PLACEMENTS={
 'energetici_fc':(638,235,72,86), 'renewables':(640,227,70,84),
 'energentus':(634,216,64,94), 'rdm_fc':(638,228,68,86),
 'rdm_world':(640,227,68,84), 'rdm_internazionale':(634,214,72,72),
}

def cutout(original):
 """Remove only edge-connected neutral background; preserve interior white."""
 rgba=original.convert('RGBA')
 width,height=rgba.size
 rgb=rgba.load()
 visited=bytearray(width*height)
 queue=deque()
 def background(x,y):
  r,g,b,a=rgb[x,y]
  return a==0 or (min(r,g,b)>=210 and max(r,g,b)-min(r,g,b)<=25)
 def visit(x,y):
  index=y*width+x
  if not visited[index] and background(x,y):
   visited[index]=1
   queue.append((x,y))
 for x in range(width): visit(x,0);visit(x,height-1)
 for y in range(height): visit(0,y);visit(width-1,y)
 while queue:
  x,y=queue.popleft()
  if x: visit(x-1,y)
  if x+1<width: visit(x+1,y)
  if y: visit(x,y-1)
  if y+1<height: visit(x,y+1)
 alpha=rgba.getchannel('A')
 pixels=alpha.load()
 for y in range(height):
  for x in range(width):
   if visited[y*width+x]: pixels[x,y]=0
 rgba.putalpha(alpha)
 bounds=alpha.getbbox()
 if not bounds: raise ValueError('Empty crest after removing exterior background')
 return rgba.crop(bounds)

if __name__=='__main__':
 source=json.loads((ROOT/'assets'/'manifest.json').read_text(encoding='utf-8'))
 records={}
 for concept,(cx,cy,max_width,max_height) in PLACEMENTS.items():
  front_path=ROOT/'assets'/'kits'/concept/'front.jpg'
  logo_path=ROOT/source['logos'][concept]['path']
  with Image.open(front_path) as im: base=im.convert('RGB')
  with Image.open(logo_path) as im: crest=cutout(im)
  crest.thumbnail((max_width,max_height),Image.Resampling.LANCZOS)
  # A restrained sewn-patch rim; the crest itself is never stretched or blurred.
  edge=crest.getchannel('A').filter(ImageFilter.MaxFilter(3))
  patch=Image.new('RGBA',crest.size,(245,245,245,255));patch.putalpha(edge)
  patch.alpha_composite(crest)
  x,y=cx-crest.width//2,cy-crest.height//2
  composite=base.copy()
  composite.paste(patch,(x,y),patch)
  out=ROOT/'assets'/'mockups'/concept
  out.mkdir(parents=True,exist_ok=True)
  full=out/'front_with_crest.png'
  detail=out/'detail_with_crest.png'
  composite.save(full)
  # Native 560px crop: no resize, no upscale, no invented garment area.
  crop=(380,50,940,610)
  composite.crop(crop).save(detail)
  records[concept]={'front':full.relative_to(ROOT).as_posix(),
   'detail':detail.relative_to(ROOT).as_posix(),'source':front_path.relative_to(ROOT).as_posix(),
   'logo':logo_path.relative_to(ROOT).as_posix(),'crest_box':[x,y,x+crest.width,y+crest.height],
   'detail_crop':list(crop),'width':base.width,'height':base.height,
   'source_sha256':hashlib.sha256(front_path.read_bytes()).hexdigest(),
   'logo_sha256':hashlib.sha256(logo_path.read_bytes()).hexdigest()}
 (ROOT/'assets'/'crest_previews.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 lines=['# Preview con stemma','',
  'Composizione degli asset originali, senza rigenerazione della maglia. Frontale 1000×1000 e dettaglio nativo 560×560.',
  'Le viste detail originali mostrano il petto destro: il nuovo dettaglio è un ritaglio del frontale sul lato cuore.',
  '', '| Concept | File maglia principale | File detail con stemma | Logo usato |','|---|---|---|---|']
 for concept,r in records.items(): lines.append(f"| {concept} | `{r['front']}` | `{r['detail']}` | `{r['logo']}` |")
 (ROOT/'CREST_PREVIEWS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('Saved six 1000x1000 front previews and six native 560x560 details.')
