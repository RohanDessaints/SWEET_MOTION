import streamlit as st

# Custom imports
from multipleapp import MultiPage
from apps import belib, velib,pollution,home,geo_velib_belib # import your pages here

# Create an instance of the app
app = MultiPage()
st.set_page_config(layout="wide")
# Title of the main page
#
#image = Image.open('6.png')

#st.image(image)

st.title("")
st.title("")
st.title("")
st.title("")
# Add all your applications (pages) here
app.add_page("Je book mon sweet motion",geo_velib_belib.app)
app.add_page("Se brancher pour mieux avancer", belib.app)
app.add_page("Have a break, Have a Vélib'",velib.app)
app.add_page("Rouler à vélo c'est respirer",pollution.app)
app.add_page('Une équipe incroyable',home.app)
# The main app
app.run()