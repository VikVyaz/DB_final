from abc import ABC, abstractmethod


class AbcDBManager(ABC):
    """
    Абстрактный класс для работы с БД
    """

    @abstractmethod
    def to_update_db(self):
        """
        Метод обновление таблицы с вакансиями
        """
        pass

    @abstractmethod
    def get_companies_and_vacancies_count(self):
        """
        Метод получения списка всех компаний и кол-ва их вакансий
        """
        pass

    @abstractmethod
    def get_all_vacancies(self):
        """
        Метод получения всех вакансий с указанием
        названия компании, названия вакансии, зп и ссылки на нее
        """
        pass

    @abstractmethod
    def get_avg_salary(self):
        """
        Метод получения средней зп по вакансиям
        """
        pass

    @abstractmethod
    def get_vacancies_with_higher_salary(self):
        """
        Метод получения списка вакансий, зп которых выше среднего по вакансиям
        """
        pass

    @abstractmethod
    def get_vacancies_with_keyword(self, keyword: str):
        """
        Метод получения всех вакансий по ключевому слову
        """
        pass
