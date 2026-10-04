"""Read-only inventory; writes inspection reports beneath runtime/assets_audit."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json
from PIL import Image, ImageDraw
import io
import hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runtime'/'assets_audit'
OUT.mkdir(parents=True,exist_ok=True)
extensions={'.jpg','.jpeg','.png','.webp','.avif','.gif','.svg'}
inventory=[]
for base in [ROOT/'assets'/'logos'/'2. LOGHI',ROOT/'assets'/'kits'/'1. MAGLIETTE']:
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.suffix.lower() in extensions:
            item={'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            try:
                with Image.open(p) as im: item['size']=list(im.size)
            except Exception: pass
            inventory.append(item)
(OUT/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
doc=ROOT/'assets'/'kits'/'1. MAGLIETTE'/'MAGLIETTE_2026.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with ZipFile(doc) as z:
    rel={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
    context=''
    mapping=[]
    for p in ET.fromstring(z.read('word/document.xml')).findall('.//w:p',ns):
        text=''.join(t.text or '' for t in p.findall('.//w:t',ns))
        if text: context=text
        for b in p.findall('.//a:blip',ns):
            target=rel.get(b.attrib.get('{'+ns['r']+'}embed'))
            if target:
                data=z.read('word/'+target)
                output=OUT/Path(target).name
                output.write_bytes(data)
                mapping.append({'context':context,'image':output.name,'source':target})
    sheet=Image.new('RGB',(1000,300*((len(mapping)+3)//4)),'white')
    draw=ImageDraw.Draw(sheet)
    for i,item in enumerate(mapping):
        im=Image.open(OUT/item['image']).convert('RGB'); im.thumbnail((240,250))
        x=(i%4)*250;y=(i//4)*300
        sheet.paste(im,(x+(250-im.width)//2,y))
        draw.text((x+5,y+255),item['image'],fill='black')
        draw.text((x+5,y+275),item['context'],fill='black')
    sheet.save(OUT/'document_contact.jpg')
    print(json.dumps(mapping,ensure_ascii=False,indent=2))
print('Inventory',len(inventory),'images; see runtime/assets_audit/inventory.json')
groups={}
for item in inventory:
    p=ROOT/item['path']
    if p.suffix.lower()=='.jpg' and p.name not in ('Macron_4_the_planet_Packaging_2_1.jpg','Macron_4_the_planet_Packaging_2_2.jpg','charon_eco.jpg') and '(1)' not in p.name:
        groups.setdefault(p.parent.name,[]).append(p)
for group,files in groups.items():
    sheet=Image.new('RGB',(1000,220*((len(files)+4)//5)),'#eeeeee'); draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(files):
        im=Image.open(p).convert('RGB'); im.thumbnail((195,180))
        x=i%5*200;y=i//5*220
        sheet.paste(im,(x+(200-im.width)//2,y))
        draw.text((x+3,y+182),p.name[-27:],fill='black')
    sheet.save(OUT/(group+'.jpg'))
