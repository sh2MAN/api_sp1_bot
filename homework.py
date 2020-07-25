import os
import logging
import requests
import telegram
import time
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

PROXY_URL = 'socks5://192.162.124.158:1080'
proxy = telegram.utils.request.Request(proxy_url=PROXY_URL)
TELEGRAM_BOT = telegram.Bot(token=TELEGRAM_TOKEN, request=proxy)

FORMAT_LOG = '%(asctime)s #%(levelname)s %(filename)s[%(lineno)d] %(message)s'
logging.basicConfig(format=FORMAT_LOG, level=logging.INFO)


def parse_homework_status(homework):
    try:
        assert homework.get('homework_name') is not None
        assert homework.get('status') is not None
        assert homework.get('status') in ('rejected', 'approved')
    except AssertionError as e:
        logging.error('Неверный ответ сервера.')

    homework_name = homework.get('homework_name')
    if homework.get('status') != 'approved':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = 0

    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers=headers,
            params={'from_date': current_timestamp}
        )
        return homework_statuses.json()
    except requests.exceptions.RequestException as e:
        logging.error(f'PRACTICUM: Connection error.')
        return {}


def send_message(message):
    bot = TELEGRAM_BOT
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get('current_date')  # обновить timestamp
            time.sleep(600)  # опрашивать раз в десять минут

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
