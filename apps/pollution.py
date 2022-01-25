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
from bs4 import BeautifulSoup

def app():
    url = 'https://www.airparif.asso.fr/'
    navigator = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)'
    response = requests.get(url, headers={'User-Agent': navigator, "Accept-Language": "fr-FR,fr;q=0.9"})
    soup = BeautifulSoup(response.text, 'html.parser')
    today = []
    tomorrow = []
    for z in soup.find_all("div", class_="bg-light equal-heights shadow-lg-dark"):
        today.append(z.find('div', class_='row dataviz today open').find('div',
                                                                         class_='global-indice-label position-relative').find(
            'h3').string)
    for y in soup.find_all("div", class_="bg-light equal-heights shadow-lg-dark"):
        tomorrow.append(y.find('div', class_="row dataviz tomorrow").find('div',
                                                                          class_="global-indice-label position-relative").find(
            "h3").string)
    tomorrow  # (la mise à jour de la prévision pour demain se fait à 11h30)
    # on zip les deux listes en un dict
    liste_zip = zip(today, tomorrow)
    liste_dict = dict(liste_zip)
    liste_dict
    # on crée le Dataframe
    df_critair = pd.DataFrame.from_dict(liste_dict, orient='index')
    df_critair.reset_index(inplace=True)
    df_critair.rename(columns={'index': "Qualité_Air_Aujourd'hui", 0: 'Qualité_Air_Demain'}, inplace=True)
    df_critair["Qualité_Air_Aujourd'hui"] = df_critair["Qualité_Air_Aujourd'hui"].apply(lambda x: 'Bonne' if x == 'low'
    else 'Moyenne' if x ==                      'average'
    else 'Dégradée' if x == 'degrade'
    else 'Mauvaise' if x == 'high'
    else 'Très mauvaise' if x == 'very-high'
    else 'Inconnue' if x == '-'
    else 'Extrêmement mauvaise')
    df_critair["Qualité_Air_Demain"] = df_critair["Qualité_Air_Demain"].apply(lambda x: 'Bonne' if x == 'low'
    else 'Moyenne' if x == 'average'
    else 'Dégradée' if x == 'degrade'
    else st.metric(label="demain",value='mauvaise') if x == 'high'
    else 'Très mauvaise' if x == 'very-high'
    else 'Inconnue' if x == '-'
    else 'Extrêmement mauvaise')

    #st.metric(label="demain",value='mauvaise')
    #st.write(df_critair)

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
    df3.rename(columns={"fields.code_insee_commune": "c_arinsee", "fields.statut_pdc": "bornes recharge disponibles"},
               inplace=True)
    df3["c_arinsee"] = df3["c_arinsee"].astype(int)
    dfgeoA = gpd.read_file("arrondissements.geojson")
    dfgeoA = pd.merge(dfgeoA, df3, on="c_arinsee")
    dfgeoA.rename(columns={"l_ar": "Arrondissement"}, inplace=True)
    lieu = adresse("10 rue du Louvre 75001".capitalize())
    carte_lieu = folium.Map(location=lieu, zoom_start=12)
    cp = folium.Choropleth(
        geo_data=dfgeoA,
        name="geometry",
        data=dfgeoA,
        columns=["c_arinsee", "bornes recharge disponibles"],
        key_on='feature.properties.c_arinsee',
        fill_color='YlGn',
        fill_opacity=0.6,
        line_opacity=0.6,
        legend_name=("Nombre de bornes recharges dispos par arrondissements"),
        highlight=True,
        bins=4).add_to(carte_lieu)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    folium.LayerControl('topright', collapsed=True).add_to(carte_lieu)
    folium.GeoJsonTooltip(['Arrondissement', 'bornes recharge disponibles']).add_to(cp.geojson)
    folium_static(carte_lieu)