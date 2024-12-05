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
            return f'Наименование товара: {data['product_name']}\nЦена товара: {data['product_discount_price']}\n\n'
        except Exception as err:
            return None
            return f'[-] При работе с ссылкой возникла ошибка {err}.'

    def __call__(self, *args, **kwds):
        self.go_get()
        time.sleep(0.1)
        self.driver.refresh()
        time.sleep(0.1)
        return self.go_product_datas()


@app.route('/parse', methods=['POST'])
def parse_product():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    while True:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--enable-javascript")
            options.add_argument(f"user-agent={UserAgent().random}")

            with webdriver.Chrome(options=options) as driver:
                ozon_parser = Ozon(driver=driver, url=url)
                product_data = ozon_parser()
                if product_data:
                    return jsonify(product_data), 200
                else:
                    continue
        except:
            continue




