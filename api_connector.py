import requests
import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import json


class ApiConnectorException(Exception): ...


class ApiConnector:
    """
    Provides a simple interface to interact with the jcatlm web api.
    Authentication happens on initialization.

    It authenticates using informaion provided by the www.viacaocometa.com.br (such as
    client_id and AuthId key to obtain the api access token)

    It fetches the client_id using BeautifulSoup to parse the html and, for that reason
    it will always log out while authentication. ALERT: If you don't want the logs,
    you can set the features argument in the BeatifulSoup initialization, but that could
    cause incompatibility problems.
    """

    def __init__(self) -> None:
        self.api_url = "https://api.jcatlm.com.br/"
        self._set_client_id()
        self._set_access_token()

    def _set_client_id(self) -> None:
        """
        sets the client id for this ApiConnector session
        """
        self.client_id = self._fetch_client_id()

    def _fetch_client_id(self) -> str:
        """
        Fetches (from the base_url html) the client_id and sets it
        in the current ApiConnector Session.
        """
        base_url = "https://www.viacaocometa.com.br/"
        response = requests.get(base_url)
        soup = BeautifulSoup(markup=response.text)

        id = soup.find(id="clientId")

        if id == None:
            raise ApiConnectorException(
                f"Could not fetch user id from base url -> {base_url}"
            )

        if not "value" in id.attrs.keys():
            raise ApiConnectorException(
                "There had been a update in the interface. The code should be refactored."
            )

        return id.attrs["value"]

    def _set_access_token(self) -> None:
        """
        sets the client id for this ApiConnector session
        """
        self.access_token = self._fetch_access_token()

    def _fetch_access_token(self) -> str:
        """
        ALERT: This function should not be called externally.

        SHOULD BE CALLED AFTER _set_client_id in the initialization chain.

        Logs in to the https://api.jcatlm.com.br/ using the methods hidden in the
        viacaocometa.com.br website.
        """

        base_url = "https://www.viacaocometa.com.br/content/jca/cometa/pt-br/jcr:content.authorization.json?clear=1"

        response = requests.get(base_url, timeout=15)

        if response.status_code != 200:
            raise ApiConnectorException(
                f"Something went wrong with the login api "
                "end point -> {response.text} <-"
            )

        try:
            json_body = json.loads(response.text)
            if not json_body.get("isSuccess"):
                raise ApiConnectorException(
                    f"Something went wrong while authenticating the api endpoint -> {json_body} <-\n"
                    f"{response.text}"
                )
            res = json_body.get("result")

            assert res != None
            assert isinstance(res, dict)

            authId = res.get("authorizationId")

            if authId == None or authId == "":
                raise ApiConnectorException(
                    f"There's something wrong with the api endpoint {base_url}; The code should be refactored"
                )

            api_login_url = f"{self.api_url}oauth/v3/login"

            response = requests.post(
                api_login_url,
                headers={
                    "Authorization": authId,
                    "client_id": self.client_id,
                    "Content-Type": "application/json",
                },
                data=json.dumps({"grant_type": "client_credentials"}),
            )

            json_body_login = json.loads(response.text)

            token = json_body_login.get("access_token")

            if token == None or token == "":
                raise ApiConnectorException(
                    f"Something is wrong with the SECOND called endpoint -> {api_login_url} <- \n"
                    f"RESPONSE: {response.text}"
                )

            return token

        except Exception as e:
            raise ApiConnectorException(f"Could not fetch access token -> {repr(e)}")

    def set_locales_info(self) -> None:
        """
        SHOULD BE CALLED BEFORE get_locale_id();

        Sets the map of locations based on the api response.
        """
        response = requests.get(
            f"{self.api_url}place/v1/searchOrigin",
            headers={
                "Client_id": self.client_id,
                "Access_token": self.access_token,
            },
        )

        if response.status_code != 200:
            raise ApiConnectorException(
                f"The API is unreacheable. Cannot crawl urls. -> {response.text}"
            )

        try:
            json_body = json.loads(response.text)
            assert json_body.get("success") == True
            assert json_body.get("result") != None

            self.locales_info = json_body.get("result")

        except Exception:
            raise ApiConnectorException(
                "The API response is not propertly formatted. The code needs refactoring."
            )

    def get_locale_id(self, locale: str) -> int:
        """
        returns:
            The integer id of the locale:str passed.

        args:
            locale: str -> Should be a string with the name exactly mathing those on the
            api locales_info.

        ALERT: before calling it, the set_locales_info should be called at least once.
        """
        if self.locales_info == None:
            raise ApiConnectorException(
                "Set_locales_info should be called before this function."
                "No locale id could be found"
            )

        for locale_info in self.locales_info:
            locale_id = locale_info.get("id")
            city = locale_info.get("city")

            if city == None or isinstance(locale_id, int) != True:
                raise ApiConnectorException(
                    "The current list of locales/info is invalid -> "
                    f"{self.locales_info} <- \n please, set a proper one."
                )

            if locale_info.get("city") == locale:
                return locale_id

    def _prepare_base_api_request(self) -> requests.PreparedRequest:
        """
        returns:
            a prepared request with only the base_url set and the authentication
            headers.

        ALERT:
            Should be called only when both the client_id and access_token are
            defined and valid.
        """
        req = requests.Request(
            url=self.api_url,
            headers={
                "Client_id": self.client_id,
                "Access_token": self.access_token,
                "Content-Type": "application/json",
            },
        )

        return req.prepare()

    def prepare_route_request(
        self, origin_id: int, destination_id: int, departure_date: str | datetime.date
    ) -> requests.PreparedRequest:
        """
        Returns:
            A prepared request to the sessions's api to be called later.

        Args:
            origin_id: int -> the trips origin/departure id (obtained from the
            get_locale_id method)

            destination_id: int -> the trips destination/arrival id (obtained from the
            get_locale_id method)

            departure_date: str -> a string-date formatted as YYYY-MM-DD
        """
        try:
            if not isinstance(departure_date, str):
                try:
                    departure_date = departure_date.strftime("%Y-%m-%d")
                except:
                    raise ApiConnectorException(
                        f"Cannot parse date.\n {departure_date}"
                    )

            base_req = self._prepare_base_api_request()
            base_req.prepare_method("POST")
            base_req.prepare_url(params=None, url=f"{self.api_url}route/v1/getRoutes")

            base_req.prepare_body(
                data=json.dumps(
                    {
                        "origin": origin_id,
                        "destination": destination_id,
                        "departureDate": departure_date,
                        "availability": True,
                    }
                ),
                files=None,
            )

            return base_req
        except Exception as e:
            raise ApiConnectorException(f"Could not prepare request -> {repr(e)} <-")

    def get_routes(
        self, origin_id: int, destination_id: int, departure_date: str | datetime.date
    ) -> List[Dict[str, Any]]:
        """
        Returns:
            A List[Dict[str, Any]] with all the available routes from that origin_id to
            destination_id

        Args:
            origin_id: int -> the trips origin/departure id (obtained from the
            get_locale_id method)

            destination_id: int -> the trips destination/arrival id (obtained from the
            get_locale_id method)

            departure_date: str -> a string-date formatted as YYYY-MM-DD
        """
        prepared_req = self.prepare_route_request(
            origin_id=origin_id,
            destination_id=destination_id,
            departure_date=departure_date,
        )

        session = requests.Session()

        response = session.send(prepared_req)

        session.close()

        if response.status_code != 200:
            raise ApiConnectorException(f"Could not fetch routes -> {response.text} <-")

        try:
            json_body = json.loads(response.text)
            assert json_body.get("success")

            result: Dict[str, Any] = json_body.get("result")

            assert result != None

            services: List[Dict[str, Any]] | None = result.get("servicesList")

            assert services != None

        except Exception:
            raise ApiConnectorException(
                "The response is not propertly formatted. The code needs refatorization"
            )

        return services
