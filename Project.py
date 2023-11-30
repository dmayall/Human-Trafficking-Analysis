import pandas as pd 
import altair as alt
import streamlit as st
from vega_datasets import data

alt.data_transformers.disable_max_rows()
@st.cache_data
def readData():
    data = pd.read_csv('Trafficking_Data.csv')
    coordinates = pd.read_csv('countries_codes_and_coordinates.csv')
    coordinates = coordinates[['Country', 'Alpha-3 code', 'Latitude (average)', 'Longitude (average)', 'Numeric code']]
    coordinates['Alpha-3 code'] = coordinates['Alpha-3 code'].str.replace('"','')
    coordinates['Longitude (average)'] = coordinates['Longitude (average)'].str.replace('"','').astype(float)
    coordinates['Latitude (average)'] = coordinates['Latitude (average)'].str.replace('"','').astype(float)
    coordinates['Numeric code'] = coordinates['Numeric code'].str.replace('"','').astype(int)
    

    return data, coordinates

trafficking, coordinates = readData()
st.title('Human Trafficking Analysis')
st.write('This Dashboard is to show the different types of trafficking and show the patterns of what people are being trafficked for in different parts of the world.')
#Some prprocessing of the data so that it is easily graphed
trafficking = trafficking.fillna(0)
#I chose to fill with 0's because of the binary part of the conditions of the trafficking
#Here i am replacing the 0's in columns I would rather NA
#Not using np.nan because they are string types not float so doesn't have an affect
trafficking['citizenship'] = trafficking['citizenship'].replace(0,"NA")
trafficking['CountryOfExploitation'] = trafficking['CountryOfExploitation'].replace(0,"NA")
trafficking['traffickMonths'] = trafficking['traffickMonths'].replace(0,'NA') 
#merging to get coordinate data for my map with my coordinate data
coordinates['Alpha-3 code'] = coordinates['Alpha-3 code'].str.strip()
coordinates['Country'] = coordinates['Country'].str.strip()
trafficking['CountryOfExploitation'] = trafficking['CountryOfExploitation'].str.strip()
trafficking = pd.merge(trafficking, coordinates, how='left', left_on='CountryOfExploitation',right_on='Alpha-3 code')

_='''
    Graphing Ideas:
    -Map showing density of country of exploitation
    -Show the reason for trafficking and sex of those being trafficked
    -Show age ranges being trafficked to look for patterns
    Filter ideas
    -Filter by country of citizenship that you are interested in
    -add an optional filter for year
    -optional filter for the types of trafficking 
    '''

#Starting on making a map
#_______________________________________________________________
countries = alt.topo_feature(data.world_110m.url, 'countries')
#Setting the background of all the countries
# background = alt.Chart(countries).mark_geoshape(
#     fill='lightgray',
#     stroke='white'
# ).project(
#     "equirectangular"
# ).properties(
#     width=500,
#     height=300
# )
#Getting data for the points

graph_data = trafficking.groupby('Alpha-3 code').size().reset_index(name='count')
graph_data = pd.merge(graph_data, trafficking, how='left', on='Alpha-3 code')
plot = alt.Chart(countries).mark_geoshape().encode(
    color='count:Q',
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(graph_data, key='Numeric code', fields=['Country', 'count'])
).project('equirectangular')\
.properties(
    width=500,
    height=300,
    title='Denstiy Of Trafficking Destinations'
)

st.altair_chart(plot, use_container_width=True)
