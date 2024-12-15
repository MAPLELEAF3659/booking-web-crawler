# Booking.com Web Crawler

A web crawler that collects hotel data and reviews from [Booking.com](https://booking.com) to generate the JSON dataset.

- Github repo link: [https://github.com/MAPLELEAF3659/booking-web-crawler](https://github.com/MAPLELEAF3659/booking-web-crawler)

- Made by MAPLELEAF3659

## System Environment

- Python version: 3.12.2
- Packages (see requirements.txt for full packages)
  - beautifulsoup4: 4.12.3
  - selenium: 4.27.1
  - tqdm: 4.67.1
- WebDriver: Chrome

## Setup

1. Create virtual environment

   ```bash
   pip install virtualenv
   virtualenv venv
   ```

1. Enter virtual environment

   - Windows Powershell

   ```bash
   .\venv\Scripts\Activate.ps1
   ```

   - Linux

   ```bash
   source venv/Scripts/activate
   ```

1. Install required packages

   ```bash
   pip install -r requirements.txt
   ```

## Execution

1. Run main.py

   ```bash
   py main.py --search "東京澀谷" --check_in 2025-02-01 --check_out 2025-02-02 --num_adults 2 --num_children 0 --num_rooms 1
   ```

   - Command arguments

     | short name | full name        | description                          | type | default value | required?                    |
     | ---------- | ---------------- | ------------------------------------ | ---- | ------------- | ----------------------       |
     | `-s`       | `--search`       | keywords of search.                  | str  | None          | **Y**                        |
     | `-ci`      | `--check_in`     | check-in date. format: `yyyy-MM-dd`  | str  | None          | **Y** if `check_out` existed |
     | `-co`      | `--check_out`    | check-out date. format: `yyyy-MM-dd` | str  | None          | **Y** if `check_in` existed  |
     | `-na`      | `--num_adults`   | number of adults.                    | int  | 2             | N                            |
     | `-nc`      | `--num_children` | number of children.                  | int  | 0             | N                            |
     | `-nr`      | `--num_rooms`    | number of rooms.                     | int  | 1             | N                            |
     | `-mi`      | `--max_item`     | max item for web-crawling            | int  | 999           | N                            |
     | `-mp`      | `--max_page`     | max review page in an item           | int  | 999           | N                            |

1. The results will save in `.json` at `./result/`

## Output Dataset Format

The output of result data will be an array of [BookingData](#bookingdata) object in json format. Each [BookingData](#bookingdata) object represents hotel information, including its properties, star ([Star](#star) object, including `count` and `type`), and user reviews (including [OverallRating](#overallrating) object, `count`, `count_crawled`, and array of [Review](#review) object). The detail of the structure are described as following sections.

- Overall example:

    ```json
    [
        BookingData,
        {
            "name": "hotel name",
            "address": "hotel address",
            "slogan": "hotel slogan",
            "description": "hotel description",
            "star": { -> Star
                "count": 5,
                "type": "official"
            },
            "user_review": {
                "overall_rating": { -> OverallRating
                    "type": "booking",
                    "average": 8.2,
                    "staff": 9.1,
                    "facilities": 8.2,
                    "cleanliness": 8.4,
                    "comfort": 8.5,
                    "value": 8.0,
                    "location": 9.4,
                    "wifi": 9.0
                },
                "count": 2344,
                "count_crawled": 500,
                "reviews": [
                        Review,
                        {
                            "user_name": "user name",
                            "user_type": "user type",
                            "country": "user country",
                            "room_name": "room name",
                            "num_night": 1,
                            "stay_date": "yyyy-MM",
                            "review_date": "yyyy-MM-dd",
                            "title": "review title",
                            "positive_description": "positive review description",
                            "negative_description": "negative review description",
                            "rating": 10.0
                        },
                        ...
                ]
            }
        },
        ...
    ]
    ```

### BookingData

The BookingData object represents a hotel's core information, rating summary, and reviews.

Fields:

- `name`: (Optional, String) - The name of the hotel.

- `address`: (Optional, String) - The address of the hotel.

- `slogan`: (Optional, String) - The hotel's slogan or tagline.

- `description`: (Optional, String) - A brief description of the hotel.

- `star`: ([Star](#star)) - Star rating details.

- `user_review`: ([UserReview](#userreview)) - Summary and detailed user reviews.

### Star

The star object provides information about the hotel's star rating.

Fields:

- `count`: (Optional, Integer) - The star rating of the hotel (range: 0-5).

- `type`: (Optional, String) - Type of the star rating (e.g., "official", "booking").

### UserReview

The user_review object represents user feedback and reviews for the hotel.

Fields:

- `overall_rating`: ([OverallRating](#overallrating)) - Aggregated ratings of the hotel.

- `count`: (Optional, Integer) - Total number of reviews.

- `count_crawled`: (Optional, Integer) - Number of crawled reviews.

- `reviews`: (List[[Review](#review)]) - Detailed individual reviews.

### OverallRating

The overall_rating object contains aggregated scores for various attributes of the hotel.  
\*_All value expects `type` are ranged in 0.0~10.0._

Fields:

- `type`: (Optional, String) - Rating type. (options: "booking", "external")

- `average`: (Optional, Float) - Average overall rating.

- `staff`: (Optional, Float) - Rating for the hotel staff.

- `facilities`: (Optional, Float) - Rating for facilities.

- `cleanliness`: (Optional, Float) - Rating for cleanliness.

- `comfort`: (Optional, Float) - Rating for comfort.

- `value`: (Optional, Float) - Rating for value for money.

- `location`: (Optional, Float) - Rating for location.

- `wifi`: (Optional, Float) - Rating for Wi-Fi quality.

### Review

The Review object represents a detailed review from a user.

Fields:

- `user_name`: (Optional, String) - Name of the reviewer.

- `user_type`: (Optional, String) - Type of user (options: "single", "family", "couple", "group").

- `country`: (Optional, String) - Reviewer's country of origin.

- `room_name`: (Optional, String) - Name or type of the room stayed in.

- `num_stay_night`: (Optional, Integer) - Number of nights stayed.

- `stay_date`: (Optional, String) - Date of stay. (format: yyyy-MM)

- `review_date`: (Optional, String) - Date of review. (format: yyyy-MM-dd)

- `title`: (Optional, String) - Title of the review.

- `positive_description`: (Optional, String) - Positive aspects mentioned in the review.

- `negative_description`: (Optional, String) - Negative aspects mentioned in the review.

- `rating`: (Optional, Float) - Overall rating provided by the user (range: 0.0-10.0).
