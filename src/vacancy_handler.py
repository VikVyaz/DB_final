class VacHandler:
    """
    Класс работы с вакансиями
    """

    @staticmethod
    def to_give_emp_params(vac_data: dict):

        employer_id = int(vac_data.get('id', 'уже проверено в api_handler.py'))
        employer_name = vac_data.get('name', None)
        comp_url = vac_data.get('alternate_url', None)
        vacancies_url = vac_data.get('vacancies_url', None)
        if vac_data.get('employer_rating', False):
            rating = float(vac_data.get('employer_rating', {}).get('total_rating', 'обработано'))
        else:
            rating = None
        employer_trusted = vac_data.get('trusted', None)

        return [employer_id, employer_name, comp_url, vacancies_url, rating, employer_trusted]

    @staticmethod
    def to_give_vac_params(vac_data: dict, emp_data: dict):

        vacancy_id = int(vac_data.get('id', 'обработано'))
        vacancy_name = vac_data.get('name', None)
        city = vac_data.get('area', {}).get('name', None)
        vacancy_url = vac_data.get('alternate_url', None)
        schedule = vac_data.get('schedule', {}).get('name', None)

        if vac_data.get('salary'):
            vac_salary_from = vac_data['salary'].get('from', None)
            vac_salary_to = vac_data['salary'].get('to', None)
            vac_currency = vac_data['salary'].get('currency', None)
            if vac_salary_from and vac_salary_to:
                vac_avg_salary = (vac_salary_from + vac_salary_to) / 2
            elif vac_salary_from:
                vac_avg_salary = vac_salary_from
            elif vac_salary_to:
                vac_avg_salary = vac_salary_to
            else:
                vac_avg_salary = None
        else:
            vac_salary_from = None
            vac_salary_to = None
            vac_currency = None
            vac_avg_salary = None

        employer_id = emp_data[0]

        return [vacancy_id, vacancy_name, city, vacancy_url, schedule,
                vac_salary_from, vac_salary_to, vac_currency, vac_avg_salary, employer_id]
