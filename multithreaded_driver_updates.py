import requests
import re
from multiprocessing.pool import ThreadPool as Pool
import subprocess
from datetime import datetime
import time


code = []
with open ('..\storesList.txt', 'r') as File: 
    for i in File: code.append(i.rstrip('\n'))
actualversion = requests.get('http://srv1.5555.int/updateinfo.json').json()
psexesvc_not_responding = []   # ip
psexesvc_not_responding_code = []
yesterday_offline_arr = []

def null_driver_finder():
    ip_arr = []
    for c in code:
        for t in get_terminals(1):
            if t['code'] == c and t['driverVersion'] == None: ip_arr.append(c)
    return ip_arr

# первый ночью перезапускает и обновляет соединения терминалов (ККТ), второй никогда (только после обновления сервера)
def get_terminals(num):
    terminals = requests.get(f'http://srv{num}.5555.int/pos/Terminals/GetAllTerminals?key=DCndfvdfvbpwt7v').json()
    return terminals

def check_psexesvc(ip_arr):
    for ip in ip_arr:
        with open(f'.\log\PSEXESVC_{ip}.log', 'w', encoding = "UTF-8") as log:
            if subprocess.call(['psexec.exe', f'\\\\{ip}', '-nobanner', \
                '-accepteula', '-e', '-s', 'cmd', '/c', 'cd \ && cd', '2>&1'], stdin=log, stdout=log, stderr=log) != 0:
                psexesvc_not_responding.append(ip)
                for t in get_terminals(1):
                    ip_pars = t['address']
                    re_format = r"\d+\.\d+\.\d+\.\d+"
                    find_ip = re.findall(re_format, ip_pars)
                    if find_ip[0] == ip: psexesvc_not_responding_code.append(t['code'])

def check_is_active(num, save_first_check=0):
    not_active = []
    for c in code:
        for t in get_terminals(num):
            if t['code'] == c and t['isNotActive'] == True:
                not_active.append(t['code'])
    if save_first_check == 1: 
        for i in not_active:
            yesterday_offline_arr.append(i)
    return not_active

def check_update(num):
    not_updated = []
    for c in code:
        for t in get_terminals(num):
            if t['code'] == c and t['driverVersion'] != actualversion['actualDriverVersion']:
                    not_updated.append(t['code'])
    return not_updated

def check_lost_id(num):
    lost_id = []
    for c in code:
        if not re.findall(r"{}".format(c), str(get_terminals(num))):
            lost_id.append(c)
    return lost_id

def check_arr(arr, i=0): # if i=1 check code exist in array 'code'  
    if i == 0:
        if len(arr) > 0:
            return arr
        else:
            return "None"
    else:
        uniq_arr = []
        for i in arr:
            if i in code: uniq_arr.append(i)
        if len(uniq_arr) > 0:
            return uniq_arr
        else: return "None"

def check_yesterday(array = []):
    arr = []
    if len(array) == 0:
        for i in check_update(2):
            if i not in yesterday_offline_arr and i not in psexesvc_not_responding_code:
                arr.append(i)
        return arr
    else: 
        for i in array:
            if i in check_update(2):
                arr.append(i)
        return arr

def print_arr(get_ip_or_code):
    for i in get_ip_or_code:
        print(i[0])

def get_ip_or_code(num, i=0): # i=1 if need to get code
    ip_arr = []
    ip_tmp = []
    code_tmp = []
    for c in code:
        for t in get_terminals(num):
            if t['code'] == c and t['driverVersion'] != actualversion['actualDriverVersion'] and t['isNotActive'] == False:
                ip_pars = t['address']
                re_format = r"\d+\.\d+\.\d+\.\d+"
                find_ip = re.findall(re_format, ip_pars)
                ip_tmp.append(find_ip)
                if i != 0: code_tmp.append(t['code'])
    for ip in ip_tmp:
        if ip not in ip_arr: ip_arr.append(ip)
    if i == 0: return ip_arr
    else: return code_tmp

def update_driver(ip_arr):
    for ip in ip_arr:
        print("#" + f" {ip}   # 0%")
        with open(f'.\log\{ip}.log', 'w', encoding = "UTF-8") as logfile:
            subprocess.run(['pwsh', '-executionpolicy', 'remotesigned', '-command', \
                '.\\updateDriverRemoteScript.ps1', '-ip', f'{ip}', '-Verbose'], stdout=logfile, stderr=logfile)
        print("#" + f" {ip}   ########## 100%")

def send_telegram_message(text):
    method = "sendMessage"
    token = "456456456:AAFg6pgfhbfgbfgbfgbfgGNtdfgbhso"
    url = f"https://api.telegram.org/bot{token}/{method}"
    send_text = f"{text}"
    data = {"chat_id": -5945645613, "text": send_text}
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

def timer(h):
    while True:
        if datetime.now().strftime('%H') != h:
            print(str(datetime.now().hour) + ":" + str(datetime.now().minute))
            time.sleep(60)
        else: break

if __name__ == '__main__':

    send_telegram_message(f" {3*'='} Script started..\n{16*'='}")

    timer("16") # time to download driver(with maxThreads)
    subprocess.run(['pwsh', '-noprofile', '-command', 'cd', '..', '&& .\\scripts\\findKKTip.ps1', '-downloadFoundedIPs', '-maxThreads', '40'], shell=True, check=True)
    send_telegram_message(f" {3*'='} Driver downloaded..\n{16*'='}")
    timer("23") # time to start update
    subprocess.run(['pwsh', '-noprofile', '-command', 'git', 'stash', '&& git', 'pull'], shell=True, check=True)

    print("Lost id in srv1:")
    print(check_lost_id(1))
    print("Lost id in srv2:")
    print(check_lost_id(2))
    print("Update queue:")
    print_arr(get_ip_or_code(1))
    print("\nOffline in srv1:")
    for n in check_is_active(1,1): print(n)
    print("\nOffline in srv2:")
    for n in check_is_active(2): print(n)
    print("\nPSEXESVC not responding:")
    InitPool(check_psexesvc, get_ip_or_code(1), 20).start_pool()
    print(psexesvc_not_responding)
    send_telegram_message(f"\t {3*'='} Check before update:\
        \nOffline:\n{check_arr('; '.join(check_is_active(1)))}\n\
        \nPSEXESVC not responding:\n{check_arr('; '.join(psexesvc_not_responding_code))}\n\
        \nLost id in srv1:\n{check_arr('; '.join(check_lost_id(1)))}\n\
        \nLost id in srv2:\n{check_arr('; '.join(check_lost_id(2)))}\n\
        \n\nUpdate is started . . . \n{16*'='}\n")
    print(f"\n======== Start update:")
    startTime = datetime.now()
    InitPool(update_driver, get_ip_or_code(1), 10).start_pool()
    print ("\n\n======== Spent time: ", datetime.now() - startTime)

    print("\n\n\n\n======== 1th check of 2:         . . . sleep 15m . . .")
    time.sleep(900)
    print("Not updated:")
    print_arr(get_ip_or_code(1))
    print("\nOffline:")
    for n in check_is_active(1): print(n)
    send_telegram_message(f" {6*'='} 1th check of 2:\
        \nNot updated:\n{'; '.join(check_arr(get_ip_or_code(1,1),1))}; {check_arr('; '.join(check_is_active(1)))}\n\
        \nOffline:\n{check_arr('; '.join(check_is_active(1)))}\n\
        \nRestart update & sleep for 10min . . .\n{16*'='}\n")
    print("\n======== Restart update:")
    InitPool(update_driver, get_ip_or_code(1), 10).start_pool()

    print("\n\n\n\n======== 2th check of 2:         . . . sleep 10m . . .")
    time.sleep(600)
    print("Not updated:")
    print_arr(get_ip_or_code(1))
    print("\nOffline:")
    for n in check_is_active(1): print(n)
    send_telegram_message(f" {6*'='} 2th check of 2:\
        \nNot updated:\n{'; '.join(check_arr(get_ip_or_code(1,1),1))}; {check_arr('; '.join(check_is_active(1)))}\n\
        \nOffline:\n{check_arr('; '.join(check_is_active(1)))}\n\
        \nLost id in srv1:\n{check_arr('; '.join(check_lost_id(1)))}\n\
        \nLost id in srv2:\n{check_arr('; '.join(check_lost_id(2)))}\n\
        \n\n  sleep 11h . . .\n{16*'='}")
    print("\n\n======== sleep 11h . . .")

    print("\n======== Report")
    time.sleep(36000)
    print("Not updated:")
    print_arr(get_ip_or_code(1))
    print("\nOffline:")
    for n in check_is_active(1): print(n)
    send_telegram_message(f" {6*'='} Report:\
        \nAll code:\n{'; '.join(code)}\n\
        \nNot updated(all):\n{'; '.join(check_update(2))}\n\
        \nYesterday offline:\n{check_arr('; '.join(check_yesterday(yesterday_offline_arr)))}\n\
        \nYesterday psexec trouble:\n{check_arr('; '.join(check_yesterday(psexesvc_not_responding_code)))}\n\
        \nUnknow reason:\n{check_arr('; '.join(check_yesterday()))}\n\
        \n\n        Done!\n{16*'='}")
    print("\n\n======== Done!")

# "statusMessage":"Принтер ККТ найден и подключён."
