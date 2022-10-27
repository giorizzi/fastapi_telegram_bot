import time
from datetime import date
from logging import getLogger, INFO
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlencode

logger = getLogger(__name__)
logger.setLevel(INFO)


def get_availability(query: str, start_date: date, end_date: date):
    driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub', options=webdriver.ChromeOptions())
    try:
        query_kwargs = {'q': query, 'sort': 'available', 'checkin': start_date.strftime('%m/%d/%Y'),
                        'checkout': end_date.strftime('%m/%d/%Y')}
        url = f'https://www.recreation.gov/search?' + urlencode(query_kwargs)

        driver.set_window_size(700, 1000)
        driver.implicitly_wait(10)
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'rec-flex-card-image-wrap'))
        )

        driver.find_element(By.XPATH, "//button[@aria-label='Show filters']").click()
        filter_ids = [
            'camping',
            'include_unavailable',
            'include_notreservable',
            'include_partially_available',
            'campsite-type-standard',
            'campsite-type-tent-only',
            'campsite-type-walkto',
        ]
        wait = WebDriverWait(driver, 10)
        for id in filter_ids:
            element = driver.find_element(By.XPATH, f"//input[@id='{id}']")
            element.location_once_scrolled_into_view
            element.click()

        driver.find_element(By.XPATH, "//button[@id='testhook-apply']").click()
        time.sleep(3)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'rec-flex-card-wrap'))
        )
        time.sleep(3)
        sortby_select = Select(driver.find_element(By.XPATH, "//select[@id='search-sort-dropdown']"))
        sortby_select.select_by_value('available')

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'rec-flex-card-wrap'))
        )

        results = driver.find_element(By.CLASS_NAME, 'search-outer-wrap').find_elements(By.XPATH, "*")

        clean_results: List[Dict[str, str]] = []
        for result in results:
            if result.find_element(By.TAG_NAME, 'a').find_elements(By.XPATH, "./div")[1].text == 'AVAILABLE':
                split_text = result.find_element(By.TAG_NAME, 'h2').find_element(By.XPATH, './..').text.split('\n')
                href = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                result_summary = {}
                result_summary['name'] = split_text[0]
                result_summary['location'] = split_text[1]
                result_summary['href'] = href
                result_summary['info'] = split_text[2]
                result_summary['distance'] = next((x for x in split_text if 'mile' in x), None)
                if result_summary['distance']:
                    try:
                        result_summary['distance_miles'] = int(result_summary['distance'].split(' ')[0])
                    except:
                        pass
                clean_results.append(result_summary)
        return clean_results

        # result.click()
        # driver.switch_to.window(driver.window_handles[1])
        # driver.find_element(By.XPATH, "//table[@id='availability-table']")

    finally:
        driver.quit()


# print(get_availability('camp 4 yosemite', date(2022,12,10), date(2022,12,15)))