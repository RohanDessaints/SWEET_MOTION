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


def app():
  def current_time():
    now = datetime.now() + timedelta(hours = 1)
    return now.strftime("%H:%M:%S")
  def retrieve_data():
    link = 'https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json'
    r = requests.get(link)
    data = r.json()
    return pd.json_normalize(data['data'], record_path='stations')
  #schedule.every(60).seconds.do(retrieve_data)
  velib = pd.DataFrame(retrieve_data())

  def retrieve_data2():
    req =requests.get('https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json')
    data = req.json()
    return pd.json_normalize(data['data'], record_path='stations')
  #schedule.every(60).seconds.do(retrieve_data2)
  velib_bornes = pd.DataFrame(retrieve_data2())

  velib_tot = pd.merge(velib,velib_bornes,
                       on='stationCode')

  velib_tot['mechanical'] = velib_tot['num_bikes_available_types'].apply(lambda x : x[0]['mechanical'])
  velib_tot['e_bike'] = velib_tot['num_bikes_available_types'].apply(lambda x : x[1]['ebike'])

  velib_tot['capacity'] = velib_tot['capacity'].astype(str)

  st.header("Carte des emplacements Vélib", anchor=None)

  # Récuperation de l'adresse
  def adresse(adresse_postale):
    adresse_postale=adresse_postale.replace(" ","+")
    link = f"https://api-adresse.data.gouv.fr/search/?q={adresse_postale}"
    r= requests.get(link)
    coords=r.json()["features"][0]["geometry"]["coordinates"]
    my_tuple=coords[1],coords[0]
    return(list(my_tuple))

  lieu=adresse(st.text_input("0ù êtes-vous ?").capitalize())
  #st.write('Your locaion is', lieu)


  # Création de la carte
  carte_lieu= folium.Map(location =lieu, zoom_start= 16)
  folium.raster_layers.TileLayer(tiles="Stamen Terrain").add_to(carte_lieu)
  folium.map.LayerControl('topright', collapsed=False).add_to(carte_lieu)
  marker2=folium.Marker(location=lieu, tooltip='Vous êtes-ici', icon=folium.Icon(color="red",icon="male", prefix='fa'))
  marker2.add_to(carte_lieu)

  for i,col in velib_tot.iterrows():
    label= 'ebike: {}, bike: {}'.format(col["e_bike"], col["mechanical"])
    location=[col["lat"],col["lon"]]
    marker=folium.Marker(location=location, tooltip=col["name"], popup=label, icon=folium.Icon(color="blue",icon="bicycle", prefix='fa'))
    #icon=folium.Icon(color="green",icon="bolt", prefix='fa')
    marker.add_to(carte_lieu)


  folium_static(carte_lieu)
