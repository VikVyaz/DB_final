from src.db_manager import DBManager
import pandas as pd


def human_response(data: list):
    """
    Функция очеловечивания ответа методов класса
    """
    if data:
        return pd.DataFrame(data)
    else:
        return 'Таких вакансий не найдено'


def main():
    """
    Функция взаимодействия с пользователем
    """

    print(
        'Привет!\n'
        'Перед тобой программа взаимодействия с БД.\n'
        'Программа автоматически создает (если БД не существовало) и подключается к БД.\n'
        'БД представляет из себя вакансии от 10 разных компаний с HH.ru\n'
    )

    incorrect_input = True
    db_name = ''
    while incorrect_input:
        # db_name = input('Введите имя БД. Это должна быть строка(буквы и/или цифры) без знаков:\n')
        db_name = 'check_db'
        if db_name.isalnum() or '_' in db_name:
            incorrect_input = False
            print(f'Отлично! Имя для БД - {db_name}\n')
        else:
            print('Только буквы и цифры. Давай еще раз.')

    with DBManager(db_name) as db:
        if db.db_exists:

            # rewrite = input("Похоже такая БД существует, обновить последние данные?\nда/нет\n".lower())
            rewrite = 'нет'
            while rewrite not in ['да', 'нет']:
                print('Ответ либо "да", либо "нет")')
                rewrite = input("да/нет\n").lower()

            if rewrite == 'да':
                db.to_update_db()
                print('БД обновлена')
            else:
                print('БД не обновлена')
        else:
            db.to_update_db()

        print(
            'Сейчас продемонстрирую функционал:\n'
            '---1. Получение списка всех компаний и кол-ва их вакансий---\n'
            f'{human_response(db.get_companies_and_vacancies_count())}\n\n'
            '---2. Получение всех вакансий с указанием названия компании, названия вакансии, зп и ссылки на нее---\n'
            f'{human_response(db.get_all_vacancies())}\n\n'
            '---3. Получение средней зп по вакансиям---\n'
            f'{human_response([db.get_avg_salary()])}\n\n'
            '---4. Получение списка вакансий, зп которых выше среднего по вакансиям\n'
            f'{human_response(db.get_vacancies_with_higher_salary())}\n\n'
            '---5.1 Получение всех вакансий по ключевому слову(допустим "Чат")---\n'
            f'{db.get_vacancies_with_keyword('Чат')}\n\n'
            '---5.2 Получение всех вакансий по ключевому слову(допустим "Космонавт")---\n'
            f'{human_response(db.get_vacancies_with_keyword('Космонавт'))}\n\n'
        )


if __name__ == '__main__':
    main()
