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
    st.title("Plus de Vélib', moins de pollution ?")
    st.subheader("")
    st.header("Ça respire...?")
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

    vp19 = pd.read_csv('vp19.csv', sep=',')
    vp20 = pd.read_csv('vp20.csv', sep=',')
    vp21 = pd.read_csv('vp21.csv', sep=',')

    st.header("La pollution et l'utilisation des Vélib' à Paris depuis 2019")
    st.subheader('Et ça pédale fort depuis trois ans !')

    st.write(
        "Si la crise sanitaire a bousculé nos sociétés, elle a été une véritable bouffée "
        "d'air pour notre planète ! L'année 2020 a enregsitré une baisse de la pollution significative. "
        "Et si, nous parisiens, nous profitions de cette période pour passer au monde d'après ? Grâce aux données "
        "d'AirParif et de la mairie de Paris, nous pouvons mettre en lien l'utilisation des Vélib' et le taux de "
        "pollution dans le capitale, sur ces 3 dernières années.")

    annees2 = st.selectbox("Pour filtrer le graphique sur les années :", ('Toutes les années', '2019', '2020', '2021'),
                           key=1)

    if annees2 == '2019':
        figp19 = go.Figure(data=[go.Scatter(
            x=vp19['Date'], y=vp19['Vélib'],
            mode='markers+lines',
            name='2019',
            marker=dict(
                size=vp19['Pollution'], color='rgb(0,134,149)'))])
        figp19.update_layout(
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            title="Année 2019 : le monde d'avant ",
            font=dict(
                size=14))
        st.plotly_chart(figp19, clear_figure=True)

    if annees2 == "2020":
        figp20 = go.Figure(data=[go.Scatter(
            x=vp20['Date'], y=vp20['Vélib'],
            mode='markers+lines',
            name='2020',
            marker=dict(
                size=vp20['Pollution'], color='rgb(35,181,128)'))])
        figp20.update_layout(
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            title="Année 2020 : le confinement ",
            font=dict(
                size=14))

        st.plotly_chart(figp20, clear_figure=True)

    if annees2 == "2021":
        figp21 = go.Figure(data=[go.Scatter(
            x=vp21['Date'], y=vp21['Vélib'],
            mode='markers+lines',
            name='2021',
            marker=dict(
                size=vp21['Pollution'], color='rgb(102,194,175)'))])
        figp21.update_layout(
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            title="Année 2021 : le monde d'après ? ",
            font=dict(
                size=14))

        st.plotly_chart(figp21, clear_figure=True)

    if annees2 == 'Toutes les années':
        figpall = go.Figure(data=[go.Scatter(
            x=vp19['Date'], y=vp19['Vélib'],
            mode='markers+lines',
            name="2019 : le monde d'avant",
            marker=dict(
                size=vp19['Pollution'] * 0.85, color='rgb(0,134,149)')

        )])
        figpall.add_trace(go.Scatter(
            x=vp20['Date'], y=vp20['Vélib'],
            mode='markers+lines',
            name="2020 : le confinement",
            marker=dict(
                size=vp20['Pollution'] * 0.85, color='rgb(35,181,128)')
        ))

        figpall.add_trace(go.Scatter(
            x=vp21['Date'], y=vp21['Vélib'],
            mode='markers+lines',
            name="2021 : le monde d'après",
            marker=dict(
                size=vp21['Pollution'] * 0.85, color='rgb(102,194,175)')
        ))

        figpall.update_layout(
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            title="Depuis 2019 ",
            legend_title="Pollution par année",
            font=dict(
                size=14))
        st.plotly_chart(figpall, clear_figure=True)

    st.caption("Pollution = émission moyenne de Monoxyde de carbone (No) et Dioxyde de carbone (No2).")
    st.caption(
        "Comptage horaire moyen = utilisation en moyenne, par heure, des vélos, sur l'ensemble des bornes parisiennes.")

    st.write(
        "La taille des cercles est ici proportionnelle aux émissions de pollution et les courbes correspondent à l'utilisation horaire moyen de Vélib'.")
    st.header(
        "Les chiffres sont clairs : 2021 enregistre une nette baisse de la pollution et une augmentation de l'utilisation des Vélib' !")

    # PARTIE 2

    st.write(
        " Les deux graphiques suivants permettent de distinguer et comparer plus en détails les émissions de pollution et l'utilisation des Vélib'.")

    velib_mois = pd.read_csv('velib_mois.csv', sep=',')
    annees = st.selectbox("Pour filtrer les deux graphiques sur les années:",
                          ('Toutes les années', '2019', '2020', '2021'), key=2)

    if annees == '2019':
        figp19 = go.Figure(data=[go.Scatter(
            x=vp19['Date'], y=vp19['Pollution'],
            line=dict(color="rgb(0,134,149)"),
            mode='markers+lines')])
        figp19.update_layout(
            title='Pollution en 2019',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Pollution moyenne",
            font=dict(
                size=14))
        st.plotly_chart(figp19, clear_figure=True)

        figv19 = go.Figure()
        figv19.add_trace(
            go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2019'], name='2019',
                       line=dict(color="rgb(0,134,149)")))

        figv19.update_layout(
            title='Utilisation des vélib en 2019',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=14))
        st.plotly_chart(figv19, clear_figure=True)

    if annees == '2020':
        figp20 = go.Figure(data=[go.Scatter(
            x=vp20['Date'], y=vp20['Pollution'],
            line=dict(color="rgb(35,181,128)"),
            mode='markers+lines')])
        figp20.update_layout(
            title='Pollution en 2020',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Pollution moyenne",
            font=dict(
                size=14))
        st.plotly_chart(figp20, clear_figure=True)

        figv20 = go.Figure()
        figv20.add_trace(
            go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2020'], name='2020',
                       line=dict(color="rgb(35,181,128)")))

        figv20.update_layout(
            title='Utilisation des vélib en 2020',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=14))
        st.plotly_chart(figv20, clear_figure=True)

    if annees == '2021':
        figp21 = go.Figure(data=[go.Scatter(
            x=vp21['Date'], y=vp21['Pollution'],
            line=dict(color="rgb(102,194,175)"),
            mode='markers+lines')])
        figp21.update_layout(
            title='Pollution en 2021',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Pollution moyenne",
            font=dict(
                size=14))
        st.plotly_chart(figp21, clear_figure=True)

        figv21 = go.Figure()
        figv21.add_trace(
            go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2021'], name='2021',
                       line=dict(color="rgb(102,194,175)")))

        figv21.update_layout(
            title='Utilisation des vélib en 2020',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=14))
        st.plotly_chart(figv21, clear_figure=True)

    if annees == 'Toutes les années':
        figpall = go.Figure(data=[go.Scatter(
            x=vp19['Date'], y=vp19['Pollution'], name='2019',
            mode='markers+lines', line=dict(color="rgb(0,134,149)"))])
        figpall.add_trace(go.Scatter(
            x=vp20['Date'], y=vp20['Pollution'], name='2020',
            mode='markers+lines', line=dict(color="rgb(35,181,128)")))
        figpall.add_trace(go.Scatter(
            x=vp21['Date'], y=vp21['Vélib'], name='2021',
            mode='markers+lines', line=dict(color="rgb(102,194,175)")))

        figpall.update_layout(
            title='Pollution depuis 2019',
            autosize=False,
            width=1200,
            height=500,
            xaxis_title="Par mois",
            yaxis_title="Pollution moyenne",
            font=dict(
                size=14))
        st.plotly_chart(figpall, clear_figure=True)

        figvall = go.Figure()

        figvall.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2019'],
                                     line=dict(color="rgb(0,134,149)"), name='2019'))
        figvall.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2020'],
                                     line=dict(color="rgb(35,181,128)"), name='2020'))
        figvall.add_trace(go.Scatter(x=velib_mois['Date de comptage'], y=velib_mois['Comptage horaire 2021'],
                                     line=dict(color="rgb(102,194,175)"), name='2021'))

        figvall.update_layout(
            autosize=False,
            width=1200,
            height=500,
            title='Utilisation des vélib depuis 2019',
            xaxis_title="Par mois",
            yaxis_title="Comptage horaire moyen",
            legend_title="Année",
            font=dict(
                size=14))
        st.plotly_chart(figvall, clear_figure=True)

