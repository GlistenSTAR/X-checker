import requests
from bs4 import BeautifulSoup
from dateutil import parser
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_event_name_and_date(url):
    if 'axs.' in url:
        return check_axs(url)

def make_request(url):
    headers = {
        # 'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36.',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0 Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0.'
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200 or r.status_code == 506:
        return BeautifulSoup(r.content, 'html.parser')
    print(r.status_code, url)

def check_axs(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36.'
    chrome_options.add_argument('--user-agent=%s' % user_agent)
    # chrome_options.add_argument('--headless')
    while True:
        try:
            driver = webdriver.Chrome(
                'chromedriver', chrome_options=chrome_options)
            break
        except Exception as E:
            pass

    # Check if it's working
    driver.get('https://www.google.com/')
    try:
        driver.find_element_by_id("L2AGLb").click()
        time.sleep(0.5)
    except:
        pass

    driver.find_element_by_css_selector('input[name="q"]')
    time.sleep(1)


    driver.get(url)
    time.sleep(3)
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@class="btn--single btn btn-default"]'))
        )
    except:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ackBtn"]'))
            )
        except:
            flag = False
    finally:
        flag = True
    time.sleep(2)
    if flag:
        try:
            driver.find_element_by_xpath('//*[@class="btn--single btn btn-default"]').click()
        except:
            driver.find_element_by_xpath('//button[@id="ackBtn"]').click()
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        try:
            name = soup.find('div', {'class':'event-summary-headline__event'}).text.strip()
        except:
            name = soup.find('h1', {'class':'c-marquee__headliner h-ellipsis'}).find_next('a').text.strip()
        try:
            venue = soup.find('span', {'class': 'venue'}).text.strip()
        except:
            venue = soup.find('div', {'class': 'c-event-info__venue c-event-info__venue--sticky-nav'}).text.strip()
        name = name + "-/-" + venue
        try: 
            date = soup.find('span', {'class':'event-header-date'}).text.strip()
            date = parser.parse(date.split('–')[0]).strftime('%Y-%m-%d')
        except:
            date = soup.find('span', {'class':'c-event-info__table-date'}).text.strip()
            date = parser.parse(date.split('–')[0]).strftime('%Y-%m-%d')
    # print(f'date>>>>>>>{date}')
    # time.sleep(3000)
    driver.quit()
    print("Add the Event on Google sheet.....")
    return name, date

# for url in ['https://basscanyonfestival.frontgatetickets.com/event/i8co6kruzz405we8',
#             'https://www.ticketfly.com/purchase/event/1803134/tfly',
#             'https://www.eventbrite.com/e/casablanca-the-montalban-rooftop-movies-tickets-54783106747?aff=erelexpmlt#tickets',
#             'https://www.etix.com/ticket/p/3379234/hartmut-sauers-musikkabinettduosassoninocturne-wandel-durch-die-nacht-dresdensch%C3%B6nfeld-deutschlands-zauberschloss?partner_id=430',
#             'https://www.ticketweb.com/event/lords-of-acid-with-special-brick-by-brick-tickets/9072935?REFERRAL_ID=twflash']:
#     print('for url', url)
#     print(get_event_name_and_date(url))
