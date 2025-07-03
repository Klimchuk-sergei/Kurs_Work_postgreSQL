import requests
from typing import List, Dict, Any


class HHApiHandler:
    """
    Класс для работы с API HeadHunter.
    Получаем информацию о компаниях и их вакансиях.
    """
    BASE_URL = 'https://api.hh.ru'

    def get_employers(self, employer_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получает информацию о нескольких работодателях по их ID.
        employer_ids: Список ID работодателей, которые нас интересуют.
        return возвращает список словарей с данными о работодателях.
        """
        employers_data = []
        print("Получение данных о компаниях...")
        for employer_id in employer_ids:
            url = f"{self.BASE_URL}/employers/{employer_id}"
            try:
                response = requests.get(url)
                response.raise_for_status()  # Проверка на ошибки (код 4xx или 5xx)
                employers_data.append(response.json())
                print(f"  - Компания с ID {employer_id} успешно загружена.")
            except requests.RequestException as e:
                print(f"Ошибка при запросе данных о компании {employer_id}: {e}")
        return employers_data

    def get_vacancies_for_employer(self, employer_id: str) -> List[Dict[str, Any]]:
        """
        Получает список всех вакансий для одного конкретного работодателя.
        Метод автоматически обрабатывает пагинацию (перелистывание страниц) API.
        employer_id: ID работодателя.
        return возвращает список словарей с данными о вакансиях.
        """
        params = {
            'employer_id': employer_id,
            'per_page': 100,  # Максимальное количество вакансий на одной странице
            'page': 0,  # Начинаем с первой страницы (индексация с 0)
            'archive': False  # Поиск только в открытых вакансиях
        }
        all_vacancies = []

        while True:
            url = f"{self.BASE_URL}/vacancies"
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                vacancies_on_page = data.get('items', [])
                all_vacancies.extend(vacancies_on_page)

                # Проверяем, есть ли еще страницы для загрузки
                if data['pages'] - 1 == params['page']:
                    break

                params['page'] += 1  # Переходим на следующую страницу

            except requests.RequestException as e:
                print(f"Ошибка при запросе вакансий для компании {employer_id} на странице {params['page']}: {e}")
                break  # В случае ошибки прерываем загрузку вакансий для этой компании

        return all_vacancies
