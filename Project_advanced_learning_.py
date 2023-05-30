from __future__ import print_function
import openai
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
import time 
import re
import speech_recognition as sr
import os 
import webbrowser
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
import google.auth
import streamlit as st
import soundfile as sf
import sounddevice as sd
import wavfile as wav
import numpy as np
import wave 
import tempfile
import functools
#--Définition de la clé API OpenAI---#
openai.api_key = "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"

# Convert speech to text
@st.cache_data
def myCommand(audio_file):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    try:
        command = r.recognize_google(audio).lower()
        print( "your command:' + command + '\n')
    except sr.UnknownValueError:
        print('Your last command couldn\'t be heard')
        return None 
    return command

# Fonction pour enregistrer l'audio
@st.cache_data
def record_audio(duration):
    fs = 44100  # Fréquence d'échantillonnage
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Attente de la fin de l'enregistrement

    # Sauvegarde de l'audio en tant que fichier WAV
    filename = "enregistrement.wav"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        audio_file = tmpfile.name
        sf.write(tmpfile.name, audio, fs) 
    return audio_file

# Titre du formulaire
st.title("Quiz Form")
st.write("Record your audio:")
# Affichage de l'interface utilisateur pour l'enregistrement audio
duration = st.slider("Recording time (in seconds)", 1, 10, 5)
record_button = st.button("Submit")

if record_button:
    st.info("Enregistrement en cours...")
    audio_file = record_audio(duration)
    st.success("Enregistrement terminé !")

    # Utilisez la variable 'audio_file' pour accéder au fichier audio WAV enregistré

    # Appel de la fonction myCommand() pour obtenir le texte de la commande audio
    text = myCommand(audio_file)

    # Using OpenAI API to get text-based response from user
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": text}
        ]
    )
    print(completion.choices[0].message.content)
    # Using regular expressions to extract questions, options and answers from the resulting text

    quest = re.compile(r'^\d+(?:\)|\.|\-)(.+\?$)')  
    opt = re.compile(r'^[a-zA-Z](?:\)|\.|\-)(.+$)')
    ans= re.compile(r'Answer:\s[a-zA-Z](?:\)|\.|\-)(.+$)')
    text = completion.choices[0].message.content
    questions = []
    options=[]
    sub =[]
    answers =[]
    for line in text.splitlines():
        if line == '':
            if sub:
                options.append(sub)
                sub=[]
        else:
            if quest.match(line):
                line_mod = line.strip()
                questions.append(line_mod)
            if opt.match(line):
                line_mod = line.strip()
                sub.append(line_mod)
            if ans.match(line):
                line_mod= line.strip()
                if line_mod.lower()== "all of the above":
                    answers.append(options[-1])
                else:
                    answers.append([line_mod,])
    if sub:
        options.append(sub)
   
    print(len(questions))
    print(len(options))
    print(len(answers))

#Content_text ="I need Deep Learning 10 questions and multiple-choice with their answers"
#-------------------Create Quiz Form ----------------------#
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('C:/Users/asus/OneDrive/Bureau/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

# Request body for creating a form
    NEW_FORM = {
        "info": {
            "title": "Quiz form",
        }
    }
# Creates the initial form
    result = form_service.forms().create(body=NEW_FORM).execute()
# Request body to add a multiple-choice question
# JSON to convert the form into a quiz
    update = {
        "requests": [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            }
        ]
    }
# Converts the form into a quiz
    question_setting = form_service.forms().batchUpdate(formId=result["formId"],body=update).execute()
    for i in range(len(questions)): 
        sorted_options = sorted(options[i])
        NEW_QUESTION = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": questions[i],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value":j} for j in sorted_options],
                                    "shuffle": True
                                }
                            }
                        },
                    },
                    "location": {
                        "index": i

                    }
                }
            }]
        }
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()
    get_result = form_service.forms().get(formId=result["formId"]).execute()
    print(get_result['responderUri'])

# Titre du formulaire
    st.title("Quiz link")
    st.write(get_result['responderUri'])
# Affichage de chaque question et récupération des réponses de l'utilisateur
#   for i in range(len(questions)):
#       st.subheader(f"Question {i+1}: {questions[i]}")
#       user_input = st.radio("Choisissez une option", options[i], key=f"question_{i}")
#       st.write("Votre réponse:", user_input)
#       st.write("---")
