import datetime
import requests
import logging
import json
from typing import Dict, List
from request_generator import ApiRoutesRequestGenerator

challenge_list_of_trips = [
    {"São Paulo (Rod. Tietê)": "Belo Horizonte"},
    {"Belo Horizonte": "São Paulo (Rod. Tietê)"},
    {"São Paulo (Rod. Tietê)": "Ribeirão Preto"},
    {"Ribeirão Preto": "São Paulo (Rod. Tietê)"},
    {"São Paulo (Rod. Tietê)": "Curitiba"},
    {"Curitiba": "São Paulo (Rod. Tietê)"},
    {"Rio de Janeiro (Novo Rio)": "Belo Horizonte"},
    {"São Paulo (Rod. Barra Funda)": "São José do Rio Preto (Rodoviária)"},
    {"São José do Rio Preto (Rodoviária)": "São Paulo (Rod. Barra Funda)"},
    {"Rio de Janeiro (Novo Rio)": "Campinas"},
]


def validate_api_response(response: requests.Response) -> Dict[str, bool | str]:
    """
    params:
        response: a request.Response object from a api call defined in the
        ApiConnector. More spefically, it validates if a getRoutes called
        was succesfull.

    returns:
        {
        "success": (True|False),
        "msg": (string with message),
        }
    """

    if response.status_code == 401:
        return {"success": False, "msg": "Could not authenticate to the endpoint"}

    if response.status_code == 200:
        try:
            json_body = json.loads(response.text)
            assert json_body.get("success") == True
            return {"success": True, "msg": ""}

        except:
            return {
                "success": False,
                "msg": "Response's body could not be json converted or "
                "it did not got the expected params",
            }

    else:
        return {
            "success": False,
            "msg": f"Could not reach end point.\n STATUS: {response.status_code}\n"
            f"BODY: {response.text}",
        }


def main() -> None:
    # ApiConnector interface initialization/auth
    req_gen = ApiRoutesRequestGenerator()

    date = datetime.datetime.now()

    print("Started crawling.")

    # 7 days range.
    for _ in range(0, 8):
        req_gen.add_trips(
            challenge_list_of_trips, departure_date=date.strftime("%Y-%m-%d")
        )
        date = datetime.timedelta(days=1) + date

    print("Added all routes to the queue.")

    # with open("./trips.json", "w") as file:
    #     try:
    #         file.write(json.dumps(req_gen.trips))
    #     except Exception as e:
    #         logging.warning(f"could not parse\n{req_gen.trips}")

    # generates all of the requests
    req_gen.generate_requests()

    # start requests session to make all of the
    # api calls.
    session = requests.Session()

    responses: List[requests.Response] = []

    print("Starting requests.")

    for request in req_gen.requests:
        responses += [session.send(request)]
        print("Completed another request.")

    print("Finished requests")

    session.close()

    valid_responses: List[requests.Response] = []
    invalid_responses: List[requests.Response] = []

    print("Filtering responses")
    for resp in responses:
        is_valid_dict = validate_api_response(resp)

        if is_valid_dict.get("success"):
            valid_responses += [resp]
            continue

        # gives a friendly warning to all the requests
        # that did not completed normally
        invalid_responses += [resp]
        logging.warning(
            f"Invalid call: STATUS: \n{resp.status_code} \n" f"BODY: {resp.text}"
        )

    output_valid = []
    output_invalid = []

    # stores the good and bad responses separately
    for invalid_res in valid_responses:
        trip = json.loads(invalid_res.text)
        trip["collect_at"] = {
            "timezone": "UTC",
            "datetime": datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%s"
            ),
        }
        output_valid += [trip]

    for invalid_res in invalid_responses:
        trip = {
            "response.body": invalid_res.text,
            "response.code": invalid_res.status_code,
        }
        trip["collect_at"] = {
            "timezone": "UTC",
            "datetime": datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%s"
            ),
        }
        output_invalid += [trip]

    filepath_valid = "./result_api.json"
    filepath_invalid = "./result_api_invalid.json"

    print("writing to response.json")
    with open(filepath_valid, "w") as file:
        try:
            file.write(json.dumps(output_valid))
        except Exception as e:
            logging.warning(f"could not parse\n{repr(e)}")
            file.write(str(output_valid))

    print(f"The output has been written to {filepath_valid}")

    print("writing to response_invalid.json")
    with open(filepath_invalid, "w") as file:
        try:
            file.write(json.dumps(output_invalid))
        except Exception as e:
            logging.warning(f"could not parse\n{repr(e)}")
            file.write(str(output_valid))

    print("Done.")


if __name__ == "__main__":
    main()
