import re
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.map import Layer
from folium import plugins
#import numpy as np
import pandas as pd
import requests
#import schedule
from datetime import datetime, timedelta
import geopandas as gpd
import json
from shapely.ops import transform
from geopandas import GeoDataFrame
from geopandas.tools import sjoin
from shapely.geometry import Point, mapping,shape


def app():
    st.title(" Have a break Have a Vélib'")
    st.header("")

    st.subheader("Le nom Vélib’ est un mélange des mots français « vélo » et « liberté ».")
    # texte introduction
    st.markdown("Le Vélib’ est un système de vélo en libre-service à grande échelle de la ville de Paris. \
    Lancé le 15 juillet 2007, il comprenait environ 14 500 vélos et 1230 stations de vélos, réparties sur l’ensemble de Paris et dans certaines communes de la région parisienne. \
    Désormais, l'offre comporte plus de 20000+ vélos répartis dans Paris, et dans plus de 60 villes de la petite couronne. \
    L’initiative a été proposée par Bertrand Delanoë, ancien maire de Paris et membre du Parti socialiste français. Le système a été lancé le 15 juillet 2007 après le succès de Vélo’v à Lyon \
    et le projet pionnier de La Rochelle en 1974. 7000 vélos ont d’abord été introduits dans la ville, puis répartis dans 750 stations de location automatisées, avec une quinzaine ou plus de places de stationnement pour vélos chacune. \
    L’année suivante, l’initiative a été élargie à quelque 16 000 vélos et 1200 stations de location, avec environ une station tous les 300 mètres (980 pieds) dans le centre-ville. \
    Forte de son succès, l'offre Vélib’ s’est imposée comme un moyen de transport quotidien pour des centaines de milliers de Parisiens et d’habitants d’Île-de-France. \
    Vélib’ est aussi devenu un moyen unique pour de nombreux touristes et visiteurs de découvrir Paris. \
    Velib’ propose désormais également des vélos électriques de couleur turquoise.")



    ## fonctions récup DATA vélib
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
    py_data = velib_tot.copy()
    # création dict pour map
    statuses = ["dispo", "moyen", "pas_dispo"]  # status dispo vélib
    colors = ["green", "orange", "red"]  # couleurs des icones
    color_dict = dict(zip(statuses, colors))  # dict
    velib_tot["icon_color"] = velib_tot["status"].map(color_dict)  # création couleur par taux de dispo

    # CLUSTER
    col1, col2 = st.columns([3, 1])
    selection = st.sidebar.selectbox("Status vélib", ("plus de 5 vélos", "5 vélos ou moins", "aucun vélo"), key=1)
    # selection = st.sidebar.selectbox("Status vélib",list(velib_tot["status"].unique()), key=1)
    # type_velo = st.sidebar.selectbox("Type de vélo",("mechanical","e_bike")), key=2) #à développer

    if selection == "plus de 5 vélos":
        filtre = "dispo"
    elif selection == "5 vélos ou moins":
        filtre = "moyen"
    elif selection == "aucun vélo":
        filtre = "pas_dispo"

    velib_df = velib_tot[velib_tot["status"] == filtre]
    center = [48.856614, 2.3522219]
    locations = list(zip(velib_df["lat"], velib_df["lon"]))  # récup des latlon

    cluster_colors = []
    for i, col in velib_df.iterrows():
        cluster_colors.append(folium.Icon(icon="bicycle", prefix="fa", color=col["icon_color"]))  # icones

    map_paris = folium.Map(tiles="Stamen terrain", location=center, zoom_start=12)  # carte centrée
    cluster = folium.FeatureGroup(name='cluster')  # création du cluster
    cluster.add_child(plugins.MarkerCluster(locations=locations, icons=cluster_colors)).add_to(map_paris)
    with col1:
        st.header("Réseau Vélib' Paris", anchor=None)
        st.subheader("carte des emplacements")
        folium_static(map_paris)  # affichage
    with col2:
        st.header("En chiffres ", anchor=None)
        # création widget temps réel
        velib_tot["velib_emprunts"] = velib_tot["num_docks_available"] - velib_tot["num_bikes_available"]
        velib_tot.head()

        photo = velib_tot[["num_bikes_available", "mechanical", "e_bike", "velib_emprunts"]].sum() \
            .reset_index() \
            .rename(columns={"index": "status", 0: "count"})

        st.subheader("Vélib' dispo")
        st.subheader(str(photo.iloc[0, 1]))
        st.write("dont mécaniques :")
        st.write(photo.iloc[1, 1])
        st.write("dont électriques :")
        st.write(photo.iloc[2, 1])
        st.write("")
        st.subheader("Vélib' empruntés :")
        st.subheader(str(photo.iloc[3, 1]))

    #lieu=adresse(st.text_input("0ù êtes-vous ?").capitalize())
    #st.write('Your locaion is', lieu)

    # choropleth Vélib’
    st.header("Disponibilité des Vélib’ par quartier", anchor=None)
    # texte choropleth Vélib
    st.markdown("La capitale possède exactement 20 arrondissements et 80 quartiers, ce qui peut très vite devenir complexe à gérer. \
    Nous souhaitions fournir un dashboard qui permette de visualiser rapidement et en temps réels quels sont les quartiers qui possèdent le plus de Vélib’ disponibles et lesquels sont les saturés. \
    Ce choropleth qui fait la dichotomie entre Vélib’ mécaniques et Vélib’ électriques, a pour but d’aider les agents "
    "de la ville de Paris à mieux gérer leur parc de Vélib’ installés afin de réagir rapidement à la demande lors des heures de pointe.")



    dfgeoq = gpd.read_file("quartier_paris.geojson")
    link = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json'
    r = requests.get(link)
    data = r.json()
    velib = pd.json_normalize(data['data'], record_path='stations')
    req =requests.get('https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json')
    data = req.json()
    velib_bornes = pd.json_normalize(data['data'], record_path='stations')
    velib_tot = pd.merge(velib,velib_bornes,
                         on='stationCode')
    velib_tot['mechanical'] = velib_tot['num_bikes_available_types'].apply(lambda x : x[0]['mechanical'])
    velib_tot['e_bike'] = velib_tot['num_bikes_available_types'].apply(lambda x : x[1]['ebike'])
    velib_tot.rename(columns={"lat": "latitude", "lon":"longitude"}, inplace = True)
    velib_tot['capacity'] = velib_tot['capacity'].astype(int)
    velib_tot['mechanical'] = velib_tot['mechanical'].astype(int)
    velib_tot['e_bike'] = velib_tot['e_bike'].astype(int)
    velib_tot.drop(columns=["station_id_x", "numBikesAvailable","num_bikes_available_types","numDocksAvailable","station_id_y"], inplace=True)
    velib_tot.rename(columns={"capacity":"capacité_station", "mechanical" : "std_velos_dispos", "e_bike":"e_bike_dispos", "num_bikes_available":"velos_dispos"}, inplace=True)
    velib_tot['point'] = velib_tot.apply(lambda x : Point(float(x["longitude"]), float(x["latitude"])), axis=1)
    velib_tot.drop_duplicates(subset='stationCode', keep='first', inplace=True)
    velib_tot= gpd.GeoDataFrame(
        velib_tot, geometry="point")
    velib_tot.set_crs(epsg=4326, inplace=True)
    velib_tot.to_crs(epsg=4326, inplace=True)
    dfgeoqfinalvelo = gpd.sjoin(dfgeoq,velib_tot,how = "left", predicate="intersects" )


    #Création du sunburst
    dfsunburst = dfgeoqfinalvelo.copy()
    dfgeoqfinalvelo = (dfgeoqfinalvelo.merge(dfgeoqfinalvelo.groupby(by="c_quinsee")["velos_dispos","std_velos_dispos","e_bike_dispos"].sum().reset_index(), on="c_quinsee", how="left"))
    dfgeoqfinalvelo.drop_duplicates(subset='c_quinsee', keep='first', inplace=True)
    dfgeoqfinalvelo.reset_index(inplace = True)
    dfgeoqfinalvelo.rename(columns={"l_qu":"quartier","c_ar":"arrondissement","velos_dispos_y":"velos_dispos", "std_velos_dispos_y":"std_velos_dispos", "e_bike_dispos_y":"e_bike_dispos"}, inplace = True)
    dfgeoqfinalvelo.drop(columns=["velos_dispos_x","std_velos_dispos_x","e_bike_dispos_x","index_right","index"], inplace=True)
    def adresse(adresse_postale):
      adresse_postale=adresse_postale.replace(" ","+")
      link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
      r= requests.get(link)
      coords=r.json()["features"][0]["geometry"]["coordinates"]
      my_tuple=coords[1],coords[0]
      return(list(my_tuple))
    lieu=adresse("10 rue du Louvre 75001".capitalize())
    carte_lieu= folium.Map(location =lieu, zoom_start= 12)
    cp = folium.Choropleth(
        geo_data = dfgeoqfinalvelo,
        name="geometry",
        data = dfgeoqfinalvelo,
        columns = ["c_quinsee", "velos_dispos"],
        key_on='feature.properties.c_quinsee',
        fill_color ='Blues' ,
        fill_opacity=0.6,
        line_opacity=0.6,
        legend_name = ("Nombre de bornes recharges dispos par quartier"),
        highlight=True,
        bins=6).add_to(carte_lieu)
    folium.raster_layers.TileLayer(tiles="Stamen Terrain", overlay=True).add_to(carte_lieu)
    folium.LayerControl('topright', collapsed=True).add_to(carte_lieu)
    folium.GeoJsonTooltip(["quartier",'velos_dispos','std_velos_dispos','e_bike_dispos']).add_to(cp.geojson)
    folium_static(carte_lieu)


    ### Sunburst

    st.header("Répartition des Vélib’ disponibles par arrondissement", anchor=None)
    # texte Sunburst Vélib’
    st.markdown("En complément de la répartition des Vélib’ par quartiers, nous proposons une répartition par arrondissements. \
    Ce sunburst permet de visualiser rapidement et en temps réels quels sont les arrondissements qui disposent le plus de Vélib’ et lesquels sont les saturés. \
    Il est également possible de filtrer et cibler les arrondissements uns par uns afin d’avoir la répartition entre Vélib’ mécaniques et Vélib’ électriques. \
    Ceci est une aide supplémentaire pour mieux gérer le parc de Vélib’ installés.")

    ## Création colonne Sunburst(s)
    col1, col2 = st.columns(2)

    with col1:
        dfsunburst.rename(columns={"l_qu": "quartier", "c_ar": "arrondissement", "velos_dispos_y": "velos_dispos",
                                   "std_velos_dispos_y": "std_velos_dispos", "e_bike_dispos_y": "e_bike_dispos"},
                          inplace=True)
        dfsunburst = (dfsunburst.merge(dfsunburst.groupby(by="arrondissement")[
                                           "velos_dispos", "std_velos_dispos", "e_bike_dispos"].sum().reset_index(),
                                       on="arrondissement", how="left"))
        dfsunburst.drop_duplicates(subset='arrondissement', keep='first', inplace=True)
        dfsunburst.reset_index(inplace=True)
        dfsunburst = dfsunburst[["arrondissement", "velos_dispos_y", "std_velos_dispos_y", "e_bike_dispos_y"]]
        dfsunburst.rename(columns={"velos_dispos_y": "Total dispo", "std_velos_dispos_y": "Vélib' classique",
                                   "e_bike_dispos_y": "Vélib' électrique"}, inplace=True)
        dfsunburst.sort_values(by="arrondissement", ascending=True, inplace=True)
        dfsunburst["Ville"] = "Paris"
        import plotly.express as px
        fig0 = px.sunburst(dfsunburst,
                           path=["Ville", "arrondissement", "Total dispo"],
                           values='Total dispo',
                           branchvalues="total",
                           color='Total dispo',
                           hover_data=["Vélib' classique", "Vélib' électrique"],
                           color_continuous_scale='blues'
                           )
        st.plotly_chart(fig0)
    # filtre sunburst par arrondissement
    arrondissement = st.selectbox("Arrondissement", sorted(list(dfsunburst["arrondissement"].unique())), key=1)
    with col2:
        sunburst1 = dfsunburst.set_index("arrondissement").loc[[arrondissement]]
        sunburst1 = sunburst1.T
        sunburst1["Ville"] = "Paris"
        sunburst1.drop(["Ville", "Total dispo"], inplace=True)
        sunburst1.rename(columns={arrondissement:"test"}, inplace=True)
        fig1 = px.sunburst(sunburst1,
                           path=["Ville", "test"],
                           values='test',
                           branchvalues="total",
                           color='test',
                           color_continuous_scale='blues'
                           )
        st.plotly_chart(fig1)

    # PIE CHART DISPO VELIB
    # split en double colonne  texte/pie_chart
    st.title("")

    col1, col2 = st.columns([2, 1])
    dispo_colors = ['steelblue', 'lightskyblue', 'lightcyan']
    with col1:
        # Pie chart Disponibilité Vélib’
        st.subheader("Disponibilité des Vélib’ par seuil", anchor=None)
        # texte Sunburst Vélib’
        st.markdown("Cette visualisation permet de répartir en 3 catégories la disponibilité des Vélib’ sur l’ensemble de la ville de Paris.  \
        Ainsi, on offre une vue globale et en temps réel sur la disponibilité des Vélib’ en fonction des seuils suivants : \
        Dispo : agrège toutes les stations qui possèdent 5 Vélib’ ou plus \
        Moyen : agrège toutes les stations qui possèdent entre 3 et 5 Vélib’ \
        Pas dispo : agrège toutes les stations ne possèdent aucun Vélib’. ")
    with col2:
        pie_1 = py_data["status"].value_counts().plot(kind="pie", ylabel="", figsize=(10, 6), colors=dispo_colors);
        st.write(pie_1.figure)