import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from flask import Flask, request, jsonify
import time
import json
import os

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-javascript")


def init_webdriver():
    driver = webdriver.Chrome(options=options)
    stealth(driver, platform="Win32")
    return driver


print("Браузер успешно открыт")

app = Flask(__name__)

driver = init_webdriver()


def del_to_not_dig(s: str):
    for dig in s:
        if not dig.isdigit():
            s = s.replace(dig, '')
    n = 1
    for d in range(len(s))[::-1]:
        if n == 3:
            s = s[:d] + ' ' + s[d:]
            n = 0
        else:
            n += 1
    return s + ' ₽'

@app.route('/parse', methods=['POST'])
def handle_post():
    url = request.json['url']
    print(url)
    driver.get(url)
    time.sleep(5)
    print(driver.page_source)
    page = str(driver.page_source)
    soup = BeautifulSoup(page, 'lxml')

    product_name = soup.find('div', attrs={'data-widget': 'webProductHeading'}).find('h1').text.strip()
    try:
        list_tag_prices = soup.find('span', string='без Ozon Карты').parent.parent.find('div').find_all('span')
        product_discount_price = list_tag_prices[0].text
    except:
        product_discount_price = None

    product_data = {
        'product_name': product_name,
        'product_discount_price': del_to_not_dig(product_discount_price),
    }

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    # return product_data

    # jsonData = driver.find_element(By.TAG_NAME, "body").text

    response_data = {'status': 'success', 'message': f'{product_data}'}
    return jsonify(response_data)