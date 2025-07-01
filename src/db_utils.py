import psycopg2
from typing import Dict, Any, List


def create_database(db_name: str, params: Dict[str, Any]) -> None:
    """
    Создаем новую базу данных в PostgreSQl.
    """

    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cur.execute(f"CREATE DATABASE {db_name}")
        print(f"База данных '{db_name}' успешно создана.")
    except psycopg2.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        cur.close()
        conn.close()


def create_tables(conn) -> None:
    """
    Создаем таблицы 'employers' и 'vacancies' в указанной БД.
    Таблица 'vacancies' связывается с 'employers' через внешний ключ
    """
    commands = (
        """
                CREATE TABLE employers (
                    employer_id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    url VARCHAR(255)
                )
                """,
        """
        CREATE TABLE vacancies (
            vacancy_id INTEGER PRIMARY KEY,
            employer_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            salary INTEGER,
            url VARCHAR(255),
            FOREIGN KEY (employer_id) REFERENCES employers (employer_id) ON DELETE CASCADE
        )
        """
    )
    try:
        with conn.cursor() as cur:
            for command in commands:
                cur.execute(command)
        conn.commit()
        print("Таблицы 'employers' и 'vacancies' успешно созданы.")
    except psycopg2.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
        conn.rollback()


def populate_tables(conn, employers_data: List[Dict[str, Any]], vacancies_data: List[Dict[str, Any]]) -> None:
    """
    Заполняем таблицы 'employers' и 'vacancies' данными, полученными от API
    """
    insert_employers_query = "INSERT INTO employers (employer_id, name, url) VALUES (%s, %s, %s)"
    insert_vacancies_query = ("INSERT INTO vacancies (vacancy_id, employer_id, title, salary, url) "
                              "VALUES (%s, %s, %s, %s, %s)")
    try:
        with conn.cursor() as cur:
            # заполняем таблицу employers
            for emp in employers_data:
                cur.execute(insert_employers_query, (emp['id'], emp['name'], emp['alternate_url']))
            # заполняем таблицу vacancies
            for vac in vacancies_data:
                # Пропускаем вакансии без id работодателя или с id, которого нет в нашем списке
                if not any(emp['id'] == vac['employer']['id'] for emp in employers_data):
                    continue
                salary = vac.get('salary')
                salary_from = salary['from'] if salary and salary.get('from') else None
                cur.execute(insert_vacancies_query,
                            (vac['id'], vac['employer']['id'], vac['name'], salary_from, vac['alternate_url']))
        conn.commit()  # Сохраняем все вставки
        print("Данные успешно загружены в таблицы.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка при заполнении таблиц: {error}")
        conn.rollback()  # Откатываем в случае ошибки
