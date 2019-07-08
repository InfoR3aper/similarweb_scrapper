import csv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib
from captcha2upload import CaptchaUpload
import time


# setting the firefox driver
def init_driver():
    driver = webdriver.Firefox(executable_path=r'./geckodriver')
    driver.implicitly_wait(5)
    return driver


# solving the captcha (with 2captcha.com)
def captcha_solver(driver):
    captcha_src = driver.find_element_by_id('recaptcha_challenge_image').get_attribute("src")
    urllib.urlretrieve(captcha_src, "captcha.jpg")
    captcha = CaptchaUpload("4cfd308fd703d40291a7e250d743ca84")  # 2captcha API KEY
    captcha_answer = captcha.solve("captcha.jpg")
    wait = WebDriverWait(driver, 10)
    captcha_input_box = wait.until(
        EC.presence_of_element_located((By.ID, "recaptcha_response_field")))
    captcha_input_box.send_keys(captcha_answer)
    driver.implicitly_wait(5)
    captcha_input_box.submit()


# inputting the domain in similar web search box and finding necessary values
def lookup(driver, domain, short_method):
    # short method - inputting the domain in the url 
    if short_method:
        driver.get("https://www.similarweb.com/website/" + domain)
    else:
        driver.get("https://www.similarweb.com")
    attempt = 0
    # trying 3 times before quiting (due to second refresh by the website that clears the search box)
    while attempt < 3:
        try:
            captcha_body_page = driver.find_elements_by_class_name("block-page")
            driver.implicitly_wait(0)
            if captcha_body_page:
                print "Captcha ahead, solving the captcha, it may take a few seconds"
                captcha_solver(driver)
                print "Captcha solved! the program will continue shortly"
                time.sleep(10)  # to prevent second refresh affecting the upcoming elements finding after captcha solved
	    # for normal method, inputting the domain in the searchbox instead of url
            if not short_method:
                input_element = driver.find_element_by_id("js-swSearch-input")
                input_element.click()
                input_element.send_keys(domain)
                input_element.submit()
            wait = WebDriverWait(driver, 10)
            total_visits = wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='engagementInfo-valueNumber js-countValue']")))
            country_name = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[@class='country-name country-name--link']")))
            percentage_of_total_visits = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//span[@class='traffic-share-valueNumber js-countValue']")))

            total_visits_line = "the monthly total visits to %s is %s" % (domain, total_visits.text)
            print '\n' + total_visits_line

            # always printing the first 5 countries (if available)
            x = 0
            num_of_countries = len(country_name)
            response_lines = []
            while x < num_of_countries:
                response_line = "%s is responsible for %s of the total visits" % (
                    country_name[x].text, percentage_of_total_visits[x].text)
                response_lines.append(response_line)
                print response_line
                x += 1

            out = open(domain + '.csv', 'w')
            out.write('%s \n' % total_visits_line)
            for line in response_lines:
                out.write('%s' % line)
                out.write('\n')
            out.close()
            attempt += 3


        except TimeoutException:
            print("Box or Button or Element not found in similarweb while checking %s" % domain)
            attempt += 1
            print "attempt number %d... trying again" % attempt


# main
if __name__ == "__main__":
    with open('big_domains.csv', 'rb') as f:
        reader = csv.reader(f)
        driver = init_driver()
        for row in reader:
            domain = row[0]
            lookup(driver, domain, True) # user need to give as a parameter True or False, True will activate the
            # short method, False will take the normal method
