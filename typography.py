"""Bundled Comic Neue fonts for the web page, Plotly, Matplotlib and SVG images."""
from pathlib import Path
from functools import lru_cache
import base64

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def configure_fonts():
    from matplotlib import font_manager, rcParams
    import plotly.io as pio
    for name in ('Regular', 'Bold', 'Italic', 'BoldItalic'):
        font_manager.fontManager.addfont(str(ROOT / f'ComicNeue-{name}.ttf'))
    # Comic Neue omits some symbols (for example the match-minute prime).
    rcParams['font.family'] = ['Comic Neue', 'DejaVu Sans']
    # Cover charts with an explicit built-in template as well as default charts.
    for name in list(pio.templates):
        pio.templates[name].layout.font.family = 'Comic Neue, sans-serif'
        pio.templates[name].layout.hoverlabel.font.family = 'Comic Neue, sans-serif'


@lru_cache(maxsize=1)
def font_faces():
    rules = []
    for name, weight, style in [('Regular', 400, 'normal'), ('Bold', 700, 'normal'),
                                ('Italic', 400, 'italic'), ('BoldItalic', 700, 'italic')]:
        encoded = base64.b64encode((ROOT / f'ComicNeue-{name}.ttf').read_bytes()).decode('ascii')
        rules.append("@font-face{font-family:'Comic Neue';src:url(data:font/ttf;base64," + encoded +
                     ") format('truetype');font-weight:" + str(weight) + ";font-style:" + style + ";font-display:block;}")
    return ''.join(rules)


def page_font_css():
    # Target text without overriding Streamlit's Material Symbols icon font.
    return '<style>' + font_faces() + """
    .stApp,[data-testid="stDataFrame"] {
        --gdg-font-family:'Comic Neue',sans-serif;
        --gdg-header-font-family:'Comic Neue',sans-serif;
        --gdg-editor-font-family:'Comic Neue',sans-serif;
    }
    html,body,.stApp,.stAppViewContainer,[data-testid="stSidebar"],
    .stApp p,.stApp label,.stApp input,.stApp button,.stApp textarea,
    .stApp select,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6,
    .stApp table,.stApp th,.stApp td,.stApp a,.stApp strong,.stApp small,
    .stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricLabel"],.stApp [data-baseweb="select"],
    .stApp [data-baseweb="select"] *,[data-baseweb="popover"],[data-baseweb="popover"] * {
        font-family:'Comic Neue',sans-serif!important;
    }
    </style>"""


def embed_svg_font(svg):
    """SVG image data URLs cannot inherit a font from the surrounding page."""
    if '<text' not in svg:
        return svg
    end = svg.index('>') + 1
    return svg[:end] + '<style>' + font_faces() + '</style>' + svg[end:]
