# Файл для работы с базой данной
import sqlite3

class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)

    def users_info(self, user_id, birth_year, sex, city, relation):
        try:
            cursor = self.connection.cursor()
            cursor = self.connection.cursor()
            cursor.execute("SELECT user_id, birth_year, sex, city, relation FROM Users_info "
                           "WHERE user_id==? and birth_year==? and sex==? and city==? and relation ==?",
                           (user_id, birth_year, sex, city, relation,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO Users_info VALUES (?,?,?,?,?)", (user_id, birth_year, sex, city, relation))
                self.connection.commit()
                cursor.close()
            else:
                pass
        except sqlite3.Error as error:
            print(error)
            pass

    def users_candidates(self, user_id, candidate_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT user_id, candidate_id FROM users_candidates WHERE user_id ==? and "
                                "candidate_id ==?", (user_id, candidate_id,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO users_candidates VALUES (?,?)", (user_id, candidate_id))
                self.connection.commit()
                cursor.close()
            else:
                pass
        except sqlite3.Error as error:
            print(error)
            pass

    def black_list(self, user_id, candidate_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT user_id, candidate_id FROM black_list WHERE user_id ==? and "
                                "candidate_id ==?", (user_id, candidate_id,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO black_list VALUES (?,?)", (user_id, candidate_id))
                self.connection.commit()
                cursor.close()
            else:
                pass
        except sqlite3.Error as error:
            print(error)
            pass
