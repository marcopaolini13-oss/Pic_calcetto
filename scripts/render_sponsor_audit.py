"""Render a local contact sheet to inspect all six real jersey previews."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image,ImageDraw
from src.config import ROOT,CONCEPTS
from src.assets import image_paths,load_image

labels=['Cosφ 0.9','Perdite < 1%','MPPT & Chill','Fuori Computo','Variante in Corso','Da Verificare in Cantiere']
sheet=Image.new('RGB',(1080,800),'#f4f6f8')
for index,(concept,sponsor) in enumerate(zip([c for choices in CONCEPTS.values() for c in choices],labels)):
    picture=load_image(image_paths(concept,'kit',concept,'test-sponsor',sponsor)[0])
    picture.thumbnail((350,350))
    x=(index%3)*360;y=(index//3)*400
    sheet.paste(picture,(x,y+30))
    ImageDraw.Draw(sheet).text((x+10,y+10),concept,fill='black')
target=ROOT/'runtime'/'sponsor_audit.jpg'
target.parent.mkdir(exist_ok=True)
sheet.save(target,quality=95)
print('Saved runtime/sponsor_audit.jpg. Original assets unchanged.')
