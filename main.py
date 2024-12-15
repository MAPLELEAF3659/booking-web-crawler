import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import json
import re
from tqdm import tqdm
from data_model_booking import BookingData, Review, subrating_mapping, user_type_mapping


def get_data_from_hotel_page(driver: webdriver.Chrome, url: str, max_page: int):
    data = BookingData()
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # basic infos
    data.name = soup.find('h2', class_="pp-header__title").getText(strip=True)
    data.address = soup.find(
        'div', class_="a53cbfa6de f17adf7576").contents[0].getText(strip=True)

    slogan_div = soup.find('h3', class_="e1eebb6a1e b484330d89")
    data.slogan = slogan_div.getText() if slogan_div else None

    data.description = soup.find(
        'p', class_="a53cbfa6de b3efd73f69").getText(strip=True)

    # stars
    star_div = soup.find('span', class_="hp__hotel_ratings")
    data.star.count = len(star_div.find_all(
        'span', class_="fcd9eec8fb d31eda6efc c25361c37f"))
    if data.star.count > 0:
        star_text = star_div.find(
            'span', class_="a455730030 d542f184f1").get("data-testid")
        data.star.type = "official" if star_text == "rating-stars" else "booking"

    # reviews
    average_rating_div = soup.find('div', id="js--hp-gallery-scorecard")
    try:
        # get average rating
        data.user_review.overall_rating.average = (float)(
            average_rating_div.attrs.get("data-review-score", 0))

        # get subrating
        subrating_divs = soup.find_all(
            'div', class_="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942")
        for subrating_div in subrating_divs[int(len(subrating_divs)/2):]:
            subrating = subrating_div.getText(
                strip=True).split(" ")  # "name 0.0"
            data.user_review.overall_rating.update_subrating_by_keyword(subrating[0],
                                                                        float(subrating[1]))
    except:
        try:
            # external average rating
            average_overall_rating_div = soup.find('div',
                                                   class_="a3b8729ab1 e6208ee469 cb2cbb3ccb")
            data.user_review.overall_rating.average = float(re.findall(r'\d+\.\d+',
                                                                       (average_overall_rating_div.text))[0])
        except:
            None

    # get total count of reviews
    review_count_div = soup.find(
        'div', class_="abf093bdfe f45d8e4c32 d935416c47")
    try:
        review_count_origin = review_count_div.text
        data.user_review.count = int(
            re.search(r'(\d[\d,]*)', review_count_origin).group(1).replace(',', ''))
    except:
        # if there is no review then skip
        data.user_review.count = 0
        print("No review.")
        return data

    # click review button
    review_button = driver.find_element(
        By.ID, "reviews-tab-trigger")
    review_button.click()
    time.sleep(3)

    # reparse and get review sidebar
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_section = soup.find('div', class_="b89e77822a")
        page_count = 1
        with tqdm(total=data.user_review.count) as pbar:
            while True:
                pbar.set_description(f"Getting review page {page_count}")
                current_review_divs = review_section.find_all(
                    'div', class_="d799cd346c")
                for review_div in current_review_divs:
                    review = Review()

                    review.user_name = review_div.find(
                        'div', class_="a3332d346a e6208ee469").getText(strip=True)

                    country_div = review_div.find(
                        'span', class_="afac1f68d9 a1ad95c055")
                    review.country = country_div.getText(
                        strip=True) if country_div else None

                    review.room_name = review_div.find(
                        'span', {"data-testid": "review-room-name"}).getText(strip=True)

                    # transform "n 晚" to "n"(int)
                    num_stay_night_div = review_div.find(
                        'span', {"data-testid": "review-num-nights"})
                    review.num_stay_night = int(num_stay_night_div.getText(
                        separator=" ", strip=True)[0])

                    # transform "yyyy 年 MM 月" to "yyyy-MM"
                    stay_date_origin = review_div.find(
                        'span', class_="abf093bdfe d88f1120c1").text
                    stay_date_matched = re.search(
                        r'(\d{4}) 年 (\d{1,2}) 月', stay_date_origin)
                    review.stay_date = \
                        f"{stay_date_matched.group(1)}-" + \
                        f"{stay_date_matched.group(2).zfill(2)}"

                    user_type_div = review_div.find(
                        'span', {"data-testid": "review-traveler-type"})
                    review.user_type = user_type_mapping[f"{
                        user_type_div.text}"] if user_type_div else None

                    # transform "yyyy 年 MM 月 dd 日" to "yyyy-MM-dd"
                    review_date_origin = review_div.find(
                        'span', class_="abf093bdfe f45d8e4c32").text
                    review_date_matched = re.search(
                        r'(\d{4}) 年 (\d{1,2}) 月 (\d{1,2}) 日', review_date_origin)
                    review.review_date = \
                        f"{review_date_matched.group(1)}" +\
                        f"-{review_date_matched.group(2).zfill(2)}" +\
                        f"-{review_date_matched.group(3).zfill(2)}"

                    review.title = review_div.find(
                        'h3', {"data-testid": "review-title"}).text

                    positive_description_div = review_div.find(
                        'div', {"data-testid": "review-positive-text"})
                    review.positive_description = positive_description_div.getText(
                        strip=True) if positive_description_div else None

                    negative_description_div = review_div.find(
                        'div', {"data-testid": "review-negative-text"})
                    review.negative_description = negative_description_div.getText(
                        strip=True) if negative_description_div else None

                    review.rating = float(review_div.find(
                        'div', {"data-testid": "review-score"}).getText(strip=True).split('分')[-1])

                    data.user_review.reviews.append(review)

                pbar.update(len(current_review_divs))

                if page_count >= max_page:  # page limiter
                    pbar.set_description(
                        f"Getting review page {page_count} [max page reached]")
                    break

                # click and change to next page
                try:  # check if next button exist
                    next_page_button = driver.find_element(
                        By.XPATH, '//button[@aria-label="下一頁"]')
                    if next_page_button.is_enabled():  # click if clickable(no disable attr)
                        next_page_button.click()
                        page_count += 1
                        time.sleep(3)
                    else:
                        break
                except:
                    break
    except Exception as e:
        print(f"Error when getting reviews. Message:\n{e}")

    return data.to_dict()


def booking_web_crawler(args):
    start_time = time.time()

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
    prefs = {"profile.default_content_settings.images": 2,
             "profile.managed_default_content_settings.images": 2}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    # build up query url
    url_query = "https://www.booking.com/searchresults.zh-tw.html"
    url_query += f"?ss={query['search']}"
    if query["check_in"]:
        url_query += f"&checkin={query['check_in']}"
    if query["check_out"]:
        url_query += f"&checkout={query['check_out']}"
    url_query += f"&group_adults={query['num_adults']}"
    url_query += f"&no_room={query['num_rooms']}"
    url_query += f"&group_children={query['num_children']}"
    print(f"Query URL: {url_query}")
    print(f"Max web-crawling items: {args.max_item}. " +
          f"Max review page: {args.max_page}")

    driver.get(url_query)
    time.sleep(5)  # Wait for results to load

    # close first visit dialog
    driver.find_element(By.CLASS_NAME,
                        "a83ed08757.c21c56c305.f38b6daa18.d691166b09.ab98298258.f4552b6561").click()

    # scroll for lazy load
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
    # click load more after lazy load stop
    while True:
        try:
            load_more_button = driver.find_element(
                By.CLASS_NAME, "a83ed08757.c21c56c305.bf0537ecb5.f671049264.af7297d90d.c0e0affd09")
            driver.execute_script(
                "arguments[0].scrollIntoView(false);", load_more_button)
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(load_more_button)).click()
            time.sleep(3)
        except:
            break

    # get all result url
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    urls_result = list(map(lambda item: item.get("href"),
                           soup.find_all('a', class_="a78ca197d0")))

    # start web-crawling for every url
    dataset = []
    for i, url in enumerate(urls_result):
        print(f"Web-crawling item {i+1}/{len(urls_result)}...")

        try:
            data = get_data_from_hotel_page(driver,
                                            url,
                                            args.max_page)
            dataset.append(data)
        except Exception as e:
            print(f"Error when web-crawling. Skip. Message:\n{e}")

        if (i+1) >= args.max_item:  # item count limiter
            print("Max item reached. Saving data at current position.")
            break

    # save to json
    filename = f"result_{query['search']}"
    if query["check_in"]:
        filename += f"_{query['check_in']}"
    if query["check_out"]:
        filename += f"_{query['check_out']}"
    filename += f"_room{query['num_rooms']}"
    filename += f"_adult{query['num_adults']}"
    filename += f"_child{query['num_children']}"
    with open(f"result/{filename}.json", "w", encoding='utf8') as file:
        json.dump(dataset, file, ensure_ascii=False, indent=5)

    driver.close()

    end_time = time.time()
    print(f"Total execution time: {timedelta(seconds=end_time-start_time)}. " +
          f"Dataset length: {len(dataset)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str,
                        help="Search keywords.", required=True)
    parser.add_argument("-ci", "--check_in", type=str,
                        help="Check-in date. Format: yyyy-MM-dd")
    parser.add_argument("-co", "--check_out", type=str,
                        help="Check-out date. Format: yyyy-MM-dd")
    parser.add_argument("-na", "--num_adults", type=int,
                        help="Number of adults.", default=2)
    parser.add_argument("-nc", "--num_children", type=int,
                        help="Number of children.", default=0)
    parser.add_argument("-nr", "--num_rooms", type=int,
                        help="Number of rooms.", default=1)
    parser.add_argument("-mp", "--max_page", type=int,
                        help="Number of max review page.", default=999)
    parser.add_argument("-mi", "--max_item", type=int,
                        help="Number of max result items.", default=999)
    args = parser.parse_args()

    # check-in and check-out date checker
    if args.check_in or args.check_out:
        if not(args.check_in and args.check_out):
            raise ValueError("Check-in and check-out date must be used at same time.")
        
        current_date = datetime.now().date()
        try:
            check_in_date = datetime.strptime(args.check_in, "%Y-%m-%d").date()
            check_out_date = datetime.strptime(args.check_out, "%Y-%m-%d").date()
        except:
            raise ValueError("Invalid date format for check-in or check-out date. should be \"yyyy-MM-dd\"")
        
        if check_in_date < current_date or check_out_date < current_date:
            raise ValueError("Check-in or check-out date cannot be an past date.")
        if check_in_date >= check_out_date:
            raise ValueError("Check-out date must greater then check-in date and should not in same date.")

    booking_web_crawler(args)
