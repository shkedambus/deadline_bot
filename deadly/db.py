import pymysql.cursors
from datetime import datetime
from config import host, user, password, database


try: # подключение к базе данных

    connection = pymysql.connect(host=host,
                                 user=user,
                                 password=password,
                                 database=database,
                                 charset="utf8mb4",
                                 cursorclass=pymysql.cursors.DictCursor)

    cursor = connection.cursor()
    create_table_query = "CREATE TABLE IF NOT EXISTS tasks (id int(11) NOT NULL AUTO_INCREMENT, user varchar(255) COLLATE utf8_bin NOT NULL, deadline datetime, task varchar(255) COLLATE utf8_bin NOT NULL, primary key (id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=1 ;"
    cursor.execute(create_table_query)


    def make_pretty(rows):  # красивый вывод дедлайнов

        months = {"01": "Января", "02": "Февраля", "03": "Марта",
                  "04": "Апреля", "05": "Мая", "06": "Июня",
                  "07": "Июля", "08": "Августа", "09": "Сентября",
                  "10": "Октября", "11": "Ноября", "12": "Декабря"}
        
        text = ""
        ind = 1
        for row in rows:
            deadline = str(row["deadline"].date()).split("-")
            date_str = deadline[2] + " " + months[deadline[1]] + " " + deadline[0]
            task = row["task"]
            text += f"{ind}) {task} ({date_str}) \n"  
            ind += 1
        return text


    def check_task(user_id, task):  # проверка на то, существует ли уже такой дедлайн пользователя
        rows = get_from_db(user_id, task)
        if rows:
            return False
        return True


    def convert_to_deadline(date_str):  # перевод строки в объект datetime
        date_format = "%d-%m-%Y"
        deadline = datetime.strptime(date_str, date_format).date()
        return deadline


    def insert_into_db(user_id, date_str, task):  # добавление ответа пользователя в таблицу
        if check_task(user_id, task):

            insert_query = "INSERT INTO tasks (user, deadline, task) VALUES (%s, %s, %s)"

            deadline = convert_to_deadline(date_str)            
            today = datetime.today().date()
            if deadline >= today:
                cursor.execute(insert_query, (user_id, deadline, task))
                connection.commit()
                return "Дедлайн был успешно сохранен!"
            return "Дедлайн устарел."

        return "Такой дедлайн уже существует."


    def remove_from_db(user_id, task):  # удаление задачи из таблицы
        remove_query = "DELETE FROM tasks WHERE user = %s AND task = %s"
        cursor.execute(remove_query, (user_id, task))
        connection.commit()
        return "Дедлайн пользователя был успешно удален!"


    def get_from_db(user_id, task=""):  # получение всех задач пользователя

        if task:
            select_query = "SELECT deadline, task FROM tasks WHERE user = %s AND task = %s ORDER BY deadline"
            cursor.execute(select_query, (user_id, task))
            rows = cursor.fetchall()
            return rows

        else:
            select_query = "SELECT deadline, task FROM tasks WHERE user = %s ORDER BY deadline"
            cursor.execute(select_query, user_id)
            rows = cursor.fetchall()
            return rows


    def clear_db(user_id="all"):  # очистить базу данных
        if user_id == "all":
            clear_query = "DROP TABLE tasks"
            cursor.execute(clear_query)
            connection.commit()
            return "Таблица успешно очищена"
        else:
            clear_query = "DELETE FROM tasks WHERE user = %s"
            cursor.execute(clear_query, user_id)
            connection.commit()
            return "Все дедлайны успешно удалены"


except Exception as ex:
    print("Ошибка подключения к базе данных...")
    print(ex)