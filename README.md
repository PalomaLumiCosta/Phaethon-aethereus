# Projeto Phaethon aethereus — CEMAVE / ICMBio

# Projeto desemvolvido por Paloma Lumi Costa- Bolsista de Apoio Cientifico GEFMAR -CEMAVE/ICMBIO
# Este é apenas o primeiro protótipo que deve ainda aperfeiçoar o layout , nome científico, e vizualização....

## Arquivos
- `tratamento_phaethon.py`: leitura, limpeza, validação e tabelas derivadas.
- `PhaethonAnalise.py`: fluxo automático que gera CSVs em `resultados/`.
- `app_streamlit_phaethon.py`: painel interativo.
- `.gitignore`: impede o envio da planilha sensível ao GitHub.

## Estrutura
```text
Projeto_Phaethon_Streamlit/
├── app_streamlit_phaethon.py
├── PhaethonAnalise.py
├── tratamento_phaethon.py
├── requirements.txt
├── .gitignore
├── .streamlit/config.toml
├── dados/
└── resultados/
```

## Instalação
```powershell
cd caminho\Projeto_Phaethon_Streamlit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Preparar os dados
# Opção por enquanto por se tratar de dados sensíveis
Copie a planilha `.xlsx` para a pasta `dados/`. O painel também aceita envio direto pela barra lateral.

## Gerar as bases tratadas
```powershell
python PhaethonAnalise.py
```

## Rodar o Streamlit
```powershell
streamlit run app_streamlit_phaethon.py
```

## Análises disponíveis
- colocação e recuperação;
- anilhas distintas e taxa de recuperação;
- histórico individual;
- tempo entre colocação e recuperação;
- locais e série temporal;
- recorrência da mesma anilha no mesmo ninho;
- mudança de ninho;
- qualidade, inconsistências e duplicatas;
- downloads em CSV.

## Dados sensíveis
Não publique a planilha em repositório público. O `.gitignore` bloqueia arquivos Excel dentro de `dados/`.


## Identidade visual do PARNA Abrolhos

O painel foi adaptado para a identidade visual da tela de referência:

- cabeçalho institucional;
- fundo azul-claro;
- títulos e textos em branco;
- filtros em azul-petróleo;
- cartões de indicadores em fundo claro;
- abas com destaque em azul-escuro;
- ilustração de ave na barra lateral.

Os arquivos visuais estão na pasta `assets/`.
