import requests
import json
import re
import os
import time
from multiprocessing.pool import ThreadPool as Pool
import subprocess
from datetime import datetime

code = [
'78-71842',
'78-76692',
'50-71622',
'77-76652',
'53-74412',
'78-71892',
'29-71138'
]

actualversion = requests.get('http://pw-pos.567856875678.int/updateinfo.json').json()
psexesvc_not_responding = []

# для поиска терминалов с версией драйвера null
def null_driver_finder():
    ip_arr = []
    for c in code:
        for t in get_terminals(1):
            if t['code'] == c and t['driverVersion'] == None: ip_arr.append(c)
    return ip_arr

# после 2 часов ночи srv2
def get_terminals(num):
    terminals = requests.get(f'http://pw-pos.{num}.567856875678.int/pos/Terminals/GetAllTerminals?key=DCnF4567865785678pwt7v').json()
    return terminals

def check_psexesvc(ip_arr):
    for ip in ip_arr:
        with open(f'.\log\PSEXESVC_{ip}.log', 'w', encoding = "UTF-8") as log:
            if subprocess.call(['psexec.exe', f'\\\\{ip}', '-nobanner', \
                '-accepteula', '-e', '-s', 'cmd', '/c', 'cd \ && cd', '2>&1'], stdin=log, stdout=log, stderr=log) != 0:
                psexesvc_not_responding.append(ip)

def check_is_active(num):
    not_active = []
    for c in code:
        for t in get_terminals(num):
            if t['code'] == c and t['isNotActive'] == True:
                not_active.append(t['code'])
    return not_active

def check_lost_id(num):
    lost_id = []
    for c in code:
        if not re.findall(r"{}".format(c), str(get_terminals(num))):
            lost_id.append(c)
    return lost_id

def check_arr(arr):
    if len(arr) > 0:
        return arr
    else:
        return "None"

def print_arr(get_ip):
    for ip in get_ip:
        print(ip[0])

def get_ip(num):
    ip_arr = []
    ip_tmp = []
    for c in code:
        for t in get_terminals(num):
            if t['code'] == c and t['driverVersion'] != actualversion['actualDriverVersion'] and t['isNotActive'] == False:
                ip_pars = t['address']
                re_format = r"\d+\.\d+\.\d+\.\d+"
                find_ip = re.findall(re_format, ip_pars)
                ip_tmp.append(find_ip)

    for ip in ip_tmp:
        if ip not in ip_arr: ip_arr.append(ip)
    return ip_arr

def update_driver(ip_arr):
    for ip in ip_arr:
        print("#" + f" {ip}   # 0%")
        with open(f'.\log\{ip}.log', 'w', encoding = "UTF-8") as logfile:
            subprocess.run(['powershell', '-executionpolicy', 'remotesigned', '-command', \
                '.\\updateDriverRemoteScript.ps1', '-ip', f'{ip}', '-Verbose'], stdout=logfile, stderr=logfile)
        print("#" + f" {ip}   ########## 100%")

def send_telegram_message(text):
    method = "sendMessage"
    token = "1715677257:AAFg6pMb9GoA67g567h567jh0QYGNtCIFB7tso"
    url = f"https://api.telegram.org/bot{token}/{method}"
    send_text = f"{text}"
    data = {"chat_id": -56786784313, "text": send_text}
    requests.post(url, data=data)

class InitPool():
    def __init__(self, func, arr, p):
        self.func = func
        self.arr = arr
        self.p = p

    def start_pool(self):
        pool = Pool(self.p)
        pool.map(self.func, self.arr)
        pool.close()
        pool.join()

if __name__ == '__main__':
    print("Lost id in srv1:")
    print(check_lost_id(1))
    print("Lost id in srv2:")
    print(check_lost_id(2))
    print("Update queue:")
    print_arr(get_ip(1))
    print("\nOffline in srv1:")
    for n in check_is_active(1): print(n)
    print("\nOffline in srv2:")
    for n in check_is_active(2): print(n)
    print("\nPSEXESVC not responding:")
    InitPool(check_psexesvc, get_ip(1), 20).start_pool()
    print(psexesvc_not_responding)
    send_telegram_message(f"\t {3*'='} Check before update:\
        \nOffline:\n{check_arr(', '.join(check_is_active(1)))}\n\nPSEXESVC not responding:\
        \n{check_arr(', '.join(psexesvc_not_responding))}\
        \n\nUpdate is started . . . \n {16*'='}")

    print(f"\n======== Start update:")
    startTime = datetime.now()
    InitPool(update_driver, get_ip(1), 10).start_pool()
    print ("\n\n======== Spent time: ", datetime.now() - startTime)

    print("\n\n\n\n======== 1th check of 2:         . . . sleep 10m . . .")
    time.sleep(600)
    print("Not updated:")
    print_arr(get_ip(1))
    print("\nOffline:")
    for n in check_is_active(1): print(n)
    send_telegram_message(f" {6*'='} 1th check of 2:\
        \nNot updated:\n{check_arr(', '.join(str(v[0]) for v in get_ip(1)))}\n\nOffline:\n{check_arr(', '.join(check_is_active(1)))}\n\nLost id in srv*:\
        \n{check_arr(', '.join(check_lost_id(1)))}\n\nRestart update & sleep for 10min . . .\n {16*'='}")
    print("\n======== Restart update:")
    InitPool(update_driver, get_ip(1), 10).start_pool()

    print("\n\n======== 2th check of 2:         . . . sleep 10m . . .")
    time.sleep(600)
    print("Not updated:")
    print_arr(get_ip(1))
    print("\nOffline:")
    for n in check_is_active(1): print(n)
    send_telegram_message(f" {6*'='} 2th check of 2:\
        \nNot updated:\n{check_arr(', '.join(str(v[0]) for v in get_ip(1)))}\n\nOffline:\n{check_arr(', '.join(check_is_active(1)))}\
        \n\nLost id in srv*:\n{check_arr(', '.join(check_lost_id(1)))}\n\nSleep for 8h . . .\n {16*'='}")

    # print("\n======== Last check:         . . . sleep 8h . . .")
    # time.sleep(28800)
    # print("Not updated:")
    # print_arr(get_ip(2))
    # print("\nOffline:")
    # for n in check_is_active(2): print(n)
    # send_telegram_message(f" {6*'='} Last check:\
    #     \nNot updated:\n{check_arr(', '.join(str(v[0]) for v in get_ip(2)))}\n\nOffline:\n{check_arr(', '.join(check_is_active(2)))}\
    #     \n\nLost id in srv*:\n{check_arr(', '.join(check_lost_id(2)))}\n\nDone!\n {16*'='}")

    # print(null_driver_finder())
