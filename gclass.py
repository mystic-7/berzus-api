#Recursos
import pandas as pd
import numpy as np
import re
import os.path
import pickle
import base64
import codecs
from datetime import date, datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class gapi:
    def __init__(self, number):
        self.number = number

    def call(self):
        #Si se modifican los SCOPES, borrar el archivo token.pickle.
        SCOPES = ['https://mail.google.com/','https://www.googleapis.com/auth/spreadsheets']
        #Proceso de conexión
        self.creds = None
        #Busqueda de token
        if os.path.exists('token.pickle'+str(self.number)+''):
            with open('token.pickle'+str(self.number)+'', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/Users/keilamarin/Documents/Bancumbre/Bot_ZELLE/API/berzus_creds.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle'+str(self.number)+'', 'wb') as token:
                pickle.dump(self.creds, token)

    def mail(self):
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Encontrar LabelId de etiqutas
        results = gmail.users().labels().list(
            userId='me'
        ).execute()
        labels = results.get('labels',[])
        
        data_list = []
        tag_list = ['BOFA', 'TRU', 'CHASE', 'WELLS', 'REGIONS']
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
                    #Si etiqueta es BOFA o CHASE se utiliza metadata
                    if tag == 'BOFA' or tag == 'CHASE':
                        #Filtrar mensajes por lable, no leidos y sacar de spam
                        results = gmail.users().messages().list(
                            userId='me', 
                            labelIds=[str(id)],
                            q='is:unread',
                            includeSpamTrash=True
                        ).execute()
                        messages = results.get('messages', [])
                        #Extraer metadata
                        for message in messages:
                            msg = gmail.users().messages().get(
                                userId='me', 
                                id=message['id'],  
                                format='metadata',
                                metadataHeaders=['To','Date','Subject']
                            ).execute()
                            #Marcar como leido
                            results = gmail.users().messages().modify(
                                userId='me',
                                id=message['id'],
                                body={
                                    "addLabelIds": [],
                                    "removeLabelIds": ['SPAM','UNREAD']
                                }
                            ).execute()
                            #Encontrar headers
                            headers = msg['payload']['headers']
                            for header in headers:
                                if header['name']=='To':
                                    to_index = headers.index(header)
                                elif header['name']=='Date':
                                    date_index = headers.index(header)
                                elif header['name']=='Subject':
                                    sbj_index = headers.index(header)

                            #Datos extraidos
                            recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                            date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                            name = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[0]).replace('sent you','').replace('le ha enviado','').upper() #Nombre
                            amount = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[1]) #Monto
                            data = {
                                'msg_id':message['id'],
                                'cuenta':recipient,
                                'banco':tag,
                                'fecha':date,
                                'remitente':name,
                                'monto':amount   
                            }
                            data_list.append(data)

                    else:
                        #Filtrar threads por lable, no leidos y sacar de spam
                        results = gmail.users().threads().list(
                            userId='me', 
                            labelIds=[str(id)],
                            q='is:unread',
                            includeSpamTrash=True
                        ).execute()
                        threads = results.get('threads', [])
                        #Extraer threadId de thread
                        for thread in threads:
                            thr = gmail.users().threads().get(
                                userId='me', 
                                id=thread['id'],
                            ).execute()
                            #Marcar como leido
                            results = gmail.users().threads().modify(
                                userId='me',
                                id=thread['id'],
                                body={
                                    "addLabelIds": [],
                                    "removeLabelIds": ['SPAM','UNREAD']
                                }
                            ).execute()
                            #Extraer mensajes
                            messages = thr.get('messages', [])
                            for message in messages:
                                msg = gmail.users().messages().get(
                                    userId='me', 
                                    id=message['id']
                                ).execute()
                                #Encontrar headers
                                headers = msg['payload']['headers']
                                for header in headers:
                                    if header['name']=='To':
                                        to_index = headers.index(header)
                                    elif header['name']=='Date':
                                        date_index = headers.index(header)

                                #Extraer datos
                                if tag == 'WELLS':
                                    recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                    date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                    name = str((str((str(msg['snippet']).split('®'))[1]).split('.'))[0]).replace('le envió dinero','')#Nombre
                                    amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0])
                                    data = {
                                        'msg_id':message['id'],
                                        'cuenta':recipient,
                                        'banco':tag,
                                        'fecha':date,
                                        'remitente':name,
                                        'monto':amount   
                                    }
                                    data_list.append(data)
                                elif tag == 'REGIONS':
                                    recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                                    date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                                    name = str((str((str(msg['snippet']).split('payment from'))[1]).split('('))[0])#Nombre
                                    amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0])
                                    data = {
                                        'msg_id':message['id'],
                                        'cuenta':recipient,
                                        'banco':tag,
                                        'fecha':date,
                                        'remitente':name,
                                        'monto':amount   
                                    }
                                    data_list.append(data)

                                # elif tag == 'TRU':
                                #         body = str(msg['payload']['parts'][0]['body']['data'])
                                #         #body = base64.b64decode(str(msg['payload']['parts'][0]['body']['data'])[0:9998]+'==').decode('utf-8')
                                #         print(len(body))
        df = pd.DataFrame(data_list)
        print('Correos recogidos')
        return(df)
    
    








        

