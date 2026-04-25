import os
import random

import pandas as pd
import streamlit as st
from rapidfuzz import process

import kagglehub
from kagglehub import KaggleDatasetAdapter

import openpyxl




@st.cache_data(show_spinner=True)
def load_data(name: str) -> pd.DataFrame:
    path = "database"
    # Set the path to the file you'd like to load
    file_path = "database/5k version.xlsx"  # Adjust this to the correct path in your Kaggle dataset

    df = kagglehub.load_dataset(
    KaggleDatasetAdapter.PANDAS,
    "doggotheshia/5k-bgg-dataset",
    file_path, sql_query=None
    # Provide any additional arguments like 
    # sql_query or pandas_kwargs. See the 
    # documenation for more information:
    # https://github.com/Kaggle/kagglehub/blob/main/README.md#kaggledatasetadapterpandas
    )

    print("First 5 records:", df.head())
    if os.path.exists(path):
        return pd.read_csv(path, index_col="game_id")

        st.error(f"Could not find '{name}'. Place it in the working directory or set up the data path.\nTried:\n" + "\n".join(file_path))


def find_similar(query: str, choices, limit: int = 10):
    results = process.extract(query, choices, limit=limit, score_cutoff=0)
    return [item[0] for item in results]


def valid_random_game(df_games: pd.DataFrame):
    valid_ids = df_games.index[df_games["name"].notna()].tolist()
    return random.choice(valid_ids)


def build_characteristic_lists(df_mechs: pd.DataFrame, df_themes: pd.DataFrame):
    mech_labels = [f"mechanic: {col}" for col in df_mechs.columns.tolist()]
    theme_labels = [f"theme: {col}" for col in df_themes.columns.tolist()]
    return mech_labels, theme_labels, mech_labels + theme_labels


def display_game_info(wanted_id: int, df_games, df_mechs, df_themes, df_subdomains):
    if wanted_id not in df_games.index:
        st.error("Game not found.")
        return

    game = df_games.loc[wanted_id]
    st.header(f"{game['name']} (ID: {wanted_id})")
    if "bgg_url" in df_games.columns:
        st.markdown(f"[Ver no BoardGameGeek]({game['bgg_url']})")

    metadata_columns = [
        "rank",
        "year",
        "min_players",
        "max_players",
        "avg_time",
        "min_time",
        "max_time",
        "weight",
        "age",
        "avg_rating",
        "geek_rating",
        "num_votes",
        "owned",
        "designer",
    ]
    metadata = {col: game[col] for col in metadata_columns if col in df_games.columns}
    st.write(metadata)

    wanted_mechs = df_mechs.loc[wanted_id]
    wanted_themes = df_themes.loc[wanted_id]
    wanted_subdomains = df_subdomains.loc[wanted_id]

    wanted_mechs = wanted_mechs.index[wanted_mechs == 1].tolist()
    wanted_themes = wanted_themes.index[wanted_themes == 1].tolist()
    wanted_subdomains = wanted_subdomains.index[wanted_subdomains == 1].tolist()

    st.subheader("Subdomínios")
    st.write(wanted_subdomains or "Nenhum subdomínio registrado.")

    st.subheader("Mecânicas")
    st.write(wanted_mechs or "Nenhuma mecânica registrada.")

    st.subheader("Temas")
    st.write(wanted_themes or "Nenhum tema registrado.")

    def top_similar_games(df_feature: pd.DataFrame, selected_features: list):
        if not selected_features:
            return []
        df_subset = df_feature[selected_features].copy()
        df_subset["sum"] = df_subset.sum(axis=1)
        top_values = sorted(df_subset["sum"].unique(), reverse=True)[:2]
        if 0 in top_values:
            top_values.remove(0)
        if not top_values:
            return []
        candidates = df_subset[df_subset["sum"].isin(top_values)].index.tolist()
        candidates = [i for i in candidates if i != wanted_id]
        return df_games.loc[candidates, "name"].tolist()

    similar_by_mechs = top_similar_games(df_mechs, wanted_mechs)
    similar_by_themes = top_similar_games(df_themes, wanted_themes)

    st.subheader("Jogos com mecânicas similares")
    st.write(similar_by_mechs or "Nenhum jogo similar encontrado.")

    st.subheader("Jogos com temas similares")
    st.write(similar_by_themes or "Nenhum jogo similar encontrado.")


def init_akinator_state(df_games, df_mechs, df_themes, df_subdomains):
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
        df_games = load_data('5k version.xlsx')
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    min_id = int(df_games.index.min())
    max_id = int(df_games.index.max())
    mech_labels, theme_labels, all_characteristics = build_characteristic_lists(df_mechs, df_themes)

    page = st.sidebar.selectbox(
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
        wanted_id = st.number_input("Digite o ID do jogo:", min_value=min_id, max_value=max_id, value=min_id)
        if st.button("Buscar"):
            display_game_info(wanted_id, df_games, df_mechs, df_themes, df_subdomains)

    elif page == "Buscar por nome parecido":
        query = st.text_input("Digite o nome ou parte do nome do jogo:")
        if query:
            matches = find_similar(query, df_games["name"].tolist(), limit=10)
            chosen = st.selectbox("Escolha um jogo", matches)
            if st.button("Mostrar detalhes"):
                selected_id = int(df_games[df_games["name"] == chosen].index[0])
                display_game_info(selected_id, df_games, df_mechs, df_themes, df_subdomains)

    elif page == "Jogo aleatório":
        if st.button("Sortear jogo"):
            random_id = valid_random_game(df_games)
            display_game_info(random_id, df_games, df_mechs, df_themes, df_subdomains)

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
                    display_game_info(chosen_id, df_games, df_mechs, df_themes, df_subdomains)

    elif page == "Akinator":
        run_akinator(df_games, df_mechs, df_themes, df_subdomains)


if __name__ == "__main__":
    main()
