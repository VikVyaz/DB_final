# -*- coding: utf-8 -*-
from src.api_handler import to_get_10_employers
import psycopg2
from psycopg2 import sql
from psycopg2.errors import UndefinedColumn, UndefinedTable, UniqueViolation, DuplicateTable
from psycopg2.extras import RealDictCursor
from src.vacancy_handler import VacHandler
from src.abstract_cls import AbcDBManager
import os
from dotenv import load_dotenv

load_dotenv()


class DBManager(AbcDBManager):
    """
    Класс работы с БД
    """

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.__conn = None
        self.__cur = None
        self.db_exists = True

        self.__conn_params = {
            'host': "localhost",
            'port': 5432,
            'dbname': db_name,
            'user': "postgres",
            'password': os.getenv('PSTGRE_PASS')
        }

    def __enter__(self):

        try:
            self.__conn = psycopg2.connect(**self.__conn_params)
            self.__conn.autocommit = True
        except UnicodeDecodeError:
            self.__conn_params['dbname'] = 'postgres'
            self.db_exists = False

            err_conn = psycopg2.connect(**self.__conn_params)
            err_conn.autocommit = True
            err_cur = err_conn.cursor()
            err_cur.execute(sql.SQL("create database {}").format(sql.Identifier(self.db_name)))
            err_cur.close()
            err_conn.close()

            self.__conn_params['dbname'] = self.db_name
            self.__conn = psycopg2.connect(**self.__conn_params)
            self.__conn.autocommit = True

        self.__cur = self.__conn.cursor(cursor_factory=RealDictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__cur:
            self.__cur.close()
        if self.__conn:
            if exc_type is None:
                self.__conn.commit()
            else:
                self.__conn.rollback()
            self.__conn.close()
            print('Соединение отключено')

    def to_update_db(self):
        """
        Метод обновление таблицы с вакансиями
        """

        try:
            self.__to_add_data(self.__cur)
            print('Запись БД закончена')
        except (UndefinedTable, UndefinedColumn, UniqueViolation, DuplicateTable):
            print('Обновление БД начата...')
            self.__cur.execute('drop table if exists vacancies;')
            self.__cur.execute('drop table if exists employers;')
            self.__to_add_data(self.__cur)
            print('Обновление БД закончена')

    @staticmethod
    def __to_add_data(cur):
        """
        Метод добавления данных в БД
        """

        cur.execute("""
            CREATE TABLE employers (
                employer_id INT,
                employer_name VARCHAR,
                comp_url VARCHAR,
                vacancies_url VARCHAR,
                rating REAL,
                employer_trusted BOOLEAN,

                CONSTRAINT pk_companies_company_id PRIMARY KEY (employer_id)
            );
        """)

        cur.execute("""
            CREATE TABLE vacancies (
                vacancy_id INT,
                vacancy_name VARCHAR,
                city VARCHAR,
                vacancy_url VARCHAR,
                schedule VARCHAR,
                vac_salary_from INT,
                vac_salary_to INT,
                vac_currency VARCHAR,
                vac_avg_salary INT,
                employer_id INT,
                
                CONSTRAINT pk_vacancies_vacancy_id PRIMARY KEY (vacancy_id),
                CONSTRAINT fk_employers_to_vacancies FOREIGN KEY (employer_id) REFERENCES employers(employer_id)
            );
        """)

        print('Получение данных с HH.ru...')
        api_response = to_get_10_employers()
        print('Данные получены.')

        vacancies = VacHandler()

        for vac in api_response:
            employer_field = vac['employer']

            emp_params = vacancies.to_give_emp_params(employer_field)

            comp_query = """
                        INSERT INTO employers 
                        (employer_id, employer_name, comp_url, vacancies_url, rating, employer_trusted)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (employer_id) DO NOTHING;
                        """
            comp_data = (*emp_params,)
            cur.execute(comp_query, comp_data)

            vac_params = vacancies.to_give_vac_params(vac, emp_params)

            query = """
                    INSERT INTO vacancies (vacancy_id, vacancy_name, city, vacancy_url, schedule, vac_salary_from,
                    vac_salary_to, vac_currency, vac_avg_salary, employer_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vacancy_id) DO UPDATE SET
                    vacancy_name = EXCLUDED.vacancy_name,
                    city = EXCLUDED.city,
                    vacancy_url = EXCLUDED.vacancy_url,
                    schedule = EXCLUDED.schedule,
                    vac_salary_from = EXCLUDED.vac_salary_from,
                    vac_salary_to = EXCLUDED.vac_salary_to,
                    vac_currency = EXCLUDED.vac_currency,
                    vac_avg_salary = EXCLUDED.vac_avg_salary,
                    employer_id = EXCLUDED.employer_id;
                    """
            vacancy_data = (*vac_params,)

            cur.execute(query, vacancy_data)

    def get_companies_and_vacancies_count(self) -> list:
        """
        Метод получения списка всех компаний и кол-ва их вакансий
        """

        self.__cur.execute("""
        SELECT COUNT(v.vacancy_id) AS vac_count, e.employer_id, e.employer_name
        FROM vacancies AS v
        JOIN employers AS e USING (employer_id)
        GROUP BY e.employer_id, e.employer_name
        ORDER BY vac_count DESC;
        """)

        return [dict(row) for row in self.__cur.fetchall()]

    def get_all_vacancies(self) -> list:
        """
        Метод получения всех вакансий с указанием
        названия компании, названия вакансии, зп и ссылки на нее
        """

        self.__cur.execute("""
            SELECT e.employer_name, v.vacancy_name, v.vac_salary_from, v.vac_salary_to, v.vac_avg_salary, v.vacancy_url
            FROM vacancies AS v
            JOIN employers AS e USING (employer_id);
        """)

        return [dict(row) for row in self.__cur.fetchall()]

    def get_avg_salary(self) -> dict:
        """
        Метод получения средней зп по вакансиям
        """

        self.__cur.execute("""
            SELECT AVG(vac_avg_salary) AS average_salary
            FROM vacancies;
        """)

        avg_salary = self.__cur.fetchall()
        avg_salary[0]['average_salary'] = round(float(avg_salary[0]['average_salary']), 2)

        return dict(avg_salary[0])

    def get_vacancies_with_higher_salary(self) -> list:
        """
        Метод получения списка вакансий, зп которых выше среднего по вакансиям
        """

        self.__cur.execute("""
            SELECT *
            FROM vacancies
            WHERE vac_avg_salary > (
                SELECT AVG(vac_avg_salary)
                FROM vacancies);
        """)

        return [dict(row) for row in self.__cur.fetchall()]

    def get_vacancies_with_keyword(self, keyword: str) -> list | None:
        """
        Метод получения всех вакансий по ключевому слову
        """

        if isinstance(keyword, str):
            self.__cur.execute("""
                SELECT *
                FROM vacancies
                WHERE vacancy_name
                ILIKE %s;""", (f'%{keyword}%',))

            return [dict(row) for row in self.__cur.fetchall()]

# if __name__ == '__main__':
#     with DBManager('testdb') as db:
# print('Проверка связи')
# db.to_update_db()
# print(type(db.get_companies_and_vacancies_count()[0]))
# print(db.get_companies_and_vacancies_count())
# print(db.get_all_vacancies())
# print(db.get_avg_salary())
# print(db.get_vacancies_with_higher_salary())
# print("-----", db.get_vacancies_with_keyword('чат'))
