#Чертеж объекта бот
import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests
import time
import logging
import traceback
from config import token_api

from database import Database
from handler import Handler
from keyboard import Keyboards


logging.basicConfig(filename='logs/log.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

class VKinder:
    def __init__(self, token, group_id):
        #Для Longpoll
        self.vk = vk_api.VkApi(token=token)
        self.api = vk_api.VkApi(token=token_api)
        #Настройка подключения к longpoll
        self.long_poll = VkBotLongPoll(self.vk, group_id)
        #Для использования методов VK
        self.vk_api = self.vk.get_api()
        self.db = Database('db/Database.db')
        self.handler = Handler()
        self.kb = Keyboards()
        self.main_kb = self.kb.get_keyboard('main')
        self.peer_id = 0
        self.msg = ''
        self.user_id = 0
        self.birth_year = 0
        self.sex = 0
        self.city = 0
        self.relation = 0

        logging.info('Запуск файла бота...')

    #Ф-я отправки сообщения в чат
    def send_msg(self, peer_id, msg, attachment=None, keyboard=None):
        self.vk.method('messages.send', {'peer_id': peer_id, 'message': msg, 'attachment': attachment,
                                         'keyboard': self.main_kb, 'random_id': 0})

    # Ф-я получения имени пользователя
    def get_name(self, user_id):
        response = self.vk_api.users.get(user_ids=user_id, fields=('first_name', 'last_name'))
        r = response[0]
        name = r['first_name']
        last_name =r['last_name']
        return (name +" "+ last_name)

    # Ф-я получения информции по пользователю
    def get_user_info(self, user_id, peer_id):
        response = self.vk_api.users.get(user_ids=user_id, fields=('bdate', 'sex', 'city', 'relation'))
        info = response[0]
        print(info)
        if 'bdate' not in info.keys():
            self.send_msg(peer_id, 'Год рожения не указан в профиле. Введите год рождения: ')
            for event in self.long_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.birth_year = event.obj['message']['text'].lower()
                    break
        else:
            self.birth_year = info['bdate'][-4:]
        if 'relation' not in info.keys():
            self.send_msg(peer_id, 'Семейное положение не указано в профиле. Выберите семейное положение:\n '
                                              '1 — не женат/не замужем \n'
                                              '2 — есть друг/есть подруга \n'
                                              '3 — помолвлен/помолвлена \n'
                                              '4 — женат/замужем \n'
                                              '5 — всё сложно \n'
                                              '6 — в активном поиске \n'
                                              '7 — влюблён/влюблена \n'
                                              '8 — в гражданском браке \n')
            for event in self.long_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.relation = event.obj['message']['text']
                    break
        else:
            self.relation = info['relation']
        if self.relation in [2, 3, 4, 5, 7, 8]:
            self.send_msg(peer_id, 'У вас уже есть вторая половинка. Пока')
            return self.start()
        if 'city' not in info.keys():
            self.send_msg(peer_id, 'Город проживания не указан в профиле. Введите наименование города: ')
            for event in self.long_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    city_name = event.obj['message']['text'].lower()
                    self.city = self.api.get_api().database.getCities(country_id=1, q=city_name)['items'][0]['id']
                    break
        else:
            self.city = info['city']['id']
        if 'sex' not in info.keys():
            self.send_msg(peer_id, 'Пол не указан в профиле. Выберите ваш пол:\n1 - женский\n2 - мужской \n')
            for event in self.long_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.sex = event.obj['message']['text']
                    break
        else:
            self.sex = info['sex']
        self.add_user_inDB()

    # Ф-я добавления пользователя в БД
    def add_user_inDB(self):
        sql = f"""INSERT INTO Users_info (user_id, birth_year, sex, city, relation)
                                        VALUES
                                        ({self.user_id}, {self.birth_year}, {self.sex}, {self.city}, {self.relation})"""
        self.db.query(sql)

    # Ф-я проверки нахождения пользователя в БД
    def check_user_inDB(self, user_id):
        sql = f"""SELECT * FROM Users_info where user_id = {user_id}"""
        exists = self.db.select_with_fetchall(sql)
        if not exists:
            self.get_user_info(user_id, self.peer_id)

    # Ф-я добавления кандидата в БД
    def add_candidate_inDB(self, candidate_id):
        sql = f"""INSERT INTO users_candidates   (user_id, candidate_id)
                                    VALUES
                                    ({self.user_id}, {candidate_id})"""
        self.db.query(sql)

    #Ф-я проверки нахождения кандидата в БД
    def check_candidate_inDB(self, candidate_id):
        sql = f"""SELECT * FROM users_candidates where user_id = {self.user_id} and candidate_id = {candidate_id}"""
        exists = self.db.select_with_fetchone(sql)
        return exists

    # Ф-я отправки фото в чат
    def get_photo(self, candidate_id):
        res = self.api.method('photos.get', {'owner_id': candidate_id,
                                               'album_id': 'profile',
                                               'extended': 1,
                                               'photo_sizes': 1,
                                               'count': 100})
        all_photos = res['items']
        sorted_photo = sorted(all_photos, key=lambda k: k['likes']['count'], reverse=True)[:3]
        for photo in sorted_photo:
            photo_url = photo['sizes'][-1]['url']
            download = requests.get(photo_url)
            with open('candidate_photo/%s' % '1.jpg', 'wb+') as file:
                file.write(download.content)
                upload = vk_api.VkUpload(self.vk)
                photo = upload.photo_messages('candidate_photo/%s' % '1.jpg')
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                access_key = photo[0]['access_key']
                attachment = f'photo{owner_id}_{photo_id}_{access_key}'
                self.send_msg(self.peer_id, '', attachment=attachment)

    # Ф-я поиска кандидатов
    def search_candidates(self, user_id):
        sql = f"""SELECT * FROM Users_info where user_id = {user_id}"""
        result = self.db.select_with_fetchall(sql)
        search_params = {}
        for row in result:
            search_params['birth_year'] = row[1]
            sex = row[2]
            if sex == 2:
                search_params['sex'] = 1
            elif sex == 1:
                search_params['sex'] = 2
            search_params['city'] = row[3]
            search_params['relation'] = row[4]
            search_params['count'] = 1000
            search_params['has_photo'] = 1
        res = self.api.method('users.search', search_params)
        res_all = res['items']
        all_candidates = []
        for candidate in res_all:
            if candidate['is_closed'] is False:
                candidate_id = candidate['id']
                all_candidates.append(candidate_id)
        with open('candidates.txt', 'w') as f:
            f.writelines("%s\n" % line for line in all_candidates)

    # Ф-я отправки результатов поиска
    def send_result(self, user_id):
        self.search_candidates(user_id)
        with open('candidates.txt', 'r') as file:
            for row in file:
                candidate_id = row.rstrip()
                exists = self.check_candidate_inDB(candidate_id)
                if exists:
                    pass
                elif not exists:
                    self.add_candidate_inDB(candidate_id)
                    candidate_url = f'https://vk.com/id{candidate_id}'
                    self.send_msg(self.peer_id, candidate_url)
                    self.get_photo(candidate_id)
                    break

    def start(self):
        logging.info('Запущен основной цикл')
        try:
            for event in self.long_poll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self.peer_id = event.obj['message']['peer_id']
                    self.msg = event.obj['message']['text'].lower()
                    if self.msg == 'помощь':
                        response = self.handler.msg_handler(self.peer_id, self.msg)
                        self.send_msg(self.peer_id, response)
                    if self.msg == 'найти кандидатов':
                        response = self.handler.msg_handler(self.peer_id, self.msg)
                        self.send_msg(self.peer_id, response)
                        for event in self.long_poll.listen():
                            if event.type == VkBotEventType.MESSAGE_NEW:
                                self.user_id = event.obj['message']['text'].lower()
                                name = self.get_name(self.user_id)
                                self.send_msg(self.peer_id, f'Ищем кандидатов для {name}')
                                self.check_user_inDB(self.user_id)
                                self.send_result(self.user_id)
                                for event in self.long_poll.listen():
                                    if event.type == VkBotEventType.MESSAGE_NEW:
                                        self.msg = event.obj['message']['text'].lower()
                                        if self.msg == 'далее':
                                            resp = self.handler.msg_handler(self.peer_id, self.msg)
                                            self.send_msg(self.peer_id, resp)
                                            self.send_result(self.user_id)
                                        if self.msg == 'стоп':
                                            resp = self.handler.msg_handler(self.peer_id, self.msg)
                                            self.send_msg(self.peer_id, resp)
                                            pass


        except requests.exceptions.ReadTimeout:
            error_msg = traceback.format_exc()
            logging.error(f'Ошибка подключения {error_msg}')
            time.sleep(15)
        except Exception:
            error_msg = traceback.format_exc()
            print(f'Произошла ошибка в файле бота: \n    {error_msg}\nПерезапуск...')
            logging.error(f'Произошла оибка в файле бота{error_msg}')
            logging.info('Перезапуск')
            time.sleep(15)