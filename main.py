#Главный файд

import time
import logging

from config import token
from VKinder import VKinder

logging.info('Запуск VKinder...')

while True:
    try:
        bot = VKinder(token, 207720873)
        bot.start()
    except Exception as error_msg:
        print(f'Произошла ошибка в главном файле: \n    {error_msg}\nПерезапуск...')
        logging.error(f'Произошла оибка в главном файле{error_msg}')
        logging.info('Перезапуск')
        time.sleep(15)
logging.info('Скрипт завершен')
