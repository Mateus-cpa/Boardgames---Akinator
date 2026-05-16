# 🎲 Boardgame Akinator

Uma interface interativa em Streamlit para descobrir jogos de tabuleiro usando dados do BoardGameGeek.

## Funcionalidades

- Buscar por ID
- Buscar por nome parecido
- Jogo aleatório
- Por mecânica ou tema
- Akinator (modo experimental)

## Instalação

### Pré-requisitos

- Python 3.9+
- Poetry ([Instalar Poetry](https://python-poetry.org/docs/#installation))

### Setup com uv

```bash
uv init
uv venv
source .venv/Scripts/activate

uv add streamlit
uv add pandas
uv add rapidfuzz
uv run streamlit run streamlit_app.py
```

```bash
deactivate #para finalizar o ambiente virtual
```

### Setup com poetry

```bash
# Clonar o repositório
git clone https://github.com/Mateus-cpa/Boardgames---Akinator.git
cd Boardgames---Akinator

# Instalar dependências e criar ambiente virtual
poetry install

# Ativar o ambiente virtual
poetry shell

# Executar a aplicação
streamlit run streamlit_app.py
```

A aplicação estará disponível em: `http://localhost:8501`

### Comandos Úteis

```bash
# Executar sem ativar shell
poetry run streamlit run streamlit_app.py

# Adicionar nova dependência
poetry add package_name

# Remover dependência
poetry remove package_name

# Atualizar dependências
poetry update
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
```
Boardgames---Akinator/
├── streamlit_app.py
├── pyproject.toml
├── poetry.lock
├── README.md
└── database/
    └── 5k version.xlsx
```
