from datetime import datetime
import json
from time import sleep
from crawl_from_website import Crawler
from selenium import webdriver


def test_flow_case_predefined() -> None:
    crawl = Crawler("https://www.viacaocometa.com.br/")
    driver = webdriver.Firefox()

    # ensure we at the proper page
    driver.get(crawl.base_url)

    trip = crawl.trips[0]
    departure = list(trip.keys())[0]
    arrival = trip[departure]

    crawl.search_for_trip(
        driver=driver,
        departure=departure,
        arrival=arrival,
        departure_date=datetime.now(),
    )

    sleep(10)  # waiting loading

    crawl.crawl_trips(driver)

    with open("test_results.json", "w") as file:
        file.write(json.dumps(crawl.results))
