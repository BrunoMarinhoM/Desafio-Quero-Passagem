from datetime import date, datetime, timedelta
import json
from time import sleep
from crawler import Crawler
from selenium import webdriver

base_url = "https://www.viacaocometa.com.br/"

challenge_list_of_trips = [
    {"São Paulo (Rod. Tietê) (SP)": "Belo Horizonte (MG)"},
    {"Belo Horizonte (MG)": "São Paulo (Rod. Tietê) (SP)"},
    {"São Paulo (Rod. Tietê) (SP)": "Ribeirão Preto (SP)"},
    {"Ribeirão Preto (SP)": "São Paulo (Rod. Tietê) (SP)"},
    {"São Paulo (Rod. Tietê) (SP)": "Curitiba (PR)"},
    {"Curitiba (PR)": "São Paulo (Rod. Tietê) (SP)"},
    {"Rio de Janeiro (Novo Rio) (RJ)": "Belo Horizonte (MG)"},
    {"São Paulo (Rod. Barra Funda) (SP)": "São José do Rio Preto (Rodoviária) (SP)"},
    {"São José do Rio Preto (Rodoviária) (SP)": "São Paulo (Rod. Barra Funda) (SP)"},
    {"Rio de Janeiro (Novo Rio) (RJ)": "Campinas (SP)"},
]


def main() -> None:
    crawler = Crawler(base_url)

    driver = crawler.get_driver()

    initial_date = datetime.now()

    dates = [initial_date]

    _curr_date = initial_date
    _curr_trip = {}

    for i in range(0, 8):
        dates += [initial_date + timedelta(days=i)]

    try:
        for date in dates:
            _curr_date = date
            for trip in challenge_list_of_trips:
                driver.get(
                    base_url
                )  # ensure we are at the beggining of the page when start
                sleep(2)  # waiting loading
                for departure, arrival in trip.items():
                    _curr_trip = {"dep": departure, "arr": arrival}
                    crawler.search_for_trip(
                        driver=driver,
                        departure=departure,
                        arrival=arrival,
                        departure_date=date,
                    )
                    sleep(5)  # waiting loading

                    crawler.crawl_trips(driver=driver)

                    sleep(5)  # waiting loading

        with open("./results_webcrawl.json", "w") as file:
            file.write(json.dumps(crawler.results))
        print("done")

    except Exception as e:
        with open("./results_webcrawl_partial.json", "w") as file:
            file.write(json.dumps(crawler.results))

        print(f"Could not complete -> {e}")
        print(
            f"Was at {_curr_date.strftime('%Y-%m-%d')} and at trip {_curr_trip}\n"
            " Please, take over from there."
        )


if __name__ == "__main__":
    main()
