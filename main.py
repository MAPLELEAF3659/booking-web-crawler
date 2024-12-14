import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
from enum import Enum
import re
from tqdm import tqdm


user_type_mapping = {
    "團體": "group",
    "家庭": "family",
    "獨行旅客": "single",
    "情侶": "couple"
}

subrating_mapping = {
    "員工素質": "staff",
    "設施": "facilities",
    "清潔程度": "cleanliness",
    "舒適程度": "comfort",
    "性價比": "value",
    "住宿地點": "location",
    "免費 WiFi": " wifi"
}


def get_data_from_hotel_page(driver: webdriver.Chrome, url: str, max_page: int):
    data = {
        "name": None,
        "address": None,
        "slogan": None,
        "description": None,
        "star": {
            "count": None,  # 0-5
            "type": None  # official, booking
        },
        "user_review": {
            "overall_rating": { # 0.0~10.0
                "average": None,
                "staff": None,
                "facilities": None,
                "cleanliness": None,
                "comfort": None,
                "value": None,
                "location": None,
                "wifi": None,
            },
            "count": None, # number
            "count_crawled": None, # number
            "reviews": None # Review object
        }
    }
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # basic infos
    data['name'] = soup.find('h2', class_="pp-header__title").text
    data['address'] = soup.find(
        'div', class_="a53cbfa6de f17adf7576").contents[0].getText(strip=True)
    
    slogan_div = soup.find('h3', class_="e1eebb6a1e b484330d89")
    data['slogan'] = slogan_div.getText() if slogan_div else None
    
    data['description'] = soup.find('p', class_="a53cbfa6de b3efd73f69").text

    # stars
    star_div = soup.find('span', class_="hp__hotel_ratings")
    data['star']['count'] = len(star_div.find_all(
        'span', class_="fcd9eec8fb d31eda6efc c25361c37f"))
    if data['star']['count'] > 0:
        star_text = star_div.find(
            'span', class_="a455730030 d542f184f1").get("data-testid")
        data['star']['type'] = "official" if star_text == "rating-stars" else "booking"

    # reviews
    average_rating_div = soup.find('div', id="js--hp-gallery-scorecard")
    try:
        # get average rating
        data['user_review']['overall_rating']['average'] = (float)(
            average_rating_div.attrs.get("data-review-score", 0))
        
        # get subrating
        subrating_divs = soup.find_all(
            'div', class_="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942")
        for subrating_div in subrating_divs[int(len(subrating_divs)/2):]:
            subrating = subrating_div.text.split(" ")  # "name 0.0"
            data['user_review']['overall_rating'][subrating_mapping[subrating[0]]] = float(
                subrating[1])
    except:
        try:
            # external average rating
            average_overall_rating_div = soup.find('div',
                                                   class_="a3b8729ab1 e6208ee469 cb2cbb3ccb")
            data['user_review']['overall_rating']['average'] = \
                (float)(re.findall(r'\d+\.\d+',
                                   (average_overall_rating_div.text))[0])
        except:
            None

    # get total count of reviews
    review_count_div = soup.find(
        'div', class_="abf093bdfe f45d8e4c32 d935416c47")
    try:
        review_count_origin = review_count_div.text
        data['user_review']['count'] = int(
            re.search(r'(\d[\d,]*)', review_count_origin).group(1).replace(',', ''))
    except:
        # if there is no review then skip
        data['user_review']['count'] = 0
        print("No review.")
        return data

    # click review button
    review_button = driver.find_element(
        By.ID, "reviews-tab-trigger")
    review_button.click()
    time.sleep(3)

    # reparse and get review sidebar
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    review_section = soup.find('div', class_="b89e77822a")
    page_count = 1
    review_total_count = data['user_review']['count']
    with tqdm(total=review_total_count) as pbar:
        while True:
            pbar.set_description(f"Getting review page {page_count}")
            current_review_divs = review_section.find_all(
                'div', class_="d799cd346c")
            for review_div in current_review_divs:
                review = {
                    "user_name": None,
                    "user_type": None,
                    "country": None,
                    "room_name": None,
                    "num_night": None, # int
                    "stay_date": None,
                    "review_date": None,
                    "title": None,
                    "positive_description": None,
                    "negative_description": None,
                    "rating": None, # 0.0~10.0
                }

                review['user_name'] = review_div.find(
                    'div', class_="a3332d346a e6208ee469").text

                country_div = review_div.find(
                    'span', class_="afac1f68d9 a1ad95c055")
                review['country'] = country_div.text if country_div else None

                review['room_name'] = review_div.find(
                    'span', {"data-testid": "review-room-name"}).text

                # transform "n 晚" to "n"(int)
                num_night_div = review_div.find(
                    'span', {"data-testid": "review-num-nights"})
                review['num_night'] = int(num_night_div.getText(
                    separator=" ", strip=True)[0])

                # transform "yyyy 年 MM 月" to "yyyy-MM"
                stay_date_origin = review_div.find(
                    'span', class_="abf093bdfe d88f1120c1").text
                stay_date_matched = re.search(
                    r'(\d{4}) 年 (\d{1,2}) 月', stay_date_origin)
                review['stay_date'] = \
                    f"{stay_date_matched.group(1)}-" + \
                    f"{stay_date_matched.group(2).zfill(2)}"

                user_type_div = review_div.find('span', {"data-testid": "review-traveler-type"})
                review['user_type'] = user_type_mapping[f"{user_type_div.text}"] if user_type_div else None

                # transform "yyyy 年 MM 月 dd 日" to "yyyy-MM-dd"
                review_date_origin = review_div.find(
                    'span', class_="abf093bdfe f45d8e4c32").text
                review_date_matched = re.search(
                    r'(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日', review_date_origin)
                review['review_date'] = \
                    f"{review_date_matched.group(1)}" +\
                    f"-{review_date_matched.group(2).zfill(2)}" +\
                    f"-{review_date_matched.group(3).zfill(2)}"

                review['title'] = review_div.find(
                    'h3', {"data-testid": "review-title"}).text

                positive_description_div =  review_div.find('div', {"data-testid": "review-positive-text"})
                review['positive_description'] = positive_description_div.text if positive_description_div else None

                negative_description_div =  review_div.find('div', {"data-testid": "review-negative-text"})
                review['negative_description'] = negative_description_div.text if negative_description_div else None

                review['rating'] = float(review_div.find(
                    'div', {"data-testid": "review-score"}).getText(separator="分", strip=True)[2])

                data["user_review"]['reviews'].append(review)
                review_total_count += 1
                pbar.update(1)

            if page_count >= max_page:
                pbar.set_description(
                    f"Getting review page {page_count} [max page reached]")
                break

            next_page_button = driver.find_element(
                By.CLASS_NAME, "a83ed08757.c21c56c305.f38b6daa18.d691166b09.ab98298258.bb803d8689.a16ddf9c57")
            if next_page_button.is_enabled:
                next_page_button.click()
                page_count += 1
                time.sleep(3)
            else:
                break

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
    prefs = {"profile.managed_default_content_settings.images": 2,
             "profile.managed_default_content_settings.stylesheets": 2}
    options.add_experimental_option('prefs', prefs)
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

    print("Scrolling for lazy load...")
    current_height = driver.execute_script(
        'window.scrollTo(0,document.body.scrollHeight);')
    while True:
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        time.sleep(3)
        new_height = driver.execute_script('return document.body.scrollHeight')
        if new_height == current_height:
            break
        current_height = new_height

    # Click the first of searched results
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    urls_result = list(map(lambda item: item.get("href"),
                           soup.find_all('a', class_="a78ca197d0")))
    dataset = []

    for i, url in enumerate(urls_result):
        print(f"Crawling item {i+1}/{len(urls_result)}...")
        data = get_data_from_hotel_page(driver,
                                        url,
                                        args.max_page)
        dataset.append(data)
        if (i+1) >= args.max_item:
            print("Max item reached. Saving data at current position.")
            break

    with open(f"result/result_{query['search']}_{query['check_in']}_{query['check_out']}_room{query['num_rooms']}_adult{query['num_adults']}+child{query['num_children']}.json", "w", encoding='utf8') as file:
        json.dump(dataset, file, ensure_ascii=False, indent=5)
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
    parser.add_argument("-mp", "--max_page", type=int,
                        help="Number of max review page.", default=999)
    parser.add_argument("-mi", "--max_item", type=int,
                        help="Number of max result items.", default=999)
    args = parser.parse_args()

    booking_web_crawler(args)
