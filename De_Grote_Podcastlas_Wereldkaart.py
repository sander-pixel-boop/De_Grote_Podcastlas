import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    # Inladen van de CSV
    df = pd.read_csv("data.csv")
    # Verwijder eventuele spaties rondom kolomnamen
    df.columns = df.columns.str.strip()
    
    # Hover-tekst configureren: begin met een hoofdletter
    if "Aflevering" in df.columns:
        df["Hover_Info"] = df["Aflevering"].str.replace("Afl.", "Aflevering", case=False).str.capitalize()
    return df

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")
st.title("📍 De Grote Podcastlas Explorer")

df = load_data()

# Check of de essentiële kolommen aanwezig zijn
required_columns = ["Weergave_Naam", "Categorie", "Aflevering", "Kaartweergave"]
missing = [col for col in required_columns if col not in df.columns]

if missing:
    st.error(f"De volgende kolommen ontbreken in data.csv: {', '.join(missing)}")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    weergave = st.radio("Kies kaartweergave:", ["2D (Plat)", "3D (Wereldbol)"], horizontal=True)
with col2:
    categorie_opties = ["Alles"] + list(df["Categorie"].unique())
    gekozen_categorie = st.selectbox("Kies categorie:", categorie_opties)

# Filter data op basis van categorie
filtered_df = df.copy()
if gekozen_categorie != "Alles":
    filtered_df = filtered_df[filtered_df["Categorie"] == gekozen_categorie]

# Tabel met selectie-mogelijkheid
st.subheader("Selecteer een aflevering om te highlighten")
df_display = filtered_df[["Weergave_Naam", "Categorie", "Aflevering"]].copy()
df_display = df_display.rename(columns={"Weergave_Naam": "Naam"})
df_display.index = range(1, len(df_display) + 1)

# Gebruik st.dataframe met selection_mode (beschikbaar in recente Streamlit versies)
event = st.dataframe(
    df_display, 
    use_container_width=True, 
    on_select="rerun", 
    selection_mode="single_row"
)

# Bepaal welk item geselecteerd is
selected_name = None
if event and hasattr(event, 'selection') and len(event.selection.get("rows", [])) > 0:
    selected_row_index = event.selection["rows"][0]
    selected_name = df_display.iloc[selected_row_index]["Naam"]

# Kaartconfiguratie
gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"

# Markeer highlight (2 voor geselecteerd, 1 voor standaard)
filtered_df["Highlight"] = filtered_df["Weergave_Naam"].apply(lambda x: 2 if x == selected_name else 1)

landen_df = filtered_df[filtered_df["Kaartweergave"] == "Land"]
steden_df = filtered_df[filtered_df["Kaartweergave"] == "Punt"].copy()

# Teken de landen
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

# Teken de punten
if not steden_df.empty:
    if 'Latitude' in steden_df.columns and 'Longitude' in steden_df.columns:
        steden_df = steden_df.dropna(subset=['Latitude', 'Longitude'])
        steden_df["Point_Color"] = steden_df["Weergave_Naam"].apply(lambda x: "yellow" if x == selected_name else "red")
        steden_df["Point_Size"] = steden_df["Weergave_Naam"].apply(lambda x: 15 if x == selected_name else 8)
        
        fig.add_scattergeo(
            lon=steden_df["Longitude"],
            lat=steden_df["Latitude"],
            hoverinfo="text",
            text="<b>" + steden_df["Weergave_Naam"] + "</b><br>" + steden_df["Hover_Info"],
            marker=dict(
                size=steden_df["Point_Size"], 
                color=steden_df["Point_Color"], 
                line=dict(width=1, color="black")
            )
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
