import psycopg2
from typing import List, Tuple, Any, Optional


class DBManager:
    """
    Класс для взаимодействия с базой данных PostgreSQL
    """

    def __init__(self, params: dict):
        """
        Класс для взаимодействия с базой данных PostgreSQL.
        """
        try:
            self.conn = psycopg2.connect(**params)
        except psycopg2.OperationalError as e:
            print(f"Не удалось подключиться к базе данных: {e}")
            raise

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании.

        :return: Список кортежей (название_компании, количество_вакансий).
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.name, COUNT(v.vacancy_id)
                FROM employers e
                LEFT JOIN vacancies v ON e.employer_id = v.employer_id
                GROUP BY e.name
                ORDER BY COUNT(v.vacancy_id) DESC;
            """)
            return cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple[str, str, int, str]]:
        """
        Получает список всех вакансий с указанием компании, зарплаты и ссылки.

        :return: Список кортежей (название_компании, название_вакансии, зарплата, ссылка).
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT e.name, v.title, v.salary, v.url
                FROM vacancies v
                JOIN employers e ON v.employer_id = e.employer_id
                ORDER BY e.name, v.salary DESC;
            """)
            return cur.fetchall()

    def get_avg_salary(self) -> Optional[float]:
        """
        Получает среднюю зарплату по всем вакансиям (где зарплата указана).

        :return: Средняя зарплата в виде float или None, если вакансий с зарплатой нет.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(salary)
                FROM vacancies
                WHERE salary IS NOT NULL;
            """)
            result = cur.fetchone()
            # Убеждаемся, что результат не пустой и содержит не NULL
            return float(result[0]) if result and result[0] is not None else None

    def get_vacancies_with_higher_salary(self) -> List[Tuple[str, int, str]]:
        """
        Получает список вакансий, у которых зарплата выше средней по всем вакансиям.

        :return: Список кортежей (название_вакансии, зарплата, ссылка).
        """
        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            # Если среднюю зарплату посчитать не удалось, возвращаем пустой список
            print("Не удалось рассчитать среднюю зарплату. Невозможно найти вакансии выше средней.")
            return []

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT title, salary, url
                FROM vacancies
                WHERE salary > %s
                ORDER BY salary DESC;
            """, (avg_salary,))
            return cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, int, str]]:
        """
        Получает список вакансий, в названии которых содержится переданное ключевое слово.
        Поиск регистронезависимый.

        :param keyword: Ключевое слово для поиска.
        :return: Список кортежей (название_вакансии, зарплата, ссылка).
        """
        with self.conn.cursor() as cur:
            # Используем lower() для регистронезависимого поиска и оператор LIKE
            cur.execute("""
                SELECT title, salary, url
                FROM vacancies
                WHERE lower(title) LIKE lower(%s)
                ORDER BY salary DESC;
            """, (f'%{keyword}%',))
            return cur.fetchall()

    def disconnect(self) -> None:
        """
        Закрывает соединение с базой данных.
        """
        if self.conn:
            self.conn.close()
            print("Соединение с БД закрыто.")
