import socks
import socket
import requests 
import threading
import logging, sys, re
import smtplib
import time
import random
from stem import Signal
from stem.control import Controller

#VERSION: Pre-release

#[USER CONFIGURABLE GLOBAL VARIABLES]===========================================

SITES = [
    'url_here'
]

KEYWORDS = [
'GTX 1060',
'GTX 1070',
'GTX 1080',
'GTX1060',
'GTX1070',
'GTX1080',
'RX 480',
'RX 470',
'RX 570',
'RX 580',
'RX480',
'RX470',
'RX570',
'RX580'
]

# Use a throwaway account, don't store passwords in plaintext
EMAIL = 'senders@addre.ss'
RECIPIENT = 'recipients@addre.ss'
PW = 'senders email password'

# Number of times to refresh page using the same ip
IP_CHANGE_ROUNDS = 9

# Enable/disable info messages
INFO = True

#[NOT OF INTEREST TO USER]======================================================
_MATCHED_KEYWORDS = dict()
_CURRENT_ROUND = 0
_CACHE = set()
_TEMPSOCKET = socket.socket
_CONTROLLER = Controller.from_port(port=9051)
print('Controller assigned.')

#[BEGIN CODE]===================================================================

def info(s):
    if INFO:
        print('INFO>', s)

def init_MATCHED_KEYWORDS():
    for url in SITES:
        _MATCHED_KEYWORDS[url] = list() 

def init_tor():
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
    socket.socket = socks.socksocket
    info('Tor connected.')
    print_ip()

def print_ip():
    print('IP> ', requests.get("http://icanhazip.com").text[:-1])

def search_site_for_keyword(url):
    info('Searching ' + url[:60] + '...')
    info('For keyword(s) ' + ' '.join(KEYWORDS)[:60] + '...')
    rawhtml = requests.get(url).text
    hashedhtml = hash(rawhtml)
    existing_keywords = _MATCHED_KEYWORDS[url]

    #Ignore html if it is the same as before
    #Store hash to save space
    if hashedhtml in _CACHE: 
        info('Cached copy exists.')
        return
    else:
        info('Adding hash %d to cache.' %(hashedhtml))
        _CACHE.add(hashedhtml)

    #Return website if a keyword is detected
    for keyword in KEYWORDS:
        if keyword in rawhtml:
            if keyword not in existing_keywords: #Do not send redundant emails
                _MATCHED_KEYWORDS[url] += [keyword]
                info('%s found at ' %(keyword) + url)
                return url
        elif keyword in existing_keywords: 
            existing_keywords.remove(keyword)
            info('%s no longer in stock at ' %(keyword) + url)
            return url

def email(url):
    SERVER = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465)
    SERVER.login(EMAIL, PW)

    item = ', '.join(_MATCHED_KEYWORDS[url])
    msg = 'Stock change detected at ' + url + '\n %s currently in stock' %(item)

    SERVER.sendmail(EMAIL, RECIPIENT, msg)
    info('Mail sent to ' + RECIPIENT)

def update_ip():
    global _CURRENT_ROUND

    _CURRENT_ROUND += 1
    
    if _CURRENT_ROUND % IP_CHANGE_ROUNDS == 0:
        _CONTROLLER.authenticate()
        _CONTROLLER.signal(Signal.NEWNYM)
        print_ip()
    else:
        nextround = IP_CHANGE_ROUNDS - _CURRENT_ROUND % IP_CHANGE_ROUNDS
        info("Updating IP in %d rounds" %(nextround))

def main():
    init_tor()
    init_MATCHED_KEYWORDS()
    updated_site = None
    sleeptime = random.randrange(10, 30)

    while 1:
        for site in SITES:
            try:
                updated_site = search_site_for_keyword(site)
            except requests.exceptions.ConnectionError:
                info('Max requests, updating IP')
                update_ip()
            if updated_site:
                email(updated_site)
        sleeptime = random.randrange(20, 50)
        info('Waiting ' + str(sleeptime) + ' sec.')
        time.sleep(sleeptime)
        update_ip()

main()








