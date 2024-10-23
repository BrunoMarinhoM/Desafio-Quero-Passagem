import requests
from api_connector import ApiConnector
from typing import Dict, List, Any


class RequestGenerator:
    def __init(self) -> None:
        self.requests: List[requests.PreparedRequest] = []
        self.trips: List[Dict[str, Any]] = []

    def generate_requests(self) -> None: ...

    def set_trips(self, trips: Dict[str, str], departure_date: str) -> None: ...


class ApiRoutesRequestGenerator(RequestGenerator):
    """
    Generates requests using the ApiConnector interface to authenticate propertly
    using viacaocometa.com.br credentials
    """

    def __init__(self) -> None:
        self.api = ApiConnector()
        self.api.set_locales_info()
        self.requests = []
        self.trips = []

    def add_trips(self, trips: Dict[str, str], departure_date: str) -> None:
        """
        Adds to ApiRoutesRequestGenerator.trips property the trips according to the
        way the ApiConnector interface requires.

        All of the added trips will be put in the requests property to, then, be invoked by
        a requests.Session.send()

        Args:
            trip:
                The trips should be formatted the following way:

                {
                    Origin_city_name: Arrival_city_name
                }

            departure_date: str -> [YYYY-MM-DD]
        """
        assert isinstance(trips, dict)
        for departure, arrival in trips.items():
            self.trips += [
                {
                    "from": self.api.get_locale_id(departure),
                    "to": self.api.get_locale_id(arrival),
                    "departureDate": departure_date,
                }
            ]

    def set_trips(self, trips: Dict[str, str], departure_date: str) -> None:
        """
        Sets ApiRoutesRequestGenerator.trips property the trips according to the
        way the ApiConnector interface requires.

        All of the added trips will be put in the trips property to, then, be maped to
        a request (by the generate_requests method).

        Args:
            trip:
                The trips should be formatted the following way:

                {
                    Origin_city_name: Arrival_city_name
                }

            departure_date: str -> [YYYY-MM-DD]
        """
        assert isinstance(trips, dict)
        self.trips = []
        self.add_trips(trips=trips, departure_date=departure_date)

    def generate_requests(self) -> None:
        """
        Populates the requests property with proper api authentication according to the
        ApiConnector interface.

        This requests should be called with the requests.session.send() method

        """
        for trip in self.trips:
            self.requests += [
                self.api.prepare_route_request(
                    origin_id=trip.get("from"),
                    destination_id=trip.get("to"),
                    departure_date=trip.get("departureDate"),
                )
            ]
