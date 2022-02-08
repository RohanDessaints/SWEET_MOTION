import streamlit as st

# Custom imports
from multipleapp import MultiPage
from apps import belib, velib,pollution,home # import your pages here

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
app.add_page('Une incroyable équipe',home.app)
app.add_page("Rouler à vélo c'est respirer",pollution.app)
app.add_page("Se brancher pour avancer", belib.app)
app.add_page("Have a break, Have a vélib",velib.app)

# The main app
app.run()