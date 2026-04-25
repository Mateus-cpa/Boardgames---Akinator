import os
import random

import pandas as pd
import streamlit as st
from rapidfuzz import process

#import kagglehub
#from kagglehub import KaggleDatasetAdapter


@st.cache_data(show_spinner=True)
def load_data():
    file_path = "database/5k version.xlsx"
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo '{file_path}' não encontrado.")
        
    df_games = pd.read_excel(file_path, index_col='id')
    # apenas ids únicos
    df_games = df_games[~df_games.index.duplicated(keep='first')]
    df_mechs = pd.DataFrame(df_games.mechanic.str.split(",").explode().unique().tolist(), columns=['mechanic'])
    df_themes = pd.DataFrame(df_games.category.str.split(",").explode().unique().tolist(), columns=['category'])
    df_subdomains = pd.DataFrame(df_games.domain.str.split(",").explode().unique().tolist(), columns=['domain'])
    df_family = pd.DataFrame(df_games.family.str.split(",").explode().unique().tolist(), columns=['family'])
    return df_games, df_mechs, df_themes, df_subdomains, df_family

def find_similar(query: str, choices, limit: int = 10):
    results = process.extract(query, choices, limit=limit, score_cutoff=0)
    return [item[0] for item in results]


def valid_random_game(df_games: pd.DataFrame):
    valid_ids = df_games.index[df_games["name"].notna()].tolist()
    return random.choice(valid_ids)


def build_characteristic_lists(df_games: pd.DataFrame):
    # listar todas mecânicas em uma lista e pegar os valores únicos
    mech_labels = [df_games.mechanic.str.split(",").explode().unique().tolist()]
    #st.info(mech_labels)
    theme_labels = [df_games.category.str.split(",").explode().unique().tolist()]
    #st.info(theme_labels)
    subdomain_labels = [df_games.domain.str.split(",").explode().unique().tolist()]
    #st.info(subdomain_labels)
    family_labels = [df_games.family.str.split(",").explode().unique().tolist()]
    #st.info(family_labels)


    return mech_labels, theme_labels, subdomain_labels, family_labels, mech_labels + theme_labels + subdomain_labels + family_labels


def display_game_info(wanted_id: int, df_games, list_mechs, list_themes):
    if wanted_id not in df_games.index:
        st.info("ID não encontrado. Por favor, escolha um ID válido.")
        return

    else:
        game = df_games.loc[wanted_id,:]
        st.header(f"{game['name']} (ID: {wanted_id})")
    
    if "bgg_url" in df_games.columns:
        st.markdown(f"[Ver no BoardGameGeek]({game['bgg_url']})")

    metadata_columns = [
        "rank",
        "year",
        "minplayers",
        "maxplayers",
        "designer",
        "description",
        "family"
        "avg_time",
        "minplaytime",
        "maxplauytime",
        "average_weight",
        "age",
        "average_rating"
        
    ]
    st.subheader("Informações básicas")
    for col in metadata_columns:
        if col in df_games.columns:
            st.write(f"**{col.capitalize()}:** {game[col]}")

    st.subheader("Mecânicas e jogos similares")
    wanted_mechs = df_games.mechanic[df_games.index == wanted_id].tolist()[0]
    for mech in wanted_mechs.split(","):
        st.write(f'- {mech.strip()}')
    similar_mechs_mask = df_games['mechanic'].str.contains(wanted_mechs.split(",")[0].strip(), na=False)
    st.write(df_games[similar_mechs_mask][['name', 'year', 'mechanic']].head(5))
    
    st.subheader("Temas e jogos similares")
    wanted_themes = df_games.category[df_games.index == wanted_id].tolist()[0]
    for theme in wanted_themes.split(","):
        st.write(f'- {theme.strip()}')
    similar_themes_mask = df_games['category'].str.contains(wanted_themes.split(",")[0].strip(), na=False)
    st.write(df_games[similar_themes_mask][['name', 'year', 'category']].head(5))
        
    st.subheader("Família")
    wanted_family = df_games.family[df_games.index == wanted_id].tolist()[0]
    for family in wanted_family.split(","):
        st.write(f'- {family.strip()}')
    
    st.subheader("Subdomínios")
    wanted_subdomains = df_games.domain[df_games.index == wanted_id].tolist()[0]
    for sub in wanted_subdomains.split(","):
        st.write(f'- {sub.strip()}')
    
   



def init_akinator_state(df_games, df_mechs, df_themes, df_subdomains, df_family):
    mech_labels, theme_labels, list_characteristics = build_characteristic_lists(df_mechs, df_themes)
    df_themes_temp = df_themes.copy()
    df_mechs_temp = df_mechs.copy()
    df_themes_temp.columns = ["theme: " + col for col in df_themes.columns]
    df_mechs_temp.columns = ["mechanic: " + col for col in df_mechs.columns]

    df_total = df_games.copy()
    df_total = df_total.merge(df_themes_temp, how="left", left_index=True, right_index=True)
    df_total = df_total.merge(df_mechs_temp, how="left", left_index=True, right_index=True)
    df_total[list_characteristics] = df_total[list_characteristics].fillna(0)
    df_total["akinator"] = 0

    return {
        "df_total": df_total,
        "questions": list_characteristics.copy(),
        "asked": [],
        "scores": {},
        "step": "start",
        "players": None,
        "current_question": None,
        "results": None,
    }


def pick_next_question(state):
    remaining = [q for q in state["questions"] if q not in state["asked"]]
    if not remaining:
        return None
    return random.choice(remaining)


def compute_akinator_scores(state, answer: str, question: str):
    if answer == "Y":
        state["df_total"]["akinator"] += state["df_total"][question]
    elif answer == "N":
        state["df_total"]["akinator"] -= state["df_total"][question]
    state["asked"].append(question)

    df_results = state["df_total"][["name", "min_players", "max_players", "akinator"]]
    best_score = df_results["akinator"].max()
    top_matches = df_results[df_results["akinator"] == best_score]
    state["results"] = top_matches
    return top_matches


def run_akinator(df_games, df_mechs, df_themes, df_subdomains):
    if "akinator_state" not in st.session_state:
        st.session_state["akinator_state"] = init_akinator_state(df_games, df_mechs, df_themes, df_subdomains)

    state = st.session_state["akinator_state"]

    st.sidebar.write("### Configuração do Akinator")
    if st.sidebar.button("Reiniciar jogo"):
        st.session_state["akinator_state"] = init_akinator_state(df_games, df_mechs, df_themes, df_subdomains)
        state = st.session_state["akinator_state"]

    if state["step"] == "start":
        players = st.number_input("Quantos jogadores o jogo suporta?", min_value=1, max_value=100, value=2)
        if st.button("Começar"):
            state["players"] = int(players)
            state["df_total"]["akinator"] = 0
            state["df_total"]["akinator"] += state["df_total"].apply(
                lambda row: 100 if state["players"] >= row["min_players"] and state["players"] <= row["max_players"] else 0,
                axis=1,
            )
            state["step"] = "question"
            state["current_question"] = pick_next_question(state)

    if state["step"] == "question":
        st.write(f"Jogadores: {state['players']}")
        if not state["current_question"]:
            st.warning("Não há mais perguntas disponíveis.")
            state["step"] = "finished"
            return

        st.write(f"A pergunta atual é: {state['current_question']}")
        answer = st.radio("Resposta", ["Y", "N"], key="akinator_answer")
        if st.button("Enviar resposta"):
            compute_akinator_scores(state, answer, state["current_question"])
            top_matches = state["results"]
            if top_matches.shape[0] == 1:
                state["step"] = "finished"
            else:
                state["current_question"] = pick_next_question(state)
                if state["current_question"] is None:
                    state["step"] = "finished"

        if state["results"] is not None:
            st.write(f"Jogos candidatos atuais: {state['results'].shape[0]}")
            st.dataframe(state["results"].head(10))

    if state["step"] == "finished":
        if state["results"] is not None and state["results"].shape[0] >= 1:
            best_id = int(state["results"].index[0])
            st.success("O Akinator escolheu um jogo!")
            display_game_info(best_id, df_games, df_mechs, df_themes, df_subdomains)
        else:
            st.warning("Nenhum resultado definitivo foi encontrado.")


def main():
    st.set_page_config(page_title="Boardgame Akinator", layout="wide")
    st.title("Boardgame Akinator")
    st.write("Uma interface interativa para encontrar jogos de tabuleiro usando dados do BoardGameGeek.")

    try:
        df_games, df_mechs, df_themes, df_subdomains, df_family = load_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    min_id = int(df_games.index.min())
    max_id = int(df_games.index.max())
    list_mechs, list_themes, list_subdomains, list_families, all_characteristics = build_characteristic_lists(df_games)

    page = st.selectbox(
        "Escolha uma opção",
        [
            "Buscar por ID",
            "Buscar por nome parecido",
            "Jogo aleatório",
            "Por mecânica ou tema",
            "Akinator",
        ],
    )
    

    if page == "Buscar por ID":
        wanted_id = st.selectbox("Digite o ID do jogo:", options=df_games.index.tolist())
        wanted_id = 444
        #if st.button("Buscar"):
        display_game_info(wanted_id, df_games, list_mechs, list_themes)
        

    elif page == "Buscar por nome parecido":
        query = st.text_input("Digite o nome ou parte do nome do jogo:")
        if query:
            matches = find_similar(query, df_games["name"].tolist(), limit=10)
            chosen = st.selectbox("Escolha um jogo", matches)
            if st.button("Mostrar detalhes"):
                selected_id = int(df_games[df_games["name"] == chosen].index[0])
                display_game_info(selected_id, df_games)

    elif page == "Jogo aleatório":
        if st.button("Sortear jogo"):
            random_id = valid_random_game(df_games)
            display_game_info(random_id, df_games)

    elif page == "Por mecânica ou tema":
        characteristic = st.selectbox("Escolha uma característica", [""] + all_characteristics)
        if characteristic:
            if st.button("Buscar jogos com essa característica"):
                field, value = characteristic.split(": ", 1)
                value = value.strip()
                if field == "mechanic":
                    ids = df_mechs.index[df_mechs[value] == 1].tolist()
                else:
                    ids = df_themes.index[df_themes[value] == 1].tolist()
                st.write(f"Encontrados {len(ids)} jogos com {characteristic}.")
                st.dataframe(df_games.loc[ids, ["name", "year", "weight", "avg_rating"]].head(100))
                chosen_id = st.selectbox("Selecione um jogo", ids, format_func=lambda x: f"{x} - {df_games.at[x, 'name']}" if x in df_games.index else str(x))
                if st.button("Ver detalhes do jogo"):
                    display_game_info(chosen_id, df_games)

    elif page == "Akinator":
        run_akinator(df_games)

    #temporário para visualizar as colunas do dataframe
    #st.write(df_games.columns)
    
if __name__ == "__main__":
    main()
