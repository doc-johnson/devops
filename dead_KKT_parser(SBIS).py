import requests
from datetime import datetime
import json
import re

addresses = [
'г.Пермь, ул.Мира, д.4',
'г.Пермь, ул.Мира, д.4',
'г.Пермь, ул.Крупской',
'г.Пермь, ул.Крупской',
'Ставропольский край, г.Минеральные Воды, пр-кт Карла Маркса, д.8',
'Краснодарский край, Кавказский р-н, г.Кропоткин, ул.Красная, д.2-Д',
'652870, Кемеровская обл., г.Междуреченск, Коммунистический пр-кт, д.2',
'Чувашская Республика - Чувашия, г.Новочебоксарск, ул.Винокурова, д.5',
'659315, Алтайский край, г. Бийск, ул. имени Героя Советского Союза Васильева, д. 4',
'обл.Кемеровская область - Кузбасс, г.Новокузнецк, Центральный р-н, пр-кт Металлургов, д.5',
'обл. Кемеровская область - Кузбасс, г. Новокузнецк, Заводской р-н, пр-кт Советской Армии, д. 1'
]

trash = ['пр', 'кт', 'ул', 'Санкт', 'обл', 'г', 'д']
address_arr_true_srv1 = []

terminals = requests.get('http://pw-pos.int/pos/Terminals/GetAllTerminals?key=DCnFPqBdyhj6t7jfjv').json()

def find_adress():
    tmp = []
    for address in addresses:
        a_pattern = r'\W+'
        a_address = re.split(a_pattern, address)
        for t in terminals:
            if t['kktSerialNumber'] == None:
                b_address_pars = t['salesPointName']
                b_pattern = r'\W+'
                b_address = re.split(b_pattern, b_address_pars)
                temp_arr = []
                for a in a_address:
                    if not re.findall(r"{}".format(a), str(trash)):
                        for b in b_address:
                            if re.match(r"\w\w+", a) and a == b:
                                temp_arr.append(a)
                if len(temp_arr) >= 3:
                    for te in temp_arr:
                        if re.match(r"\d+", te):
                            tmp.append(t['code'])
                            # print("\n\n\tСБИС= " + address)
                            # print("\tСОВПАДЕНИЯ= " + str(temp_arr))
                            # print("\tГДЕ ПАРСИЛ= " + str(t['salesPointName']))
    for a in tmp:
        if a not in address_arr_true_srv1 : address_arr_true_srv1.append(a)

if __name__ == '__main__':
    startTime = datetime.now()
    find_adress()
    stopTime = datetime.now() - startTime
    print(f"\n {8*'='} Spent time:" + str(stopTime))
    print(f"\n\n\n {8*'='} Matches found:\n")
    buff = 0
    for num, i in enumerate(address_arr_true_srv1):
        print(i)
        buff = num + 1
    print(f"\n\n\n {8*'='} Total: " + str(buff) + "\n\n\n\n")