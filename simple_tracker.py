import time 
from selenium.webdriver.common.keys import Keys
from amazon_config import (
    get_web_driver_options,
    get_chrome_web_driver,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    set_automation_as_head_less,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)

from selenium.common.exceptions import NoSuchElementException
import json
from datetime import datetime

class GenerateReport:
    def __init__(self, file_name, filters, base_link, currency, data):
        self.data = data
        self.file_name = file_name  # 파일명
        self.filters = filters      # 필터
        self.base_link = base_link  # base_link
        self.currency = currency    # 화폐
        report = {                              # report 딕셔너리 객체를 만들어줌
            'title': self.file_name,
            'date': self.get_now(),             # get_now 메서드를 이용해 현재 시간을 date의 value값으로 저장
            'best_item': self.get_best_item(),  # 가장 저렴한 가격을 리턴하는데, 기존 data파라미터로 받은 값을 가지고 best item으로  key-value값을 지정함.
            'currency': self.currency,
            'filters': self.filters,
            'base_link': self.base_link,
            'products': self.data
        }
        print("Creating report...")
        with open(f'{DIRECTORY}/{file_name}.json', 'w') as f:  # with open() as 를 사용해서 디렉토리 경로와 파일 이름을 지정하고 'w' 옵션으로 작성함
            json.dump(report, f)                               # f객체로 작성한 파일에 report 파라미터로 받은 값을 dump 메소드를 이용해서 json으로 변환함     
        print("Done...")    # 마침내 종료!!!!!!!!!

    @staticmethod       # 별도의 입력값과 외부 인스턴스를 통한 데이터 변환 없이 datetime 패키지를 이용해 시간에 대한 값만 찍어서 리턴함
    def get_now():
        now = datetime.now()
        return now.strftime("%d/%m/%Y %H:%M:%S")    # strftime() 메서드를 통해서 포맷을 지정함(일,월,년 시간,분,초)

    def get_best_item(self):
        try:
            return sorted(self.data, key=lambda k: k['price'])[0]   # data 딕셔너리에서 price 키를 기준으로 오름차순으로 정렬된 0번째 인덱스를 bestitem으로 리턴함
        except Exception as e:
            print(e)
            print("Problem with sorting items")
            return None

class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):               # AmazonAPI 인스턴스 생성시 호출되는 메서드, 그 안에 정의되고 호출될 메서드들
        self.base_url = base_url                                                # 아마존 url
        self.search_term = search_term                                          # 검색 키워드
        options = get_web_driver_options()                                      # 옵션 객체 생성
        set_ignore_certificate_error(options)                                   # certificate error 발생 무시
        set_browser_as_incognito(options)                                       # 크롬 시크릿 모드 실행
        self.driver = get_chrome_web_driver(options)                            # 웹 드라이버 인스턴스 생성
        self.currency = currency                                                # 화페 속성 
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00" # url에서 가격 필터 파라미터 값 지정 

    def run(self):
        print("Starting Script...")
        print(f"Looking for {self.search_term} products...")
        links = self.get_products_links()                                       # 제품 링크 목록에 대한 메서드를 돌려서 return값을 리스트 변수를 생성함
        if not links:                                                           # 링크가 없는 경우 stop                                                 
            print("Stopped script.")
            return
        print(f"Got {len(links)} links to products...")                         # 링크내 몇개가 있는지 알려줌
        print("Getting info about products...")
        products = self.get_products_info(links)
        print(f"Got info about {len(products)} products...")                    # 리스트 안에 몇개의 딕셔너리로 정리된 값이 있는지 알려줌
        self.driver.quit()                                                      # 브라우저 수행을 종료함
        return products
    
    def get_products_links(self):
        self.driver.get(self.base_url)                                                  # 지정한 url값을 갖고 웹페이지를 띄움
        element = self.driver.find_element_by_xpath('//*[@id="twotabsearchtextbox"]')   # 검색창에 객체를 생성 
        element.send_keys(self.search_term)                                             # 검색창에 send_keys 메소드로 키워드를 입력함
        element.send_keys(Keys.ENTER)                                                   # 엔터키 누름
        time.sleep(2)                                                                   # 페이지가 뜰때까지 2초기다림
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')                # 기존url과 가격 filter를 파라미터로 넘겨줌    
        print(f"Our url: {self.driver.current_url}")
        time.sleep(2)                                                                   # 2초 기다림
        result_list = self.driver.find_elements_by_class_name('s-result-list')          # 제품 리스트 페이지에서 class 네임을 갖고 있는 data를 넘겨줌(참고! ~elements~ 복수개라 전체를 갖고옴) 
        links = []                                                                      # 각 제품을 url 링크를 담을 empty 리스 변수 생성
        try:
            results = result_list[0].find_elements_by_xpath(                            # xpath를 이용해서 링크 데이터를 정제함
                "//div/span/div/div/div[2]/div[2]/div/div[1]/div/div/div[1]/h2/a")
            links = [link.get_attribute('href') for link in results]                    # 컴프리헨션을 이용해서 하나씩 링크를 리스트 변수에 저장
            return links                                                                
        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links

    def get_products_info(self, links):                  # 각 제품에 대한 정보를 processing할 메서드
        asins = self.get_asins(links)                    # 아마존 asin, 일명 아마존 식별 번호에 대한 메서드를 돌림(파라미터 값은 이전에 받은 links로 입력함) 184번 줄의 메서드 호출함
        products = []
        for asin in asins:                              
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)                # 리스트에 딕셔너리 값을 차례대로 append함
        return products                                 # 리스트안의 각 제품에 대한 딕셔너리로 정리된 값을 반환함 

    def get_asins(self, links):
        return [self.get_asin(link) for link in links] # static method인 get_asin을(187라인) 통해서 컴프리핸션을 이용해 값을 리턴함

    def get_single_product_info(self, asin):           # asin 파라미터를 입력 받고 제품 한개씩 processiong함 
            print(f"Product ID: {asin} - getting data...")
            product_short_url = self.shorten_url(asin)  
            self.driver.get(f'{product_short_url}?language=en_KO') # 언어별로 해당 제품의 웹페이지를 다시 로드함
            time.sleep(2)                                          # 2초 wait
            title = self.get_title()                               # 제품 타이틀을 리턴받아 저장
            seller = self.get_seller()                             # 제품 판매자에 대한 값을 리턴받아 저장함
            price = self.get_price()                               # 제품 가격에 대한 값을 리턴받아 저장함
            if title and seller and price:                         # 제목, 판매자, 가격에 대한 값이 온전히 있는 경우, product_info라는 딕셔너리로 asin~price까지 key-value pair값으로 정리함
                product_info = {
                    'asin': asin,
                    'url': product_short_url,
                    'title': title,
                    'seller': seller,
                    'price': price
                }
                return product_info                                 # 딕셔너리로 리턴함 
            return None                                             # 제품명, 판매자, 가격 그중 하나라도 값이 없는 경우 None으로 리턴함 

    def get_title(self):                                                # 싱글 제품에 대한 제목을 가져옴
        try:            
            return self.driver.find_element_by_id('productTitle').text  # find_element_by_id 메소드를 이용해 해당 id에 위치한 text를(제목)가져옴
        except Exception as e:                                          
            print(e)
            print(f"Can't get title of a product - {self.driver.current_url}") # 해당 url에 id가 없음을 터미널창에 출력함
            return None
        

    def get_seller(self):
        try:
            return self.driver.find_element_by_id('bylineInfo').text   # find_element_by_id 메소드를 이용해 해당 id에 위치한 text를(판매자)가져옴
        except Exception as e:
            print(e)
            print(f"Can't get seller of a product - {self.driver.current_url}") # 해당 url에 id가 없음을 터미널창에 출력함
            return None

    def get_price(self): # 가격의 경우, 특정 품목마다 id값이 다르므로 그에 맞게 경우의 수를 고려하여 로직을 구성함
        price = None
        try:
            price = self.driver.find_element_by_id('priceblock_ourprice').text
            price = self.convert_price(price)
        except NoSuchElementException: # NoSuchElementException 에러가 발생한 경우, 위 id값이 없는 경우.
            try:
                availability = self.driver.find_element_by_id('availability').text  # availability의 id 값인
                if 'Available' in availability:
                    price = self.driver.find_element_by_class_name('olp-padding-right').text
                    price = price[price.find(self.currency):] #화폐 기호를 기준으로 가격(str) 값을 가져옴.
                    price = self.convert_price(price)               
            except Exception as e:
                print(e)
                print(f"Can't get price of a product - {self.driver.current_url}") # 위 try문을 통해 의도한 로직을 수행 하지 못할 경우 제품 가격 정보를 가져 올 수 없음을 터미널창에 출력함
                return None                                                        # None으로 반환함
        except Exception as e:         # Exception 에러인 경우 로직을 처리함
            print(e)
            print(f"Can't get price of a product - {self.driver.current_url}")
            return None
        return price                   # 오류 없이 처리된 경우 str 값을 반환해줌 

    def convert_price(self, price):
        price = price.split(self.currency)[1]
        try:
            price = price.split("\n")[0] + "." + price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0] + price.split(",")[1]
        except:
            Exception()
        return float(price)


    def shorten_url(self, asin):            # 'dp/' 와 asin을 조합하여 싱글 제품에 대한 url을 만들어 return함
        return self.base_url + 'dp/' + asin


    @staticmethod   # 인스턴스의 상태를 변경 시키지 않음.
    def get_asin(product_link):
        return product_link[product_link.find('/dp/') + 4:product_link.find('/ref')]



if __name__ == '__main__':
    am = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY) # AmazonAPI의 인스턴스인 am를 생성함 
    data = am.run()                                   # run() 메서드로 로직을 돌리고 그 결과를 data 변수에 저장
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data) # json 파일로 저장할 GenerateReport() 클래스를 호출하여 실행함