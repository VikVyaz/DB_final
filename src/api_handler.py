import requests
from time import sleep


def to_get_10_employers():
    """
    Получение 10 самых свежих вакансий с HH
    """

    url = "https://api.hh.ru/vacancies"
    headers = {"User-Agent": "HH-User-Agent"}
    params = {"page": 0, "per_page": 50, "area": 113}
    company_id = []

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    vacancies = response.json()["items"]
    for vac in vacancies:
        if vac.get('employer', {}).get('id', False):
            company_id.append(vac['employer']['id'])
    response.close()

    all_vacs = []

    emp_params = [("employer_id", emp_id) for emp_id in list(set(company_id))[:10]]
    emp_params += [("per_page", 100), ('area', 113)]

    emp_response = requests.get(url, headers=headers, params=emp_params)
    emp_response.raise_for_status()
    data = emp_response.json()

    all_vacs.extend(data['items'])
    sleep(0.2)

    return all_vacs

#
# if __name__ == '__main__':
#     print(to_get_10_vacs())
