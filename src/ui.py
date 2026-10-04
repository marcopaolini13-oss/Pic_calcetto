import hashlib
import base64
import io
from PIL import Image
import streamlit as st
from src.utils import images, placeholder
from src.assets import load_image, view_label

def style():
    st.markdown('''<style>
    .block-container {max-width:1200px;padding-top:2rem}
    h1,h2,h3 {letter-spacing:-.03em}
    div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:18px;box-shadow:0 8px 28px #0002}
    .stButton button {border-radius:12px;min-height:48px;transition:transform .15s}
    .stButton button:hover {transform:translateY(-2px)}
    div[data-testid="stImage"] img {border-radius:12px;object-fit:contain;background:#f4f6f8}
    div[class*="st-key-asset_card_"] {border:2px solid transparent;border-radius:18px}
    div[class*="st-key-asset_card_"] {padding:8px;background:#18263b}
    div[class*="st-key-asset_card_selected_ENERGETICI"] {border-color:#e53b49;box-shadow:0 0 0 2px #e53b4933}
    div[class*="st-key-asset_card_selected_RDM"] {border-color:#38a9e6;box-shadow:0 0 0 2px #38a9e633}
    div[class*="st-key-asset_main_"] img {height:auto!important;max-height:380px;max-width:100%;object-fit:contain}
    div[class*="st-key-asset_main_"] div[data-testid="stImage"] {margin-left:auto;margin-right:auto}
    div[class*="st-key-asset_thumbs_"] button img {height:72px!important;max-height:72px!important;width:100%;object-fit:contain;display:block}
    div[class*="st-key-asset_thumbs_"] button p {white-space:normal;width:100%;font-size:.8rem}
    div[class*="st-key-asset_thumbs_"] button {padding:6px;min-height:108px}
    div[role="dialog"] div[data-testid="stImage"] img {height:auto!important;max-height:70vh;max-width:100%;object-fit:contain}
    @media(max-width:900px) {
      .block-container{padding:1rem} h1{font-size:2rem}
      div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] div[class*="st-key-asset_card_"]) {flex-direction:column}
      div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] div[class*="st-key-asset_card_"]) > div[data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important}
      div[class*="st-key-asset_thumbs_"] div[data-testid="stHorizontalBlock"] {flex-wrap:nowrap}
      div[class*="st-key-asset_thumbs_"] div[data-testid="stColumn"] {min-width:0;flex:1 1 0;width:auto}
      div[class*="st-key-asset_main_"] img {max-height:340px}
    }
    </style>''', unsafe_allow_html=True)

def select_view(key,index):
    st.session_state[key]=index

def display_picture(picture,max_width=380,max_height=380):
    # Preserve source assets and aspect ratio; never upscale the display copy.
    width,height=picture.size
    scale=min(1,max_width/width,max_height/height)
    # Send a sharp 2x display image, not a full-resolution PNG on every click.
    buffer=optimized_image(picture.tobytes(),picture.size,max_width*2,max_height*2)
    st.image(buffer,width=max(1,int(width*scale)))

@st.cache_data(max_entries=128,show_spinner=False)
def optimized_image(rgb,size,max_width,max_height):
    picture=Image.frombytes('RGB',size,rgb)
    picture.thumbnail((max_width,max_height),Image.Resampling.LANCZOS)
    output=io.BytesIO()
    picture.save(output,format='JPEG',quality=92)
    return output.getvalue()

def thumbnail_label(picture,label):
    return _thumbnail_label(picture.tobytes(),picture.size,label)

@st.cache_data(max_entries=128,show_spinner=False)
def _thumbnail_label(rgb,size,label):
    picture=Image.frombytes('RGB',size,rgb)
    small=picture.copy()
    small.thumbnail((160,160))
    output=io.BytesIO()
    small.save(output,format='PNG')
    url='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode()
    return f'![{label}]({url})  \n{label}'

def close_lightbox():
    st.session_state.pop('asset_open_lightbox',None)

def open_lightbox(scope,index):
    st.session_state.asset_open_lightbox=(scope,index)
    # Opening again must start from the currently selected thumbnail.
    st.session_state.pop('asset_dialog_view_'+scope,None)

@st.dialog('Anteprima immagine',width='large',on_dismiss=close_lightbox)
def lightbox(files,label,index,team,kit,scope):
    st.subheader(label)
    if len(files)>1:
        index=st.selectbox('Vista',list(range(len(files))),index=index,
            format_func=lambda i:view_label(files[i]),key='asset_dialog_view_'+scope)
    picture=load_image(files[index]) if files else None
    display_picture(picture if picture is not None else placeholder(label,team,kit),800,680)
    if st.button('Chiudi',key='asset_dialog_close',width='stretch'):
        close_lightbox()
        st.rerun()

def show_image(concept, label, team, kind='logo', name=None, sponsor=None, gallery=False,sponsor_label=None):
    files=images(concept,kind,name,sponsor,sponsor_label)
    scope=hashlib.sha1(f'{concept}|{kind}|{name}|{sponsor}|{sponsor_label}|{files}'.encode()).hexdigest()[:12]
    state_key='gallery_view_'+scope
    index=st.session_state.get(state_key,0)
    if not isinstance(index,int) or not 0<=index<len(files): index=0
    picture=load_image(files[index]) if files else None
    with st.container(key='asset_main_'+scope):
        display_picture(picture if picture is not None else placeholder(label,team,kind=='kit'))
    if picture is None:
        st.caption('Immagine in preparazione · non disponibile')
    elif gallery:
        st.caption(view_label(files[index]))
    if gallery and len(files)>1:
        with st.container(key='asset_thumbs_'+scope):
            for start in range(0,len(files),3):
                for col,i in zip(st.columns(min(3,len(files)-start)),range(start,min(start+3,len(files)))):
                    with col:
                        thumb=load_image(files[i])
                        content=thumbnail_label(thumb if thumb is not None else placeholder(label,team,True),view_label(files[i]))
                        st.button(content,key=f'asset_thumb_{scope}_{i}',help='Mostra '+view_label(files[i]),
                            type='primary' if i==index else 'secondary',width='stretch',
                            on_click=select_view,args=(state_key,i))
    st.button('🔍 Ingrandisci',key='asset_zoom_'+scope,width='stretch',disabled=picture is None,
              on_click=open_lightbox,args=(scope,index))
    opened=st.session_state.get('asset_open_lightbox')
    if opened and opened[0]==scope:
        lightbox(files,label,opened[1],team,kind=='kit',scope)

def cards(options, choice_key, team, kind=None, name=None, sponsor=None,sponsor_label=None):
    cols = st.columns(len(options))
    for col, (value,label) in zip(cols,options.items()):
        selected = st.session_state.get(choice_key) == value
        with col, st.container(border=True,key=f'asset_card_{"selected" if selected else "idle"}_{team}_{choice_key}_{value}'):
            st.subheader(('✓ ' if selected else '') + label)
            if kind:
                show_image(value,label,team,kind,name,sponsor,kind=='kit',sponsor_label)
            action='Scegli questa proposta' if choice_key=='vote_name' else 'Scegli questa maglia' if choice_key=='vote_kit' else 'Scegli'
            st.button('Selezionato ✓' if selected else action, key=choice_key+'_'+value,
                      type='primary' if selected else 'secondary', width='stretch',
                      on_click=choose_option,args=(choice_key,value))

def choose_option(key,value):
    st.session_state[key]=value
    st.session_state.vote_confirm=False
