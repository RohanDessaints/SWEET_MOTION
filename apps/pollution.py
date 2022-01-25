import pandas as pd
import re
import numpy as np
import json
import requests
import folium
import streamlit as st
from streamlit_folium import folium_static
import folium.plugins as plugins
import matplotlib.pyplot as plt
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

def app():
    def clean_data_belib():
        # création du DF dispo en temps réel
        link = "https://parisdata.opendatasoft.com/api/records/1.0/search/?dataset=belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel&q=&rows=10000&facet=statut_pdc&facet=last_updated&facet=arrondissement"
        r = requests.get(link)
        data = r.json()
        dispo = pd.json_normalize(data["records"])
        return dispo

    df3 = clean_data_belib()

    def adresse(adresse_postale):
        adresse_postale = adresse_postale.replace(" ", "+")
        link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
        r = requests.get(link)
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        my_tuple = coords[1], coords[0]
        return (list(my_tuple))

    df3 = df3[df3["fields.statut_pdc"] == "Disponible"].groupby(by="fields.code_insee_commune").count()
    df3.reset_index(inplace=True)
    df3.drop(columns=["fields.id_pdc"], inplace=True)
    df3.rename(columns={"fields.code_insee_commune": "c_arinsee", "fields.statut_pdc": "bornes_dispo"}, inplace=True)
    df3["c_arinsee"] = df3["c_arinsee"].astype(int)
    dfgeoA = gpd.read_file("arrondissements.geojson")
    dfgeoA.keys()
    dfgeoA = pd.merge(dfgeoA, df3, on="c_arinsee")
    dfgeoA
    lieu = adresse("10 rue du Louvre 75001".capitalize())
    carte_lieu = folium.Map(location=lieu, zoom_start=12)
    folium.Choropleth(
        geo_data=dfgeoA,
        name="geometry",
        data=dfgeoA,
        columns=["c_arinsee", "bornes_dispo"],
        key_on='feature.properties.c_arinsee',
        fill_color='RdBu',
        fill_opacity=0.6,
        line_opacity=0.6,
        legend_name="Nombre de bornes recharges dispos par arrondissements").add_to(carte_lieu)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    folium.LayerControl('topright', collapsed=True).add_to(carte_lieu)
    folium_static(carte_lieu)