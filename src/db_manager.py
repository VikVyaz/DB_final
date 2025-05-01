# -*- coding: utf-8 -*-
from src.api_handler import to_get_10_vacs
import psycopg2
from psycopg2 import sql
from psycopg2.errors import UndefinedColumn, UndefinedTable, UniqueViolation, DuplicateTable
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()


class DBManager:
    """
    Класс работы с БД
    """

    def __init__(self, db_name: str):
        if isinstance(db_name, str):
            self.db_name = db_name
        else:
            raise TypeError('Доступно только в формате str')

        self.__conn = None
        self.__cur = None

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
            print(f'Подключено к {self.db_name}')
        except UnicodeDecodeError:
            print(f'БД {self.db_name} не существует. Создаю..')
            self.__conn_params['dbname'] = 'postgres'
            err_conn = psycopg2.connect(**self.__conn_params)
            err_conn.autocommit = True
            err_cur = err_conn.cursor()
            err_cur.execute(sql.SQL("create database {}").format(sql.Identifier(self.db_name)))
            print('БД создана')
            err_cur.close()
            err_conn.close()

            self.__conn = psycopg2.connect(**self.__conn_params)
            print(f'Подключено к {self.db_name}')

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
                vac_avg_salary INT,
                employer_id INT,
                
                CONSTRAINT pk_vacancies_vacancy_id PRIMARY KEY (vacancy_id),
                CONSTRAINT fk_employers_to_vacancies FOREIGN KEY (employer_id) REFERENCES employers(employer_id)
            );
        """)

        print('Получение данных с HH.ru...')
        vacancies = to_get_10_vacs()
        print('Данные получены.')

        for vac in vacancies:
            employer_field = vac['employer']

            employer_id = int(employer_field['id'])
            employer_name = employer_field['name']
            comp_url = employer_field['alternate_url']
            vacancies_url = employer_field['vacancies_url']
            rating = float(
                employer_field.get('employer_rating', {}).get('total_rating', None)) if employer_field[
                'employer_rating'] else None
            employer_trusted = employer_field['trusted']

            comp_query = """
                        INSERT INTO employers 
                        (employer_id, employer_name, comp_url, vacancies_url, rating, employer_trusted)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (employer_id) DO NOTHING;
                        """
            comp_data = (employer_id, employer_name, comp_url, vacancies_url, rating, employer_trusted)
            cur.execute(comp_query, comp_data)

            vacancy_id = int(vac['id'])
            vacancy_name = vac['name']
            city = vac['area']['name']
            vacancy_url = vac['alternate_url']
            schedule = vac['schedule']['name']

            if vac['salary']:
                vac_salary_from = vac['salary']['from']
                vac_salary_to = vac['salary']['to']
                if vac_salary_from and vac_salary_to:
                    vac_avg_salary = (vac_salary_from + vac_salary_to) / 2
                elif vac_salary_from:
                    vac_avg_salary = vac_salary_from
                else:
                    vac_avg_salary = vac_salary_to
            else:
                vac_salary_from = None
                vac_salary_to = None
                vac_avg_salary = None

            employer_id = int(vac['employer']['id'])

            query = """
                    INSERT INTO vacancies (vacancy_id, vacancy_name, city, vacancy_url, schedule, vac_salary_from,
                    vac_salary_to, vac_avg_salary, employer_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (vacancy_id) DO UPDATE SET
                    vacancy_name = EXCLUDED.vacancy_name,
                    city = EXCLUDED.city,
                    vacancy_url = EXCLUDED.vacancy_url,
                    schedule = EXCLUDED.schedule,
                    vac_salary_from = EXCLUDED.vac_salary_from,
                    vac_salary_to = EXCLUDED.vac_salary_to,
                    vac_avg_salary = EXCLUDED.vac_avg_salary,
                    employer_id = EXCLUDED.employer_id;
                    """
            vacancy_data = (vacancy_id, vacancy_name, city, vacancy_url, schedule, vac_salary_from, vac_salary_to,
                            vac_avg_salary, employer_id)
            cur.execute(query, vacancy_data)

    def get_companies_and_vacancies_count(self):
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

    def get_all_vacancies(self):
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

    def get_avg_salary(self):
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

    def get_vacancies_with_higher_salary(self):
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

    def get_vacancies_with_keyword(self, keyword: str):
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
        else:
            print('Ключевое слово должно быть в формате str')



# if __name__ == '__main__':
    # with DBManager('testdb') as db:
    # db.to_update_db()
    # print(type(db.get_companies_and_vacancies_count()[0]))
    # print(db.get_companies_and_vacancies_count())
    # print(db.get_all_vacancies())
    # print(db.get_avg_salary())
    # print(db.get_vacancies_with_higher_salary())
    # print(db.get_vacancies_with_keyword('Матрос'))
