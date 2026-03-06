import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import base64
import os

if 'selected_name' not in st.session_state:
    st.session_state.selected_name = None

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip().str.replace('^[^a-zA-Z0-9]+', '', regex=True)
    if "Weergave_Naam" not in df.columns:
        df.rename(columns={df.columns[0]: "Weergave_Naam"}, inplace=True)
    if "Aflevering" in df.columns:
        df["Hover_Info"] = df["Aflevering"].str.replace("Afl.", "Aflevering", case=False).str.capitalize()
    if "Link" not in df.columns:
        df["Link"] = ""
    return df

@st.cache_data
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

st.set_page_config(page_title="De Grote Podcastlas", layout="wide")

logo_base64 = get_base64_image("logodegrotepodcastlas.png")
img_src = f"data:image/png;base64,{logo_base64}" if logo_base64 else ""

titel_html = f"""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <a href="https://www.grotepodcastlas.nl/" target="_blank">
        <img src="{img_src}" 
             alt="Logo De Grote Podcastlas" 
             style="height: 60px; margin-right: 20px; border-radius: 50%;">
    </a>
    <h1 style="margin: 0;">De Grote Podcastlas Explorer</h1>
</div>
"""
st.markdown(titel_html, unsafe_allow_html=True)

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

gekozen_projectie = "orthographic" if weergave == "3D (Wereldbol)" else "natural earth"
filtered_df["Highlight"] = filtered_df["Weergave_Naam"].apply(lambda x: 2 if x == st.session_state.selected_name else 1)

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
    steden_df["Point_Color"] = steden_df["Weergave_Naam"].apply(lambda x: "yellow" if x == st.session_state.selected_name else "red")
    steden_df["Point_Size"] = steden_df["Weergave_Naam"].apply(lambda x: 15 if x == st.session_state.selected_name else 8)
    
    fig.add_scattergeo(
        lon=steden_df["Longitude"],
        lat=steden_df["Latitude"],
        hoverinfo="text",
        text="<b>" + steden_df["Weergave_Naam"] + "</b><br>" + steden_df["Hover_Info"],
        marker=dict(size=steden_df["Point_Size"], color=steden_df["Point_Color"], line=dict(width=1, color="black"))
    )

fig.update_layout(coloraxis_showscale=False, margin={"r":0,"t":0,"l":0,"b":0}, height=750)

if st.session_state.selected_name:
    sel_data = df[df["Weergave_Naam"] == st.session_state.selected_name]
    if not sel_data.empty:
        lat = sel_data.iloc[0]["Latitude"]
        lon = sel_data.iloc[0]["Longitude"]
        
        if pd.notna(lat) and pd.notna(lon):
            lat, lon = float(lat), float(lon)
            if weergave == "3D (Wereldbol)":
                fig.update_geos(projection_rotation=dict(lon=lon, lat=lat, roll=0))
            else:
                fig.update_geos(center=dict(lon=lon, lat=lat), projection_scale=5)

map_selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")

if map_selection and "selection" in map_selection and map_selection["selection"].get("points"):
    point_data = map_selection["selection"]["points"][0]
    clicked_text = point_data.get("hovertext") or point_data.get("text")
    
    if clicked_text:
        if "<b>" in clicked_text:
            clicked_name_clean = clicked_text.split("</b>")[0].replace("<b>", "")
        else:
            clicked_name_clean = clicked_text

        if st.session_state.selected_name != clicked_name_clean:
            st.session_state.selected_name = clicked_name_clean
            st.rerun()

df_display = filtered_df[["Weergave_Naam", "Categorie", "Aflevering", "Link"]].copy()
df_display = df_display.rename(columns={"Weergave_Naam": "Naam"})

if st.session_state.selected_name and st.session_state.selected_name in df_display["Naam"].values:
    selected_row = df_display[df_display["Naam"] == st.session_state.selected_name]
    other_rows = df_display[df_display["Naam"] != st.session_state.selected_name]
    df_display = pd.concat([selected_row, other_rows])

df_display.index = range(1, len(df_display) + 1)

gb = GridOptionsBuilder.from_dataframe(df_display)

gb.configure_column("Link", headerName="Website", cellRenderer=JsCode('''
    function(params) {
        if (params.value && params.value.trim() !== "") {
            return '<a href="' + params.value + '" target="_blank" style="text-decoration: none; font-weight: bold; color: #1f77b4;">🎧 Luisteren</a>';
        }
        return '';
    }
'''))

if st.session_state.selected_name in df_display["Naam"].values:
    gb.configure_selection(selection_mode="single", use_checkbox=False, pre_selected_rows=[0])
else:
    gb.configure_selection(selection_mode="single", use_checkbox=False)

gridOptions = gb.build()

grid_response = AgGrid(
    df_display,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    theme='streamlit'
)

if grid_response.get('selected_rows'):
    sel = grid_response['selected_rows']
    clicked_table_name = None
    
    if isinstance(sel, pd.DataFrame) and not sel.empty:
        clicked_table_name = sel.iloc[0]["Naam"]
    elif isinstance(sel, list) and len(sel) > 0:
        clicked_table_name = sel[0]["Naam"]

    if clicked_table_name and st.session_state.selected_name != clicked_table_name:
        st.session_state.selected_name = clicked_table_name
        st.rerun()
