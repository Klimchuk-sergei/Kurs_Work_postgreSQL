import configparser

import psycopg2

from src.api_handler import HHApiHandler
from src.db_utils import create_database, create_tables, populate_tables
from src.db_manager import DBManager

"""Список ID компаний"""
EMPLOYER_IDS = [
    '1740',     # Яндекс
    '15478',    # VK
    '3529',     # Сбер
    '78638',    # Тинькофф
    '2180',     # Ozon
    '84585',    # Авито
    '1122462',  # Skyeng
    '4181',     # Контур
    '64174',    # 2ГИС
    '1057',     # Лаборатория Касперского
    '8923296',  # TenderLive
    '55828',    # Insyres
    '1245158',  # SummitGroup
    '1888961',  # Lead
    '2371',     # Акрихин
    '3407499',  # IT школа Hello world
    '6093775',  # Aston
    '4877534',  # Стафэксперт
    '596426',   # Russian Robotics
    '2460975',  # iLocks
    '2222250',  # Аптека Апрель
    '6382712'   # Instore
]


def load_db_config(filename='database.ini', section='postgresql'):
    """Читаем параметры конфигурации из файла"""
    parser = configparser.ConfigParser()
    parser.read(filename)
    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception(f'Секция {section} не найдена в файле {filename}. '
                        f'Убедитесь в правильной настройке database.ini и его существовании')
    return db_params


def setup_database():
    """
    Выполняем настройку базы дданых:
    1. Получаем данные от API
    2. Создаем БД и таблицы
    3. Заполняем таблицы данными
    """
    config_for_creation = load_db_config()
    db_name = config_for_creation.pop('database')

    print("---Создание базы данных---")
    create_database(db_name, config_for_creation)

    print("\n---Получение данных с hh.ru---")
    api_handler = HHApiHandler()

    # Получаем данные о компаниях
    employers_data = api_handler.get_employers(EMPLOYER_IDS)
    if not employers_data:
        print("Не удалось  получить данные о компаниях.")
        return

    # получаем данные о вакансиях
    all_vacancies_data = []
    seen_vacancy_ids = set()  # Множество для хранения ID уже добавленных вакансий

    for emp in employers_data:
        print(f"Получение вакансий для компании '{emp['name']}'...")
        vacancies = api_handler.get_vacancies_for_employer(emp['id'])

        # Фильтруем дубликаты перед добавлением
        unique_vacancies = []
        for vacancy in vacancies:
            if vacancy['id'] not in seen_vacancy_ids:
                unique_vacancies.append(vacancy)
                seen_vacancy_ids.add(vacancy['id'])

        all_vacancies_data.extend(unique_vacancies)
        print(f"  > Найдено {len(vacancies)} вакансий, из них уникальных: {len(unique_vacancies)}.")

    print(f"\nВсего найдено уникальных вакансий: {len(all_vacancies_data)}")

    print("\n---Создание таблиц и их заполнение___")
    config_for_connection = load_db_config()
    conn = None
    try:
        conn = psycopg2.connect(**config_for_connection)
        create_tables(conn)
        populate_tables(conn, employers_data, all_vacancies_data)
    except Exception as e:
        print(f"Произошла ошибка при работе с БД: {e}")
    finally:
        if conn:
            conn.close()
    print("\n---Настройка БД завершена")


def user_interaction():
    """функция для взаимодейстивя с пользователем"""
    config = load_db_config()
    try:
        db_manager = DBManager(config)
    except Exception:
        print("\nНе удалось подключиться к БД")
        return

    while True:
        print("\n================ Меню ================")
        print("1 - Показать список всех компаний и количество вакансий")
        print("2 - Показать список всех вакансий (компания, вакансия, зарплата, ссылка)")
        print("3 - Показать среднюю зарплату по вакансиям")
        print("4 - Показать вакансии с зарплатой выше средней")
        print("5 - Найти вакансии по ключевому слову")
        print("0 - Выход")

        choice = input("Введите ваш выбор").strip()

        print(f"Вы ввели: '{choice}', тип данных: {type(choice)}")

        if choice == '1':
            companies = db_manager.get_companies_and_vacancies_count()
            print("\n---Компании и количество вакансий---")
            for company, count in companies:
                print(f"{company}: {count} вакансйи")

        elif choice == '2':
            vacancies = db_manager.get_all_vacancies()
            print("\n---Списсок вакансий")
            for company, title, salary, url in vacancies:
                salary_str = f"{salary} руб." if salary else "Не указана"
                print(f" Компания: {company}\n Вакансия: {title}\n зарплата: {salary_str}\n ссылка: {url}\n")


        elif choice == '3':
            avg_salary = db_manager.get_avg_salary()
            if avg_salary:
                print(f"\nСредняя зарплата по всем найденным вакансиям: {avg_salary:.2f} руб.")
            else:
                print("\nНе удалось рассчитать среднюю зарплату (возможно, нет вакансий с указанной ЗП).")


        elif choice == '4':
            vacancies = db_manager.get_vacancies_with_higher_salary()
            print("\n--- Вакансии с зарплатой выше средней ---")
            if vacancies:
                for title, salary, url in vacancies:
                    print(f"  - {title} (Зарплата: {salary} руб.) -> {url}")
            else:
                print("Нет вакансий с зарплатой выше средней или не удалось рассчитать среднюю ЗП.")


        elif choice == '5':
            keyword = input("Введите ключевое слово для поиска (например, Python, Аналитик, Java): ").strip()
            if not keyword:
                print("Вы не ввели ключевое слово.")
                continue
            vacancies = db_manager.get_vacancies_with_keyword(keyword)
            print(f"\n--- Вакансии по запросу '{keyword}' ---")
            if vacancies:
                for title, salary, url in vacancies:
                    salary_str = f"{salary} руб." if salary else "Не указана"
                    print(f"  - {title} (Зарплата: {salary_str}) -> {url}")
            else:
                print("Вакансии с таким ключевым словом не найдены.")


        elif choice == '0':
            db_manager.disconnect()
            print("Программа завершена.")
            break


        else:
            print("Некорректный ввод. Пожалуйста, выберите существующий пункт меню.")


if __name__ == '__main__':
    print("Добро пожаловать в программу по работе с вакансиями с hh.ru!")

    prompt = "Нажмите 's' (setup) для первоначальной настройки БД или любую другую клавишу для работы с данными: "
    action = input(prompt).lower().strip()

    # Проверяем, не пустая ли строка и начинается ли она с 's'
    if action and action.startswith('s'):
        setup_database()
        user_interaction()
    else:
        user_interaction()
