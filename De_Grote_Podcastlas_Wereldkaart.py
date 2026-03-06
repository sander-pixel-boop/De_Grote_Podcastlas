import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

df = load_data()

col1, col2 = st.columns(2)
with col1:
    weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
with col2:
    categorie_opties = ["Alles"] + list(df["Categorie"].unique())
    gekozen_categorie = st.selectbox("Kies categorie:", categorie_opties)

gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"

if gekozen_categorie != "Alles":
    df = df[df["Categorie"] == gekozen_categorie]

landen_df = df[df["Kaartweergave"] == "Land"]
steden_df = df[df["Kaartweergave"] == "Punt"].copy()

fig = px.choropleth(
    landen_df,
    locations="Locatie",
    locationmode="country names",
    color="Waarde",
    hover_name="Weergave_Naam",
    hover_data={"Waarde": False, "Locatie": False, "Categorie": True, "Aflevering": True},
    projection=gekozen_projectie, 
    color_continuous_scale="greens"
)

if not steden_df.empty:
    if 'Latitude' in steden_df.columns and 'Longitude' in steden_df.columns:
        steden_df = steden_df.dropna(subset=['Latitude', 'Longitude'])
        fig.add_scattergeo(
            lon=steden_df["Longitude"],
            lat=steden_df["Latitude"],
            hoverinfo="text",
            text=steden_df["Weergave_Naam"] + "<br>" + steden_df["Aflevering"],
            marker=dict(size=8, color="red", line=dict(width=1, color="darkred"))
        )
    else:
        st.error("Let op: De kolommen 'Latitude' en 'Longitude' ontbreken in je data.csv bestand.")

fig.update_layout(
    coloraxis_showscale=False,
    margin={"r":0,"t":0,"l":0,"b":0},
    geo=dict(
        showcoastlines=True, coastlinecolor="Black",
        showland=True, landcolor="lightgrey",
        showocean=True, oceancolor="azure"
    )
)

st.plotly_chart(fig, use_container_width=True)
st.dataframe(df[["Weergave_Naam", "Categorie", "Aflevering"]])
