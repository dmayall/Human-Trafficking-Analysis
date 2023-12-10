import pandas as pd 
import altair as alt
import streamlit as st
import urllib
import json
import datetime
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

with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json") as url:
        world = json.load(url)

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
    -Filter by country of citizenship that you are interested in -Done
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
    countries = alt.topo_feature('https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json', 'countries')
    graph_data = graph_data.groupby('Alpha-3 code_x').size().reset_index(name='count')
    graph_data = pd.merge(graph_data, trafficking, how='right', on='Alpha-3 code_x')
    graph_data = graph_data.drop_duplicates(subset=['Numeric code_x'])
    scale_ = alt.Scale(type='band',nice=False, scheme="orangered")
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
        height=500,
        title='Denstiy Of Trafficking Destinations'
    )
    st.altair_chart(plot, use_container_width=True)
    bar = alt.Chart(graph_data).transform_window(
        rank='rank(count)',
        sort=[alt.SortField('count', order='descending')]
    ).transform_filter(
        alt.datum.rank <= 5
    ).mark_bar(color='maroon').encode(
        x='count:Q',
        y='Country_x:O',
        
    )
    
    st.altair_chart(bar, use_container_width=True)
    return plot


def types_bar(graph_data):
    graph_data = graph_data[['Country_x','isForcedLabour','isSexualExploit','isOtherExploit']]
    graph_data = graph_data.set_index('Country_x')
    graph_data = graph_data.eq(1).dot(graph_data.columns + ',').str[:-1].reset_index(name='type')
    graph_data = graph_data.groupby('type').size().reset_index(name='count')
    graph_data = graph_data.replace('', 'Unknown')
    bar = alt.Chart(graph_data, title='Types Of Traffickign by Citizenship').mark_bar(color='maroon').encode(
        x='count',
        y='type',
    )
    st.altair_chart(bar, use_container_width=True)
    return(bar)

def trafficking_over_time(graph_data):
    graph_data = graph_data[['yearOfRegistration','isForcedLabour','isSexualExploit','isOtherExploit']]
    graph_data = graph_data.set_index('yearOfRegistration')
    graph_data = graph_data.eq(1).dot(graph_data.columns + ',').str[:-1].reset_index(name='type')
    graph_data = graph_data.groupby(['yearOfRegistration','type']).size().reset_index(name='count')
    graph_data = graph_data[graph_data['yearOfRegistration'] != 0]
    graph_data = graph_data.replace('', 'Unknown')
    scale_ = alt.Scale(type='band',nice=False, scheme="orangered")
    highlight = alt.selection_point(on='mouseover', fields=['type'], nearest=True)
    base = alt.Chart(graph_data).mark_line(
        interpolate='step-after',
        line=True
    ).encode(
        alt.Color('type:N', scale=scale_),
        x='yearOfRegistration:N',
        y='count',
        tooltip=['type:N','count'],
    )
    points = base.mark_circle().encode(
        opacity=alt.value(0)
    ).add_params(highlight)

    lines = base.mark_line().encode(
    size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )
    plot = points + lines
    st.altair_chart(plot, use_container_width=True)
    return plot

tab1, tab2, tab3 = st.tabs(['Map Density', 'Types of trafficking', 'Amount of trafficking over time'])


with tab1:
    years = trafficking['yearOfRegistration'].astype(int).unique().tolist()
    year = years.remove(0)
    slider = st.slider('Slider for Year', min(years), max(years))
    trafficking = trafficking[trafficking['yearOfRegistration'].isin(range(min(years), slider))]
    map(trafficking)

with tab2:
    types_bar(trafficking)

with tab3:
    trafficking_over_time(trafficking) 
