import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

@st.cache_data
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="podcastlas_app")
    try:
        time.sleep(0.5) # Voorkomt blokkades door de Nominatim API
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

# Filters
col1, col2 = st.columns(2)
with col1:
    weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
with col2:
    categorie = st.radio("Kies categorie:", ["Alles", "Reguliere afleveringen", "Specials & Overig"], horizontal=True)

gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"

df = load_data()

# Data filteren op basis van selectie
if categorie == "Reguliere afleveringen":
    df = df[df["Aflevering"].str.contains("Afl.", na=False)]
elif categorie == "Specials & Overig":
    df = df[df["Aflevering"].str.contains("#", na=False)]

landen_df = df[df["Type"] == "Land"]
steden_df = df[df["Type"] == "Stad"].copy()

steden_df["Coordinates"] = steden_df["Locatie"].apply(get_coordinates)
steden_df[["Latitude", "Longitude"]] = pd.DataFrame(steden_df["Coordinates"].tolist(), index=steden_df.index)

fig = px.choropleth(
    landen_df,
    locations="Locatie",
    locationmode="country names",
    color="Waarde",
    hover_name="Weergave_Naam",
    hover_data={"Waarde": False, "Locatie": False, "Aflevering": True},
    projection=gekozen_projectie, 
    color_continuous_scale="greens"
)

if not steden_df.empty:
    fig.add_scattergeo(
        lon=steden_df["Longitude"],
        lat=steden_df["Latitude"],
        hoverinfo="text",
        text=steden_df["Weergave_Naam"] + "<br>" + steden_df["Aflevering"],
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
st.dataframe(df[["Weergave_Naam", "Type", "Aflevering"]])
