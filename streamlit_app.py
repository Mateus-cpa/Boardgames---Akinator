import os
import random

import pandas as pd 
import streamlit as st 
from rapidfuzz import process
#import plotly.express as px



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
    # transformar colunas em listas de valores únicos
    mech_labels = [df_games.mechanic.str.split(",").explode().unique().tolist()]
    #st.info(mech_labels)
    theme_labels = [df_games.category.str.split(",").explode().unique().tolist()]
    #st.info(theme_labels)
    subdomain_labels = [df_games.domain.str.split(",").explode().unique().tolist()]
    #st.info(subdomain_labels)
    family_labels = [df_games.family.str.split(",").explode().unique().tolist()]
    #st.info(family_labels)
    designer_labels = [df_games.designer.str.split(",").explode().unique().tolist()]
    artist_labels = [df_games.artist.str.split(",").explode().unique().tolist()]
    
    #concatenar todas as características em uma única lista para o menu de seleção
    all_characteristics = [f"mechanic: {m}" for m in mech_labels[0]] + [f"theme: {t}" for t in theme_labels[0]] + [f"subdomain: {s}" for s in subdomain_labels[0]] + [f"family: {f}" for f in family_labels[0]] + [f"designer: {d}" for d in designer_labels[0]] + [f"artist: {a}" for a in artist_labels[0]]
    #st.write(all_characteristics)
    return mech_labels, theme_labels, subdomain_labels, family_labels, all_characteristics

def similar_caracteristics(df_games, column, wanted_list, title, key_prefix, min_common=2, top_n=5):
    wanted_list = [w.strip() for w in wanted_list if w and isinstance(w, str)]
    if not wanted_list:
        st.info("Nenhuma característica selecionada.")
        return pd.DataFrame()

    def count_common(x):
        if pd.isna(x):
            return 0
        values = [v.strip() for v in x.split(",")]
        return sum(1 for w in wanted_list if w in values)

    df_similar = df_games.copy()
    df_similar["common_count"] = df_similar[column].apply(count_common)
    df_similar = df_similar[df_similar["common_count"] >= min_common]
    df_similar = df_similar.sort_values("common_count", ascending=False)

    st.subheader(title)

    if df_similar.empty:
        st.write("Nenhum jogo similar com pelo menos 2 características em comum.")
        return df_similar

    # Mostra as características do jogo buscado em 3 colunas
    col1, col2, col3 = st.columns(3)
    for i, value in enumerate(wanted_list):
        target = col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3
        target.write(f"- {value}")

    # Exibe jogos similares
    for game in df_similar.head(top_n).itertuples():
        game_values = [v.strip() for v in getattr(game, column).split(",") if v.strip()]
        colored_values = ", ".join(
            f'<span style="color:blue">{v}</span>' if v in wanted_list else v
            for v in game_values
        )

        left, right = st.columns([0.05, 0.95])
        with right:
            st.markdown(
                f"{game.name} ({game.year}) - {colored_values}",
                unsafe_allow_html=True,
            )
        with left:
            if st.checkbox("", key=f"{key_prefix}_{game.Index}"):
                st.session_state.chosen_id = game.Index

    return df_similar

def display_game_info(wanted_id: int, df_games, list_mechs, list_themes):
    if wanted_id not in df_games.index:
        st.info("ID não encontrado. Por favor, escolha um ID válido.")
        return

    else:
        game = df_games.loc[wanted_id,:]
        st.header(f"{game['name']} [id: {wanted_id}] ({game['year']}) - Rank {game['rank_global']}")
        st.subheader("Informações básicas")

        col1, col2, col3 = st.columns(3)
        
        metadata_columns = [
            "designer",
            "year",
            "minplayers",
            "maxplayers",
            "description",
            
            "artist",
            "average_weight",
            "minplaytime",
            "maxplaytime",
            "age"]
        
        for col in metadata_columns[0:5]:
            col1.write(f"**{col.capitalize()}:** {game[col]}")
        
        for col in metadata_columns[5:]:
            col2.write(f"**{col.capitalize()}:** {game[col]}")

        if "image" in df_games.columns:
            col3.image(game["image"], width=300)
            
        wanted_mechs = df_games.at[wanted_id, "mechanic"]
        wanted_mechs_list = [m.strip() for m in wanted_mechs.split(",") if m.strip()]
        similar_caracteristics(
            df_games,
            column="mechanic",
            wanted_list=wanted_mechs_list,
            title="Mecânicas e jogos similares",
            key_prefix="similar_mech",
        )

        wanted_themes = df_games.at[wanted_id, "category"]
        wanted_themes_list = [t.strip() for t in wanted_themes.split(",") if t.strip()]
        similar_caracteristics(
            df_games,
            column="category",
            wanted_list=wanted_themes_list,
            title="Temas e jogos similares",
            key_prefix="similar_theme",
        )

        wanted_designers = df_games.at[wanted_id, "designer"]
        wanted_designers_list = [d.strip() for d in wanted_designers.split(",") if d.strip()]
        similar_caracteristics(
            df_games,
            column="designer",
            wanted_list=wanted_designers_list,
            title="Designers e jogos similares",
            key_prefix="similar_designer",
        )

        wanted_artists = df_games.at[wanted_id, "artist"]
        wanted_artists_list = [a.strip() for a in wanted_artists.split(",") if a.strip()]
        similar_caracteristics(
            df_games,
            column="artist",
            wanted_list=wanted_artists_list,
            title="Artistas e jogos similares",
            key_prefix="similar_artist",
        )
            
        wanted_family = df_games.at[wanted_id, "family"]
        wanted_family_list = [f.strip() for f in wanted_family.split(",") if f.strip()]
        similar_caracteristics(
            df_games,
            column="family",
            wanted_list=wanted_family_list,
            title="Famílias e jogos similares",
            key_prefix="similar_family",
        )
        
        wanted_subdomains = df_games.at[wanted_id, "domain"]
        wanted_subdomains_list = [s.strip() for s in wanted_subdomains.split(",") if s.strip()]
        similar_caracteristics(
            df_games,
            column="domain",
            wanted_list=wanted_subdomains_list,
            title="Subdomínios e jogos similares",
            key_prefix="similar_subdomain",
        )



def init_akinator_state(df_games, all_characteristics):
    df_total = df_games.copy()
    df_total["akinator"] = 0
    return {
        "df_total": df_total,
        "questions": all_characteristics.copy(),
        "asked": [],
        "scores": {},
        "step": "start",
        "players": None,
        "current_question": None,
        "results": None,
    }

def pick_next_question(state):
    """
    Seleciona a próxima pergunta priorizando características mais comuns
    entre os jogos candidatos (com score > 0)
    """
    # Excluir perguntas já feitas
    remaining = [q for q in state["questions"] if q not in state["asked"]]
    
    if not remaining:
        return None
    
    # Filtrar apenas jogos com a maior pontuação (melhores candidatos)
    best_score = state["df_total"]["akinator"].max()
    df_candidates = state["df_total"][state["df_total"]["akinator"] == best_score]
    
    # Extrair características presentes apenas nos jogos candidatos
    candidate_characteristics = set()
    
    # Extrair todas as características dos candidatos
    for _, row in df_candidates.iterrows():
        if pd.notna(row["mechanic"]):
            for m in row["mechanic"].split(","):
                candidate_characteristics.add(f"mechanic: {m.strip()}")
        if pd.notna(row["category"]):
            for c in row["category"].split(","):
                candidate_characteristics.add(f"theme: {c.strip()}")
        if pd.notna(row["domain"]):
            for d in row["domain"].split(","):
                candidate_characteristics.add(f"subdomain: {d.strip()}")
        #if pd.notna(row["family"]):
        #    for f in row["family"].split(","):
        #        candidate_characteristics.add(f"family: {f.strip()}")
        if pd.notna(row["designer"]):
            for d in row["designer"].split(","):
                candidate_characteristics.add(f"designer: {d.strip()}")
        if pd.notna(row["artist"]):
            for a in row["artist"].split(","):
                candidate_characteristics.add(f"artist: {a.strip()}")
    
    # Filtrar apenas perguntas restantes que existem nos candidatos
    relevant_questions = [q for q in remaining if q in candidate_characteristics]
    
    # Contar frequência de cada característica nos candidatos
    characteristic_count = {}
    
    for question in relevant_questions:
        field, value = question.split(": ", 1)
        value = value.strip()
        
        # Contar quantos jogos candidatos têm essa característica
        if field == "mechanic":
            count = df_candidates["mechanic"].str.contains(value, na=False).sum()
        elif field == "theme":
            count = df_candidates["category"].str.contains(value, na=False).sum()
        elif field == "subdomain":
            count = df_candidates["domain"].str.contains(value, na=False).sum()
        elif field == "family":
            count = df_candidates["family"].str.contains(value, na=False).sum()
        elif field == "designer":
            count = df_candidates["designer"].str.contains(value, na=False).sum()
        elif field == "artist":
            count = df_candidates["artist"].str.contains(value, na=False).sum()
        else:
            count = 0
        
        characteristic_count[question] = count

    # Selecionar a pergunta com maior frequência entre os candidatos
    best_question = max(characteristic_count.items(), key=lambda x: x[1])[0]
    return best_question

def compute_akinator_scores(state, answer: str, question: str):
    # Extrair campo e valor da pergunta
    field, value = question.split(": ", 1)
    value = value.strip()
    
    # Criar máscara de quais jogos têm essa característica
    if field == "mechanic":
        mask = state["df_total"]["mechanic"].str.contains(value, na=False, regex=False)
    elif field == "theme":
        mask = state["df_total"]["category"].str.contains(value, na=False, regex=False)
    elif field == "subdomain":
        mask = state["df_total"]["domain"].str.contains(value, na=False, regex=False)
    elif field == "family":
        mask = state["df_total"]["family"].str.contains(value, na=False, regex=False)
    elif field == "designer":
        mask = state["df_total"]["designer"].str.contains(value, na=False, regex=False)
    elif field == "artist":
        mask = state["df_total"]["artist"].str.contains(value, na=False, regex=False)
    else:
        mask = pd.Series([False] * len(state["df_total"]))
    
    # Pontuação a adicionar/remover
    points = 10
    
    if answer == "Sim":
        state["df_total"].loc[mask, "akinator"] += points
    elif answer == "Não":
        state["df_total"].loc[mask, "akinator"] -= points
    
    state["asked"].append(question)

    df_results = state["df_total"][["name", "minplayers", "maxplayers", "year", "akinator"]]
    best_score = df_results["akinator"].max()
    top_matches = df_results[df_results["akinator"] == best_score]
    state["results"] = top_matches
    return top_matches

def run_akinator(df_games, all_characteristics):
    if "akinator_state" not in st.session_state:
        st.session_state["akinator_state"] = init_akinator_state(df_games, all_characteristics)

    state = st.session_state["akinator_state"]

    if st.button("Reiniciar jogo"):
        st.session_state["akinator_state"] = init_akinator_state(df_games, all_characteristics)
        state = st.session_state["akinator_state"]

    if state["step"] == "start":
        col1, col2 = st.columns([0.4, 0.6])
        players = col1.number_input("Quantos jogadores o jogo suporta?", min_value=1, max_value=100, value=2)
        
        if st.button("Começar"):
            state["players"] = int(players)
            state["df_total"]["akinator"] = 0
            state["df_total"]["akinator"] += state["df_total"].apply(
                lambda row: 100 if state["players"] >= row["minplayers"] and state["players"] <= row["maxplayers"] else 0,
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

        st.write(f"**Pergunta {len(state['asked']) + 1}:** {state['current_question']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            answer = st.radio("Sua resposta:", ["Sim", "Não"], key=f"answer_{state['current_question']}")
        with col2:
            if st.button("Confirmar resposta", key="next_btn"):
                compute_akinator_scores(state, answer, state["current_question"])
                top_matches = state["results"]
                
                if top_matches.shape[0] == 1:
                    state["step"] = "finished"
                else:
                    state["current_question"] = pick_next_question(state)
                    if state["current_question"] is None:
                        state["step"] = "finished"
                
                st.rerun()

        # Debug: monitorar pontuações e características
        with st.expander("📊 Debug - Monitoramento detalhado", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Pontuações atuais (top 15):**")
                top_scores = state["df_total"][["name", "akinator"]].sort_values("akinator", ascending=False).head(15)
                st.dataframe(top_scores, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**Distribuição de pontuações:**")
                score_dist = state["df_total"]["akinator"].value_counts().sort_index(ascending=False).head(10)
                st.bar_chart(score_dist)
            
            with col3:
                st.write("**Perguntas respondidas:**")
                if state["asked"]:
                    for i, q in enumerate(state["asked"], 1):
                        st.write(f"{i}. {q}")
                else:
                    st.write("Nenhuma pergunta respondida ainda")
            
            # Debug da última pergunta
            if state["asked"]:
                st.write("---")
                st.write("**Debug da última resposta:**")
                last_q = state["asked"][-1]
                field, value = last_q.split(": ", 1)
                
                if field == "mechanic":
                    col_name = "mechanic"
                elif field == "theme":
                    col_name = "category"
                elif field == "subdomain":
                    col_name = "domain"
                else:
                    col_name = field
                
                games_with_feature = state["df_total"][state["df_total"][col_name].str.contains(value.strip(), na=False, regex=False)].shape[0]
                st.write(f"Pergunta: {last_q}")
                st.write(f"Jogos com '{value.strip()}': {games_with_feature}")
                st.write(f"Pontuação mín/máx/média: {state['df_total']['akinator'].min()} / {state['df_total']['akinator'].max()} / {state['df_total']['akinator'].mean():.1f}")

    if state["step"] == "finished":
        if state["results"] is not None and state["results"].shape[0] >= 1:
            best_id = int(state["results"].index[0])
            st.success("O Akinator escolheu um jogo!")
            display_game_info(best_id, df_games, None, None)
        else:
            st.warning("Nenhum resultado definitivo foi encontrado.")

def main():
    st.set_page_config(page_title="Boardgame Akinator", layout="wide")
    st.title("Navegação BGG")
    st.write("Uma interface interativa para encontrar jogos de tabuleiro usando dados do BoardGameGeek.")

    st.session_state.setdefault("chosen_id", None)

    try:
        df_games, df_mechs, df_themes, df_subdomains, df_family = load_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    list_mechs, list_themes, list_subdomains, list_families, all_characteristics = build_characteristic_lists(df_games)

    st.segmented_control(
        label="Navegue pelo menu:",
        options=[
            "Buscar por ID",
            "Buscar por nome parecido",
            "Jogo aleatório",
            "Por característica",
            "Akinator",
            "Painel de dados"
        ],
        key="main_menu"
        
    )
    
    # reiniciar st.session_state.chosen_id ao mudar de menu para evitar mostrar detalhes de um jogo anterior
    st.session_state.chosen_id = None
    
    page = st.session_state.get("main_menu", "Por característica")
    
    # -- MENU 1: ID --
    if page == "Buscar por ID":
        wanted_id = st.selectbox("Digite o ID do jogo:", options=df_games.index.tolist())
        #wanted_id = 444
        if st.button("Buscar"):
            st.session_state.chosen_id = wanted_id

    # -- MENU 2: NOME PARECIDO --
    elif page == "Buscar por nome parecido":
        query = st.text_input("Digite o nome ou parte do nome do jogo:")
        if query:
            matches = find_similar(query, df_games["name"].tolist(), limit=10)
            chosen = st.selectbox("Escolha um jogo", matches)
            if st.button("Mostrar detalhes"):
                selected_id = int(df_games[df_games["name"] == chosen].index[0])
                st.session_state.chosen_id = selected_id

    # -- MENU 3: JOGO ALEATÓRIO --
    elif page == "Jogo aleatório":
        if st.button("Sortear jogo"):
            st.session_state.chosen_id = valid_random_game(df_games)
            
    # -- MENU 4: POR CARACTERÍSTICA --
    elif page == "Por característica":
        st.session_state.setdefault("characteristic_ids", [])
        search_text = st.text_input("Buscar característica:")
        filtered_characteristics = [c for c in all_characteristics if search_text.lower() in c.lower()] if search_text else all_characteristics

        if filtered_characteristics:
            characteristic = st.selectbox("Escolha uma característica", [""] + filtered_characteristics)
        else:
            st.info("Nenhuma característica encontrada")
            characteristic = ""
        if st.button("Buscar jogos com essa característica"):
            field, value = characteristic.split(": ", 1)
            value = value.strip()
            if field == "mechanic":
                ids = df_games.index[df_games["mechanic"].str.contains(value, na=False)].tolist()
            elif field == "theme":
                ids = df_games.index[df_games["category"].str.contains(value, na=False)].tolist()
            elif field == "subdomain":
                ids = df_games.index[df_games["domain"].str.contains(value, na=False)].tolist()
            elif field == "family":
                ids = df_games.index[df_games["family"].str.contains(value, na=False)].tolist()
            elif field == "designer":
                ids = df_games.index[df_games["designer"].str.contains(value, na=False)].tolist()
            elif field == "artist":
                ids = df_games.index[df_games["artist"].str.contains(value, na=False)].tolist()
            
            st.session_state.characteristic_ids = ids
        
        # Mostrar segmented_control se há resultados
        if st.session_state.characteristic_ids:
            st.session_state.chosen_id = st.segmented_control(
                label=f"Navegue pelos {len(st.session_state.characteristic_ids)} jogos encontrados:",
                options=st.session_state.characteristic_ids,
                key="found_games",
                format_func=lambda x: f"{x} {df_games.at[x, 'name']} ({df_games.at[x, 'year']}) - rank {df_games.at[x, 'rank_global']}" if x in df_games.index else str(x)
            )
                

    # -- MENU 5: AKINATOR --
    elif page == "Akinator":
        run_akinator(df_games, all_characteristics)
    
    # -- MENU 6: PAINEL DE DADOS --
    elif page == "Painel de dados":
        st.subheader("Filtrar jogos")
        
        
        
        # Filtros
        with st.expander("Filtros numéricos", expanded=False):
            min_year, max_year, min_players, max_players, min_weight, max_weight = None, None, None, None, None, None
            if st.checkbox("Filtro mínimo ano", key="check_min_year"):
                min_year = st.slider("Ano mínimo:", int(df_games["year"].min()), int(df_games["year"].max()), int(df_games["year"].min()), key="filter_min_year")
            if st.checkbox("Filtro máximo ano", key="check_max_year"):
                max_year = st.slider("Ano máximo:", int(df_games["year"].min()), int(df_games["year"].max()), int(df_games["year"].max()), key="filter_max_year")
            if st.checkbox("Filtro mínimo jogadores", key="check_min_players"):
                min_players = st.slider("Mínimo de jogadores:", 1, int(df_games["minplayers"].max()), 1, key="filter_min_players")
            if st.checkbox("Filtro máximo jogadores", key="check_max_players"):
                max_players = st.slider("Máximo de jogadores:", 1, int(df_games["maxplayers"].max()), int(df_games["maxplayers"].max()), key="filter_max_players")
            if st.checkbox("Filtro mínimo peso", key="check_min_weight"):
                min_weight = st.slider("Peso mínimo:", 0.0, 5.0, 0.0, step=0.1, key="filter_min_weight")
            if st.checkbox("Filtro máximo peso", key="check_max_weight"):
                max_weight = st.slider("Peso máximo:", 0.0, 5.0, 5.0, step=0.1, key="filter_max_weight")
            
        
        # Filtros de características
        col1, col2 = st.columns(2)
        
        with col1:
            selected_mechanics = st.multiselect(
                "Mecânicas:",
                list_mechs[0],
                key="selected_mechanics"
            )
            selected_designers = st.multiselect(
                "Designers:",
                [d for d in df_games["designer"].str.split(",").explode().unique() if pd.notna(d)],
                key="selected_designers"
            )
        
        with col2:
            selected_themes = st.multiselect(
                "Temas:",
                list_themes[0],
                key="selected_themes"
            )
            selected_artists = st.multiselect(
                "Artistas:",
                [a for a in df_games["artist"].str.split(",").explode().unique() if pd.notna(a)],
                key="selected_artists"
            )
        
        # Aplicar filtros
        df_filtered = df_games.copy()
        
        # Filtros numéricos
        if min_year:
            df_filtered = df_filtered[df_filtered["year"] >= min_year]
        if max_year:
            df_filtered = df_filtered[df_filtered["year"] <= max_year]
        if min_players:
            df_filtered = df_filtered[df_filtered["minplayers"] >= min_players]
        if max_players:
            df_filtered = df_filtered[df_filtered["maxplayers"] <= max_players]
        if min_weight:
            df_filtered = df_filtered[df_filtered["average_weight"] >= min_weight]
        if max_weight:
            df_filtered = df_filtered[df_filtered["average_weight"] <= max_weight]

        
        # Filtros de características
        if selected_mechanics:
            for mech in selected_mechanics:
                df_filtered = df_filtered[df_filtered["mechanic"].str.contains(mech, na=False)]
        
        if selected_themes:
            for theme in selected_themes:
                df_filtered = df_filtered[df_filtered["category"].str.contains(theme, na=False)]
        
        if selected_designers:
            for designer in selected_designers:
                df_filtered = df_filtered[df_filtered["designer"].str.contains(designer, na=False)]
        
        if selected_artists:
            for artist in selected_artists:
                df_filtered = df_filtered[df_filtered["artist"].str.contains(artist, na=False)]
        
        
        #gráfico de barras por ano
        st.subheader("Distribuição por ano")
        st.bar_chart(df_filtered["year"].value_counts().sort_index(), use_container_width=True)
        
        #gráfico por mecânica
        st.subheader("Quantidade por mecânica")
        control_top_mechanics = st.slider("Número de mecânicas a exibir:", 1, 50, 20, key="slider_top_mechanics")
        mech_counts = df_filtered["mechanic"].str.split(",").explode().value_counts()        
        st.bar_chart(mech_counts.head(control_top_mechanics), use_container_width=True, horizontal=True, sort=False)
        
        #gráfico por tema
        st.subheader("Quantidade por tema")
        control_top_themes = st.slider("Número de temas a exibir:", 1, 50, 20, key="slider_top_themes")
        theme_counts = df_filtered["category"].str.split(",").explode().value_counts()
        st.bar_chart(theme_counts.head(control_top_themes), use_container_width=True, horizontal=True, sort=False)
        
        #gráfico por artista
        st.subheader("Quantidade por artista")
        control_top_artists = st.slider("Número de artistas a exibir:", 1, 50, 20, key="slider_top_artists")
        artist_counts = df_filtered["artist"].str.split(",").explode().value_counts()
        st.bar_chart(artist_counts.head(control_top_artists), use_container_width=True, horizontal=True, sort=False)


        # Seleção de colunas a exibir
        columns_to_show = st.multiselect(
            "Selecione as colunas a exibir:",
            df_filtered.columns.tolist(),
            default=["name", "year", "rank_global", "minplayers", "maxplayers", "average_weight"],
            key="columns_display"
        )
        
        
        st.subheader("Jogos encontrados")
        st.write(f"**Total de jogos encontrados:** {len(df_filtered)}")
        if columns_to_show:
            st.dataframe(df_filtered[columns_to_show].sort_values("rank_global"), use_container_width=True)

        
    if st.session_state.chosen_id:
        display_game_info(st.session_state.chosen_id, df_games, list_mechs, list_themes)

    
        
    
    
if __name__ == "__main__":
    main()
