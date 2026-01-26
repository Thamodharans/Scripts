import time
import requests
from termcolor import cprint


class TrendsFetcher:
    def __init__(self, timeout=(10, 90), api_key=None):
        self.timeout = timeout
        self.api_key = api_key
        self.token_payload = {}
        self.api_base_url = "https://www.searchapi.io/api/v1/search"
        
        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })


    def fetch_related_queries(self, q, tz=420, cat=0, timeframe='today 12-m', geo='', gprop=''):
        """
        Fetch related queries with retries and backoff.
        This is network-safe and SaaS-safe.
        """

        payload = {
            'q': q,
            'data_type': 'RELATED_QUERIES',
            'cat': cat,
            'geo': geo,
            'tz': tz,
            'gprop': gprop,
            'time': timeframe,
            'engine': 'google_trends'
        }

        MAX_RETRIES = 3
        BACKOFF_SECONDS = 5

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    self.api_base_url,
                    params=payload,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    response_data = response.json()

                    if 'related_queries' in response_data and isinstance(response_data['related_queries'], dict):
                        return {
                            'top': response_data['related_queries'].get('top', None),
                            'rising': response_data['related_queries'].get('rising', None)
                        }

                    return {'top': None, 'rising': None}

                # Non-200 but not network failure
                raise Exception(
                    f"API error {response.status_code}: {response.text}"
                )

            except requests.exceptions.ReadTimeout:
                if attempt == MAX_RETRIES:
                    raise Exception("SearchAPI timed out after retries")

                time.sleep(BACKOFF_SECONDS * attempt)

            except requests.exceptions.ConnectionError:
                if attempt == MAX_RETRIES:
                    raise Exception("SearchAPI connection failed after retries")

                time.sleep(BACKOFF_SECONDS * attempt)