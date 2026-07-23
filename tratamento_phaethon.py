from __future__ import annotations
from pathlib import Path
from typing import BinaryIO, Union
import re
import numpy as np
import pandas as pd

ESPECIE_ALVO = 'Phaethon aethereus'
ABA_PADRAO = 'TABELA_GERAL_RECAPTURAS'

COLUNAS = {
    'CÓDIGO ANILHA':'codigo_anilha','SEQ_ANILHA':'seq_anilha','SEQ_ANILHA.1':'seq_anilha_1',
    'RECUPERADA/COLOCADA':'evento','Espécie (Nome científico)':'especie_original',
    'DATA RECUPERAÇÃO':'data_evento','LOCALIDADE':'localidade','MUNICÍPIO':'municipio','UF':'uf',
    'NÚMERO NINHO':'numero_ninho','LATITUDE':'latitude','LONGITUDE':'longitude',
    'INSTRUMENTO DE CAPTURA':'instrumento_captura','ESTADO ATUAL DA AVE':'estado_ave',
    'ANILHA FOI RETIRADA?':'anilha_retirada','FORMA DE OBTENÇÃO':'forma_obtencao',
    'OBS':'observacao','RECUPERADOR':'recuperador','e-mail RECUPERADOR':'email_recuperador'
}
 # Preciso fazer a contagem de dados com NA no fluxo da analise.

def limpar_texto(v):
    if pd.isna(v): return pd.NA
    t=' '.join(str(v).strip().split())
    return t if t else pd.NA

def normalizar_especie(v):
    v=limpar_texto(v)
    return 'Não informada' if pd.isna(v) else str(v).lower().capitalize()

def padronizar_anilha(v):
    v=limpar_texto(v)
    return pd.NA if pd.isna(v) else re.sub(r'\s+','',str(v).upper())

def padronizar_ninho(v):
    v=limpar_texto(v)
    if pd.isna(v): return pd.NA
    t=str(v).upper()
    return t[:-2] if re.fullmatch(r'\d+\.0',t) else t

def localizar_planilha(base_dir: Path) -> Path:
    pasta=base_dir/'dados'
    encontrados=sorted(pasta.glob('*.xlsx'))
    if not encontrados:
        raise FileNotFoundError('Coloque a planilha .xlsx na pasta dados/.')
    return encontrados[0]

def ler_planilha(fonte: Union[str,Path,BinaryIO], aba: str=ABA_PADRAO) -> pd.DataFrame:
    try: return pd.read_excel(fonte,sheet_name=aba)
    except ValueError: return pd.read_excel(fonte,sheet_name=0)

def validar_colunas(df: pd.DataFrame) -> None:
    obrig=['CÓDIGO ANILHA','RECUPERADA/COLOCADA','Espécie (Nome científico)','DATA RECUPERAÇÃO','LOCALIDADE','MUNICÍPIO','UF','NÚMERO NINHO']
    falt=[c for c in obrig if c not in [str(x).strip() for x in df.columns]]
    if falt: raise ValueError('Colunas obrigatórias ausentes: '+', '.join(falt))

def tratar_eventos(df_original: pd.DataFrame, somente_especie_alvo: bool=True) -> pd.DataFrame:
    df=df_original.copy(); df.columns=[str(c).strip() for c in df.columns]; validar_colunas(df)

    df=df.rename(columns={str(k).strip():v for k,v in COLUNAS.items()})
    for c in ['codigo_anilha','seq_anilha','seq_anilha_1','evento','especie_original','localidade','municipio','uf','numero_ninho','estado_ave','forma_obtencao','instrumento_captura','anilha_retirada','observacao','recuperador','email_recuperador']:
        if c in df.columns: df[c]=df[c].map(limpar_texto)

    df['evento']=df['evento'].astype('string').str.upper().str.strip()

    df['especie']=df['especie_original'].map(normalizar_especie)

    df['data_evento']=pd.to_datetime(df['data_evento'],errors='coerce',dayfirst=True)
    # A identificação completa é SEQ_ANILHA.1 (ex.: P15197).
    # Quando ausente, concatena o código alfabético e a sequência numérica.
   
    df['anilha']=df['seq_anilha_1'].map(padronizar_anilha) if 'seq_anilha_1' in df.columns else pd.Series(pd.NA,index=df.index,dtype='string')
    if 'codigo_anilha' in df.columns and 'seq_anilha' in df.columns:
        composta=(df['codigo_anilha'].astype('string').fillna('')+df['seq_anilha'].astype('string').str.replace(r'\.0$','',regex=True).fillna('')).map(padronizar_anilha)
        df['anilha']=df['anilha'].fillna(composta)
    for c in ['localidade','municipio','uf']:
        df[c]=df[c].astype('string').str.upper().str.strip()

    df['ninho_padronizado']=df['numero_ninho'].map(padronizar_ninho)

    comps=['ninho_padronizado','localidade','municipio','uf']

    df['id_ninho']=df[comps].astype('string').fillna('NÃO INFORMADO').agg(' | '.join,axis=1)

    df.loc[df['ninho_padronizado'].isna(),'id_ninho']=pd.NA
    for c in ['latitude','longitude']:
        if c in df.columns: df[c]=pd.to_numeric(df[c].astype('string').str.replace(',','.',regex=False),errors='coerce')

    df['ano']=df['data_evento'].dt.year.astype('Int64'); df['mes']=df['data_evento'].dt.month.astype('Int64'); df['ano_mes']=df['data_evento'].dt.to_period('M').astype('string')
    if somente_especie_alvo: df=df[df['especie'].eq(ESPECIE_ALVO)].copy()
    return df.reset_index(drop=True)

def construir_tabelas(df_eventos: pd.DataFrame) -> dict[str,pd.DataFrame]:

    col=df_eventos[df_eventos['evento'].eq('COLOCADA')].copy(); rec=df_eventos[df_eventos['evento'].eq('RECUPERADA')].copy()

    primeira_col=(col.dropna(subset=['anilha','data_evento']).sort_values('data_evento').drop_duplicates('anilha')[[
        'anilha','data_evento','localidade','municipio','uf','id_ninho','latitude','longitude']].rename(columns={
        'data_evento':'data_colocacao','localidade':'localidade_colocacao','municipio':'municipio_colocacao','uf':'uf_colocacao','id_ninho':'ninho_colocacao','latitude':'latitude_colocacao','longitude':'longitude_colocacao'}))

    hist=rec.dropna(subset=['anilha']).sort_values(['anilha','data_evento']).merge(primeira_col,on='anilha',how='left')

    hist['dias_desde_colocacao']=(hist['data_evento']-hist['data_colocacao']).dt.days; hist['anos_desde_colocacao']=hist['dias_desde_colocacao']/365.25; hist['ordem_recuperacao']=hist.groupby('anilha').cumcount()+1

    primeira_rec=(hist.sort_values('data_evento').drop_duplicates('anilha')[[
        'anilha','data_evento','localidade','municipio','uf','id_ninho']].rename(columns={'data_evento':'primeira_recuperacao','localidade':'localidade_primeira_recuperacao','municipio':'municipio_primeira_recuperacao','uf':'uf_primeira_recuperacao','id_ninho':'ninho_primeira_recuperacao'}))

    ultima_rec=hist.sort_values('data_evento').drop_duplicates('anilha',keep='last')[['anilha','data_evento']].rename(columns={'data_evento':'ultima_recuperacao'})

    cont=rec.groupby('anilha').size().rename('numero_recuperacoes').reset_index()

    resumo=primeira_col.merge(primeira_rec,on='anilha',how='outer').merge(ultima_rec,on='anilha',how='outer').merge(cont,on='anilha',how='outer')

    resumo['numero_recuperacoes']=resumo['numero_recuperacoes'].fillna(0).astype(int); resumo['foi_recuperada']=resumo['numero_recuperacoes'].gt(0)

    resumo['dias_ate_primeira_recuperacao']=(resumo['primeira_recuperacao']-resumo['data_colocacao']).dt.days; resumo['anos_ate_primeira_recuperacao']=resumo['dias_ate_primeira_recuperacao']/365.25

    resumo['dias_entre_primeira_ultima_recuperacao']=(resumo['ultima_recuperacao']-resumo['primeira_recuperacao']).dt.days

    resumo['recuperacao_sem_colocacao_na_base']=resumo['primeira_recuperacao'].notna() & resumo['data_colocacao'].isna(); resumo['recuperacao_anterior_colocacao']=resumo['dias_ate_primeira_recuperacao'].lt(0)

    rn=rec.dropna(subset=['anilha','id_ninho','data_evento']).sort_values(['anilha','id_ninho','data_evento']).copy(); rn['dias_desde_recuperacao_anterior_mesmo_ninho']=rn.groupby(['anilha','id_ninho'])['data_evento'].diff().dt.days

    recorr=(rn.groupby(['anilha','id_ninho']).agg(numero_recuperacoes_mesmo_ninho=('data_evento','size'),numero_datas_distintas=('data_evento','nunique'),primeira_recuperacao_ninho=('data_evento','min'),ultima_recuperacao_ninho=('data_evento','max'),localidade=('localidade','first'),municipio=('municipio','first'),uf=('uf','first'),latitude=('latitude','median'),longitude=('longitude','median')).reset_index())

    recorr['dias_entre_primeira_ultima_no_ninho']=(recorr['ultima_recuperacao_ninho']-recorr['primeira_recuperacao_ninho']).dt.days; recorr['recorrente_mesmo_ninho']=recorr['numero_recuperacoes_mesmo_ninho'].ge(2)

    ninhos=rn.groupby('anilha').agg(numero_ninhos_distintos=('id_ninho','nunique'),numero_recuperacoes_com_ninho=('id_ninho','size')).reset_index(); ninhos['mudou_de_ninho']=ninhos['numero_ninhos_distintos'].gt(1)

    serie=df_eventos.dropna(subset=['ano']).groupby(['ano','evento']).size().rename('numero_eventos').reset_index()

    locais=df_eventos.groupby(['evento','localidade','municipio','uf'],dropna=False).size().rename('numero_eventos').reset_index().sort_values('numero_eventos',ascending=False)

    dup=df_eventos.groupby(['anilha','evento','data_evento','id_ninho'],dropna=False).size().rename('numero_registros').reset_index(); dup=dup[dup['numero_registros'].gt(1)]

    return {'eventos_tratados':df_eventos,'colocacoes':col,'recuperacoes':rec,'historico_recuperacoes':hist,'resumo_anilhas':resumo,'recorrencia_ninhos':recorr,'casos_recorrentes_mesmo_ninho':recorr[recorr['recorrente_mesmo_ninho']].copy(),'resumo_ninhos_por_anilha':ninhos,'mudancas_ninho':ninhos[ninhos['mudou_de_ninho']].copy(),'serie_temporal':serie,'locais':locais,'duplicatas_chave':dup}

def indicadores(t: dict[str,pd.DataFrame]) -> dict[str,float]:
    col=t['colocacoes']; rec=t['recuperacoes']; resumo=t['resumo_anilhas']; recorr=t['casos_recorrentes_mesmo_ninho']

    a=set(col['anilha'].dropna()); b=set(rec['anilha'].dropna()); c=a & b

    return {'eventos_totais':len(t['eventos_tratados']),'eventos_colocacao':len(col),'eventos_recuperacao':len(rec),'anilhas_distintas':t['eventos_tratados']['anilha'].nunique(),'anilhas_colocadas':len(a),'anilhas_recuperadas':len(b),'anilhas_colocadas_e_recuperadas':len(c),'taxa_recuperacao_percentual':len(c)/len(a)*100 if a else np.nan,'anilhas_recorrentes_mesmo_ninho':recorr['anilha'].nunique(),'pares_anilha_ninho_recorrentes':len(recorr),'anilhas_em_multiplos_ninhos':len(t['mudancas_ninho']),'mediana_anos_ate_primeira_recuperacao':resumo.loc[resumo['anos_ate_primeira_recuperacao'].ge(0),'anos_ate_primeira_recuperacao'].median()}
