import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip()
    
    # Zorg dat de weergave met een hoofdletter begint (bijv. "Wereldstad #14")
    df["Hover_Info"] = df["Aflevering"].str.capitalize()
    return df

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

df = load_data()

col1, col2 = st.columns(2)
with col1:
    weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
with col2:
    if "Categorie" in df.columns:
        categorie_opties = ["Alles"] + list(df["Categorie"].unique())
        gekozen_categorie = st.selectbox("Kies categorie:", categorie_opties)
    else:
        gekozen_categorie = "Alles"

gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"

if gekozen_categorie != "Alles" and "Categorie" in df.columns:
    df = df[df["Categorie"] == gekozen_categorie]

if "Kaartweergave" in df.columns:
    landen_df = df[df["Kaartweergave"] == "Land"]
    steden_df = df[df["Kaartweergave"] == "Punt"].copy()
else:
    landen_df = df
    steden_df = pd.DataFrame()

# Kaart voor de landen (vlakken)
fig = px.choropleth(
    landen_df,
    locations="Locatie",
    locationmode="country names",
    color="Waarde",
    hover_name="Weergave_Naam",
    custom_data=["Hover_Info"],
    projection=gekozen_projectie, 
    color_continuous_scale="greens"
)

# Hover instellingen voor landen
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<extra></extra>"
)

# Toevoegen van de steden/punten
if not steden_df.empty:
    if 'Latitude' in steden_df.columns and 'Longitude' in steden_df.columns:
        steden_df = steden_df.dropna(subset=['Latitude', 'Longitude'])
        fig.add_scattergeo(
            lon=steden_df["Longitude"],
            lat=steden_df["Latitude"],
            hoverinfo="text",
            text="<b>" + steden_df["Weergave_Naam"] + "</b><br>" + steden_df["Hover_Info"],
            marker=dict(size=8, color="red", line=dict(width=1, color="darkred"))
        )

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
