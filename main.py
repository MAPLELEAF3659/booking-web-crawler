import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
from enum import Enum
import re


class Review(Enum):
    name = str
    country = str
    room_name = str
    type = str
    num_night = int
    stay_date = str
    review_date = str
    title = str
    positive_description = str
    negative_description = str
    rating = float


def get_data_from_hotel_page(driver: webdriver.Chrome, url: str):
    data = {
        "name": "",
        "address": "",
        "slogan": "",
        "description": "",
        "star": {
            "count": 0,  # 0-5
            "type": "N/A"  # official, booking
        },
        "user_review": {
            "overall_rating": {
                "average": 0.0,
                "staff": 0.0,
                "facilities": 0.0,
                "cleanliness": 0.0,
                "comfort": 0.0,
                "value": 0.0,
                "location": 0.0,
                "wifi": 0.0,
            },
            "count": 0,
            "reviews": list()
        }
    }
    driver.get(url)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # basic infos
    data['name'] = soup.find('h2', class_="pp-header__title").text
    data['address'] = soup.find(
        'div', class_="a53cbfa6de f17adf7576").contents[0].getText(strip=True)
    slogan_div = soup.find('h3', class_="e1eebb6a1e b484330d89")
    data['slogan'] = slogan_div.getText() if slogan_div else ""
    data['description'] = soup.find('p', class_="a53cbfa6de b3efd73f69").text

    # stars
    star_div = soup.find('span', class_="hp__hotel_ratings")
    data['star']['count'] = len(star_div.find_all(
        'span', class_="fcd9eec8fb d31eda6efc c25361c37f"))
    if data['star']['count'] > 0:
        star_text = star_div.find(
            'span', class_="a455730030 d542f184f1").get('data-testid')
        data['star']['type'] = "official" if star_text == "rating_stars" else "booking"

    # reviews
    average_rating_div = soup.find('div', id="js--hp-gallery-scorecard")
    try:
        data['user_review']['overall_rating']['average'] = (float)(
            average_rating_div.attrs.get("data-review-score", 0))
        subrating_divs = soup.find_all('div', class_="ccb65902b2 bdc1ea4a28")
        data['user_review']['overall_rating']['staff'] = (
            float)(subrating_divs[0].text)
        data['user_review']['overall_rating']['facilities'] = (
            float)(subrating_divs[1].text)
        data['user_review']['overall_rating']['cleanliness'] = (
            float)(subrating_divs[2].text)
        data['user_review']['overall_rating']['comfort'] = (
            float)(subrating_divs[3].text)
        data['user_review']['overall_rating']['value'] = (
            float)(subrating_divs[4].text)
        data['user_review']['overall_rating']['location'] = (
            float)(subrating_divs[5].text)
        data['user_review']['overall_rating']['wifi'] = (
            float)(subrating_divs[6].text)
    except:
        try:
            data['user_review']['overall_rating']['average'] = re.findall(
                r'\d+\.\d+', (soup.find('div', class_="a3b8729ab1 e6208ee469 cb2cbb3ccb").text))[0]
        except:
            None

    # click review button
    review_button = driver.find_element(
        By.ID, "reviews-tab-trigger")
    review_button.click()
    review_section = soup.find('div', class_="f7c2c6294c")

    return data


def booking_web_crawler(args):
    query = {
        "search": args.search,
        "check_in": args.check_in,
        "check_out": args.check_out,
        "num_adults": args.num_adults,
        "num_children": args.num_children,
        "num_rooms": args.num_rooms
    }

    # Set up Selenium WebDriver
    options = Options()
    # options.add_argument('--headless=new')
    # prefs = {"profile.managed_default_content_settings.images": 2,
    #             "profile.managed_default_content_settings.stylesheets": 2}
    # options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=options)

    url_query = "https://www.booking.com/searchresults.zh-tw.html"
    url_query += f"?ss={query['search']}"
    url_query += f"&checkin={query['check_in']}"
    url_query += f"&checkout={query['check_out']}"
    url_query += f"&group_adults={query['num_adults']}"
    url_query += f"&no_room={query['num_rooms']}"
    url_query += f"&group_children={query['num_children']}"

    driver.get(url_query)
    time.sleep(1)  # Wait for results to load

    current_height = driver.execute_script(
        'window.scrollTo(0,document.body.scrollHeight);')
    while True:
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        time.sleep(1)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == current_height:
            break
        current_height = new_height

    # Click the first of searched results
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    urls = list(map(lambda item: item.get("href"),
                    soup.find_all('a', class_="a78ca197d0")))
    result = []

    try:
        # data = get_data_from_hotel_page(driver, urls[0])
        # result.append(data)
        for url in urls:
            data = get_data_from_hotel_page(driver, url)
            result.append(data)
    except KeyboardInterrupt:
        print("Stopped by user. Save data at current position.")

    with open("result/result.json", "w", encoding='utf8') as file:
        json.dump(result, file, ensure_ascii=False)

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search",
                        help="Search keywords.", required=True)
    parser.add_argument("-ci", "--check_in",
                        help="Check-in date. Format: yyyy-MM-dd")
    parser.add_argument("-co", "--check_out",
                        help="Check-out date. Format: yyyy-MM-dd")
    parser.add_argument("-na", "--num_adults",
                        help="Number of adults.", default=2)
    parser.add_argument("-nc", "--num_children",
                        help="Number of children.", default=0)
    parser.add_argument("-nr", "--num_rooms",
                        help="Number of rooms.", default=1)
    args = parser.parse_args()

    booking_web_crawler(args)
