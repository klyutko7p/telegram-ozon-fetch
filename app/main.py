import json
from flask import Flask, request, jsonify
from selenium import webdriver
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time

app = Flask(__name__)


class Ozon:
    def __init__(self, url: str, driver: webdriver, timing=2):
        self.driver = driver
        self.url = url
        self.timing = timing

    def del_to_not_dig(self, s: str):
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

    def go_get(self) -> None:
        self.driver.get(self.url)
        time.sleep(self.timing)

    def product_data_pars(self, url: str):
        self.driver.switch_to.new_window('tab')
        self.driver.get(url)
        page = str(self.driver.page_source)
        soup = BeautifulSoup(page, 'lxml')

        product_name = soup.find('div', attrs={'data-widget': 'webProductHeading'}).find('h1').text.strip()
        try:
            list_tag_prices = soup.find('span', string='без Ozon Карты').parent.parent.find('div').find_all('span')
            product_discount_price = list_tag_prices[0].text
        except:
            product_discount_price = None

        product_data = {
            'product_name': product_name,
            'product_discount_price': self.del_to_not_dig(product_discount_price),
        }

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return product_data

    def go_product_datas(self) -> None:
        try:
            data: dict = self.product_data_pars(url=self.url)
            self.flag = True
            return {
                "product_name": data['product_name'],
                "product_discount_price": data['product_discount_price']
            }
        except Exception as err:
            return None
            return f'[-] При работе с ссылкой возникла ошибка {err}.'

    def __call__(self, *args, **kwds):
        self.go_get()
        time.sleep(0.1)
        self.driver.refresh()
        time.sleep(0.1)
        return self.go_product_datas()


# функция записи юзерагента в лог
def write_ua_logs(ua: str) -> None:
    dct: dict = {}
    try:
        with open("log_ua.json", "x", encoding='utf-8') as file:
            json.dump(dct, file)
    except FileExistsError:
        pass

    with open("log_ua.json", "r") as file:
        dct = json.load(file)

    with open("log_ua.json", "w") as file:
        dct[ua] = dct.get(ua, 0) + 1
        json.dump(dct, file, indent=4, ensure_ascii=False)


user_agents = {
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0": 9,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0": 3,
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 DuckDuckGo/7 Safari/605.1.15": 1,
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15": 2,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0 Trailer/92.3.3357.27": 1,
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15": 1,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0 Unique/97.7.7286.70": 2,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36": 3,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0 Trailer/93.3.3695.30": 1,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Config/92.2.2788.20": 1,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0 GLS/100.10.9415.94": 1,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0 Config/91.2.2121.13": 1
}

def get_best_user_agent(user_agents):
    sorted_ua = sorted(user_agents.items(), key=lambda item: item[1], reverse=True)
    return sorted_ua if sorted_ua else None

@app.route('/parse', methods=['POST'])
def parse_product():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    num_ua = -1
    while True:
        num_ua += 1
        try:
            ua = get_best_user_agent(user_agents)[num_ua][0]
            if not ua:
                print("Нет доступных юзер-агентов.")
                break
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--enable-javascript")
            options.add_argument(f"user-agent={ua}")

            with webdriver.Chrome(options=options) as driver:
                ozon_parser = Ozon(driver=driver, url=url)
                product_data = ozon_parser()
                if product_data:
                    driver.close()
                    return jsonify(product_data), 200
                else:
                    driver.close()
                    continue
        except:
            continue