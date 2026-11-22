import sqlite3
from config import DATABASE

skills = [(_, ) for _ in (['Python', 'SQL', 'API', 'Telegram'])]
statuses = [(_, ) for _ in ([
    'На этапе проектирования',
    'В процессе разработки',
    'Разработан. Готов к использованию.',
    'Обновлен',
    'Завершен. Не поддерживается'
])]


class DB_Manager:
    """
    Класс для управления базой данных SQLite: создание таблиц, добавление, обновление, получение и удаление проектов, навыков и статусов.
    """

    def __init__(self, database):
        """
        Инициализирует менеджер базы данных, сохраняя путь к файлу БД.
        """
        self.database = database

    def create_tables(self):
        """
        Создает таблицы projects, skills, project_skills и status в базе данных, если они еще не существуют.
        """
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            photo TEXT,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT UNIQUE
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT UNIQUE
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        """
        Внутренний метод для массового выполнения SQL-запросов на изменение данных (INSERT, UPDATE, DELETE) с коммитом.
        """
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()

    def __select_data(self, sql, data=tuple()):
        """
        Внутренний метод для выполнения SELECT-запросов и возврата всех найденных строк.
        """
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        """
        Заполняет справочники skills и status базовыми значениями по умолчанию (игнорируя дубликаты).
        """
        self.__executemany('INSERT OR IGNORE INTO skills (skill_name) VALUES(?)', skills)
        self.__executemany('INSERT OR IGNORE INTO status (status_name) VALUES(?)', statuses)

    def insert_project(self, data):
        """
        Добавляет новый проект в таблицу projects (принимает список кортежей вида [(user_id, project_name, url, status_id)]).
        """
        sql = 'INSERT OR IGNORE INTO projects (user_id, project_name, url, status_id) VALUES(?, ?, ?, ?)'
        self.__executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        """
        Привязывает существующий навык к проекту пользователя в связующей таблице project_skills.
        """
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    def insert_new_status(self, status_name):
        """
        Добавляет новый статус в общий справочник status.
        """
        sql = 'INSERT OR IGNORE INTO status (status_name) VALUES(?)'
        self.__executemany(sql, [(status_name,)])

    def update_status(self, old_status_name, new_status_name):
        """
        Переименовывает существующий статус в справочнике status.
        """
        sql = 'UPDATE status SET status_name = ? WHERE status_name = ?'
        self.__executemany(sql, [(new_status_name, old_status_name)])

    def insert_new_skill(self, skill_name):
        """
        Добавляет новый навык в общий справочник skills.
        """
        sql = 'INSERT OR IGNORE INTO skills (skill_name) VALUES(?)'
        self.__executemany(sql, [(skill_name,)])

    def update_skill(self, old_skill_name, new_skill_name):
        """
        Переименовывает существующий навык в справочнике skills.
        """
        sql = 'UPDATE skills SET skill_name = ? WHERE skill_name = ?'
        self.__executemany(sql, [(new_skill_name, old_skill_name)])

    def get_statuses(self):
        """
        Возвращает список всех названий статусов из таблицы status.
        """
        return self.__select_data('SELECT status_name FROM status')

    def get_status_id(self, status_name):
        """
        Возвращает ID статуса по его названию или None, если статус не найден.
        """
        res = self.__select_data('SELECT status_id FROM status WHERE status_name = ?', (status_name,))
        return res[0][0] if res else None

    def get_projects(self, user_id):
        """
        Возвращает все записи проектов, принадлежащих конкретному пользователю (user_id).
        """
        return self.__select_data('SELECT * FROM projects WHERE user_id = ?', data=(user_id,))

    def get_project_id(self, project_name, user_id):
        """
        Возвращает ID проекта по его названию и ID владельца (user_id).
        """
        return self.__select_data(
            sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?',
            data=(project_name, user_id,)
        )[0][0]

    def get_skills(self):
        """
        Возвращает все записи (ID и название) из справочника skills.
        """
        return self.__select_data(sql='SELECT * FROM skills')

    def get_project_skills(self, project_name):
        """
        Возвращает строку с перечислением всех навыков проекта через запятую.
        """
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
            JOIN project_skills ON projects.project_id = project_skills.project_id 
            JOIN skills ON skills.skill_id = project_skills.skill_id 
            WHERE project_name = ?''', data=(project_name,))
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        """
        Возвращает полную информацию о проекте (имя, описание, ссылка, текстовый статус, фото) через JOIN со справочником статусов.
        """
        sql = """
            SELECT project_name, description, url, status_name, photo FROM projects 
            JOIN status ON status.status_id = projects.status_id
            WHERE project_name=? AND user_id=?
        """
        return self.__select_data(sql=sql, data=(project_name, user_id))

    def update_projects(self, param, data):
        """
        Обновляет указанное поле (param) проекта в БД (data — кортеж (новое_значение, project_name, user_id)).
        """
        sql = f'UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?'
        self.__executemany(sql, [data])

    def delete_project(self, user_id, project_id):
        """
        Удаляет проект пользователя из таблицы projects по user_id и project_id.
        """
        sql = 'DELETE FROM projects WHERE user_id = ? AND project_id = ?'
        self.__executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        """
        Удаляет привязку конкретного навыка (skill_id) к проекту (project_id) из таблицы project_skills.
        """
        sql = 'DELETE FROM project_skills WHERE skill_id = ? AND project_id = ?'
        self.__executemany(sql, [(skill_id, project_id)])
