import datetime
import ssl
import socket
import json
import datefinder
import requests
import sys

def ssl_parsing(host):
 try:
     hostname = host
     port = '443'
     context = ssl.create_default_context()
     with socket.create_connection((hostname, port)) as sock:
         with context.wrap_socket(sock, server_hostname=hostname) as srv_sock:
             matches = datefinder.find_dates(json.loads(json.dumps(srv_sock.getpeercert()))['notAfter'])
             m = None
             for match in matches:
                 m = match
             cert_exp = (m - datetime.datetime.now()).days
             if cert_exp < alarm_days:
                 print("ALARM","!!!", cert_exp, "!!!", hostname)
                 array_exp.append(str(hostname) + ": " + str(cert_exp))
             else:
                 print("OK","(", cert_exp,")", hostname)
 except Exception:
     print("ALARM " + hostname + str(sys.exc_info()[1]))
     array_err.append(str(hostname) + ": " + str(sys.exc_info()[1]))

def check_array_exp(exp):
 if len(exp) > 0:
     return exp
 else:
     return "OK"

def check_array_err(err):
 if len(err) > 0:
     return err
 else:
     return "OK"

def get_consul_sites():
    url = 'http://consul.monitoring/urls/list.txt?raw'
    headers = {'Token': '0'}
    array_sites = requests.get(url, headers=headers).text
    spl = array_sites.splitlines()
    return spl

def send_telegram_message():
    method = "sendMessage"
    token = "0"
    url = f"https://api.telegram.org/bot{token}/{method}"
    send_text = "SSL_EXPIRED_VERIFY:\n{}\n\n----------------------" \
                "\n\nSSL_ERROR_VERIFY:\n{}".format(check_array_exp('\n'.join(array_exp)), check_array_err('\n'.join(array_err)))
    data = {"chat_id": -0, "text": send_text}
    requests.post(url, data=data)

def main():
    for sites in get_consul_sites():
        ssl_parsing(sites)

    send_telegram_message()

alarm_days = 60
array_exp = []
array_err = []

if __name__ == "__main__":
    main()
