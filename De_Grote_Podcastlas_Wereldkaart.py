import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

@st.cache_data
def load_data():
    return pd.read_csv("data.csv")

@st.cache_data
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="podcastlas_app")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

# Keuze voor 2D of 3D
weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"

df = load_data()
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
