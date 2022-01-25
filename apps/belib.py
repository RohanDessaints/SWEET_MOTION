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
# getting the belib data from API+CSV
def app():
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
        stations_cols_keep = ['ID PDC local', 'Statut du Point de charge', 'Nombre point de recharge', 'Adresse station',
                              'Coordonnées géographiques', 'Paiement CB', 'Accessibilité PMR', 'Stationnement 2 roues',
                              'Puissance max KW', 'Prise type EF', 'Prise type 2', 'Prise type Combo CCS',
                              'Prise type Chademo', 'Prise type Autre', 'Prise type 3']
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

    #création de colonnes
    #st.set_page_config(layout="wide")
    #col1, col2 = st.columns([3,1])


    # récup data API + static
    belib = clean_data_belib()
    # carte avec clusters Belib
    #with col1:
    #st.sidebar.title("Sweet Motion", anchor=None)
    st.header("Carte des emplacements Belib", anchor=None)
    belib["latitude"] = belib["latitude"].apply(lambda x: float(x))
    belib["longitude"] = belib["longitude"].apply(lambda x: float(x))  # float sinon recursion error

    # Récupération de l'adresse
    def adresse(adresse_postale):
        adresse_postale = adresse_postale.replace(" ", "+")
        link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
        r = requests.get(link)
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        my_tuple = coords[1], coords[0]
        return (list(my_tuple))


    # création carte Paris
    center = [48.856614, 2.3522219]  # Paris latlon GPS
    add_select = st.sidebar.selectbox("Emplacements Belib", ("OpenStreetMap", "Stamen Terrain", "Stamen Toner"), key=2)
    map_paris = folium.Map(tiles=add_select, location=center, zoom_start=12)
    # création détails carte
    locations = list(zip(belib["latitude"], belib["longitude"]))  # récup des latlon
    icons = [folium.Icon(icon="bolt", prefix="fa") for i in range(len(locations))]  # création des icones
    cluster = folium.FeatureGroup(name='cluster')  # cration du cluster
    cluster.add_child(plugins.MarkerCluster(locations=locations, icons=icons)).add_to(map_paris)
    folium_static(map_paris)  # affichage
    lieu = adresse(st.text_input("0ù êtes-vous ?",key=1).capitalize())

    if lieu != "":
        map_paris = folium.Map(tiles=add_select, location=lieu, zoom_start=16)
        # création détails carte
        locations = list(zip(belib["latitude"], belib["longitude"]))  # récup des latlon
        icons = [folium.Icon(icon="bolt", prefix="fa") for i in range(len(locations))]  # création des icones
        cluster = folium.FeatureGroup(name='cluster')  # cration du cluster
        cluster.add_child(plugins.MarkerCluster(locations=locations, icons=icons)).add_to(map_paris)
        marker2 = folium.Marker(location=lieu, tooltip='Vous êtes-ici',
                                icon=folium.Icon(color="red", icon="male", prefix='fa'))
        marker2.add_to(map_paris)
        folium_static(map_paris)  # affichage





    # pie_plot
    #Version 1:
    '''
    st.subheader("PieChart des emplacements Belib", anchor=None)
    pie_plot = belib["fields.statut_pdc"].value_counts().plot(kind="pie", ylabel="",explode=(0.05, 0.01, 0.01, 0.01));
    st.write(pie_plot.figure)
    '''
    #Version 2
    st.subheader("Statut des emplacements", anchor=None)
    pie_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    pie_data["code postal"] = pie_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])
    pie_data["total"] = pie_data["Disponible"] + pie_data["En maintenance"] + pie_data["Inconnu"] + pie_data[
        "Occupé (en charge)"]

    # colonnes avec graphiques en camembert
    col1, col2 = st.columns(2)
    with col1:
        arrondissement = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=1)
        pie_plot = pie_data[["Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "code postal"]] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement] \
            .plot(kind="pie", ylabel="", legend=True, title="statut des prises", figsize=(15, 10),autopct='%1.1f%%');
        st.write(pie_plot.figure)

    with col2:
        arrondissement = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=2)
        # counts= pie_data["fields.statut_pdc"].value_counts().to_list() #nb de prises selon statut
        pie_plot2 = pie_data[["Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "code postal"]] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement] \
            .plot(kind="pie", ylabel="", legend=False, title="statut des prises", figsize=(15, 10),autopct='%1.1f%%');
        st.write(pie_plot2.figure)


    # test de plot
    #st.subheader("Test de bar plot", anchor=None)
    st.title("")
    #st.markdown("Insert some text here and then move on to next chapter", unsafe_allow_html=False)

    stacked_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    stacked_data["code postal"] = stacked_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])

    stacked_chart = stacked_data.iloc[:, -5:] \
        .groupby(by="code postal").agg(sum) \
        .plot(kind="bar", stacked=True);
    st.write(stacked_chart.figure)

