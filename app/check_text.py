import streamlit as st
from st_btn_select import st_btn_select
from annotated_text import annotated_text, annotation
import pandas as pd
from somajo import SoMaJo
from iwnlp.iwnlp_wrapper import IWNLPWrapper
from io import StringIO
from docx2python import docx2python
import os
from striprtf.striprtf import rtf_to_text
from odfdo import Document

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

    Note: latest processed IWNLP dump https://dbs.cs.uni-duesseldorf.de/datasets/iwnlp/IWNLP.Lemmatizer_20181001.zip
    :return: a tuple
    """
    tokenizer_somajo = SoMaJo("de_CMC", split_camel_case=True)
    # TODO improve performance
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


def lemmatize_word(word, lemmatizer_iwnlp):
    '''
    The function returns the highest rated lemma of the given word
    :param word: a given word
    :param lemmatizer: the IWNLP lemmatizer
    :return: the word lemma
    '''
    word_lemma_list = lemmatizer_iwnlp.lemmatize_plain(word.replace(' ', ''))
    if not word_lemma_list:
        word_lemma = ''
    else:
        # TODO check if the first element in the list is the best option
        word_lemma = word_lemma_list[0]
    return word_lemma


def replace_word(token, dict_wordlist, lemmatizer):
    '''
    The text is extracted from the given token. If the extracted word is contained in the word list, then it is replaced 
    with a tuple built so that the word gets highlighted (in the syntax of st.annotated_text).
    A space is added after the word, if it present in the text (this is verified with the space_after parameter).
    Asterisks are escaped to avoid collisions with the markup syntax.
    The word is highlighted in red/green depending on whether it is marked derogatory or not in the excel file.
    :param word: a given token
    :param dict_wordlist: the researched words plus synomimes as dictionary
    :param lemmatizer: the IWNLP lemmatizer
    :return:
    '''
    word = token.text
    space_after_word = token.space_after
    word_lemma = lemmatize_word(word, lemmatizer)

    # If the word's lemma is contained in the word list, the words is highlighted.
    # else Asterisks are escaped.
    if word_lemma in dict_wordlist.keys():
        background_color = '#faaa' if dict_wordlist[word_lemma]["abwertend"] == 'ja' else '#50C878'
        replaced_word = annotation(word,
                                   background=background_color,
                                   color="black",
                                   border='1px solid gray')
    else:
        replaced_word = word.replace('*', '\*') + ' ' if space_after_word else word.replace('*', '\*')

    return replaced_word


def run_analysis(text, filename, lemmatizer):
    '''
    The function analyses a given text, substitutes to the given words a corresponding tuple so that the word can be
    highlighted with annotated_text and synonym/origin displayed in the sidebar.
    :param input_text: the text to be analysed
    :param filename: the file with the wordlist
    :return: the text + sidebar to be displayed in the app
    '''
    # read the wordlist as a dictionary
    dict_words = read_excel_to_dict(filename)

    # split text in paragraphs
    input_text = text.split('\n')
    # tokenize input text, as a list of sentences
    text_tokenized = []
    for paragraph in input_text:
        tokenized_paragraphs = tokenizer_somajo.tokenize_text([paragraph])
        text_tokenized.append([[token for token in sentence] for sentence in tokenized_paragraphs])
    # check if the input text contains the words in the wordlist (faster if using sets)
    text_tokenized_set = {lemmatize_word(word.text, lemmatizer) for paragraph in text_tokenized for sentence in paragraph for word in sentence}
    dict_words_set = set(dict_words.keys())
    text_output = []
    jiddish_set = text_tokenized_set.intersection(dict_words_set)

    if jiddish_set:
        st.info(f'Dein Text enthält {len(jiddish_set)} Stelle(n) mit aus dem Jiddischen stammenden Wörtern.')
        for paragraph in text_tokenized:
            text_output = []
            paragraph_enriched = []
            for sentence in paragraph:
                # highlight word
                sentence_enriched = [replace_word(token, dict_words, lemmatizer) for token in sentence]
                paragraph_enriched = paragraph_enriched + sentence_enriched
            paragraph_output = annotated_text(*paragraph_enriched)
            text_output.append(paragraph_output)

        # add the words' origins/synonym to the sidebar
        # turn a set into an alphabetically ordered list
        jiddish_list = list(jiddish_set)
        jiddish_list.sort(key=str.lower)
        st.sidebar.header('**Herkunft**')
        for word in jiddish_list:
            word_lemma = lemmatize_word(word, lemmatizer)
            st.sidebar.subheader(f'*{word_lemma}*')
            st.sidebar.write(f'''
                              {format_comments_for_sidebar(dict_words[word]["Kommentar"])}  
                              ***Alternative***: {dict_words[word_lemma]["Synonyme"]}  
                              ___
                              ''')

    else:
        st.info('Dein Text enthält keine aus dem Jiddischen stammenden Wörter.')
        text_output = st.write('  \n'.join(input_text))

    return text_output


def format_comments_for_sidebar(text):
    """
    Formats comments to the words in the wordlist for a clearer display in the sidebar.

    :param text: The input text to be formatted.
    :type text: str

    :return: The formatted text ready for display.
    :rtype: str
    """
    return text.replace('Jiddisch:', '*Jiddisch:*').replace('für:', '*für:*').replace('Abwertung:', '*Abwertung:*')


def read_uploaded_file_content(uploaded_file, file_extension):
    """
    Read the content of a file uploaded via st.file_uploader and return it as a string.

    :param uploaded_file: A file object representing the uploaded file.
    :param file_extension: The extension of the uploaded file.
    :return: The content of the uploaded file as a string.

    This function reads the content of an uploaded file and returns it as a string.
    Depending on the file extension, different methods are used to extract the content:

    - For `.txt` and `.rtf` files, the content is decoded and returned directly.
    - For `.docx` files, the content is extracted using `docx2python`.
    - For `.odt` files, the content is extracted using `odfdo.Document`.

    Note:
    Note that the formatting is lost, as st.annotated_text currently (Jan. 2024)
    supports custom formatting only for the annotations and not for the rest of the text.
    """
    file_content = ''
    if file_extension in ('.txt','.rtf'):
        # To convert to a string based IO:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        if file_extension == '.txt':
            file_content = stringio.read()
        elif file_extension == '.rtf':
            file_content = rtf_to_text(stringio.read())
    elif file_extension == '.docx':
        file_content = docx2python(uploaded_file,html=False).text
    elif file_extension == '.odt':
        doc = Document(uploaded_file).body
        extracted_text = []
        # Iterate through paragraphs in the document
        for paragraph in doc.get_paragraphs():
            # Add text of each paragraph to the list
            extracted_text.append(paragraph.get_formatted_text())
        # Join the list of paragraphs into a single string
        file_content='\n'.join(extracted_text)
    return file_content


# configure sidebar
st.sidebar.image('logo.png')
# configure page structure
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
    
        if st.button('Analysiere deinen Text', key='text_from_input'):
            run_analysis(text, 'app/wordlist.xlsx', lemmatizer_iwnlp)

    with tab2:
        uploaded_file = st.file_uploader('Lade hier deine Text-Datei hoch:', 
                                         type=['txt', 'rtf', 'docx', 'odt'],
                                         help='Unterstützte Formate: txt, rtf, docx, odt.')
        if st.button('Analysiere deinen Text', key='text_from_file'):
            if uploaded_file:
                file_extension = os.path.splitext(uploaded_file.name)[-1].lower()
                file_content = read_uploaded_file_content(uploaded_file, file_extension)
                run_analysis(file_content, 'app/wordlist.xlsx', lemmatizer_iwnlp)


elif page == navigation_buttons[1]:
    # st.header(" ", anchor='test')
    # expander = st.expander('Hintergrund und Quellen', expanded=False)
    # # expander.write('Background info here')
    # # expander.write('Quellen')
    st.write('''
    * Steinke, R. (2020) Antisemitismus in der Sprache. Duden Bibliograph. Instit. GmbH.
    * Deutsche Welle. Alltagsdeutsch – Podcast: Dufte! – Jiddische Wörter im Deutschen. https://www.dw.com/de/dufte-jiddische-w%C3%B6rter-im-deutschen/a-4786777. 2022
    * Schwarz-Friesel, M., & Reinharz, J. (2013). Die Sprache der Judenfeindschaft im 21. Jahrhundert (1st ed.). De Gruyter. http://www.jstor.org/stable/j.ctvbkjx39''')