import streamlit as st
from st_btn_select import st_btn_select
from annotated_text import annotated_text, annotation
import pandas as pd
from somajo import SoMaJo
from iwnlp.iwnlp_wrapper import IWNLPWrapper

st.set_page_config(page_title='Agathe App')#, layout='wide')

# load nlp components
@st.cache_data
def load_nlp_resources():
    """
    Load and initialize necessary resources for natural language processing.

    This function loads the SoMaJo tokenizer for German language with the 'de_CMC' model
    and sets the 'split_camel_case' option to True for improved tokenization performance.
    It also loads the IWNLP lemmatizer wrapper with the specified path to the lemmatizer JSON file.

    Returns:
    - tokenizer_somajo (SoMaJoTokenizer): A tokenizer object from SoMaJo.
    - lemmatizer_iwnlp (IWNLPWrapper): A wrapper object for the IWNLP lemmatizer.

    Note: IWNLP lemmatizer file http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
    :return: a tuple
    """
    tokenizer_somajo = SoMaJo("de_CMC", split_camel_case=True)
    # TODO improve performance
    # latest processed IWNLP dump: http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
    lemmatizer_iwnlp = IWNLPWrapper(lemmatizer_path='app/IWNLP.Lemmatizer_20181001.json')
    return tokenizer_somajo, lemmatizer_iwnlp


tokenizer_somajo, lemmatizer_iwnlp = load_nlp_resources()


def read_excel_to_dict(excel_file):
    '''
    Reads an excel file and converts it to a dictionary
    :param excel_file: the given (local) excel file
    :return: a dictionary
    '''
    df_from_excel = pd.read_excel(excel_file, index_col=0, dtype=str).fillna('N/A')
    dict_from_excel = df_from_excel.to_dict('index')
    return dict_from_excel


def lemmatize_word(word, lemmatizer):
    '''
    The function returns the lemma of the given word
    :param word: a given word
    :param lemmatizer: the IWNLP lemmatizer
    :return: the word lemma
    '''
    word_lemma_list = lemmatizer.lemmatize_plain(word.replace(' ', ''))
    if not word_lemma_list:
        word_lemma = ''
    else:
        # TODO check if the first element in the list is the best option
        word_lemma = word_lemma_list[0]
    return word_lemma


def replace_word(token, dict_wordlist, lemmatizer):
    '''
    The text is extracted from the given token. If the extracted word is contained in the word list, then it is replaced 
    with a tuple built so that the word gets highlighted and an alternative is displayed (in the syntax of st.annotated_text).
    A space is added after the word, if it present in the text (this is verified with the space_after parameter).
    Asterisks are escaped to avoid collisions with the markup syntax.
    :param word: a given token
    :param dict_wordlist: the researched words plus synomimes as dictionary
    :param lemmatizer: the IWNLP lemmatizer
    :return:
    '''
    word = token.text
    space_after_word = token.space_after
    word_lemma = lemmatize_word(word, lemmatizer)

    if word_lemma in dict_wordlist.keys():
        # 9F2B68
        background_color = '#faaa' if dict_wordlist[word_lemma]["abwertend"] == 'ja' else '#50C878'
        replaced_word = annotation(word,
                                   #f'Alternative: {dict_wordlist[word_lemma]["Synonyme"]}',
                                   background=background_color,
                                   color="black",
                                   border='1px solid gray')
    else:
        replaced_word = word.replace('*', '\*') + ' ' if space_after_word else word.replace('*', '\*')

    return replaced_word


def run_analysis(input_text, filename, lemmatizer):
    '''
    The function analyses a given text, substitutes to the given words a corresponding tuple so that the word can be
    highlighted and synonim displayed with annotated_text
    :param input_text: the text to be analysed
    :param filename: the file with the wordlist
    :return: the text to be displayed in the app
    '''

    # read the wordlist
    dict_words = read_excel_to_dict(filename)

    # tokenize input text, as a list of sentences
    text_tokenized = []
    for paragraph in input_text:
        tokenized_paragraphs = tokenizer_somajo.tokenize_text([paragraph])
        text_tokenized.append([[token for token in sentence] for sentence in tokenized_paragraphs])

    text_tokenized_set = {word.text for paragraph in text_tokenized for sentence in paragraph for word in sentence}

    # check if the input text contains the words in the wordlist
    dict_words_set = set(dict_words.keys())
    text_output = []
    jiddish_set = text_tokenized_set.intersection(dict_words_set)
    if jiddish_set:
        
        st.info(f'Dein Text enthält {len(jiddish_set)} Stelle(n) mit aus dem Jiddischen stammenden Wörtern.')
        for paragraph in text_tokenized:
            text_output = []
            paragraph_enriched = []
            for sentence in paragraph:
                sentence_enriched = [replace_word(token, dict_words, lemmatizer) for token in sentence]

                paragraph_enriched = paragraph_enriched + sentence_enriched
            paragraph_output = annotated_text(*paragraph_enriched)
            text_output.append(paragraph_output)

        # add the words' origins to the sidebar
        # turn a set into an alphabetically ordered list
        jiddish_list = list(jiddish_set)
        jiddish_list.sort()
        st.sidebar.header('Herkunft')
        for word in jiddish_list:
            word_lemma = lemmatize_word(word, lemmatizer)
            st.sidebar.subheader(f'*{word_lemma}*')
            st.sidebar.write(dict_words[word]['Herkunft'])
            st.sidebar.write(f'Alternative: {dict_words[word_lemma]["Synonyme"]}')
            st.sidebar.markdown('-------')

    else:
        st.info(f'Dein Text enthält keine aus dem Jiddischen stammenden Wörter.')
        text_output = st.write('  \n'.join(input_text))

    return text_output


# configure sidebar
st.sidebar.image('logo.png')
# st.sidebar.title('*Erster Entwurf*')
# st.sidebar.write('''
# Ein Projekt von:  

#  Antonella D'Avanzo  
#  Sabrina Sarkodie-Gyan  
#  Susanne Molter    
# ''')

# st.sidebar.caption('Made with python')

st.title('Agathe App')
st.subheader('*Entwurf*')
navigation_buttons = ('Textanalyse', 'Hintergrund')
page = st_btn_select(navigation_buttons, index=0)

if page == navigation_buttons[0]:
    """

    In der deutschen Sprache gibt es zahlreiche Lehnwörter, die aus dem Jiddischen stammen. Viele davon haben eine 
    ähnliche Bedeutung, sind aber im Deutschen oft negativ konnotiert. Diese Konnotation wurde den Begriffen jedoch erst 
    mit ihrer Entlehnung in die deutsche Sprache zugeschrieben. 

    Das Tool hilft dir, solche Wörter in deinen geschrieben Texten zu erkennen: es markiert sie und schlägt dir 
    eine Alternative/ein Synonym vor.

    ---"""
    tab1, tab2 = st.tabs(['Enter text', 'Upload file'])

    with tab1:
        text = st.text_area('Gib hier deinen Text ein:', '''''', help= 'Test')
        txt = text.split('\n')
    
        if st.button('Analysiere deinen Text'):
            run_analysis(txt, 'app/wordlist.xlsx', lemmatizer_iwnlp)

    with tab2:
        uploaded_file = st.file_uploader('Lade hier deine Text-Datei hoch:', help='Unterstützte Formate: txt, pdf, doc, odt.')
        st.write('placeholder, WIP')

elif page == navigation_buttons[1]:
    # st.header(" ", anchor='test')
    # expander = st.expander('Hintergrund und Quellen', expanded=False)
    # # expander.write('Background info here')
    # # expander.write('Quellen')
    st.write('''
    * Steinke, R. (2020) Antisemitismus in der Sprache. Duden Bibliograph. Instit. GmbH.
    * Deutsche Welle. Alltagsdeutsch – Podcast: Dufte! – Jiddische Wörter im Deutschen. https://www.dw.com/de/dufte-jiddische-w%C3%B6rter-im-deutschen/a-4786777. 2022
    * Schwarz-Friesel, M., & Reinharz, J. (2013). Die Sprache der Judenfeindschaft im 21. Jahrhundert (1st ed.). De Gruyter. http://www.jstor.org/stable/j.ctvbkjx39''')