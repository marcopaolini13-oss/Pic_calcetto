from pathlib import Path
from PIL import Image
import json
import re
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1]
records=[]
for directory in [ROOT/'assets'/'kits'/'1. MAGLIETTE',ROOT/'assets'/'logos']:
 for p in sorted(directory.rglob('*')):
  if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.avif','.gif','.svg'}:
   item={'path':p.relative_to(ROOT).as_posix(),'filename':p.name,'bytes':p.stat().st_size,'width':None,'height':None}
   try:
    with Image.open(p) as im: item.update(width=im.width,height=im.height)
   except OSError:
    if p.suffix.lower()=='.svg':
     try:
      svg=ElementTree.parse(p).getroot()
      bounds=svg.attrib.get('viewBox','').split()
      for key,i in [('width',2),('height',3)]:
       value=svg.attrib.get(key,'')
       if re.fullmatch(r'\d+(?:\.\d+)?(?:px)?',value): item[key]=float(value.removesuffix('px'))
       elif len(bounds)==4: item[key]=float(bounds[i])
      item['dimension_note']='SVG intrinsic dimensions/viewBox; vector, not raster pixels'
     except (ValueError,ElementTree.ParseError): pass
   records.append(item)
(ROOT/'assets'/'resolution_inventory.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
for folder in ['EN 1','EN 2','EN 3','RDM 1','RDM 2','RDM 3']:
 print('\n'+folder)
 for r in records:
  if '/'+folder+'/' in r['path'] and r['width'] and r['filename'].endswith('.jpg') and not r['filename'].startswith(('Macron','charon_eco')):
   print(r['filename'],str(r['width'])+'x'+str(r['height']),r['bytes'])
print('\nLOGOS')
for r in records:
 if '/logos/' in r['path']: print(r['path'],r['width'],r['height'],r['bytes'])
