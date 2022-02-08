import streamlit as st
from PIL import Image

# Define the multipage class to manage the multiple apps in our program
class MultiPage:
    """Framework for combining multiple streamlit applications."""

    def __init__(self) -> None:
        """Constructor class to generate a list which will store all our applications as an instance variable."""
        self.pages = []

    def add_page(self, title, func) -> None:
        """Class Method to Add pages to the project
        Args:
            title ([str]): The title of page which we are adding to the list of apps

            func: Python function to render this page in Streamlit
        """

        self.pages.append({

            "title": title,
            "function": func
        })

    def run(self):
        # Dropdown to select the page to run
        image = Image.open('6.png')
        st.sidebar.image(image)
        page = st.sidebar.selectbox(
        #page = st.selectbox(
            'Navigation',
            self.pages,
            format_func=lambda page: page['title']
        )

        # run the app function
        page['function']()