import flask
import os
from flask import render_template
from flask import  request, redirect, url_for, render_template,  jsonify
import threading 
import pandas as pd
from prova import YT_link_converter as converter
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import langid
import stanza
from prova import YT_link_converter as converter
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from statistics import mode
import random
from flask import jsonify


# Crea app Flask 
app = flask.Flask(__name__)
app.config["DEBUG"] = True

text = ''



@app.route('/', methods=['GET'])
def home():
      return render_template('input.html')





@app.route('/random_comment', methods=['GET'])
def get_random_comment():
    #link
    global text
    #converte in path
    cv = converter(text)
    file_name = f'{cv.convert_YT_link(text)}-dataframe-.csv'
    #ottengo il csv 
    csv_path = os.path.join(os.getcwd(), file_name)
    df = pd.read_csv(csv_path)

    # Ottieni una lista di commenti dal DataFrame
    commentsPool = list(df['phrase'])
    # Elimina l'ultimo elemento della lista 
    if commentsPool:
        commentsPool.pop()

    # Estrai un commento casuale dalla lista
    random_comment = random.choice(commentsPool)

    return jsonify({'random_comment': random_comment})


@app.route('/graph', methods=['GET'])
def graphs():
    global text
    sentiment = []
    emotions = []
    Sent_contatore = 0
    Psentiment = [ 0, 1, 2]
    Pemotions = ['sadness', 'joy', 'love', 'anger', 'fear', 'surprise']

    # Crea un'istanza di YT_link_converter
    cv = converter(text)
    # Converti il link YT in file path
    file_name = f'{cv.convert_YT_link(text)}-dataframe-.csv'
    csv_path = os.path.join(os.getcwd(), file_name)
    # CSV -> df 
    df = pd.read_csv(csv_path)
    for i in df['Emotion Type']:
        if i in Pemotions:
            emotions.append(i)
    
    for i in df['sentiment']:
        if i in Psentiment:
            sentiment.append(i)
            Sent_contatore += 1


    #print(emotions)
    media_sentiment = sum(sentiment) / Sent_contatore if Sent_contatore != 0 else 0

    
    # Calcola l'emozione predominante
    predominant_emotion = mode(emotions) if emotions else None


    

    return render_template('graph.html', emotions=emotions, sentiment=sentiment,
                            media_sentiment=media_sentiment, predominant_emotion= predominant_emotion)
                            







@app.route('/input', methods=['GET','POST'])
def input():
    global text
    if request.method == 'POST':
        text = request.form.get('text')
        return redirect(url_for('loading'))

    return render_template('input.html')







@app.route('/loading', methods=['GET'])
def loading():
    global text
    

    def scraping(link):

        df = pd.DataFrame(columns=['phrase', 'sentiment', 'Emotion Type'])

        #Sentiment
        stanza.download('en',package='sentiment')
        nlp = stanza.Pipeline('en',processors='tokenize,sentiment')

        #Emotions
        tokenizer = AutoTokenizer.from_pretrained("mrm8488/t5-base-finetuned-emotion",legacy=False)
        model = AutoModelForSeq2SeqLM.from_pretrained("mrm8488/t5-base-finetuned-emotion")


        # Funzione per determinare il tipo di emozione associato a un testo
        def emotionType(text):
            # Codifica il testo con l'aggiunta di '</s>'
            input_ids = tokenizer.encode(text + '</s>', return_tensors='pt')
            # Genera un output basato sugli input
            output = model.generate(input_ids=input_ids,
                                    max_length=2)
            # Decodifica gli ID token restituiti nell'output
            dec = [tokenizer.decode(ids) for ids in output]
            #print('dec',dec)
            
            # Estrae e restituisce l'etichetta dell'emozione dal risultato decodificato
            label = dec[0]
            # print('label',label)
            label = label.split(" ")
            #print('label',label)
            label = label[1]  
            #print('label',label)      
            return label






        def is_english(text):
            # Utilizza langid per rilevare la lingua del testo
            lang, _ = langid.classify(text)

            # Restituisce True se la lingua rilevata è inglese
            return lang == 'en'


        #Webdriver
        file_path_chrome = '/Users/pietro/Desktop/progettoesameIL/chromedriver-mac-arm64/chromedriver'
        # Creazione di un'istanza del servizio Chrome con il percorso del driver specificato
        service = Service(executable_path=file_path_chrome)
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(service=service, options=options)


        #strumento per convertire il link
        cv = converter(link)
        # Caricamento della pagina web
        h = driver.get(link)
        

        time.sleep(3)

        element = driver.find_element(by='xpath',value='/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[4]/div[2]/div[6]/div[1]/ytd-button-renderer[1]/yt-button-shape/button')

        # Esegui il clic sull'elemento
        element.click()
        time.sleep(2)
        for i in range(1,100): #carica i commenti
            driver.execute_script("window.scrollBy(0, 600);")
            time.sleep(0.1)
        time.sleep(2)
        #find all element by xpath comment you tube
        comments = driver.find_elements(by='xpath',value='//*[@id="content-text"]') #recupera tutti gli elementi con l'id content-text
        print('numero commenti',len(comments))
        comments = comments[:100] 
        
        
        startTime = time.time() 

        def thread(comment):
            
            

            
            # Verifica se il testo è in inglese
            try:
                if is_english(str(comment.text)): #trasforma il testo in una stringa prima di verificare se è in inglese
                    

                    doc = nlp(comment.text)  # analisi del sentiment sulla frase


                    sentimento = doc.sentences[0].sentiment
                    # print(f"Sentimento della frase: {sentiment}")
                    frase = comment.text
                    #usare funzione per ottenere emozione e inserire tipo di emozione in una nuova colonna nel csv
                    colonna_emotionType = emotionType(frase)
                    #print(colonna_emotionType)




                    add_row = {
                            'phrase': frase,
                            'sentiment': sentimento,
                            'Emotion Type': colonna_emotionType
                    }

                    # Crea un nuovo dataframe 
                    df1 = pd.DataFrame(add_row, index=[0])


                    return df1 

                else:
                    print("Il testo non è in inglese.")
                    
            except Exception as e:
                print(f"Error during sentiment analysis: {e}")
                


        for comment in comments:
            df =  df._append(thread(comment), ignore_index=True)
            print(df)
            #print(f"Commento {i} analizzato.")


        new_row= {'phrase': 'True!!!'}
        df = df._append(new_row, ignore_index=True)
        with open(f'{cv.convert_YT_link(link)}-dataframe-.csv' , 'w') as p:
            df.to_csv(p, index=False)

        driver.close()
        endTime = time.time()
        print(f"Tempo impiegato: {endTime - startTime} seconds")
        

        

    def text_analysis(text):
     scraping(text)

    


    analysis_thread = threading.Thread(target=text_analysis, args=(text,)) 
    analysis_thread.start()

    
    
    
    return render_template('loading.html')
    

@app.route('/processing', methods=['GET'])
def processing():
    global text 

    # Crea un'istanza della classe converter 
    cv = converter(text)

    # Converti il link YT in un file path 
    file_name = f'{cv.convert_YT_link(text)}-dataframe-.csv'
    csv_path = os.path.join(os.getcwd(), file_name)
    
    try:
        # CSV -> df
        df = pd.read_csv(csv_path)

        if df.iloc[-1, 0] == "True!!!":
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'})
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': f'File not found: {file_name}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'})

    


app.run()
