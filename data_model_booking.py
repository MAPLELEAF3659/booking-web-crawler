from typing import List, Optional
import json

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


class Star:
    def __init__(self,
                 count: Optional[int] = None,
                 star_type: Optional[str] = None):
        self.count = count  # 0-5
        self.type = star_type  # official, booking

    def to_dict(self):
        return {
            "count": self.count,
            "type": self.type
        }


class OverallRating:
    def __init__(
        self,
        type: Optional[str] = None,
        average: Optional[float] = None,
        staff: Optional[float] = None,
        facilities: Optional[float] = None,
        cleanliness: Optional[float] = None,
        comfort: Optional[float] = None,
        value: Optional[float] = None,
        location: Optional[float] = None,
        wifi: Optional[float] = None
    ):
        self.type = type  # "booking", "external", None
        self.average = average  # 0.0~10.0
        self.staff = staff
        self.facilities = facilities
        self.cleanliness = cleanliness
        self.comfort = comfort
        self.value = value
        self.location = location
        self.wifi = wifi

    def update_subrating_by_keyword(self, key: str, value: float):
        match subrating_mapping[key]:
            case 'staff':
                self.staff = value
            case 'facilities':
                self.facilities = value
            case 'cleanliness':
                self.cleanliness = value
            case 'comfort':
                self.comfort = value
            case 'value':
                self.value = value
            case 'location':
                self.location = value
            case 'wifi':
                self.wifi = value

    def to_dict(self):
        return {
            "type": self.type,
            "average": self.average,
            "staff": self.staff,
            "facilities": self.facilities,
            "cleanliness": self.cleanliness,
            "comfort": self.comfort,
            "value": self.value,
            "location": self.location,
            "wifi": self.wifi
        }


class Review:
    def __init__(
        self,
        user_name: Optional[str] = None,
        user_type: Optional[str] = None,
        country: Optional[str] = None,
        room_name: Optional[str] = None,
        num_stay_night: Optional[int] = None,
        stay_date: Optional[str] = None,
        review_date: Optional[str] = None,
        title: Optional[str] = None,
        positive_description: Optional[str] = None,
        negative_description: Optional[str] = None,
        rating: Optional[float] = None  # 0.0~10.0
    ):
        self.user_name = user_name
        self.user_type = user_type
        self.country = country
        self.room_name = room_name
        self.num_stay_night = num_stay_night
        self.stay_date = stay_date
        self.review_date = review_date
        self.title = title
        self.positive_description = positive_description
        self.negative_description = negative_description
        self.rating = rating

    def to_dict(self):
        return {
            "user_name": self.user_name,
            "user_type": self.user_type,
            "country": self.country,
            "room_name": self.room_name,
            "num_stay_night": self.num_stay_night,
            "stay_date": self.stay_date,
            "review_date": self.review_date,
            "title": self.title,
            "positive_description": self.positive_description,
            "negative_description": self.negative_description,
            "rating": self.rating
        }


class UserReview:
    def __init__(
        self,
        overall_rating: Optional[OverallRating] = None,
        count: Optional[int] = 0,
        count_crawled: Optional[int] = 0,
        reviews: Optional[list[Review]] = None
    ):
        self.overall_rating = overall_rating or OverallRating()
        self.count = count  # number
        self.count_crawled = count_crawled  # number
        self.reviews = reviews or []  # Review objects

    def to_dict(self):
        return {
            "overall_rating": self.overall_rating.to_dict(),
            "count": self.count,
            "count_crawled": len(self.reviews),
            "reviews": [review.to_dict() for review in self.reviews]
        }


class BookingData:
    def __init__(
        self,
        name: Optional[str] = None,
        address: Optional[str] = None,
        slogan: Optional[str] = None,
        description: Optional[str] = None,
        star: Optional[Star] = None,
        user_review: Optional[UserReview] = None
    ):
        self.name = name
        self.address = address
        self.slogan = slogan
        self.description = description
        self.star = star or Star()
        self.user_review = user_review or UserReview()

    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "slogan": self.slogan,
            "description": self.description,
            "star": self.star.to_dict(),
            "user_review": self.user_review.to_dict()
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)
