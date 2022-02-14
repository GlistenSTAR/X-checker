import random
import time
import zipfile

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def check_website(url, proxies, row, log=None, headless=False):
    print(url)
    if '.axs.' in url:
        return Axs(url, proxies, row, log, headless)


class Scraper(object):

    def __init__(self, url, proxies, rows, log=None, headless=False):
        self.log = log
        self.log_text('Checking URL: {} Rows: {}'.format(url, rows))
        with open(proxies, 'r') as f:
            self.proxies = f.read().split('\n')
        self.url = url
        self.rows = [int(x) for x in rows.split(',')]
        self.driver = self.open_driver(headless=headless)

    def wait_for_element(self, driver, element, type=By.ID):
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((type, element))
            )
        except:
            return False
        finally:
            return True

    def log_text(self, txt):
        if self.log:
            self.log.Clear()
            self.log.SetValue(txt+'...')

    def open_driver(self, use_proxy=True,
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36.',
                    headless=False):
        random_proxy = random.choice(self.proxies)
        auth, ip_port = random_proxy.split('@')
        user, pwd = auth.split(':')
        ip, port = ip_port.split(':')
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (ip, port, user, pwd)
        chrome_options = webdriver.ChromeOptions()
        if headless:
            pass
        #    chrome_options.add_argument('--headless')
        if use_proxy:
            pluginfile = 'proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
            time.sleep(1)
        # install ticket tool
        chrome_options.add_extension("TBL_AXS_Extension.zip")

        if user_agent:
            chrome_options.add_argument('--user-agent=%s' % user_agent)
        try:
            driver = webdriver.Chrome(
                'chromedriver', chrome_options=chrome_options)
        except Exception as E:
            print('Error ', E)
            return self.open_driver()

        # Check if it's working
        driver.get('https://www.google.com/')
        try:
            driver.find_element_by_id("L2AGLb").click()
            time.sleep(0.5)
        except:
            pass

        try:
            driver.find_element_by_css_selector('input[name="q"]')
        except:
            driver.quit()
            return self.open_driver()
        time.sleep(3000)
        return driver

        # if headless:
        #     chrome_options.add_argument('--headless')
        # driver = webdriver.Chrome(chrome_options=chrome_options)
        # return driver


class Axs(Scraper):

    def check_status_new_style(self, table, ret=0):

        out = []
        table = BeautifulSoup(table.get_attribute('outerHTML'), 'html.parser')
        items = table.find_all(
            'div', {'class': 'tiered-ticket-display-content-root'})
        for row in self.rows:
            item = items[row-1]
            name = item.find('h3').text.strip()
            status_element = item.find(
                'div', {'class': 'eds-ticket-card-content'}).contents[1]
           # print(status_element.prettify())
            select = status_element.find('select')
            if select:
                status = 'Available'
            else:
                status = status_element.text.strip()
            out.append({'status': status,
                        'row': row,
                        'name': name})
        return out

    def check_status(self, ret=0):

        out = []
        if '?' in self.url:
            self.url = self.url[:self.url.find('?')]
        if '#tickets' not in self.url:
            self.url += "#tickets"
        try:
            self.driver.get(self.url)

        except:
            self.driver.quit()
            self.driver = self.open_driver(headless=False)
            return self.check_status(ret)
        try:

            table = self.driver.find_element_by_class_name(
                'js-ticket-list-container')
            print(
                "*************************************preview one************************************")

        except:
            # TODO check if new style
            print(
                "**************************************new one************************************")
            _id = self.driver.find_element_by_tag_name(
                'body').get_attribute('data-event-id')

            if _id is None:
                return out
            xpath = '//*[@id="eventbrite-widget-modal-{}"]'.format(_id)

            self.driver.switch_to.frame(
                self.driver.find_element_by_xpath(xpath))
            try:
                print(":::::::::::::::::::::::::::::::::::::{}::::::::::::::::", xpath)
                table = self.driver.find_element_by_tag_name('dialog')

                return self.check_status_new_style(table)
            except IndexError:
                for row in self.rows:
                    out.append({'status': 'Sold out online',
                                'row': row,
                                'name': 'row {}'.format(row)})
                return out

            except Exception as e:
                print(e, 'cannot find table')
                for row in self.rows:
                    out.append({'status': 'Sold out online',
                                'row': row,
                                'name': 'row {}'.format(row)})
                return out

            if ret == 10:
                self.driver.quit()
                return out
            ret += 1
            time.sleep(1)
            self.driver.quit()
            self.driver = self.open_driver(headless=True)
            return self.check_status(ret)
        soup = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
        items = soup.find_all('li', {'class': 'js-ticket-item'})

        for row in self.rows:
            try:
                item = items[row - 1]
            except IndexError:
                continue
            name = item.find('h2', {'class': 'ticket-box__name'}).text.strip()
            status_element = item.find('span', {'class': 'ticket-box-status'})
            status = status_element.text.strip() if status_element else "Available"
            out.append({'status': status,
                        'row': row,
                        'name': name})
        #self.tickets_check_times[url['URL']] = {'last_checked': time.time(), 'interval': url['INTERVAL']}
        self.driver.quit()
        return out
