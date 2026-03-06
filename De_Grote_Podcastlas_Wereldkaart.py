import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Cache is verwijderd zodat je áltijd de nieuwste data.csv inlaadt
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip().str.replace('^[^a-zA-Z0-9]+', '', regex=True)
    if "Weergave_Naam" not in df.columns:
        df.rename(columns={df.columns[0]: "Weergave_Naam"}, inplace=True)
    if "Aflevering" in df.columns:
        df["Hover_Info"] = df["Aflevering"].str.replace("Afl.", "Aflevering", case=False).str.capitalize()
    return df

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

df = load_data()

col1, col2 = st.columns(2)
with col1:
    weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
with col2:
    categorie_opties = ["Alles"] + list(df["Categorie"].unique())
    gekozen_categorie = st.selectbox("Kies categorie:", categorie_opties)

filtered_df = df.copy()
if gekozen_categorie != "Alles":
    filtered_df = filtered_df[filtered_df["Categorie"] == gekozen_categorie]

df_display = filtered_df[["Weergave_Naam", "Categorie", "Aflevering"]].copy()
df_display = df_display.rename(columns={"Weergave_Naam": "Naam"})
df_display.index = range(1, len(df_display) + 1)

st.subheader("Klik op een rij in de tabel om de locatie te markeren")

# Tabel configuratie
gb = GridOptionsBuilder.from_dataframe(df_display)
gb.configure_selection(selection_mode="single", use_checkbox=False)
gridOptions = gb.build()

grid_response = AgGrid(
    df_display,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    theme='streamlit'
)

# Uitlezen van de selectie
selected_name = None
if grid_response.get('selected_rows'):
    sel = grid_response['selected_rows']
    if isinstance(sel, pd.DataFrame) and not sel.empty:
        selected_name = sel.iloc[0]["Naam"]
    elif isinstance(sel, list) and len(sel) > 0:
        selected_name = sel[0]["Naam"]

# Basis kaart setup
gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"
filtered_df["Highlight"] = filtered_df["Weergave_Naam"].apply(lambda x: 2 if x == selected_name else 1)

landen_df = filtered_df[filtered_df["Kaartweergave"] == "Land"]
steden_df = filtered_df[filtered_df["Kaartweergave"] == "Punt"].copy()

fig = px.choropleth(
    landen_df,
    locations="Locatie",
    locationmode="country names",
    color="Highlight",
    hover_name="Weergave_Naam",
    custom_data=["Hover_Info"],
    projection=gekozen_projectie, 
    color_continuous_scale=[[0, "green"], [0.5, "green"], [1, "yellow"]],
)

fig.update_traces(hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<extra></extra>")

if not steden_df.empty:
    steden_df["Point_Color"] = steden_df["Weergave_Naam"].apply(lambda x: "yellow" if x == selected_name else "red")
    steden_df["Point_Size"] = steden_df["Weergave_Naam"].apply(lambda x: 15 if x == selected_name else 8)
    
    fig.add_scattergeo(
        lon=steden_df["Longitude"],
        lat=steden_df["Latitude"],
        hoverinfo="text",
        text="<b>" + steden_df["Weergave_Naam"] + "</b><br>" + steden_df["Hover_Info"],
        marker=dict(size=steden_df["Point_Size"], color=steden_df["Point_Color"], line=dict(width=1, color="black"))
    )

fig.update_layout(coloraxis_showscale=False, margin={"r":0,"t":0,"l":0,"b":0})

# Logica om de kaart te roteren en in te zoomen
if selected_name:
    sel_data = df[df["Weergave_Naam"] == selected_name]
    if not sel_data.empty:
        lat = sel_data.iloc[0]["Latitude"]
        lon = sel_data.iloc[0]["Longitude"]
        
        # Controle of er geldige coördinaten zijn
        if pd.notna(lat) and pd.notna(lon):
            lat, lon = float(lat), float(lon)
            if weergave == "3D (Wereldbol)":
                fig.update_geos(projection_rotation=dict(lon=lon, lat=lat, roll=0))
            else:
                fig.update_geos(center=dict(lon=lon, lat=lat), projection_scale=4)
        else:
            st.warning(f"Geen coördinaten in data.csv gevonden voor {selected_name}.")

st.plotly_chart(fig, use_container_width=True)
