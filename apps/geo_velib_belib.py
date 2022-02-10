import re
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.map import Layer
from folium import plugins
import numpy as np
import pandas as pd
import requests
from geopy import distance

def app():

    ### PARTI VELIB

    def retrieve_data():
        link = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json'
        r = requests.get(link)
        data = r.json()
        df = pd.json_normalize(data['data'], record_path='stations')
        return df

    velib = pd.DataFrame(retrieve_data())

    def retrieve_data2():
        req = requests.get(
            'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json')
        data = req.json()
        df2 = pd.json_normalize(data['data'], record_path='stations')
        return df2

    velib_bornes = pd.DataFrame(retrieve_data2())

    velib_tot = pd.merge(velib, velib_bornes,
                         on='stationCode')

    velib_tot['mechanical'] = velib_tot['num_bikes_available_types'].apply(lambda x: x[0]['mechanical'])
    velib_tot['e_bike'] = velib_tot['num_bikes_available_types'].apply(lambda x: x[1]['ebike'])

    velib_tot['capacity'] = velib_tot['capacity'].astype(str)

    # Fonction de géolocalisation
    def geoloc(adresse_postale):
        adresse_postale = adresse_postale.replace(" ", "+")
        link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
        r = requests.get(link)
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        my_tuple = coords[1], coords[0]
        return (list(my_tuple))

    # créationdes icones de couleur pour folium
    # je mets orange si dispo <=5, arbitraire et changeable
    velib_tot["dispo"] = velib_tot["mechanical"] + velib_tot['e_bike']

    status = []
    for i, col in velib_tot.iterrows():
        if col["dispo"] == 0:
            status.append("pas_dispo")
        elif col["dispo"] <= 5:
            status.append("moyen")
        elif col["dispo"] > 5:
            status.append("dispo")
    velib_tot["status"] = status  # création colonne status

    # création dict pour map
    statuses = ["dispo", "moyen", "pas_dispo"]  # status dispo vélib
    colors = ["green", "orange", "red"]  # couleurs des icones
    color_dict = dict(zip(statuses, colors))  # dict
    velib_tot["icon_color"] = velib_tot["status"].map(color_dict)  # création couleur par taux de dispo




    # GEOLOCALISATION
    st.title("Je book mon sweet motion", anchor=None)
    st.title("")
    st.header("Un Vélib'")
    adresse = st.text_input('Adresse', '44 rue Alphonse Penaud 75020')
    st.write('Votre adresse actuelle est', adresse)

    col1, col2 = st.columns([3, 1])
    # affichage de la position
    lieu = geoloc(adresse)
    carte_lieu = folium.Map(location=lieu, zoom_start=16)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    marker2 = folium.Marker(location=lieu, tooltip='Vous êtes-ici',
                            icon=folium.Icon(color="blue", icon="male", prefix='fa'))
    marker2.add_to(carte_lieu)

    distances = []  # récup pr après
    for i, col in velib_tot.iterrows():
        distances.append(distance.distance((lieu[0], lieu[1]), (col["lat"], col["lon"])).m)
        label = 'ebike: {}, bike: {}'.format(col["e_bike"], col["mechanical"])
        location = [col["lat"], col["lon"]]
        marker = folium.Marker(location=location, tooltip=col["name"], popup=label,
                               icon=folium.Icon(color=col["icon_color"], icon="bicycle", prefix='fa'))
        marker.add_to(carte_lieu)
    with col1:
        folium_static(carte_lieu)  # affichage  carte
    with col2:
        st.subheader("stations proches")
        velib_tot["distances(m)"] = distances
        velib_tot["distances(m)"] = velib_tot["distances(m)"].apply(lambda x: round(x))
        dispo_proche = velib_tot[velib_tot["dispo"] != 0]
        dispo_proche = dispo_proche[["name", "dispo", "distances(m)"]].groupby(by="name").agg(
            {"dispo": sum, "distances(m)": np.mean}) \
            .sort_values(by="distances(m)", ascending=True) \
            .reset_index() \
            .rename(columns={"name": "station", "dispo": "nombre dispo", "distances(m)": "distance(m)"})
        dispo_proche["distance(m)"] = dispo_proche["distance(m)"].apply(lambda x: round(x))
        for i in range(3):
            st.write("Adresse :\n", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 0])
            st.write("Vélib dispo :", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 1])
            st.write("Distance (m):", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 2])


    ### BELIB

    # getting the belib data from API+CSV
    def clean_data_belib():
        # création du DF dispo en temps réel
        link = "https://parisdata.opendatasoft.com/api/records/1.0/search/?dataset=belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel&q=&rows=10000&facet=statut_pdc&facet=last_updated&facet=arrondissement"
        r = requests.get(link)
        data = r.json()
        dispo = pd.json_normalize(data["records"])

        dispo_cols_keep = ['fields.statut_pdc', 'fields.id_pdc']
        dispo = dispo[dispo_cols_keep]

        # création du DF stations statiques
        stations = pd.read_csv("belib-points-de-recharge-pour-vehicules-electriques-donnees-statiques.csv", sep=";")
        stations_cols_keep = ['ID PDC local', 'Statut du Point de charge', 'Nombre point de recharge',
                              'Adresse station', 'Coordonnées géographiques', 'Paiement CB', 'Accessibilité PMR',
                              'Stationnement 2 roues', 'Puissance max KW', 'Prise type EF', 'Prise type 2',
                              'Prise type Combo CCS', 'Prise type Chademo', 'Prise type Autre', 'Prise type 3']
        stations = stations[stations_cols_keep]
        stations = stations[stations["Statut du Point de charge"] == "En service"]

        to_translate = ['Paiement CB', 'Stationnement 2 roues', 'Prise type EF', 'Prise type 2', 'Prise type Combo CCS',
                        'Prise type Chademo', 'Prise type Autre', 'Prise type 3']
        for col in to_translate:
            stations[col] = stations[col].apply(lambda x: "non" if x == False else "oui")

        # merge des dataframe
        belib = stations.merge(dispo, how="left", left_on="ID PDC local", right_on="fields.id_pdc")
        belib = belib.replace(np.nan, "Inconnu")
        belib["latitude"] = belib["Coordonnées géographiques"].apply(lambda x: float(x.split(",")[0]))
        belib["longitude"] = belib["Coordonnées géographiques"].apply(lambda x: float(x.split(",")[1]))

        return (belib)

    # récup data API + static
    belib = clean_data_belib()

    # Géolocalisation


    st.header("Ou une borne Bélib'", anchor=None)
    adresse2 = st.text_input('Adresse', '44 rue Alphonse Penaud 75020',key=2)
    st.write('Votre adresse actuelle est', adresse2)

    col1, col2 = st.columns([3, 1])
    # affichage de la position
    lieu = geoloc(adresse2)
    carte_lieu = folium.Map(location=lieu, zoom_start=16)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    # folium.map.LayerControl('topright', collapsed=False).add_to(carte_lieu) #bouton choix carte fond
    marker2 = folium.Marker(location=lieu, tooltip='Vous êtes-ici',
                            icon=folium.Icon(color="blue", icon="male", prefix='fa'))
    marker2.add_to(carte_lieu)
    # affichage des bornes dispo
    belib_dispo = belib[belib["fields.statut_pdc"] == "Disponible"]
    distances = []  # pr récup distances
    for i, col in belib_dispo.iterrows():
        distances.append(distance.distance((lieu[0], lieu[1]), (col["latitude"], col["longitude"])).m)
        label = f'statut: {col["fields.statut_pdc"]}, nombre de prises: {col["Nombre point de recharge"]}, Stationnement 2 roues : {col["Stationnement 2 roues"]}, Accessibilité PMR : {col["Accessibilité PMR"]}, Paiement CB : {col["Paiement CB"]}'
        location = [col["latitude"], col["longitude"]]
        marker = folium.Marker(location=location, tooltip=col["Adresse station"], popup=label,
                               icon=folium.Icon(color="green", icon="bolt", prefix='fa'))
        marker.add_to(carte_lieu)
    with col1:
        folium_static(carte_lieu)  # affichage  carte
    with col2:
        st.subheader("stations proches")
        belib_dispo["distances"] = distances
        dispo_proche = belib_dispo[["Adresse station", "distances", "fields.statut_pdc"]] \
            .groupby(by="Adresse station").agg({"distances": np.mean, "fields.statut_pdc": "count"}) \
            .sort_values(by="distances", ascending=True) \
            .reset_index() \
            .rename(columns={"distances": "distance(m)", "fields.statut_pdc": "nombre dispo"})
        dispo_proche["distance(m)"] = dispo_proche["distance(m)"].apply(lambda x: round(x))
        for i in range(3):
            st.write("Adresse :\n", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 0])
            st.write("Distance (m):", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 1])
            st.write("Places dispo :", pd.DataFrame(dispo_proche.loc[i]).T.set_index([pd.Index([i + 1])]).iloc[0, 2])


