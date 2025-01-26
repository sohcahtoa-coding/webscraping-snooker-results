import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service

# Constants
CHROMEDRIVER_PATH = '/usr/local/share/chromedriver'
BASE_URL = "https://www.oddsportal.com/snooker/results/"
RESULTS_FILE = 'results.csv'

# XPaths
FIRST_PLAYERS_XPATH = "//*[@id='tournamentTable']/tbody/tr[4]/td[2]/a"
TOURNAMENT_BODY = '//*[@id="tournamentTable"]/tbody'
TOURNAMENT_TABLE = '//*[@id="tournamentTable"]'
SEASONS_XPATH = '//*[@id="col-content"]/div[3]/ul/li[1]/span/strong/a'
ACCEPT_COOKIES_XPATH = '//*[@id="onetrust-accept-btn-handler"]'
ODDS_BUTTON_XPATH = '//*[@id="user-header-oddsformat-expander"]/span'
HK_ODDS_XPATH = '//*[@id="user-header-oddsformat"]/li[4]/a/span'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    os.environ['PATH'] += os.pathsep + os.path.dirname(CHROMEDRIVER_PATH)
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    driver.implicitly_wait(10)
    return driver

def accept_cookies(driver):
    try:
        driver.find_element(By.XPATH, ACCEPT_COOKIES_XPATH).click()
    except NoSuchElementException:
        pass

def set_hk_odds_format(driver):
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, ODDS_BUTTON_XPATH))).click()
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, HK_ODDS_XPATH))).click()
    except TimeoutException:
        logging.error("Failed to set HK odds format.")

def check_exists_by_xpath(driver, xpath, click=False):
    try:
        element = driver.find_element(By.XPATH, xpath)
        if element.text:
            if click:
                element.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_BODY)))
            return True
    except NoSuchElementException:
        return False
    return False

def check_next_page(driver):
    current_page = driver.current_url
    try:
        next_page = driver.find_element(By.LINK_TEXT, '»')
        if next_page.text and current_page != next_page.get_attribute('href'):
            next_page.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_TABLE)))
            return True
    except NoSuchElementException:
        return False
    return False

def collect_match_results(driver, year, tournament):
    result, odds_p1, odds_p2, namelist, pop_list = [], [], [], [], []

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, TOURNAMENT_BODY)))

    namelist_elements = driver.find_elements(By.XPATH, '//*[@id="tournamentTable"]/tbody/tr[*]/td[2]/a')
    result_elements = driver.find_elements(By.XPATH, '//*[@id="tournamentTable"]/tbody/tr[*]/td[3]')
    odds_p1_elements = driver.find_elements(By.XPATH, '//*[@id="tournamentTable"]/tbody/tr[*]/td[4]/*')
    odds_p2_elements = driver.find_elements(By.XPATH, '//*[@id="tournamentTable"]/tbody/tr[*]/td[5]/*')

    for element in namelist_elements:
        namelist.append(element.text)
    for element in result_elements:
        result.append(element.text)
    for element in odds_p1_elements:
        odds_p1.append(element.text)
    for element in odds_p2_elements:
        odds_p2.append(element.text)

    if not (len(result) == len(namelist) == len(odds_p1) == len(odds_p2)):
        logging.error("Mismatched list sizes. Cannot continue.")
        return

    for idx, (r, o1, o2) in enumerate(zip(result, odds_p1, odds_p2)):
        if "-" in o1 or "-" in o2 or r in ["w.o.", "canc.", "award."]:
            pop_list.append(idx)

    for idx in reversed(pop_list):
        namelist.pop(idx)
        result.pop(idx)
        odds_p1.pop(idx)
        odds_p2.pop(idx)

    with open(RESULTS_FILE, 'a') as file:
        for name, res, o1, o2 in zip(namelist, result, odds_p1, odds_p2):
            name_split = name.split(' - ')
            res_split = res.split(':')
            if int(res_split[0]) < int(res_split[1]):
                res_split[0], res_split[1] = res_split[1], res_split[0]
                o1, o2 = o2, o1
                name_split[0], name_split[1] = name_split[1], name_split[0]
            res = ":".join(res_split)
            file.write(f"{name_split[0]}, {name_split[1]}, {res}, {o1}, {o2}, {year}, {tournament}\n")

def main():
    start_time = time.time()
    driver = setup_driver()

    try:
        driver.get(BASE_URL)
        accept_cookies(driver)
        set_hk_odds_format(driver)

        with open(RESULTS_FILE, 'w') as file:
            file.write("Winner, Loser, Result, W-odds, L-odds, Year, Tournament\n")

        url_list = [element.get_attribute('href') for element in driver.find_elements(By.XPATH, '//*[@id="col-content"]/div[*]/table/tbody/tr[*]/td[*]/a')]
        tournament_name_list = [element.text for element in driver.find_elements(By.XPATH, '//*[@id="col-content"]/div[*]/table/tbody/tr[*]/td[*]/a')]

        for url, tournament in zip(url_list, tournament_name_list):
            driver.get(url + "#/page/1")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, SEASONS_XPATH)))

            season_elements = driver.find_elements(By.XPATH, '//*[@id="col-content"]/div[3]/ul/li[*]/span/strong/a')
            season_links = [element.get_attribute('href') for element in season_elements if "snooker" in element.get_attribute('href')]
            season_names = [element.text for element in season_elements if "snooker" in element.get_attribute('href')]

            for season_link, season_name in zip(season_links, season_names):
                driver.get(season_link)
                if check_exists_by_xpath(driver, FIRST_PLAYERS_XPATH, click=True):
                    collect_match_results(driver, season_name[:4], tournament)
                    while check_next_page(driver):
                        collect_match_results(driver, season_name[:4], tournament)

    finally:
        driver.quit()
        logging.info(f"Execution time: {time.time() - start_time} seconds")

if __name__ == "__main__":
    main()
