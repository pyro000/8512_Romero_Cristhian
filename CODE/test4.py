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

sg.theme('LightGrey')
r = sr.Recognizer()
pytesseract.pytesseract.tesseract_cmd = r'lib\Tesseract-OCR\tesseract.exe'


def get_media_transcription(path, path_c):
    folder_name = f"{path[0]}-img-chunks"
    
    if path[-1] == 'pdf':
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
            
        pages = convert_from_path(path_c, 500,poppler_path=r'lib\poppler-0.68.0\bin',fmt='jpeg')
        image_counter = 0

        for page in pages:
            image_counter += 1
            filename = f"{folder_name}/page_{image_counter}.jpg"
            page.save(filename, 'JPEG')
            print(f"Saving {image_counter}: {filename}")
            time.sleep(0.5)
    
    result = ''
    
    outfile = f"out_text_{path[0]}.txt"
    f = open(outfile, "a")
    if path[-1] == 'pdf':
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
            time.sleep(0.5)
        
    elif path[-1] in ['jpg', 'png']:
        filename = f"{path}"
        
        img = cv2.imread(path_c)
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
    return result


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

"""def get_img_data(f, maxsize=(144, 158)):
    
    #Generate image data using PIL
   
    img = Image.open(f)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

layout = [[sg.Image(get_img_data('lib/icon.png'))], [sg.Button('Iniciar')]]
window = sg.Window('LTS', layout, element_justification='c')
nw = True


while True:
    ev, val = window.read()
    if ev == sg.WIN_CLOSED:
        nw = False
        break
    elif ev == 'Iniciar':
        break
window.close()


if nw:"""
layout = [[sg.Text('LTS', font='Any 20')], 
[sg.Text('Formatos permitidos: png, pdf, wav, mp3, mp4')], 
[sg.Text('Instrucciones: Subir archivo, y dar clic en comenzar:')], 
[sg.Input(key='-INPUT-'),
    sg.FileBrowse(file_types=(("Archivos Multimedia", "*.pdf *.png *.wav *.mp3 *.mp4 *.wmv")), key='FB', visible=False),
    sg.Button("Abrir Archivo..."),], [sg.Button('Comenzar')], [sg.Multiline('Resultado va aqui, advertencia, según el tamaño del archivo puede tardar varios minutos, espere por favor.', size = (75, 10), disabled = True, key='ml')], 
[sg.Text('Progreso (-%): ', key='prog'), sg.ProgressBar(100, orientation='h', size=(20, 20), key='progress')]]

window = sg.Window('LTS', layout, element_justification='c', finalize = True)

#window['progress'].update(0)
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
                
                
                result = ''
                
                if filed_s[-1] in ['wav', 'mp3', 'mp4', 'wmv']:
                    result = get_large_audio_transcription(filed_s, val['FB'])
                    
                elif filed_s[-1] in ['pdf', 'png', 'jpg']:
                    result =  get_media_transcription(filed_s, val['FB'])
                
                window['ml'].update(result);
                
                window['Abrir Archivo...'].update(disabled = False)
                window['Comenzar'].update(disabled = False)
                window['-INPUT-'].update(disabled = False)
                
                window['progress'].update(100)
                window['prog'].update('Progreso (100%): ')
                              
            else:
                sg.popup_error('[ERROR]', f'{filed} no admitido.', 'Suba archivos de formato png, pdf, wav, mp3 y mp4.')
        else:
            sg.popup_error('[ERROR]', f'Escoja o escriba la ruta del archivo.')
window.close()
    
#