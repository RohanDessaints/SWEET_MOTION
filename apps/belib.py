import pandas as pd
import re
import numpy as np
import json
import requests
import folium
import streamlit as st
from streamlit_folium import folium_static
import folium.plugins as plugins
#import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from PIL import Image
from shapely.geometry import Point
import geopandas as gpd
#from geopy import distance
# getting the belib data from API+CSV


def app():
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

    st.title("Se brancher pour mieux avancer")
    # chapitre historique bélib
    st.header("Pour commençer un peu d'histoire...", anchor=None)
    # texte introduction
    st.markdown("Pour pouvoir atteindre certaines puissances électriques minimums, \
    il est vite apparu qu’il faudrait aller au-delà de la simple prise ordinaire 10A (2,3 kW) ou même prise standard à 16 ampères (3,7 kW). \
    Les constructeurs et les équipementiers ont donc commencé à travailler chacun dans leur coin sur des prises permettant des charges plus rapides.\
    Au début de la nouvelle vague des véhicules électriques, les constructeurs ont tenté d’imposer différentes types de prise de recharge, chacun le sien ou presque.\
     En matière de voitures électriques, plusieurs catégories de prises pour systèmes de recharge existent.\
     Combo CCS, prise domestique, type 1, type 2, type 3, type 4 ou CHAdeMO, supercharger. \
     En Asie, le Type 1, ou prise Yazaki, faisait florès mais il est techniquement limité à 8 kW. \
     En Europe, deux types de prises se sont longtemps affrontés  : le type 3 et le type 2. \
    Les bornes de recharge du réseau Belib' sont universelles et pourvues de plusieurs prises :\
     type 2, type 3, domestique E/ F, câble Combo 2 ou câble CHAdeMo. Elles permettent donc de brancher tous les types de véhicules y compris les 2 roues. \
     La puissance fournie peut aller jusqu'à 22 kW.")

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
        st.header("Réseau Bélib Paris", anchor=None)
        st.subheader("carte des emplacements")
        folium_static(map_paris)  # affichage

    # table et chart statiques tout Paris
    # data
    pie_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    pie_data["code postal"] = pie_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])
    pie_data["total"] = pie_data["Disponible"] + pie_data["En maintenance"] + pie_data["Inconnu"] + pie_data[
        "Occupé (en charge)"]
    prises = ["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo",
              "Prise type Autre"]
    for prise in prises:
        pie_data[prise] = pie_data[prise].apply(lambda x: 0 if x == "non" else 1)

    st.header("Statut des prises dans Paris", anchor=None)
    st.markdown("Total Énergies, qui a récupéré le marché de reconversion des bornes Belib’ et Autolib dans la capitale, \
    a remis en service 2000 prises sur 2300. Pour 7 euros par an, visiteurs et Parisiens peuvent désormais charger leur voiture à des tarifs allant de 50 centimes à 90 centimes le quart d’heure. \
    Et de nouvelles bornes sont en cours de déploiement. Afin d’encourager la mobilité électrique, Autolib’ Vélib’ Métropole a souhaité que \
    les véhicules électriques des particuliers puissent se recharger sur les stations Autolib’. \
    Plusieurs milliers de bornes de recharge sont ainsi disponibles à un coût modique pour les franciliens possédant une voiture ou un deux-roues \
    électriques. Les données ci-dessous permettent de retrouver le statut de l'offre actuellement disponible par arrondissement sur Paris.")
    st.markdown("")
    col1, col2 = st.columns([2, 1])
    table = pie_data.groupby(by="code postal") \
        .agg(sum)[["Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "total"]]
    col1.write(table)

    status_colors = ['darkgreen', 'orange', 'yellow', 'orangered']

    pie_chart = table.T.drop(["total"]).T.sum().plot(kind="pie", ylabel="", colors=status_colors);
    col2.write(pie_chart.figure)

    st.header("Statut des emplacements", anchor=None)
    st.markdown("En sélectionnant l'arrondissement de votre choix dans le menu déroulant ci-dessous, \
    vous pourrez en consulter les disponibilités de connectiques en temps réel. \
    Les bornes de charge des emplacements Bélib sont universelles, plusieurs types de prises sont disponibles par emplacement.")

    # création des colonnes
    arrondissement = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=1)
    widget_data = pie_data.groupby(by="code postal") \
        .agg(sum)[["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo",
                   "Prise type Autre", "Disponible", "En maintenance", "Inconnu", "Occupé (en charge)", "total"]] \
        .loc[arrondissement].T.reset_index().rename(columns={"index": "type prise", arrondissement: "nombre de prises"})

    st.subheader("Connectiques disponibles sur les emplacements")
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

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    image4 = Image.open('prise_combo.JPG')
    image5 = Image.open('prise_chademo.JPG')
    col1.image(image4, width=110)
    col2.metric(widget_data.iloc[3, 0], widget_data.iloc[3, 1])
    col3.image(image5, width=100)
    col4.metric(widget_data.iloc[4, 0], widget_data.iloc[4, 1])
    col5.text(" ")
    col6.text(" ")

    col1, col2, col3 = st.columns(3)
    col1.write(widget_data.iloc[0:5, :].set_index("type prise"))
    col2.write(widget_data.iloc[6:, :].rename(
        columns={"nombre de prises": "nombre de places", "type prise": "statut prise"}).set_index("statut prise"))
    with col3:
        st.subheader("Disponibilité")
        dispo_percent = str(round((widget_data.iloc[6, 1] / widget_data.iloc[10, 1]) * 100)) + "%"
        st.subheader(dispo_percent)

    # Types de connectiques par arrondissement
    st.header("Connectiques par arrondissement", anchor=None)
    st.markdown("Paris comporte plus de 700 bornes de recharges de voitures électriques recensées dans les vingt arrondissements. \
    Il existe actuellement 5 types de connectiques disponibles dans la ville. Il est possible de consulter la répartition des connectiques \
    en fonction de l'arrondissement en sélectionnant le type de prise dans le menu déroulant ci-dessous."
                , unsafe_allow_html=False)

    stacked_data = pd.concat([belib, pd.get_dummies(belib["fields.statut_pdc"])], axis=1).reset_index()
    stacked_data["code postal"] = stacked_data["Adresse station"].apply(lambda x: re.findall("75\d+", x)[0])

    selection = st.multiselect("choisir type(s) de prise",
                               options=["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS",
                                        "Prise type Chademo"], default=["Prise type EF"], key=1)  # bouton multiselect
    prises = ["Prise type EF", "Prise type 2", "Prise type 3", "Prise type Combo CCS", "Prise type Chademo"]

    # couleurs des barres stackées
    stacked_colors = ['darkgreen', 'forestgreen', 'limegreen', 'lime', 'springgreen']

    for prise in prises:
        stacked_data[prise] = stacked_data[prise].apply(lambda x: 1 if x == "oui" else 0)

    stacked_chart = stacked_data.groupby(by="code postal").agg(sum)[selection] \
        .plot(kind="bar", stacked=True, figsize=(20, 8), xlabel="", color=stacked_colors);
    st.write(stacked_chart.figure)

    st.markdown("Avec des superficies respectives de 848 et 791 hectares, les XV et XVI arrondissements de Paris bénéficient du plus grand nombre d'emplacements Bélib'. \
    Le XVI arrondissement est également celui qui compte le taux de propriétaires de véhicules motorisés le plus élevé. \
    Avec presque 53 % de familles qui possèdent au moins un véhicule contre 36 % en moyenne sur l’ensemble de Paris, le XVIe est l’arrondissement le plus motorisé, mais aussi l’un des plus fortunés."
                , unsafe_allow_html=False)

    # comparatif entre 2 arrondissements
    st.subheader("Comparateur d'arrondissement")

    st.markdown("Afin de s'assurer de la disponibilité des emplacements dans la ville, il est possible de faire un comparatif \
    du statut par arrondissement. Le placement en vis à vis des 2 graphs permet de visualiser les status des emplacements en temps réel.\
    Le partage de cette information sous cette forme a une fin utile, étant d'aiguiller l'usager vers un arrondissement ou un autre en fonction des disponbilités des emplacements."
                , unsafe_allow_html=False)

    # test adaptation du graph
    col1, col2 = st.columns(2)
    with col1:
        arrondissement1 = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=2)
        bar_plot_1 = stacked_data[['code postal', 'Disponible', 'En maintenance', 'Inconnu', 'Occupé (en charge)']] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement1].reset_index() \
            .rename(columns={"index": "statut"}).set_index("statut").T \
            .plot(kind="barh", figsize=(10, 6), color=status_colors).legend(loc='upper right');
        st.write(bar_plot_1.figure)
    with col2:
        arrondissement2 = st.selectbox("Arrondissement", sorted(list(pie_data["code postal"].unique())), key=3)
        bar_plot_2 = stacked_data[['code postal', 'Disponible', 'En maintenance', 'Inconnu', 'Occupé (en charge)']] \
            .groupby(by="code postal") \
            .agg(sum) \
            .loc[arrondissement2].reset_index() \
            .rename(columns={"index": "statut"}).set_index("statut").T \
            .plot(kind="barh", figsize=(10, 6), color=status_colors).legend(loc='upper right');
        st.write(bar_plot_2.figure)


    ### CHLOROPETH
    st.title("")
    st.title("Disponibilité des bornes de recharges Bélib’ par quartiers", anchor=None)
    st.title("")
    # texte choropleth Bélib
    st.markdown("La capitale possède exactement 20 arrondissements et 80 quartiers, ce qui peut très vite devenir complexe à gérer. \
    Nous souhaitions fournir un dashboard qui permette de visualiser rapidement et en temps réels quels sont les quartiers qui disposent le plus de bornes libres et lesquels sont les saturés. \
    Ainsi grâce à ce choropleth, nous aidons les agents de la ville de Paris à mieux gérer leur parc de bornes installées.")



    dfgeoq = gpd.read_file("quartier_paris.geojson")
    link = "https://parisdata.opendatasoft.com/api/records/1.0/search/?dataset=belib-points-de-recharge-pour-vehicules-electriques-disponibilite-temps-reel&q=&rows=10000&facet=statut_pdc&facet=last_updated&facet=arrondissement"
    r = requests.get(link)
    data = r.json()
    dispo = pd.json_normalize(data["records"])
    dispobelib = dispo[dispo["fields.statut_pdc"] == "Disponible"]
    dispobelib = dispobelib.groupby(by="fields.adresse_station").count()[["datasetid"]]
    dispobelib.reset_index(inplace=True)
    dispobelib.rename(columns={"datasetid": "bornes_dispo"}, inplace=True)
    dispobelib["bornes_dispo"] = dispobelib["bornes_dispo"].astype(int)
    dispo = pd.merge(dispo, dispobelib, on="fields.adresse_station")
    dispo['point'] = dispo["fields.coordonneesxy"].apply(lambda x: Point(float(x[1]), float(x[0])))
    dispo.drop_duplicates(subset='fields.adresse_station', keep='first', inplace=True)
    dispo = gpd.GeoDataFrame(
        dispo, geometry="point")
    dispo.set_crs(epsg=4326, inplace=True)
    dispo.to_crs(epsg=4326, inplace=True)
    dfgeoqfinal = gpd.sjoin(dfgeoq, dispo, how="left", predicate="intersects")
    dfgeoqfinal = (
        dfgeoqfinal.merge(dfgeoqfinal.groupby(by="c_quinsee")["bornes_dispo"].sum().reset_index(), on="c_quinsee",
                          how="left"))
    dfgeoqfinal.drop_duplicates(subset='c_quinsee', keep='first', inplace=True)
    dfgeoqfinal.reset_index(inplace=True)
    dfgeoqfinal.rename(
        columns={"l_qu": "quartier", "fields.arrondissement": "arrondissement", "bornes_dispo_y": "bornes_dispo"},
        inplace=True)
    dfgeoqfinal.drop(
        columns=["bornes_dispo_x", "fields.code_insee_commune", "fields.statut_pdc", "fields.url_description_pdc",
                 "datasetid", "index_right", "index", "fields.code_insee_commune"], inplace=True)

    def adresse(adresse_postale):
        adresse_postale = adresse_postale.replace(" ", "+")
        link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
        r = requests.get(link)
        coords = r.json()["features"][0]["geometry"]["coordinates"]
        my_tuple = coords[1], coords[0]
        return (list(my_tuple))

    lieu = adresse("10 rue du Louvre 75001".capitalize())
    carte_lieu = folium.Map(location=lieu, zoom_start=12)
    cp = folium.Choropleth(
        geo_data=dfgeoqfinal,
        name="geometry",
        data=dfgeoqfinal,
        columns=["c_quinsee", "bornes_dispo"],
        key_on='feature.properties.c_quinsee',
        fill_color='YlGn',
        fill_opacity=0.6,
        line_opacity=0.6,
        legend_name=("Nombre de bornes recharges dispos par quartier"),
        highlight=True,
        bins=5).add_to(carte_lieu)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    folium.LayerControl('topright', collapsed=True).add_to(carte_lieu)
    folium.GeoJsonTooltip(['quartier', 'arrondissement', 'bornes_dispo']).add_to(cp.geojson)
    folium_static(carte_lieu)