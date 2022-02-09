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
                       color_continuous_scale='greens'
                       )
    st.plotly_chart(fig0)
    # filtre sunburst par arrondissement
    arrondissement = st.selectbox("Arrondissement", sorted(list(dfsunburst["arrondissement"].unique())), key=1)
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
                       color_continuous_scale='greens'
                       )
    st.plotly_chart(fig1)