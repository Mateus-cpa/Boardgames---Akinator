# 🎲 Boardgame Akinator

Uma interface interativa em Streamlit para descobrir jogos de tabuleiro usando dados do BoardGameGeek.

## Funcionalidades

- Buscar por ID
- Buscar por nome parecido
- Jogo aleatório
- Por mecânica ou tema
- Akinator (modo experimental)

## Instalação

```bash
# Instalação
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt

#Execução
python -m streamlit run streamlit_app.py
```

## Dados Necessários
Coloque o arquivo 5k version.xlsx na pasta database

Colunas esperadas:

- id (índice)
- name
- mechanic
- category
- family
- domain
- Outras: rank, year, minplayers, maxplayers, average_rating

## Tecnologias

Streamlit
Pandas
RapidFuzz
Kagglehub

## Estrutura

Boardgames---Akinator/
├── streamlit_app.py
├── requirements.txt
├── pyproject.toml
├── README.md
└── database/
    └── 5k version.xlsx