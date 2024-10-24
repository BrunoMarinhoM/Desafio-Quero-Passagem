from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta, timezone
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class CrawlerException(Exception): ...


class Crawler:
    def __init__(self, base_url: str, trips=[]) -> None:
        self.base_url = base_url
        self.is_on_base_url = True
        self.results = []
        self.trips = trips

    def get_driver(self) -> webdriver.Remote:
        try:
            driver = webdriver.Chrome()
        except Exception:
            try:
                driver = webdriver.Firefox()
            except:
                raise CrawlerException(
                    "Could not initialize webdriver. Please, ensure at"
                    "least one is installed."
                )
        return driver

    def crawl_trips(self, driver: webdriver.Remote) -> None:
        parsed_url = urlparse(driver.current_url)
        parsed_queries = parse_qs(parsed_url.query)

        try:
            assert parsed_url.hostname == urlparse(self.base_url).hostname

            assert (
                parsed_queries.get("data_ida") != None
                and parsed_queries.get("origem_id") != None
                and parsed_queries.get("destino_id") != None
            )
        except AssertionError:
            raise CrawlerException(f"Unexpected URL -> {driver.current_url} <-")

        departure_date_list = parsed_queries.get("data_ida")

        try:
            assert len(departure_date_list) == 1
            assert len(departure_date_list[0]) == 8
        except AssertionError:
            raise CrawlerException(
                f"Unexpected URL -> {departure_date} <- -> {len(departure_date)} <-"
            )

        departure_date = departure_date_list[0]

        try:
            departure_date = datetime.strptime(departure_date, "%d%m%Y")

        except ValueError as ve:
            raise CrawlerException(
                f"The date provided in the url -> {departure_date} <- is not valid. Cannot Crawl -> "
                "{repr(ve)} <-"
            )

        except Exception as e:
            raise CrawlerException(f"Unexpected Exception -> {repr(e)}. Cannot crawl.")

        services = driver.find_elements(By.CLASS_NAME, "list-companies-item")

        result_json = []

        for service in services:
            headers_info = service.find_element(By.CLASS_NAME, "header")

            departure_time = headers_info.find_element(
                By.XPATH,
                ".//span[@class='edit-text-departure-label']/following-sibling::span",
            ).text

            travel_time = service.find_element(
                By.XPATH, ".//div[@class='duration']/p/*[@data-js='durationLabel']"
            ).text

            departure_datetime = datetime.strptime(
                f"{departure_date.strftime('%Y-%m-%d')} {departure_time}",
                "%Y-%m-%d %H:%M",
            )

            if travel_time.find("h") == -1:
                raise CrawlerException(
                    "Cannot calculate the travel time. The code needs refactorization "
                    f"-> {travel_time} <-"
                )

            try:
                assert len(travel_time.split("h")) >= 2
            except Exception as e:
                raise NotImplementedError(
                    "Cannot handle html formmated that way. The travel time "
                    f"{travel_time} is not formatted as expected (%Hh%Mmin)"
                )

            mins = travel_time.split("h")[1]

            mins = mins[:2] if len(mins) == 5 else mins

            arrival_datetime = departure_datetime + timedelta(
                hours=int(travel_time.split("h")[0]),
                minutes=int(0 if mins == "" else mins),
            )

            offers = service.find_elements(
                By.XPATH, ".//li[starts-with(@data-js, 'offer-element-')]"
            )

            for offer in offers:
                try:
                    category = offer.find_element(
                        By.XPATH, ".//span[@class='classtypeLabel']/*[1]/*[1]"
                    ).text

                    price_label = offer.find_element(By.CLASS_NAME, "price")

                    price_trucated = price_label.find_element(
                        By.CLASS_NAME, "price-label"
                    ).text

                    price_decimals = price_label.find_element(
                        By.CLASS_NAME, "decimal-label"
                    ).text

                    price = f"{price_trucated}{price_decimals}"

                    departure_location = driver.find_element(
                        By.XPATH, "//*[@data-js='summary-label-origin']"
                    )
                    arrival_location = driver.find_element(
                        By.XPATH, "//*[@data-js='summary-label-destination']"
                    )

                    result_json += [
                        {
                            "collected_at": datetime.now(tz=timezone.utc).strftime(
                                "%Y-%m-%d %H:%M:%s"
                            ),
                            "isAvailable": price != "",
                            "price": price,
                            "category": category,
                            "originDesc": departure_location.text,
                            "destinationDesc": arrival_location.text,
                            "departureDate": f"{departure_date.strftime('%Y-%m-%d')}T{departure_time}",
                            "arrivalDate": f"{arrival_datetime.strftime('%Y-%m-%dT%H%M')}",
                        }
                    ]
                except NoSuchElementException:
                    continue

            self.results += [result_json]

    def search_for_trip(
        self,
        driver: webdriver.Remote,
        departure: str,
        arrival: str,
        departure_date: datetime,
        trial: int = 0,
    ) -> None:
        assert driver.current_url == self.base_url
        assert trial <= 5  # tries at most 5 times

        # sensible to ui changes.
        input_element = driver.find_element(By.ID, "input-departure")

        input_element.click()
        sleep(10)
        input_element.send_keys(departure)
        sleep(10)

        autocomplete = driver.find_element(
            By.XPATH, f"//*[contains(text(), '{departure}')]"
        )

        try:
            autocomplete.click()
        except Exception:
            self.search_for_trip(
                driver=driver,
                departure=departure,
                arrival=arrival,
                departure_date=departure_date,
                trial=trial + 1,
            )
            return

        sleep(10)

        # now we're automatically at the arrival input field

        input_element = driver.find_element(By.ID, "input-destination")
        input_element.click()

        input_element.send_keys(arrival)
        sleep(10)
        autocomplete = driver.find_element(
            By.XPATH, f"//*[contains(text(), '{arrival}')]"
        )

        try:
            autocomplete.click()
        except Exception:
            self.search_for_trip(
                driver=driver,
                departure=departure,
                arrival=arrival,
                departure_date=departure_date,
                trial=trial + 1,
            )
            return

        sleep(10)

        # now we should have both departure and arrival/destination fields

        # filleds, and, thus, we must fill the departure date

        input_element = driver.find_element(By.ID, "input-date")

        input_element.click()

        input_element.send_keys(departure_date.strftime("%d%m%Y"))

        search_element = driver.find_element(By.ID, "search-button")

        search_element.click()

        return
