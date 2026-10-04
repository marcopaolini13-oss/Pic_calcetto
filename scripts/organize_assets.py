"""Copy identified assets without changing originals; unresolved kits stay unassigned."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
GROUPS={
 'energetici_fc':('EN 1','51720102'),
 'renewables':('EN 2','800002850201'),
 'energentus':('EN 3','46130109'),
 'rdm_fc':('RDM 1','51720710'),
 'rdm_world':('RDM 2','800002850301'),
 'rdm_internazionale':('RDM 3','46130309'),
}
LOGOS={'energetici_fc':'ENERGETICI FC.jpeg','renewables':'RENEWABLES.jpeg',
 'energentus':'ENERGENTUS.png','rdm_fc':'RDM FC.jpeg','rdm_world':'RDM WORLD.jpeg','rdm_internazionale':'RDM INTER.jpeg'}
SUFFIXES={'':'three_quarter','_1':'three_quarter','_2':'three_quarter',
 '_02':'back','_02_1':'back','_02_2':'back','_03':'detail','_03_1':'detail','_03_2':'detail',
 '_04':'detail_02','_04_1':'detail_02','_04_2':'detail_02','_05':'detail_03','_05_1':'detail_03','_05_2':'detail_03',
 '_10':'front','_10_1':'front','_10_2':'front','_11':'back_02','_11_1':'back_02','_11_2':'back_02'}
ORDER={'front':0,'back':1,'three_quarter':2,'detail':3,'detail_02':4,'detail_03':5,'back_02':6}

def copy(source,destination):
 destination.parent.mkdir(parents=True,exist_ok=True)
 if not destination.exists() or destination.read_bytes()!=source.read_bytes(): shutil.copy2(source,destination)
 with Image.open(source) as im: width,height=im.size
 return {'path':destination.relative_to(ROOT).as_posix(),'source':source.relative_to(ROOT).as_posix(),
         'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'width':width,'height':height,'bytes':source.stat().st_size}

def quality(path):
 with Image.open(path) as im:
  return (min(im.size)>=500,im.width*im.height,min(im.size),path.stat().st_size)

if __name__=='__main__':
 manifest={'logos':{},'kits':{}}
 for concept,filename in LOGOS.items():
  source=ROOT/'assets'/'logos'/'2. LOGHI'/filename
  manifest['logos'][concept]=copy(source,ROOT/'assets'/'logos'/concept/('logo'+source.suffix))
 for group,(folder,code) in GROUPS.items():
  found={}
  for source in sorted((ROOT/'assets'/'kits'/'1. MAGLIETTE'/folder).rglob('*.jpg')):
   stem=re.sub(r'\(\d+\)$','',source.stem)
   match=re.search(re.escape(code)+r'((?:_\d+)*)$',stem)
   if match and match[1] in SUFFIXES and (not group in ('energetici_fc','rdm_fc') or match[1].endswith('_2')):
    kind=SUFFIXES[match[1]]
    if quality(source)[0] and (kind not in found or quality(source)>quality(found[kind])): found[kind]=source
  manifest['kits'][group]=[{'type':kind,**copy(source,ROOT/'assets'/'kits'/group/(kind+'.jpg'))}
                           for kind,source in sorted(found.items(),key=lambda item:ORDER[item[0]])]
  if not found: raise RuntimeError('No product photographs for '+group)
 (ROOT/'assets'/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
 # Inventory every original image with its role, including saved-page accessories.
 sources={r['source'] for r in manifest['logos'].values()}
 sources.update(v['source'] for views in manifest['kits'].values() for v in views)
 used_hashes={r['sha256'] for r in manifest['logos'].values()}
 used_hashes.update(v['sha256'] for views in manifest['kits'].values() for v in views)
 inventory=[]
 for base in [ROOT/'assets'/'logos'/'2. LOGHI',ROOT/'assets'/'kits'/'1. MAGLIETTE']:
  for p in sorted(base.rglob('*')):
   if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.avif','.gif','.svg'}:
    relative=p.relative_to(ROOT).as_posix()
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    reason='used' if relative in sources else 'duplicate' if digest in used_hashes else 'accessory' if (
      p.suffix.lower()=='.svg' or p.name.startswith(('Macron_','icone-','charon_eco'))) else 'alternate_color_or_resolution'
    width=height=None
    try:
     with Image.open(p) as im: width,height=im.size
    except OSError: pass
    inventory.append({'path':relative,'filename':p.name,'sha256':digest,'status':reason,
                      'width':width,'height':height,'bytes':p.stat().st_size})
 (ROOT/'assets'/'inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf-8')
 print('Copied 6 logos and',sum(len(v) for v in manifest['kits'].values()),'views across 6 kit groups.')
 rows=['# Asset effettivamente caricati dalla web app','',
       'File relativi alla cartella del progetto. Tutte le fotografie sono originali, senza upscale.',
       '', '| Concept | Vista | File utilizzato | Dimensione px |','|---|---|---|---|']
 for concept,views in manifest['kits'].items():
  for view in views:
   rows.append(f"| {concept} | {view['type']} | `{view['path']}` | {view['width']}×{view['height']} |")
  logo=manifest['logos'][concept]
  rows.append(f"| {concept} | logo | `{logo['path']}` | {logo['width']}×{logo['height']} |")
 rows+=['','Nessuna proposta è priva di fotografie ad alta risoluzione. Frontale disponibile per tutte e sei.',
        'Gli originali e le thumbnail restano nelle cartelle sorgente. Le copie finali delle maglie sono tutte 1000×1000 px.']
 (ROOT/'ASSET_RESOLUTIONS.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
