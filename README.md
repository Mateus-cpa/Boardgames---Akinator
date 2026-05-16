# 🎲 Boardgame Akinator (Ludonator)

Uma interface interativa em Streamlit para descobrir e explorar jogos de tabuleiro usando dados do BoardGameGeek.

## Funcionalidades

- **Buscar por ID**: Encontre informações detalhadas de um jogo específico através do seu ID no BGG.
- **Buscar por nome parecido**: Pesquisa difusa (fuzzy search) para encontrar jogos mesmo sem saber o nome exato.
- **Jogo aleatório**: Sorteia um jogo válido da base de dados.
- **Por característica**: Navegue por jogos filtrando por mecânica, tema, família, subdomínio, designer ou artista.
- **Ludonator (modo experimental)**: Tenta adivinhar ou encontrar um jogo ideal para você com base em uma série de perguntas sobre características desejadas.
- **Painel de dados**: Seção de análise com filtros avançados (ano, peso, jogadores, etc.) e gráficos de distribuição interativos.

## Instalação

### Pré-requisitos

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (gerenciador de dependências de alta performance)

### Setup com uv

O projeto agora utiliza o `uv` para o gerenciamento de dependências. 

```bash
# Clonar o repositório
git clone https://github.com/Mateus-cpa/Boardgames---Akinator.git
cd Boardgames---Akinator

# Sincronizar as dependências e criar o ambiente virtual
uv sync

# Executar a aplicação
uv run streamlit run streamlit_app.py
```

A aplicação estará disponível em: `http://localhost:8501`

### Comandos Úteis com uv

```bash
# Adicionar nova dependência
uv add package_name

# Remover dependência
uv remove package_name

# Atualizar dependências
uv lock --upgrade
```

## Dados Necessários

Coloque o arquivo `5k version.xlsx` na pasta `database/`.

Colunas esperadas no Excel:

- `id` (índice)
- `name`
- `mechanic`
- `category`
- `family`
- `domain`
- `designer`
- `artist`
- Outras: `rank_global`, `year`, `minplayers`, `maxplayers`, `average_weight`, `minplaytime`, `maxplaytime`, `age`, `description`, `image`.

## Tecnologias

- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- Kagglehub

## Estrutura do Projeto

```text
Boardgames---Akinator/
├── streamlit_app.py      # Aplicação principal
├── pyproject.toml        # Metadados e dependências
├── uv.lock               # Lockfile do uv
├── README.md             # Documentação
└── database/
    └── 5k version.xlsx   # Base de dados (não inclusa no repositório)
```
