#Основные логика бота

class Handler:
    def __init__(self):
        self.peer_id = 0
        self.msg = ''

    def msg_handler(self, peer_id, msg):
        self.peer_id = peer_id
        self.msg = msg
        if self.msg == 'помощь':
            return 'Это программа для поиска потенциальных партнеров. ' \
                   'Нажмите кнопку "найти кандидатов"' \
                   'Нажмите кнопку "далее" чтобы посмотреть на следующего кандидата' \
                   'Нажмите кнопку "стоп" чтобы закончить'
        elif self.msg == 'найти кандидатов':
            return 'Введите id пользователя VK для поиска кандидатов'
        elif self.msg == 'далее':
            return 'Следующий кандидат'
        elif self.msg == 'стоп':
            return 'Заканчиваем поиск кандидатов'
        else:
            return 'None', 'main'
        return 'None'