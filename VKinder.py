#Чертеж объекта бот
import vk_api.vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import time
import logging
import traceback
from config import token_api
from vk_api.utils import get_random_id
import json
from database import Database
from handler import Handler
from keyboard import Keyboards


logging.basicConfig(filename='logs/log.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

class VKinder:
    def __init__(self, token):
        #Для Longpoll
        self.vk = vk_api.VkApi(token=token)
        self.api = vk_api.VkApi(token=token_api)
        #Настройка подключения к longpoll
        self.long_poll = VkLongPoll(self.vk)
        #Для использования методов VK
        self.vk_api = self.vk.get_api()
        self.db = Database('db/Database.db')
        self.handler = Handler()
        self.kb = Keyboards()
        self.main_kb = self.kb.get_keyboard('main')
        self.msg = ''
        self.searching_for_id = 0
        self.user_id = 0
        self.birth_year = 0
        self.sex = 0
        self.city = 0
        self.relation = 0
        self.candidate_id = 0


        logging.info('Запуск файла бота...')

    #Ф-я отправки сообщения в чат
    def send_msg(self, user_id, msg, attachment=None, keyboard=None):
        self.vk.method('messages.send', {'user_id': user_id, 'message': msg, 'attachment': attachment,
                                         'keyboard': self.main_kb, 'random_id': get_random_id()})

    # Ф-я получения имени пользователя
    def get_name(self, id):
        response = self.vk_api.users.get(user_ids=id, fields=('first_name', 'last_name'))
        r = response[0]
        name = r['first_name']
        last_name =r['last_name']
        return (name +" "+ last_name)


    # Ф-я получения информции по пользователю
    def get_user_info(self, id):
        response = self.vk_api.users.get(user_ids=id, fields=('bdate', 'sex', 'city', 'relation'))
        info = response[0]
        Users_info = {}
        Users_info['user_id'] = self.searching_for_id
        if 'bdate' not in info.keys():
            self.send_msg(self.user_id, 'Год рожения не указан в профиле. Введите год рождения: ')
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    Users_info['birth_year'] = event.text.lower()
                    break
        elif len(info['bdate']) < 5:
            self.send_msg(self.user_id, 'Год рожения не указан в профиле. Введите год рождения: ')
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    Users_info['birth_year'] = event.text.lower()
                    break
        else:
            Users_info['birth_year'] = info['bdate'][-4:]
        if 'relation' not in info.keys():
            self.send_msg(self.user_id, 'Семейное положение не указано в профиле. Выберите семейное положение:\n '
                                              '1 — не женат/не замужем \n'
                                              '2 — есть друг/есть подруга \n'
                                              '3 — помолвлен/помолвлена \n'
                                              '4 — женат/замужем \n'
                                              '5 — всё сложно \n'
                                              '6 — в активном поиске \n'
                                              '7 — влюблён/влюблена \n'
                                              '8 — в гражданском браке \n')
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    Users_info['relation'] = event.text
                    break
        else:
            Users_info['relation'] = info['relation']
        if Users_info['relation'] in [2, 3, 4, 5, 7, 8]:
            self.send_msg(self.sender, 'У вас уже есть вторая половинка. Пока')
            return self.start()
        if 'city' not in info.keys():
            self.send_msg(self.user_id, 'Город проживания не указан в профиле. Введите наименование города: ')
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    city_name = event.text.lower()
                    Users_info['city'] = self.api.get_api().database.getCities(country_id=1, q=city_name)['items'][0]['id']
                    break
        else:
            Users_info['city'] = info['city']['id']
        if 'sex' not in info.keys():
            self.send_msg(self.user_id, 'Пол не указан в профиле. Выберите ваш пол:\n1 - женский\n2 - мужской \n')
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    Users_info['sex'] = event.text
                    break
        else:
            Users_info['sex'] = info['sex']

        self.write_json('Users_info.json', Users_info)


    # Ф-я получения записи данных в файл json
    def write_json(self, filename, data):
        json_file = open(filename, 'r+')
        json_data = json.load(json_file)
        json_file.close()
        json_data.append(data)
        json_f = open(filename, 'w')
        json_f.write(json.dumps(json_data, indent=2, ensure_ascii=False))
        json_f.close()


    # Ф-я добавления пользователя в БД
    def add_user_inDB(self):
        with open('Users_info.json', 'r') as f:
            j_data = json.load(f)
            for user in j_data:
                (user_id, birth_year, sex, city, relation) = (v for v in user.values())
                self.db.users_info(user_id, birth_year, sex, city, relation)


    # Ф-я проверки нахождения пользователя в БД
    def check_user_inDB(self, id):
        with open('Users_info.json', 'r+') as file:
            file.seek(0)
            first_char = file.read(1)
            if not first_char:
                data = [self.get_user_info(id)]
                file.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                file.seek(0)
                json_data = json.load(file)
                for user in json_data:
                    if user['user_id'] == id:
                        exists = True
                        return exists


    # Ф-я добавления кандидата в БД
    def add_candidate_inDB(self):
        with open('users_candidates.json', 'r') as f:
            j_data = json.load(f)
            for user in j_data:
                (user_id, candidate_id) = (v for v in user.values())
                self.db.users_candidates(user_id, candidate_id)


    #Ф-я проверки нахождения кандидата в БД
    def check_candidate_inDB(self, data):
        with open('black_list.json', 'r') as f:
            l = json.load(f)
            for user in l:
                if user['candidate_id'] == data['candidate_id']:
                    break
                else:
                    with open('users_candidates.json', 'r+') as file:
                        file.seek(0)
                        first_char = file.read(1)
                        if not first_char:
                            cand = []
                            cand.append(data)
                            file.write(json.dumps(cand, indent=2, ensure_ascii=False))
                        else:
                            file.seek(0)
                            j_data = json.load(file)
                            for user in j_data:
                                if user == data:
                                    existance = True
                                    return existance


    def black_list(self, id, candidate_id):
        with open('black_list.json', 'r+') as f:
            f.seek(0)
            first_char = f.read(1)
            if not first_char:
                data = [{'user_id': id, 'candidate_id': candidate_id}]
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                f.seek(0)
                json_data = json.load(f)
                for user in json_data:
                    if user['candidate_id'] == candidate_id:
                        break
                    if user['candidate_id'] != candidate_id:
                        self.write_json('black_list.json', {'user_id': id, 'candidate_id': candidate_id})
                        with open('users_candidates.json', 'r') as file:
                            j_data = json.load(file)
                            for u in j_data:
                                (user_id, candidate_id) = (v for v in u.values())
                                self.db.black_list(id, candidate_id)



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
                self.send_msg(self.user_id, '', attachment=attachment)


    # Ф-я поиска кандидатов
    def search_candidates(self, id):
        search_params = {}
        with open('Users_info.json', 'r') as file:
            data = json.load(file)
            for user in data:
                if int(user['user_id']) == id:
                    search_params['birth_year'] = int(user['birth_year'])
                    sex = user['sex']
                    if sex == 2:
                        search_params['sex'] = 1
                    elif sex == 1:
                        search_params['sex'] = 2
                    search_params['city'] = int(user['city'])
                    search_params['relation'] = int(user['relation'])
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
    def send_result(self, id):
        with open('candidates.txt', 'r') as file:
            for row in file:
                self.candidate_id = int(row.rstrip())
                data = {'user_id': id, 'candidate_id': self.candidate_id}
                existance = self.check_candidate_inDB(data)
                if existance is True:
                    pass
                else:
                    self.write_json('users_candidates.json', data)
                    candidate_url = f'https://vk.com/id{self.candidate_id}'
                    self.send_msg(self.user_id, candidate_url)
                    self.get_photo(self.candidate_id)
                    self.add_candidate_inDB()
                    self.add_user_inDB()
                    break





    def start(self):
        logging.info('Запущен основной цикл')
        try:
            for event in self.long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.user_id = event.user_id
                    self.msg = event.text.lower()
                    if self.msg == 'помощь':
                        response = self.handler.msg_handler(self.msg)
                        self.send_msg(self.user_id, response)
                    elif self.msg == 'найти кандидатов':
                        response = self.handler.msg_handler(self.msg)
                        self.send_msg(self.user_id, response)
                        for event in self.long_poll.listen():
                                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                    self.searching_for_id = int(event.text.lower())
                                    name = self.get_name(self.searching_for_id)
                                    self.send_msg(self.user_id, f'Ищем кандидатов для {name}')
                                    exists = self.check_user_inDB(self.searching_for_id)
                                    if exists is not True:
                                        self.get_user_info(self.searching_for_id)
                                    self.search_candidates(self.searching_for_id)
                                    self.send_result(self.searching_for_id)
                                    for event in self.long_poll.listen():
                                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                            self.msg = event.text.lower()
                                            if self.msg == 'добавить в черный список':
                                                resp = self.handler.msg_handler(self.msg)
                                                self.send_msg(self.user_id, resp)
                                                self.black_list(self.searching_for_id, self.candidate_id)
                                            if self.msg == 'далее':
                                                resp = self.handler.msg_handler(self.msg)
                                                self.send_msg(self.user_id, resp)
                                                self.send_result(self.searching_for_id)
                                            if self.msg == 'стоп':
                                                resp = self.handler.msg_handler(self.msg)
                                                self.send_msg(self.user_id, resp)
                                                return self.start()

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