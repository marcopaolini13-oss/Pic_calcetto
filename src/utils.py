import csv
import io
from PIL import Image, ImageDraw
from src.assets import image_paths

def images(concept, kind='logo', name=None, sponsor=None):
    return image_paths(concept,kind,name,sponsor)

def placeholder(label, team, kit=False):
    img = Image.new('RGB', (640, 480), '#18263b')
    draw = ImageDraw.Draw(img)
    color = '#e53b49' if team == 'ENERGETICI' else '#38a9e6'
    if kit:
        draw.polygon([(200,100),(260,70),(380,70),(440,100),(510,180),(440,230),(410,180),(410,400),(230,400),(230,180),(200,230),(130,180)], fill=color)
    else:
        draw.polygon([(200,80),(440,80),(440,250),(320,380),(200,250)], fill=color)
    draw.text((20,440), 'PLACEHOLDER - ' + label, fill='white')
    return img

def csv_bytes(rows):
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "'" + v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for k,v in row.items()})
    return output.getvalue().encode('utf-8-sig')
