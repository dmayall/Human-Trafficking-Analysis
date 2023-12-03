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
    data = data.fillna(0)
    #I chose to fill with 0's because of the binary part of the conditions of the trafficking
    #Here i am replacing the 0's in columns I would rather NA
    #Not using np.nan because they are string types not float so doesn't have an affect
    data['citizenship'] = data['citizenship'].replace(0,"NA")
    data['CountryOfExploitation'] = data['CountryOfExploitation'].replace(0,"NA")
    data['traffickMonths'] = data['traffickMonths'].replace(0,'NA') 
    #merging to get coordinate data for my map with my coordinate data
    coordinates['Alpha-3 code'] = coordinates['Alpha-3 code'].str.strip()
    coordinates['Country'] = coordinates['Country'].str.strip()
    data['CountryOfExploitation'] = data['CountryOfExploitation'].str.strip()

    return data, coordinates

trafficking, coordinates = readData()
st.title('Human Trafficking Analysis')
st.write('This Dashboard is to show the different types of trafficking and show the patterns of what people are being trafficked for in different parts of the world.')

trafficking = pd.merge(trafficking, coordinates, how='left', left_on='CountryOfExploitation',right_on='Alpha-3 code')
trafficking = pd.merge(trafficking, coordinates, how='left', left_on='citizenship',right_on='Alpha-3 code')
#country_y is the citizenship country
#country_x is country trafficked to
_='''
    Graphing Ideas:
    -Map showing density of country of exploitation -Done
    -Show the reason for trafficking and sex of those being trafficked
    -Show age ranges being trafficked to look for patterns

    Filter ideas
    -Filter by country of citizenship that you are interested in
    -add an optional filter for year
    -optional filter for the types of trafficking 
    '''
#Filters
country_choice = ['All'] + trafficking['Country_y'].unique().tolist()
country = st.sidebar.selectbox('Select Country of Citizenship', country_choice)
if country == 'All':
    trafficking, coordinates = readData()
    trafficking = pd.merge(trafficking, coordinates, how='left', left_on='CountryOfExploitation',right_on='Alpha-3 code')
    trafficking = pd.merge(trafficking, coordinates, how='left', left_on='citizenship',right_on='Alpha-3 code')

else:
    trafficking = trafficking[trafficking['Country_y'] == country]


def map(graph_data):
    _='''
        This function creates a cholorpleth map of the 
        denstiy of people trafficked to that country by percentage

        Parameters: 
        -Graph Data is filtered data we are tyring to graph

        Returns:
        -returns the map
    '''
    #setup for the plot
    countries = alt.topo_feature(data.world_110m.url, 'countries')
    graph_data = trafficking.groupby('Alpha-3 code_x').size().reset_index(name='count')
    graph_data = pd.merge(graph_data, trafficking, how='right', on='Alpha-3 code_x')
    graph_data = graph_data.drop_duplicates(subset=['Numeric code_x'])
    scale_ = alt.Scale(type='band',nice=False, scheme="bluegreen")
    #plotting
    plot = alt.Chart(countries).mark_geoshape().transform_lookup(
        lookup='id',
        from_=alt.LookupData(graph_data, key='Numeric code_x', fields=['Country_x', 'count'])
    ).project('equirectangular').encode(
        alt.Color('count:Q',
                scale=scale_,
                legend=alt.Legend(direction="horizontal", orient="bottom", format="10000"),

        ),
        tooltip=['Country_x:O', 'count:Q']
    ).properties(
        width=500,
        height=300,
        title='Denstiy Of Trafficking Destinations'
    )

    st.altair_chart(plot, use_container_width=True)

map(trafficking)
#End of mapping 