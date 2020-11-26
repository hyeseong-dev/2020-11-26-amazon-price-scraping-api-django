from selenium import webdriver

DIRECTORY = 'reports'
NAME = 'iphone'
CURRENCY = '$'
MIN_PRICE = '50'
MAX_PRICE = '5000'
FILTERS = {
    'min': MIN_PRICE,
    'max': MAX_PRICE,
}
BASE_URL = 'http://www.amazon.com/'

def get_chrome_web_driver(options):
    return webdriver.Chrome('./chromedriver', chrome_options=options)

def get_web_driver_options():
    return webdriver.ChromeOptions()

def set_ignore_certificate_error(options):
    options.add_argument('--ignore-certificate-errors') # 인증서의 수락을 자동화하는 방법 

def set_browser_as_incognito(options):
    options.add_argument('--incognito') # 크롬 시크릿 모드 실행

def set_automation_as_head_less(options):
    options.add_argument('--headless') # 창 안띄우고 실행 