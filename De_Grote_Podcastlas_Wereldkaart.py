import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests

@st.cache_data
def load_data():
    return pd.DataFrame({
        "Locatie": ["Albania", "Rome", "Bhutan", "Antwerp", "Uzbekistan"], 
        "Type": ["Land", "Stad", "Land", "Stad", "Land"],
        "Aflevering": ["Afl. 1", "Afl. 5", "Afl. 12", "Afl. 18", "Afl. 22"],
        "Waarde": [1, 1, 1, 1, 1] 
    })

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

df = load_data()
landen_df = df[df["Type"] == "Land"]
steden_df = df[df["Type"] == "Stad"].copy()

steden_df["Coordinates"] = steden_df["Locatie"].apply(get_coordinates)
steden_df[["Latitude", "Longitude"]] = pd.DataFrame(steden_df["Coordinates"].tolist(), index=steden_df.index)

m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
folium.Choropleth(
    geo_data=geojson_url,
    data=landen_df,
    columns=["Locatie", "Waarde"],
    key_on="feature.properties.name",
    fill_color="YlGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Besproken"
).add_to(m)

for index, row in steden_df.iterrows():
    if pd.notna(row["Latitude"]):
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            popup=f"<b>{row['Locatie']}</b><br>{row['Aflevering']}",
            tooltip=row["Locatie"],
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.9
        ).add_to(m)

st_folium(m, width=1000, height=600)
st.dataframe(df.drop(columns=["Waarde", "Coordinates"], errors='ignore'))
