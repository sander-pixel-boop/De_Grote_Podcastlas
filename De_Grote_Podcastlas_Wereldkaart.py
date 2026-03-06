import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests

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

df = load_data()
landen_df = df[df["Type"] == "Land"]
steden_df = df[df["Type"] == "Stad"].copy()

steden_df["Coordinates"] = steden_df["Locatie"].apply(get_coordinates)
steden_df[["Latitude", "Longitude"]] = pd.DataFrame(steden_df["Coordinates"].tolist(), index=steden_df.index)

# Aangepast: Gebruik Esri satellietbeelden voor een realistische weergave
m = folium.Map(
    location=[20, 0], 
    zoom_start=2, 
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
)

geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
folium.Choropleth(
    geo_data=geojson_url,
    data=landen_df,
    columns=["Locatie", "Waarde"],
    key_on="feature.properties.name",
    fill_color="YlGn",
    fill_opacity=0.5, # Iets transparanter gemaakt zodat de satellietkaart er beter doorheen schijnt
    line_opacity=0.5,
    legend_name="Besproken"
).add_to(m)

for index, row in steden_df.iterrows():
    if pd.notna(row["Latitude"]):
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            popup=f"<b>{row['Weergave_Naam']}</b><br>{row['Aflevering']}",
            tooltip=row['Weergave_Naam'],
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.9
        ).add_to(m)

st_folium(m, width=1000, height=600)
st.dataframe(df[["Weergave_Naam", "Type", "Aflevering"]])
