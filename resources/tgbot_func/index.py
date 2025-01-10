import os
import json
import requests
import base64
import boto3

FUNC_RESPONSE = {
    'statusCode': 200,
    'body': ''
}

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TELEGRAM_API_FILE_URL = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}"
SA_API_SECRET_KEY = os.environ.get("SA_API_SECRET_KEY")
SA_AWS_PUBLIC = os.environ.get("SA_AWS_PUBLIC")
SA_AWS_SECRET = os.environ.get("SA_AWS_SECRET")

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id = SA_AWS_PUBLIC, 
    aws_secret_access_key = SA_AWS_SECRET,
)

BUCKET = os.environ.get("BUCKET")
PROMPT_FILE = os.environ.get("PROMPT_FILE")
get_object_response = s3.get_object(Bucket = BUCKET, Key = PROMPT_FILE)
cont = get_object_response['Body'].read().decode('utf-8')
prompt = json.loads(cont)

def ask_question_yaGPT(question):
    prompt["messages"][1]['text'] = question
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SA_API_SECRET_KEY}",
    }
    try:
        response = requests.post(url, headers=headers, json=prompt)
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    except:
        return 'Я не смог подготовить ответ на экзаменационный вопрос.'

visionOCR = {
    "mimeType": "JPEG",
    "languageCodes": ["*"],
    "content": ""
}
def process_image_visionOCR(image):
    image_base64 = base64.b64encode(image).decode("utf-8")
    visionOCR['content'] = image_base64

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
    headers= {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {SA_API_SECRET_KEY}",
    }  
    response = requests.post(url=url, headers=headers, json=visionOCR)
    return response.json()

def downloaf_img_telegram(image_id):
    url = f"{TELEGRAM_API_URL}/getFile?file_id={image_id}"
    response = requests.get(url)
    file_path = response.json()["result"]["file_path"]
    url = f"{TELEGRAM_API_FILE_URL}/{file_path}"
    return requests.get(url).content

def send_message(text, message):
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}

    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)


def handler(event, context):

    if TELEGRAM_BOT_TOKEN is None:
        return FUNC_RESPONSE

    update = json.loads(event['body'])

    if 'message' not in update:
        return FUNC_RESPONSE

    message_in = update['message']

    if ('text' not in message_in) and ('photo' not in message_in):
        send_message('Я могу обработать только текстовое сообщение или фотографию.', message_in)
        return FUNC_RESPONSE
    
    if 'text' in message_in:
        if message_in['text'] == '/start' or message_in['text'] == '/help':
            return_text = '''Я помогу подготовить ответ на экзаменационный вопрос по дисциплине "Операционные системы".
Пришлите мне фотографию с вопросом или наберите его текстом.'''
        elif message_in['text'] == '':
            return_text = 'Пустые сообщения не обрабатываются.'
        else:
            return_text = ask_question_yaGPT(message_in['text'])
        send_message(return_text, message_in)
    elif 'photo' in message_in:
        if 'media_group_id' in message_in:
            return_text = 'Я могу обработать только одну фотографию.'
        else:          
            img_id = message_in['photo'][-1]['file_id']
            img = downloaf_img_telegram(img_id)
            try:  
                image_text = process_image_visionOCR(img)['result']['textAnnotation']['fullText']
                return_text = ask_question_yaGPT(image_text)
            except:
                return_text = "Я не могу обработать эту фотографию."
        send_message(return_text, message_in)                
    return FUNC_RESPONSE