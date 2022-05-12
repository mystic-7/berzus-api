#Recursos
import pandas as pd
import numpy as np
import re
import os.path
import pickle
import base64

from berzus import format
from datetime import date, datetime, time, timedelta
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
        print('Buscando Correos')
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
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
                            id=message['id']  
                        ).execute()
                        #Marcar como no spam
                        results = gmail.users().messages().modify(
                            userId='me',
                            id=message['id'],
                            body={
                                "addLabelIds": [],
                                "removeLabelIds": ['SPAM']
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

                        if tag == 'BOFA' or tag == 'CHASE':
                            #Datos extraidos
                            recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                            date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                            name = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[0]).replace('sent you','').replace('le ha enviado','').upper() #Nombre
                            amount = str((str(msg['payload']['headers'][sbj_index]['value']).split('$'))[1]) #Monto
                            data = {
                                'msg_id':message['id'],
                                'cuenta':recipient,
                                'banco':tag,
                                'fecha':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                'hora':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                'remitente':format(name).side_spaces(),
                                'monto':amount   
                            }
                            data_list.append(data)

                        #Extraer datos
                        elif tag == 'WELLS':
                            recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                            date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                            name = str((str((str(msg['snippet']).split('®'))[1]).split('.'))[0]).replace(' le envió dinero ','').upper() #Nombre
                            amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0])
                            data = {
                                'msg_id':message['id'],
                                'cuenta':recipient,
                                'banco':tag,
                                'fecha':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                'hora':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                'remitente':format(name).side_spaces(),
                                'monto':amount   
                            }
                            data_list.append(data)
                        elif tag == 'REGIONS':
                            recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                            date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                            name = str((str((str(msg['snippet']).split('payment from'))[1]).split('('))[0]).upper() #Nombre
                            amount = str((str((str(msg['snippet']).split('$'))[1]).split(' '))[0])
                            data = {
                                'msg_id':message['id'],
                                'cuenta':recipient,
                                'banco':tag,
                                'fecha':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                'hora':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                'remitente':format(name).side_spaces(),
                                'monto':amount   
                            }
                            data_list.append(data)

                        elif tag == 'TRU':
                            body = base64.urlsafe_b64decode(msg.get("payload").get('parts')[0].get("body").get("data").encode("ASCII")).decode("utf-8")
                            formated = format(body).clean_html()

                            recipient = str(msg['payload']['headers'][to_index]['value']) #Correo receptor
                            date = str((re.split(',|-|\n',str(msg['payload']['headers'][date_index]['value'])))[1]) #Fecha
                            name = formated.split('Sent by:')[1].split('&')[0]
                            amount = formated.split('$')[1].split(' ')[0]
                            data = {
                                'msg_id':message['id'],
                                'cuenta':recipient,
                                'banco':tag,
                                'fecha':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).date()),
                                'hora':str((datetime.strptime(date,' %d %b %Y %H:%M:%S ') + timedelta(hours=3)).time()),
                                'remitente':format(name).side_spaces(),
                                'monto':format(amount).side_spaces()   
                            }
                            data_list.append(data)

        df = pd.DataFrame(data_list)
        print('Correos recogidos')
        return(df)
    
    def read(self, emails):
        self.emails = emails
        #Llamar al API
        self.call()
        #Servicio del API
        gmail = build('gmail', 'v1', credentials=self.creds)

        #Encontrar LabelIds
        results = gmail.users().labels().list(
            userId='me'
        ).execute()
        labels = results.get('labels',[])

        data = emails.to_dict('Records')
        tag_list = ['BOFA', 'TRU', 'CHASE', 'WELLS', 'REGIONS']
        print('Marcando como leidos')
        #Extraer LabelId
        for tag in tag_list:
            for label in labels:
                if label['name'] == tag:
                    id=label['id']
                    print('Etiqueta', label['name'], 'encontrada')
                    #Filtrar mensajes por lable y no leidos
                    results = gmail.users().messages().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread'
                    ).execute()
                    messages = results.get('messages', [])
                    for message in messages:
                        for r in data:
                            if str(r['msg_id']) == str(message['id']):
                                #Marcar como leido
                                results = gmail.users().messages().modify(
                                    userId='me',
                                    id=message['id'],
                                    body={
                                        "addLabelIds": [],
                                        "removeLabelIds": ['UNREAD']
                                    }
                                ).execute()
                    #Filtrar threads por lable y no leidos
                    results = gmail.users().threads().list(
                        userId='me', 
                        labelIds=[str(id)],
                        q='is:unread'
                    ).execute()
                    threads = results.get('threads', [])
                    for thread in threads:
                        for r in data:
                            if str(r['msg_id']) == str(thread['id']):
                                #Marcar como leido
                                results = gmail.users().threads().modify(
                                    userId='me',
                                    id=thread['id'],
                                    body={
                                        "addLabelIds": [],
                                        "removeLabelIds": ['UNREAD']
                                    }
                                ).execute()
        print('Correos Leídos')








        

