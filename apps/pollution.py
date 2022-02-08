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
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

def app():
    st.header("Ici tu peux voir comment arrêter de polluer l'atmosphère,"
              " grâce à une invention incroyable qui s'appelle le vélo....")
    st.title("")
    st.subheader("Aussi, si tu vas pouvoir respirer aujourd'hui...")
    st.title("")
    st.title("")
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

    st.subheader("Indice de pollution de l'air")
    st.title("")
    col1,col2 = st.columns(2)
    df_critair = pd.DataFrame.from_dict(liste_dict, orient='index')
    df_critair.reset_index(inplace=True)
    df_critair.rename(columns={'index': "Qualité_Air_Aujourd'hui", 0: 'Qualité_Air_Demain'}, inplace=True)
    df_critair["Qualité_Air_Aujourd'hui"] = df_critair["Qualité_Air_Aujourd'hui"].apply(lambda x: col1.metric(label="Aujourd'hui",value='bonne') and col1.image(Image.open('bonne.png'),width = 150)if x == 'low'
    else col1.metric(label="Aujourd'hui",value='moyenne') and col1.image(Image.open('moyen.png'),width = 150) if x == 'average'
    else col1.metric(label="Aujourd'hui",value='dégradé')and col1.image(Image.open('degrade.png'),width = 150) if x == 'degrade'
    else col1.metric(label="Aujourd'hui",value='mauvaise')and col1.image(Image.open('mauvais.png'),width = 150) if x == 'high'
    else col1.metric(label="Aujourd'hui",value='très mauvaise')and col1.image(Image.open('tres_mauvais.png'),width = 150) if x == 'very-high'
    else col1.metric(label="Aujourd'hui",value='inconnue')and col1.image(Image.open('know.png'),width = 150) if x == '-'
    else col1.metric(label="Aujourd'hui",value=' extrêmement mauvaise')and col1.image(Image.open('extrem.png'),width = 150))
    df_critair["Qualité_Air_Demain"] = df_critair["Qualité_Air_Demain"].apply(lambda x: col2.metric(label="demain",value='bonne') and col2.image(Image.open('bonne.png'),width = 150) if x == 'low'
    else col2.metric(label="demain",value='moyenne') and col2.image(Image.open('moyen.png'),width= 150) if x == 'average'
    else col2.metric(label="demain",value='dégradé')and col2.image(Image.open('degrade.png'),width = 150) if x == 'degrade'
    else col2.metric(label="demain",value='mauvaise')and col2.image(Image.open('mauvais.png'),width = 150) if x == 'high'
    else col2.metric(label="demain",value='très mauvaise')and col2.image(Image.open('tres_mauvais.png'),width = 150) if x == 'very-high'
    else col2.metric(label="demain",value='inconnue')and col2.image(Image.open('know.png'),width = 80) if x == '-'
    else col2.metric(label="demain",value=' extrêmement mauvaise')and col2.image(Image.open('extrem.png'),width = 150))
    #image = Image.open('6.png')
    #col2.image(Image.open('moyen.png')) if x == 'average'
    #st.metric(label="demain",value='mauvaise')
    #st.write(df_critair)
    st.title("")
    st.title("")

    velib_mois = pd.read_csv('velib_mois.csv', sep=',')
    st.subheader('Utilisation des vélibs depuis 2019')
    annees = st.selectbox("Choix de l’année", ('Toutes les années', '2019', '2020', '2021'))

    if annees == '2019':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2019'], name='2019'))

        fig.update_layout(
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=18))
        st.plotly_chart(fig, clear_figure=True)

    if annees == '2020':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2020'], name='2020'))

        fig.update_layout(
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=18))
        st.plotly_chart(fig, clear_figure=True)

    if annees == '2021':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2021'], name='2021'))

        fig.update_layout(
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=18))
        st.plotly_chart(fig, clear_figure=True)

    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2019'], name='2019'))
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2020'], name='2020'))
        fig.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2021'], name='2021'))

        fig.update_layout(
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=18))
        st.plotly_chart(fig, clear_figure=True)

    st.title("")
    st.title("")
    st.subheader("Plus il y a de vélib, moins il y a de pollution...?")
    vpp = pd.read_csv('velib_pollu_T.csv', sep=',')
    fig1 = px.scatter(data_frame=vpp, x="Date", y="Vélib", size='Pollution', color='année',
                      color_discrete_map={'2019': 'darkgreen', '2020': 'mediumseagreen', '2021': 'lightgreen'})
    fig2 = px.line(data_frame=vpp[vpp['année'] == '2019'], x="Date", y="Vélib")
    fig2.update_traces(line_color='darkgreen')
    fig3 = px.line(data_frame=vpp[vpp['année'] == '2020'], x="Date", y="Vélib")
    fig3.update_traces(line_color='mediumseagreen')
    fig4 = px.line(data_frame=vpp[vpp['année'] == '2021'], x="Date", y="Vélib")
    fig4.update_traces(line_color='lightgreen')
    fig5 = go.Figure(data=fig1.data + fig2.data + fig3.data + fig4.data)
    fig5.update_layout(title_text="Moyenne d'utilisation des vélibs selon la pollution", title_x=0.5)
    fig5.update_xaxes(title_text='Mois')
    fig5.update_yaxes(title_text='Pollution(moyenne des No2, No, Nox, en microg/m3)')
    fig5.update_layout(legend_title="Années")

    st.plotly_chart(fig5, use_container_width=False, sharing="streamlit")

