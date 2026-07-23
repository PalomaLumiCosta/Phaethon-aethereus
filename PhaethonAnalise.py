from pathlib import Path
import json
import pandas as pd
from tratamento_phaethon import localizar_planilha,ler_planilha,tratar_eventos,construir_tabelas,indicadores
BASE_DIR=Path(__file__).resolve().parent; SAIDA=BASE_DIR/'resultados'
def main():
    SAIDA.mkdir(exist_ok=True); arq=localizar_planilha(BASE_DIR); print('Lendo:',arq)
    tabelas=construir_tabelas(tratar_eventos(ler_planilha(arq)))
    for nome,df in tabelas.items():
        caminho=SAIDA/f'{nome}.csv'; df.to_csv(caminho,index=False,encoding='utf-8-sig'); print('Salvo:',caminho.name,len(df))
    k=indicadores(tabelas)
    (SAIDA/'indicadores.json').write_text(json.dumps(k,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    rel=['# Relatório automático — Phaethon aethereus','']+[f'- **{a.replace("_"," ").capitalize()}:** {v}' for a,v in k.items()]
    (SAIDA/'relatorio_resumo.md').write_text('\n'.join(rel),encoding='utf-8')
    print('Fluxo concluído.')
if __name__=='__main__': main()
