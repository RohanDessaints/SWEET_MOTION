import streamlit as st

# Custom imports
from multipleapp import MultiPage
from apps import belib, velib,pollution # import your pages here

# Create an instance of the app
app = MultiPage()
st.set_page_config(layout="wide")
# Title of the main page
from PIL import Image
image = Image.open('6.png')

st.image(image)

st.title("")
st.title("")
st.title("")
st.title("")
# Add all your applications (pages) here
app.add_page("Bélib", belib.app)
app.add_page('Vélib',velib.app)
app.add_page('Pollution',pollution.app)

# The main app
app.run()