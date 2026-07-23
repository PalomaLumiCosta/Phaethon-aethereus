from pathlib import Path
from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from tratamento_phaethon import localizar_planilha,ler_planilha,tratar_eventos,construir_tabelas,indicadores
BASE_DIR=Path(__file__).resolve().parent
ASSETS_DIR=BASE_DIR/'assets'
st.set_page_config(
    page_title='Monitoramento anual de aves marinhas | Phaethon',
    page_icon='🐦',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown(
    '''
    <style>
    :root {
        --azul-topo: #12899A;
        --azul-fundo: #45A7CC;
        --azul-componente: #13889B;
        --azul-escuro: #0B6878;
        --texto-escuro: #14333D;
    }

    .stApp { background: var(--azul-fundo); }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .block-container {
        max-width: 1500px;
        padding-top: .4rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background: #299DBF;
        border-right: 1px solid rgba(255,255,255,.4);
    }
    [data-testid="stSidebar"] * { color: white; }

    h1, h2, h3, h4, p, label { color: white; }

    .titulo-painel {
        color: white;
        text-align: center;
        font-size: clamp(1.8rem,3vw,2.8rem);
        font-weight: 800;
        line-height: 1.15;
        margin: .6rem 0 .15rem;
        text-shadow: 0 2px 3px rgba(0,0,0,.2);
    }
    .subtitulo-painel {
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: var(--azul-componente);
        border-color: var(--texto-escuro);
        color: white;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] svg {
        color: white;
        fill: white;
    }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,.94);
        border-left: 6px solid var(--azul-escuro);
        border-radius: 10px;
        padding: .8rem 1rem;
        box-shadow: 0 3px 10px rgba(0,0,0,.14);
    }
    [data-testid="stMetricLabel"] *,
    [data-testid="stMetricValue"] *,
    [data-testid="stMetricDelta"] * {
        color: var(--texto-escuro) !important;
    }

    button[data-baseweb="tab"] {
        background: var(--azul-componente);
        border-radius: 8px 8px 0 0;
        margin-right: .15rem;
    }
    button[data-baseweb="tab"] p {
        color: white !important;
        font-weight: 700;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: var(--azul-escuro);
        border-bottom: 4px solid white;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        background: white;
        border-radius: 8px;
        overflow: hidden;
    }

    .stDownloadButton button {
        background: var(--azul-escuro);
        color: white;
        border: 1px solid white;
        border-radius: 8px;
        font-weight: 700;
    }

    hr { border-color: rgba(255,255,255,.4); }
    </style>
    ''',
    unsafe_allow_html=True
)

cabecalho=ASSETS_DIR/'cabecalho_institucional.png'
if cabecalho.exists():
    st.image(str(cabecalho),use_container_width=True)

st.markdown(
    '''
    <div class="titulo-painel">
      Monitoramento anual de aves marinhas<br>
      PARNA Abrolhos (<i>Phaethon aethereus</i>)
    </div>
    <div class="subtitulo-painel">
      Anilhamento, recuperações, trajetória individual e fidelidade ao ninho
    </div>
    ''',
    unsafe_allow_html=True
)

ilustracao=ASSETS_DIR/'phaethon_ilustracao.png'
if ilustracao.exists():
    st.sidebar.image(str(ilustracao),use_container_width=True)

st.sidebar.markdown(
    '''
    **CEMAVE / ICMBio**  
    Monitoramento de aves marinhas  

    **Espécie analisada**  
    *Phaethon aethereus*
    '''
)
@st.cache_data(show_spinner='Carregando e tratando dados...')
def carregar_local(c): return tratar_eventos(ler_planilha(Path(c)))
@st.cache_data(show_spinner='Tratando arquivo enviado...')
def carregar_upload(b): return tratar_eventos(ler_planilha(BytesIO(b)))
upload=st.sidebar.file_uploader('Enviar planilha Excel',type=['xlsx'])
try:
    df=carregar_upload(upload.getvalue()) if upload else carregar_local(str(localizar_planilha(BASE_DIR)))
except (FileNotFoundError,ValueError) as e:
    st.error(str(e)); st.info('Coloque a planilha na pasta dados/ ou envie pela barra lateral.'); st.stop()
anos=sorted(df['ano'].dropna().astype(int).unique()); eventos=sorted(df['evento'].dropna().unique()); ufs=sorted(df['uf'].dropna().unique())
fa=st.sidebar.slider('Intervalo de anos',min(anos),max(anos),(min(anos),max(anos))) if anos else None
fe=st.sidebar.multiselect('Tipo de evento',eventos,default=eventos); fu=st.sidebar.multiselect('UF',ufs,default=ufs)
dff=df.copy()
if fa: dff=dff[dff['ano'].between(*fa)]
if fe: dff=dff[dff['evento'].isin(fe)]
if fu: dff=dff[dff['uf'].isin(fu)]
t=construir_tabelas(df); tf=construir_tabelas(dff); k=indicadores(t)
abas=st.tabs(['Visão geral','Recuperações','Fidelidade ao ninho','Série temporal','Mapa','Dados e qualidade'])
with abas[0]:
    c=st.columns(4); c[0].metric('Anilhas colocadas',k['anilhas_colocadas']); c[1].metric('Anilhas recuperadas',k['anilhas_recuperadas']); c[2].metric('Colocadas e recuperadas',k['anilhas_colocadas_e_recuperadas']); c[3].metric('Taxa de recuperação',f"{k['taxa_recuperacao_percentual']:.1f}%")
    c=st.columns(4); c[0].metric('Eventos de colocação',k['eventos_colocacao']); c[1].metric('Eventos de recuperação',k['eventos_recuperacao']); c[2].metric('Recorrentes no mesmo ninho',k['anilhas_recorrentes_mesmo_ninho']); m=k['mediana_anos_ate_primeira_recuperacao']; c[3].metric('Mediana até 1ª recuperação','Sem dados' if pd.isna(m) else f'{m:.1f} anos')
    pe=dff['evento'].value_counts().rename_axis('evento').reset_index(name='numero_eventos'); st.plotly_chart(px.bar(pe,x='evento',y='numero_eventos',text_auto=True,title='Eventos por tipo'),use_container_width=True)
    loc=tf['locais'].head(20); fig=px.bar(loc,x='numero_eventos',y='localidade',color='evento',orientation='h',hover_data=['municipio','uf'],title='Principais localidades'); fig.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig,use_container_width=True)
with abas[1]:
    h=t['historico_recuperacoes']; hv=h[h['anos_desde_colocacao'].ge(0)]
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(px.histogram(hv,x='anos_desde_colocacao',nbins=30,title='Tempo entre colocação e recuperação'),use_container_width=True)
    with c2:
        vc=t['resumo_anilhas']['numero_recuperacoes'].value_counts().sort_index().rename_axis('numero_recuperacoes').reset_index(name='numero_anilhas'); vc=vc[vc['numero_recuperacoes'].gt(0)]; st.plotly_chart(px.bar(vc,x='numero_recuperacoes',y='numero_anilhas',title='Recuperações por anilha'),use_container_width=True)
    an=st.selectbox('Selecionar anilha',sorted(h['anilha'].dropna().unique())); st.dataframe(h[h['anilha'].eq(an)][['anilha','ordem_recuperacao','data_evento','anos_desde_colocacao','localidade','municipio','uf','numero_ninho']],use_container_width=True,hide_index=True)
with abas[2]:
    r=t['casos_recorrentes_mesmo_ninho']; m=t['mudancas_ninho']; c=st.columns(3); c[0].metric('Anilhas recorrentes no mesmo ninho',r['anilha'].nunique()); c[1].metric('Pares anilha–ninho recorrentes',len(r)); c[2].metric('Anilhas em mais de um ninho',len(m))
    if not r.empty:
        top=r.nlargest(25,'numero_recuperacoes_mesmo_ninho'); fig=px.bar(top,x='numero_recuperacoes_mesmo_ninho',y='anilha',color='id_ninho',orientation='h',hover_data=['primeira_recuperacao_ninho','ultima_recuperacao_ninho','dias_entre_primeira_ultima_no_ninho'],title='Maiores recorrências no mesmo ninho'); fig.update_layout(yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig,use_container_width=True); st.dataframe(r,use_container_width=True,hide_index=True)
with abas[3]:
    st.plotly_chart(px.line(tf['serie_temporal'],x='ano',y='numero_eventos',color='evento',markers=True,title='Eventos por ano'),use_container_width=True)
    mensal=dff.groupby(['ano_mes','evento']).size().rename('numero_eventos').reset_index(); st.plotly_chart(px.line(mensal,x='ano_mes',y='numero_eventos',color='evento',title='Eventos por mês'),use_container_width=True)
with abas[4]:
    mapa=dff.dropna(subset=['latitude','longitude'])
    if mapa.empty: st.info('Sem coordenadas válidas.')
    else: st.plotly_chart(px.scatter_map(mapa,lat='latitude',lon='longitude',color='evento',hover_name='anilha',hover_data=['data_evento','localidade','numero_ninho'],zoom=4,height=650,title='Locais dos eventos'),use_container_width=True)
with abas[5]:
    q=pd.DataFrame({'coluna':df.columns,'tipo':df.dtypes.astype(str).values,'ausentes':df.isna().sum().values,'percentual_ausente':(df.isna().mean().values*100).round(2),'valores_distintos':[df[c].nunique(dropna=True) for c in df.columns]}); st.dataframe(q,use_container_width=True,hide_index=True)
    st.write('Recuperações sem colocação registrada:',int(t['resumo_anilhas']['recuperacao_sem_colocacao_na_base'].sum())); st.write('Recuperações anteriores à colocação:',int(t['resumo_anilhas']['recuperacao_anterior_colocacao'].sum())); st.write('Combinações repetidas anilha–evento–data–ninho:',len(t['duplicatas_chave']))
    for nome,tabela in t.items(): st.download_button(f'Baixar {nome}.csv',tabela.to_csv(index=False).encode('utf-8-sig'),file_name=f'{nome}.csv',mime='text/csv',key=nome)
st.markdown('---')
st.markdown(
    '<div style="text-align:center;color:white;font-weight:600;">'
    'Dashboard científico | CEMAVE / ICMBio | '
    'Monitoramento de aves marinhas — PARNA Abrolhos'
    '</div>',
    unsafe_allow_html=True
)
