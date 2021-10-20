# Файл для работы с базой данной
import sqlite3

class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)

    #Выбор одной записи
    def select_with_fetchone(self, cmd):
        cursor = self.connection.cursor()
        cursor.execute(cmd)
        result = cursor.fetchone()
        return result


    # Выбор множества записей
    def select_with_fetchall(self, cmd):
        cursor = self.connection.cursor()
        cursor.execute(cmd)
        result = cursor.fetchall()
        return result


    #Добавить, обновить, удалить
    def query(self, cmd):
        cursor = self.connection.cursor()
        cursor.execute(cmd)
        self.connection.commit()
        print('True query')
        cursor.close()
