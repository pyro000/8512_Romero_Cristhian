import PySimpleGUI as sg
import io
import os
import ffmpeg
import speech_recognition as sr 
from pydub import AudioSegment
from pydub.silence import split_on_silence
import shutil
import pytesseract
import sys
from pdf2image import convert_from_path
import time
import cv2
from threading import Thread
import math

sg.theme('LightGrey')
r = sr.Recognizer()
pytesseract.pytesseract.tesseract_cmd = r'lib\Tesseract-OCR\tesseract.exe'


class ProcessFileIMG(Thread):
    def __init__(self):
        Thread.__init__(self, daemon=True)
        self.percent = 0
        self.result = ""
        self.path = []
        self.path_c = ""

    def run(self):
        self.percent = 0
        if self.path[-1] in ['pdf', 'png', 'jpg']:
        
            folder_name = f"{self.path[0]}-img-chunks"
            
            
            
            if self.path[-1] == 'pdf':
                if not os.path.isdir(folder_name):
                    os.mkdir(folder_name)
                    
                pages = convert_from_path(self.path_c, 500,poppler_path=r'lib\poppler-0.68.0\bin',fmt='jpeg')
                print(pages)
                pertoadd = 50/len(pages)
                
                image_counter = 0

                for page in pages:
                    image_counter += 1
                    filename = f"{folder_name}/page_{image_counter}.jpg"
                    page.save(filename, 'JPEG')
                    print(f"Saving {image_counter}: {filename}")
                    self.percent += pertoadd
                    time.sleep(0.001)
            
            result = ''
            
            outfile = f"out_text_{self.path[0]}.txt"
            f = open(outfile, "a")
            if self.path[-1] == 'pdf':
                print(f"-----------------------------------------")
                for i in range(1, image_counter):
                    filename = f"{folder_name}/page_{i}.jpg"
                    
                    img = cv2.imread(filename)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    img = cv2.medianBlur(img, 1)
                    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                    
                    text = str(pytesseract.image_to_string(img))
                    text = text.replace('-\n', '')
                    f.write(text)
                    result += text
                    print(f"Processing {i}: {filename}")
                    self.percent += pertoadd
                    time.sleep(0.001)
                
            elif self.path[-1] in ['jpg', 'png']:
                filename = f"{self.path}"
                
                img = cv2.imread(self.path_c)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = cv2.medianBlur(img, 1)
                img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
                text = str(pytesseract.image_to_string(img))
                text = text.replace('-\n', '')
                f.write(text)
                result = text
            f.close()
            
            if os.path.isdir(folder_name):
                shutil.rmtree(folder_name)
            
            self.percent = 100
            self.result = result
            
# MULTIMEDIA   
        elif self.path[-1] in ['wav', 'mp3', 'mp4', 'wmv']: 
            
            print('\nProcesando Archivo...')
            if self.path[-1] != 'wav':
                paux = f'{self.path[0]}.wav'
                (
                    ffmpeg
                    .input(self.path_c)
                    .output(paux)
                    .overwrite_output()
                    .run(cmd='lib/test/ffmpeg.exe')
                )
            
            self.percent += 10
            
            sound = AudioSegment.from_wav(paux)  
            
            self.percent += 10
            
            chunks = split_on_silence(sound,
                min_silence_len = 500,
                silence_thresh = sound.dBFS-14,
                keep_silence=500,
            )
            folder_name = f"{self.path[0]}-audio-chunks"
            
            self.percent += 10
            
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
            
            outfile = f"out_text_{self.path[0]}.txt"
            f = open(outfile, "a")
            whole_text = ""
            print('\nExtrayendo Texto...')
            
            pertoadd = 70/len(chunks)
            
            for i, audio_chunk in enumerate(chunks, start=1):
                chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
                audio_chunk.export(chunk_filename, format="wav")

                with sr.AudioFile(chunk_filename) as source:
                    audio_listened = r.record(source)
                    try:
                        text = r.recognize_google(audio_listened, language="es-ES")
                    except sr.UnknownValueError as e:
                        print("Error:", str(e))
                    else:
                        text = f"{text.capitalize()}."
                        text = text.replace('.', '. \n')
                        print(chunk_filename, ":", text)
                        whole_text += text
                self.percent += pertoadd
                
            f.write(whole_text)
            f.close()
            
            if self.path[-1] != 'wav':
                os.remove(paux)
            shutil.rmtree(folder_name)
            
            self.percent = 100
            self.result = whole_text

def get_large_audio_transcription(path, path_c):
    print('\nProcesando Archivo...')
    if path[-1] != 'wav':
        paux = f'{path[0]}.wav'
        (
            ffmpeg
            .input(path_c)
            .output(paux)
            .overwrite_output()
            .run(cmd='lib/test/ffmpeg.exe')
        )
    
    sound = AudioSegment.from_wav(paux)  
    chunks = split_on_silence(sound,
        min_silence_len = 500,
        silence_thresh = sound.dBFS-14,
        keep_silence=500,
    )
    folder_name = f"{path[0]}-audio-chunks"

    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    
    outfile = f"out_text_{path[0]}.txt"
    f = open(outfile, "a")
    whole_text = ""
    print('\nExtrayendo Texto...')
    
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")

        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            try:
                text = r.recognize_google(audio_listened, language="es-ES")
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}."
                text = text.replace('.', '. \n')
                print(chunk_filename, ":", text)
                whole_text += text
    f.write(whole_text)
    f.close()
    
    if path[-1] != 'wav':
        os.remove(paux)
    shutil.rmtree(folder_name)
    
    return whole_text


layout = [[sg.Text('LTS', font='Any 20')], 
[sg.Text('Formatos permitidos: png, pdf, wav, mp3, mp4')], 
[sg.Text('Instrucciones: Subir archivo, y dar clic en comenzar:')], 
[sg.Input(key='-INPUT-'),
    sg.FileBrowse(file_types=(('Archivos Multimedia', '*.pdf *.png *.wav *.mp3 *.mp4 *.wmv'),), key='FB', visible=False),
    sg.Button("Abrir Archivo..."),], [sg.Button('Comenzar')], [sg.Multiline('Resultado va aqui, advertencia, según el tamaño del archivo puede tardar varios minutos, espere por favor.', size = (75, 10), disabled = True, key='ml')], 
[sg.Text('Progreso (-%): ', key='prog'), sg.ProgressBar(100, orientation='h', size=(20, 20), key='progress')]]

window = sg.Window('LTS', layout, element_justification='c', finalize = True)

#window['progress'].update(0)

PFIMG = ProcessFileIMG()
processing = False

while True:
    ev, val = window.read(timeout=100)
    if ev == sg.WIN_CLOSED:
        break
    if ev == "Abrir Archivo...":
        window['FB'].click()
    elif ev == "Comenzar":
        if val['FB']:
            filed = os.path.basename(val['FB'])
            filed_s = filed.split('.')
            if os.path.exists(val['FB']) and filed_s[1] in ['pdf', 'png', 'jpg', 'wav', 'mp3', 'mp4', 'wmv']:
            
                window['Abrir Archivo...'].update(disabled = True)
                window['Comenzar'].update(disabled = True)
                window['-INPUT-'].update(disabled = True)
               
                processing = True
                
                #if filed_s[-1] in ['wav', 'mp3', 'mp4', 'wmv']:
                #    result = get_large_audio_transcription(filed_s, val['FB'])
                    
                #elif filed_s[-1] in ['pdf', 'png', 'jpg']:
                    #result =  get_media_transcription(filed_s, val['FB'])
                PFIMG.path = filed_s
                PFIMG.path_c = val['FB']
                PFIMG.start()
                
                
                              
            else:
                sg.popup_error('[ERROR]', f'{filed} no admitido.', 'Suba archivos de formato png, pdf, wav, mp3 y mp4.')
        else:
            sg.popup_error('[ERROR]', f'Escoja o escriba la ruta del archivo.')
            
    if processing is True:
        window['progress'].update(PFIMG.percent)
        window['prog'].update(f'Progreso ({math.trunc(PFIMG.percent)}%): ')
        
        if PFIMG.result != "":
            window['ml'].update(PFIMG.result);
            PFIMG.join()
            PFIMG = ProcessFileIMG()
                    
            window['Abrir Archivo...'].update(disabled = False)
            window['Comenzar'].update(disabled = False)
            window['-INPUT-'].update(disabled = False)
            processing = False
            
window.close()
    
#