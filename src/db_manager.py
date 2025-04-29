# -*- coding: utf-8 -*-
from src.abstract_cls import AbsManager
from src.api_handler import to_get_10_vacs
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()


class DBManager:
    """
    Database management class
    """

    def __init__(self, db_name: str):
        if isinstance(db_name, str):
            self.db_name = db_name
        else:
            raise TypeError('Type str only available ')

    def sync_db(self):
        """
        Creates a database or updates the data, if exists
        """

        conn_params = {
            'host': "localhost",
            'port': 5432,
            'dbname': "testdb",
            'user': "postgres",
            'password': os.getenv("PSTGRE_PASS")
        }

        try:
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor() as cur:
                    answer = input('DB exists. Rewrite? y/n')
                    if answer == 'y':
                        cur.execute("create table fuck")
                        self.__to_add_data(cur)
                    else:
                        print('DB rewrote')

        except psycopg2.OperationalError as e:
            print(e)
            conn_params['dbname'] = 'postgres'
            with psycopg2.connect(**conn_params) as conn2:
                conn2.autocommit = True
                with conn2.cursor() as cur2:
                    cur2.execute(sql.SQL("create database {}").format(sql.Identifier(self.db_name)))

            conn_params['dbname'] = self.db_name
            with psycopg2.connect(**conn_params) as conn3:
                with conn3.cursor() as cur3:
                    self.__to_add_data(cur3)
                    print(f'DB {self.db_name} is create')

    @staticmethod
    def __to_add_data(cur):
        """
        Метод добавления вакансий в БД
        """

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id INT,
                vacancy_name VARCHAR,
                employer VARCHAR,
                city VARCHAR,
                url VARCHAR,
                schedule VARCHAR,
                vac_salary_from INT,
                vac_salary_to INT,
                vac_avg_salary INT,

                CONSTRAINT pk_vacancies_id PRIMARY KEY (id)
            )
        """)

        vacancies = to_get_10_vacs()

        for vac in vacancies:
            vac_id = int(vac['id'])
            vac_name = vac['name']
            vac_employer = vac['employer']['name']
            vac_city = vac['area']['name']
            vac_url = vac['alternate_url']
            vac_schedule = vac['schedule']['name']

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

            query = "INSERT INTO vacancies VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            vacancy_data = (vac_id, vac_name, vac_employer, vac_city, vac_url, vac_schedule,
                            vac_salary_from, vac_salary_to, vac_avg_salary)
            cur.execute(query, vacancy_data)

    # def get_companies_and_vacancies_count(self):
    #     """
    #     Получение списка всех компаний и количество вакансий у каждой компании
    #     """
    #     pass
    #
    # def get_all_vacancies(self):
    #     """
    #     Получение списка всех вакансий с указанием названия компании,
    #     названия вакансии и зарплаты и ссылки на вакансию
    #     """
    #     pass
    #
    # def get_avg_salary(self):
    #     """
    #     Получение средней зарплату по вакансиям
    #     """
    #     pass
    #
    # def get_vacancies_with_higher_salary(self):
    #     """
    #     Получение списка всех вакансий, у которых зарплата выше средней по всем вакансиям
    #     """
    #     pass
    #
    # def get_vacancies_with_keyword(self):
    #     """
    #     Получение списка всех вакансий, в названии которых содержатся переданные в метод слова, например python
    #     """
    #     pass


if __name__ == '__main__':
    db = DBManager('tratata')
    db.sync_db()
