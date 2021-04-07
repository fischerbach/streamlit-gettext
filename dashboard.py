import streamlit as st
import pandas as pd
import numpy as np
import gettext
_ = gettext.gettext
from os import system, path

from zenserp import Client

language = st.sidebar.selectbox('', ['en', 'pl', 'de'])
try:
  localizator = gettext.translation('base', localedir='locales', languages=[language])
  localizator.install()
  _ = localizator.gettext 
except:
    pass

POT = st.sidebar.button(_('POT generate'))
MO = st.sidebar.button('MO generate')
localazy_upload = st.sidebar.button('Localazy upload')
localazy_download = st.sidebar.button('Localazy download')
if POT:
    system(f'cd {path.dirname(path.realpath(__file__))} & /Library/Frameworks/Python.framework/Versions/3.8/share/doc/python3.8/examples/Tools/i18n/pygettext.py -d base -o locales/base.pot dashboard.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & cp locales/base.pot locales/de/LC_MESSAGES/base.po && cp locales/base.pot locales/pl/LC_MESSAGES/base.po')

if MO:
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/de/LC_MESSAGES/base.mo locales/de/LC_MESSAGES/base & msgfmt -o locales/pl/LC_MESSAGES/base.mo locales/pl/LC_MESSAGES/base')

if localazy_upload:
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy upload')

if localazy_download:
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy download')

apikey = st.sidebar.text_input(_('Enter API key'), type='password')

client = Client(apikey)

@st.cache
def get_results(client, params):
    return client.search(params)

import base64
from io import BytesIO

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df, label='table'):
    val = to_excel(df)
    b64 = base64.b64encode(val)
    return f'<a class="streamlit-button small-button primary-button" href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">🗒️ Download {label} as xlsx file</a>'

if(apikey == ""):
    st.markdown('# Keyword Icebreaker')
    st.markdown(_('## This app uses Zenserp API'))
    st.markdown(_('To use it, you must enter your own API key. Create account: [https://zenserp.com/](https://zenserp.com/)'))
    st.markdown(_('Demo:'))
    st.markdown('<iframe width="560" height="315" src="https://www.youtube.com/embed/3xAl9ktbQGc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>', unsafe_allow_html=True)
    st.markdown(_('Article about it: [Keyword Monitoring Tool: Track your competition in search results](https://medium.datadriveninvestor.com/keyword-monitoring-tool-track-your-competition-in-search-results-83db61f0a696)'))
    st.markdown(_('It is NOT official app. We don\'t save this data anywhere, but if you want to feel safe, you can run the application on your own computer: [https://gist.github.com/fischerbach/1c93e04884f00e424137d179bd2a5093](https://gist.github.com/fischerbach/1c93e04884f00e424137d179bd2a5093) '))
    st.stop()

params = {
    'apikey': apikey
}

st.markdown('# 🧊 Keyword Icebreaker')

status = client.status()
st.markdown(f"Remaining requests: **{status['remaining_requests']}**")

search_engines = client.search_engines()
params['search_engine'] = st.sidebar.selectbox(
    _("Select search_engine domain"),
    search_engines,
    search_engines.index("google.com")
)

if st.sidebar.checkbox(_('Advanced settings')):
    params["location"] = st.sidebar.selectbox(_("The geolocation used in the query"), [""]+client.locations())
    hl = client.hl()
    codes = list(map(lambda x: x['code'], hl))
    names = list(map(lambda x: x['name'], hl))
    params["hl"] = st.sidebar.selectbox(_("Web Interface Language, autodetected from the search_engine if not supplied"), [""]+codes, 0,key=names)

    gl = client.gl()
    codes = list(map(lambda x: x['code'], gl))
    names = list(map(lambda x: x['name'], gl))
    params["gl"] = st.sidebar.selectbox(_("Googles country code, autodetected from the search_engine if not supplied"), [""]+codes, 0,key=names)

    params["num"] = st.sidebar.number_input("num", value=10)

    params['device'] = st.sidebar.radio(
        _("Which device to use: desktop or mobile"),
        ['desktop', 'mobile']
    )

params['q'] = st.text_input(_('Search Query'))

if st.checkbox(_('Show raw request')):
    st.write(params)

st.subheader(_('Settings'))
options = st.multiselect(_('Select part of results page'), ['paid', 'organic', 'related_searches','knowledge_graph','questions','images'])
show_raw_results = st.checkbox(_('Show raw results'))

def display_table(df, label=_('table')):
    st.subheader(label)
    st.write(df)
    st.markdown(get_table_download_link(df, label), unsafe_allow_html=True)

if st.button(_('🔍 Search')):
    import copy
    raw_results = get_results(client, params)
    results = copy.deepcopy(raw_results)
    for option in options:
        if option in results.keys():
            if(option == 'organic'):
                images = next((sub for sub in results[option] if 'images' in sub.keys()), None)
                if images:
                    del results[option][images['position']-1]
                    if 'images' in options:
                        display_table(pd.DataFrame(images['images']), 'images')
            if(option == 'organic'):
                questions = next((sub for sub in results[option] if 'questions' in sub.keys()), None)
                if questions:
                    del results[option][questions['position']-1]
                    if 'questions' in options:
                        display_table(pd.DataFrame(questions['questions']),'questions')
            if(len(results[option])):
                display_table(pd.DataFrame(results[option]),option)
    if(show_raw_results):
        st.write(results)