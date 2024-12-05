from flask import Flask, request, jsonify
from selenium import webdriver
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

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

@app.route('/parse', methods=['POST'])
def parse_product():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument(f"user-agent={UserAgent().random}")

    with webdriver.Chrome(options=options) as driver:
        ozon_parser = Ozon(driver=driver, url=url)
        try:
            product_data = ozon_parser.product_data_pars(url)
            return jsonify(product_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

