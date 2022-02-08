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
import warnings
warnings.filterwarnings('ignore')
from PIL import Image
from geopy import distance
# getting the belib data from API+CSV


def app():
    st.header("")
    # créer différentes pages web
    # page = st.sidebar.radio('Page affichée', ['Carte Bélib', 'Visualisations Bélib', 'Stacked plot'])
    # if page == 'Carte Bélib':
    # indenter code qui suit

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

    # page setting "wide"
    #st.set_page_config(layout="wide")

    col1, col2 = st.columns([3, 1])
    # carte avec clusters Belib
    belib["latitude"] = belib["latitude"].apply(lambda x: float(x))
    belib["longitude"] = belib["longitude"].apply(lambda x: float(x))  # float sinon recursion error
    # création carte Paris
    center = [48.856614, 2.3522219]  # Paris latlon GPS
    # selectbar pour carte de fond
    # add_select = st.sidebar.selectbox("Type de carte",("OpenStreetMap", "Stamen Terrain","Stamen Toner"), key=1)

    # création du filtre "statut prises"
    status = st.sidebar.selectbox("Status point de charge", list(belib["fields.statut_pdc"].unique()), key=2)
    statuses = list(belib["fields.statut_pdc"].unique())  # status
    colors = ["green", "red", "yellow", "orange"]  # couleurs des icones
    color_dict = dict(zip(statuses, colors))
    belib["icon_color"] = belib["fields.statut_pdc"].map(color_dict)  # création couleur par status DF

    # création du filtre "type de prise"
    prise = st.sidebar.selectbox("Type de prise", (
    "Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo", "Prise type Autre"),
                                 key=3)

    df_status = belib[belib["fields.statut_pdc"] == status]  # filtre des prises par status
    df_status = df_status[df_status[prise] == "oui"]  # filtre des prises par type de prise
    locations = list(zip(df_status["latitude"], df_status["longitude"]))  # récup des latlon
    # création détails carte
    icons = []
    for i, col in df_status.iterrows():
        icons.append(folium.Icon(icon="bolt", prefix="fa", color=col["icon_color"]))  # icones

    map_paris = folium.Map(tiles="Stamen terrain", location=center, zoom_start=12)  # carte centrée
    # folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(map_paris)
    cluster = folium.FeatureGroup(name='cluster')  # création du cluster
    cluster.add_child(plugins.MarkerCluster(locations=locations, icons=icons)).add_to(map_paris)
    with col1:
        st.title("Réseau Bélib Paris", anchor=None)
        st.subheader("carte des emplacements")
        folium_static(map_paris)  # affichage
    with col2:
        st.title("En chiffres ", anchor=None)
        st.subheader("nombre d'emplacements")
        pie_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
        pie_data["code postal"] = pie_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])
        pie_data["total"] = pie_data["Disponible"] + pie_data["En maintenance"] + pie_data["Inconnu"] + pie_data[
            "Occupé (en charge)"]
        table = pie_data.groupby(by="code postal") \
            .agg(sum)[[status]]
        table

    # Géolocalisation
    def geoloc(adresse_postale):
        adresse_postale = adresse_postale.replace(" ", "+")
        link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
        r = requests.get(link)
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        my_tuple = coords[1], coords[0]
        return (list(my_tuple))

    st.title("Géolocalisation", anchor=None)
    adresse = st.text_input('Adresse', '44 rue Alphonse Penaud 75020')
    st.write('Votre adresse actuelle est', adresse)

    col1, col2 = st.columns([3, 1])
    # affichage de la position
    lieu = geoloc(adresse)
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

    # bloc sur les connectiques et dispo
    st.title("Statut des emplacements", anchor=None)
    # data
    pie_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    pie_data["code postal"] = pie_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])
    pie_data["total"] = pie_data["Disponible"] + pie_data["En maintenance"] + pie_data["Inconnu"] + pie_data[
        "Occupé (en charge)"]
    prises = ["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo",
              "Prise type Autre"]
    for prise in prises:
        pie_data[prise] = pie_data[prise].apply(lambda x: 0 if x == "non" else 1)

    arrondissement = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=1)
    widget_data = pie_data.groupby(by="code postal") \
        .agg(sum)[["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo",
                   "Prise type Autre", "Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "total"]] \
        .loc[arrondissement].T.reset_index().rename(columns={"index": "type prise", arrondissement: "nombre de prises"})

    st.subheader("Connectiques disponibles sur les emplacements")
    # création des colonnes rang1
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    image1 = Image.open('prise_EF.JPG')
    image2 = Image.open('prise_type2.JPG')
    image3 = Image.open('prise_type3.JPG')
    col1.image(image1, width=110)
    col2.metric(widget_data.iloc[0, 0], widget_data.iloc[0, 1])
    col3.image(image2, width=100)
    col4.metric(widget_data.iloc[1, 0], widget_data.iloc[1, 1])
    col5.image(image3, width=95)
    col6.metric(widget_data.iloc[2, 0], widget_data.iloc[2, 1])
    # création des colonnes rang2
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    image4 = Image.open('prise_combo.JPG')
    image5 = Image.open('prise_chademo.JPG')
    col1.image(image4, width=110)
    col2.metric(widget_data.iloc[3, 0], widget_data.iloc[3, 1])
    col3.image(image5, width=100)
    col4.metric(widget_data.iloc[4, 0], widget_data.iloc[4, 1])
    col5.text(" ")
    col6.text(" ")
    # création des colonnes rang3 (table + table + taux dispo)
    col1, col2, col3 = st.columns(3)
    col1.write(widget_data.iloc[0:5, :].set_index("type prise"))
    col2.write(widget_data.iloc[6:, :].rename(
        columns={"nombre de prises": "nombre de places", "type prise": "statut prise"}).set_index("statut prise"))
    with col3:
        st.subheader("Disponibilité")
        dispo_percent = str(round((widget_data.iloc[6, 1] / widget_data.iloc[10, 1]) * 100)) + "%"
        st.subheader(dispo_percent)

    # table et chart statiques tout Paris
    st.title("Statut des prises dans Paris", anchor=None)
    col1, col2 = st.columns([2, 1])
    table = pie_data.groupby(by="code postal") \
        .agg(sum)[["Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "total"]]
    col1.write(table)
    pie_chart = table.T.drop(["total"]).T.sum().plot(kind="pie", ylabel="");
    col2.write(pie_chart.figure)

    # Types de connectiques par arrondissement (stacked chart filtré)
    st.title("Connectiques par arrondissement", anchor=None)
    st.markdown("Etude en détail du nombre de prises / connectiques différents selon arrondissement",
                unsafe_allow_html=False)

    stacked_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    stacked_data["code postal"] = stacked_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])

    selection = st.multiselect("choisir type(s) de prise",
                               options=["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS",
                                        "Prise type Chademo"], default=["Prise type EF"], key=1)  # bouton multiselect
    prises = ["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo"]
    for prise in prises:
        stacked_data[prise] = stacked_data[prise].apply(lambda x: 1 if x == "oui" else 0)

    stacked_chart = stacked_data.groupby(by="code postal").agg(sum)[selection] \
        .plot(kind="bar", stacked=True, figsize=(20, 8), xlabel="");
    st.write(stacked_chart.figure)

    # comparatif entre 2 arrondissements (barchart en vis a vis)
    st.subheader("Comparateur d'arrondissement")
    col1, col2 = st.columns(2)
    with col1:
        arrondissement1 = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=2)
        bar_plot_1 = \
        stacked_data[['code postal', 'Prise type EF', 'Prise type 2', 'Prise type Combo CCS', 'Prise type Chademo']] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement1].reset_index().rename(columns={"index": "statut"}).set_index("statut").T \
            .plot(kind="barh", figsize=(10, 6));
        st.write(bar_plot_1.figure)
    with col2:
        arrondissement2 = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=3)
        bar_plot_2 = \
        stacked_data[['code postal', 'Prise type EF', 'Prise type 2', 'Prise type Combo CCS', 'Prise type Chademo']] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement2].reset_index().rename(columns={"index": "statut"}).set_index("statut").T \
            .plot(kind="barh", figsize=(10, 6));
        st.write(bar_plot_2.figure)
