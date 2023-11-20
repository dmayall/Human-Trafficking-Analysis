import pandas as pd 
import altair as alt
import streamlit as st

data = pd.read_csv('Trafficking_Data.csv')

st.write(data)