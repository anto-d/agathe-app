import streamlit as st
from annotated_text import annotated_text, annotation
import pandas as pd
from somajo import SoMaJo
from nltk.stem.snowball import SnowballStemmer

st.set_page_config(page_title='Agathe App', layout='wide')

# configure sidebar
st.sidebar.image('logo.png')
st.sidebar.title('*Erster Entwurf*')
st.sidebar.write('''
Ein Projekt von:  

 Antonella D'Avanzo  
 Sabrina Sarkodie-Gyan  
 Susanne Molter    
''')

# st.sidebar.caption('Made with python')

st.title('Agathe App')
st.subheader('*Entwurf*')
"""

In der deutschen Sprache gibt es zahlreiche Lehnwörter, die aus dem Jiddischen stammen. Viele davon haben eine 
ähnliche Bedeutung, sind aber im Deutschen oft negativ konnotiert. Diese Konnotation wurde den Begriffen jedoch erst 
mit ihrer Entlehnung in die deutsche Sprache zugeschrieben. 

Das Tool hilft dir, solche Wörter in deinen geschrieben Texten zu erkennen: es markiert sie und schlägt dir 
eine Alternative/ein Synonym vor.

---"""

txt = st.text_area('Gib hier deinen Text ein:', '''''')

#


def read_excel_to_dict(excel_file):
    '''
    Reads an excel file and converts it to a dictionary
    :param excel_file: the given (local) excel file
    :return: a dictionary
    '''
    df_from_excel = pd.read_excel(excel_file, index_col=0, dtype=str)
    dict_from_excel = df_from_excel.to_dict('index')
    return dict_from_excel


def build_replacement(dict_wordlist):
    '''
    The functions builds a dictionary to be used to produce the inpu by st.annotated_text: the key is a given word
    and the value is a tuple built so that the word gets highlighted and an alternative is displayed.
    :param dict_wordlist: the researched words plus synomimes as dictionary
    :return:
    '''
    dict_replacement = {word: annotation(word,
                                         f'Alternative: {dict_wordlist[word]["Synonyme"]}',
                                         background='#faaa',
                                         color="black",
                                         border='1px solid gray')
                        for word in dict_wordlist.keys()}
    dict_replacement['schmus'] = annotation('schmusen',
                                            f'Alternative: {dict_wordlist["schmusen"]["Synonyme"]}',
                                            background='#73e000',
                                            # background='#faaa',
                                            color="black",
                                            border='1px solid gray')

    return dict_replacement


def stem_word(word):
    '''
    The function returns the stem of the given word
    :param word: a word
    :return: the word stem
    '''
    # TODO try further stemming or lemmatizing tools with spacy, treetagger or HanTa (or nltk cistem)
    snow_stemmer = SnowballStemmer(language='german')
    word_stem = snow_stemmer.stem(word.replace(' ', ''))
    return word_stem


def run_analysis(input_text, filename):
    '''
    The function analyses a given text, substitutes to the given words a coresponding tuple so that the word can be
    highlighted and synonim displayed with annotated_text
    :param input_text: the text to be analysed
    :param filename: the file with the wordlist
    :return: the text to be displayed in the app
    '''
    dict_words = read_excel_to_dict(filename)
    dict_replacements = build_replacement(dict_words)
    # TODO support for newlines
    tokenizer = SoMaJo("de_CMC", split_camel_case=True)
    sentences = tokenizer.tokenize_text([input_text])
    text_tokenized = []
    for sentence in sentences:
        for token in sentence:
            text_tokenized.append(token.text)

    text_tokenized_set = set(text_tokenized)
    dict_words_set = set(dict_words.keys())
    if text_tokenized_set.intersection(dict_words_set):
        text_enriched = [dict_replacements[item] if stem_word(item) in dict_replacements.keys() else item + ' '
                         for item in text_tokenized]
        text_output = annotated_text(*text_enriched)
    else:
        st.info(f'Dein Text enthält keine aus dem Jiddischen stammenden Wörter!')
        text_output = st.write(input_text)

    return text_output


if st.button('Analysiere deinen Text'):
    run_analysis(txt, 'app/wordlist.xlsx')

