import streamlit as st
from annotated_text import annotated_text, annotation
import pandas as pd
from somajo import SoMaJo
from iwnlp.iwnlp_wrapper import IWNLPWrapper

st.set_page_config(page_title='Agathe App', layout='wide')


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

text = st.text_area('Gib hier deinen Text ein:', '''''')
txt = text.split("\n")


def read_excel_to_dict(excel_file):
    '''
    Reads an excel file and converts it to a dictionary
    :param excel_file: the given (local) excel file
    :return: a dictionary
    '''
    df_from_excel = pd.read_excel(excel_file, index_col=0, dtype=str)
    dict_from_excel = df_from_excel.to_dict('index')
    return dict_from_excel


def replace_word(word, dict_wordlist, lemmatizer):
    '''
    If the given word is contained in the word list, then it is replaced with a tuple built so that the word gets
    highlighted and an alternative is displayed (in the syntax of st.annotated_text).
    :param word: a given word
    :param dict_wordlist: the researched words plus synomimes as dictionary
    :param lemmatizer: the IWNLP lemmatizer
    :return:
    '''
    word_lemma = lemmatize_word(word, lemmatizer)
    if word_lemma in dict_wordlist.keys():
        replaced_word = annotation(word,
                                   f'Alternative: {dict_wordlist[word_lemma]["Synonyme"]}',
                                   background='#faaa',
                                   color="black",
                                   border='1px solid gray')
    else:
        replaced_word = word + ' '

    return replaced_word


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


def run_analysis(input_text, filename):
    '''
    The function analyses a given text, substitutes to the given words a coresponding tuple so that the word can be
    highlighted and synonim displayed with annotated_text
    :param input_text: the text to be analysed
    :param filename: the file with the wordlist
    :return: the text to be displayed in the app
    '''
    dict_words = read_excel_to_dict(filename)

    text_tokenized = []
    for paragraph in input_text:
        tokenized_paragraphs = tokenizer_somajo.tokenize_text([paragraph])
        text_tokenized.append([[token.text for token in sentence] for sentence in tokenized_paragraphs])

    text_tokenized_set = {word for paragraph in text_tokenized for sentence in paragraph for word in sentence}

    dict_words_set = set(dict_words.keys())
    text_output = []
    if text_tokenized_set.intersection(dict_words_set):
        for paragraph in text_tokenized:
            text_output = []
            paragraph_enriched = []
            for sentence in paragraph:
                sentence_enriched = [replace_word(item, dict_words, lemmatizer_iwnlp) for item in sentence]
                paragraph_enriched = paragraph_enriched + sentence_enriched
            paragraph_output = annotated_text(*paragraph_enriched)
            text_output.append(paragraph_output)
    else:
        st.info(f'Dein Text enthält keine aus dem Jiddischen stammenden Wörter!')
        text_output = st.write('  \n'.join(input_text))

    return text_output


if st.button('Analysiere deinen Text'):
    run_analysis(txt, 'app/wordlist.xlsx')
