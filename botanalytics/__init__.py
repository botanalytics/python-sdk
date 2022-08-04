import os
import re
import sys
import json
import toml
import base64
import pathlib
import pkg_resources
import multiprocessing
from loguru import logger
from urllib3 import Retry
from distutils import util
import requests.status_codes
from functools import partial
from dotenv import load_dotenv
from requests_toolbelt import sessions
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor


pyproject_text = pathlib.Path('pyproject.toml').read_text()
pyproject_data = toml.loads(pyproject_text)

if 'poetry' in pyproject_data['tool']:
    __version__ = pyproject_data['tool']['poetry']['version']
else:
    __version__ = pkg_resources.get_distribution('botanalytics').version


load_dotenv()

ip_middle_octet = u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
ip_last_octet = u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
# validators url regex
regex = re.compile(
    u"^"
    u"(?:(?:https?|ftp)://)"
    u"(?:[-a-z\u00a1-\uffff0-9._~%!$&'()*+,;=:]+"
    u"(?::[-a-z0-9._~%!$&'()*+,;=:]*)?@)?"
    u"(?:"
    u"(?P<private_ip>"
    u"(?:(?:10|127)" + ip_middle_octet + u"{2}" + ip_last_octet + u")|"
    u"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + u")|"
    u"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + u"))"
    u"|"
    u"(?P<private_host>"
    u"(?:localhost))"
    u"|"
    u"(?P<public_ip>"
    u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    u"" + ip_middle_octet + u"{2}"
    u"" + ip_last_octet + u")"
    u"|"
    u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
    u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
    u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
    u")"
    u"(?::\d{2,5})?"
    u"(?:/[-a-z\u00a1-\uffff0-9._~%!$&'()*+,;=:@/]*)?"
    u"(?:\?\S*)?"
    u"(?:#\S*)?"
    u"$",
    re.UNICODE | re.IGNORECASE
)

pattern = re.compile(regex)

default_log_level = 'INFO'
default_base_url = 'https://api.botanalytics.co/v2/'
default_request_timeout = 30000
default_request_retry_limit = 10

logger.add(sys.stderr, level=default_log_level if os.getenv('BA_LOG_LEVEL') is None else os.getenv('BA_LOG_LEVEL'))

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs["timeout"]
        del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class CallbackRetry(Retry):
    def __init__(self, *args, **kwargs):
        self._callback = kwargs.pop('callback', None)
        super(CallbackRetry, self).__init__(*args, **kwargs)

    def new(self, **kw):
        # pass along the subclass additional information when creating
        # a new instance.
        kw['callback'] = self._callback
        return super(CallbackRetry, self).new(**kw)

    def increment(self, method, url, *args, **kwargs):
        if self._callback:
            self._callback(self.total)

        if 'error' in kwargs and kwargs['error'] is not None:

            logger.warning("Failed to send data.", kwargs['error'])

        return super(CallbackRetry, self).increment(method, url, *args, **kwargs)


class Base:

    def __init__(self, debug=None, api_key=None, base_url=None, channel=None,
                 is_async=None, thread_workers=0, **kwargs):

        """Client which maintains REST calls and connection to API

        :param bool debug: Enables logging (optional)
        :param str api_key: Botanalytics api key (required if not set via env variable)
        :param str base_url: URL of the api/botanalytics server(required if not set via env variable)
        :param str channel: (required)
        :param bool is_async:
        :param int thread_workers: the number of workers the client
        """

        self.debug = bool(util.strtobool(os.getenv('BA_DEBUG'))) if debug is None else debug
        self.is_async = bool(util.strtobool(os.getenv('BA_IS_ASYNC'))) if is_async is None else is_async
        self.channel = channel
        self.thread_workers = int(os.getenv('BA_THREAD_WORKERS')) if thread_workers is None else int(thread_workers)
        self.api_key = os.getenv('BA_API_KEY') if api_key is None else api_key
        self.base_url = (default_base_url if os.getenv('BA_BASE_URL') is None else os.getenv('BA_BASE_URL')) \
            if base_url is None else base_url

        # Check if channel is None
        if self.channel is None:
            raise Exception("Please set channel by passing parameters")

        # Check if api key is not set
        if not self.api_key:
            raise Exception("Please set api key either via environment variables "
                            "(`BA_API_KEY`) or by passing parameters "
                            "`api_key`")

        # Check if base url is not set
        if not self.base_url:
            raise Exception("Please set api base url either via environment variables "
                            "(`BA_BASE_URL`) or by passing parameters "
                            "`base_url`")
        # Validate base url
        if not self.validateBaseUrl():
            raise Exception('Base Url is not valid.')

        # Basic validation for API key
        self.validateApiKey()

        # Configure thread pool executor when async
        if self.is_async:

            if self.thread_workers == 0:

                number_of_workers = 2 if multiprocessing.cpu_count() * 2 == 0 else multiprocessing.cpu_count() * 2

                logger.info('Thread workers not set with is_async mode, using `cpu count * 2` number as thread worker : %s' % number_of_workers)

                self.thread_workers = number_of_workers

            self.pool = ThreadPoolExecutor(max_workers=self.thread_workers)

        request_retry_limit = (default_request_retry_limit if os.getenv('BA_REQUEST_RETRY_LIMIT')
                                                              is None else int(os.getenv('BA_REQUEST_RETRY_LIMIT'))) \
            if 'request_retry_limit' not in kwargs else int(kwargs['request_retry_limit'])

        request_timeout = (default_request_timeout if os.getenv('BA_REQUEST_TIMEOUT')
                                                      is None else int(os.getenv('BA_REQUEST_TIMEOUT'))) \
            if 'request_timeout' not in kwargs else kwargs['request_timeout']

        # Configure http client
        retries = CallbackRetry(total=request_retry_limit,
                                backoff_factor=1,
                                allowed_methods=["POST"],
                                status_forcelist=[429, 500, 502, 503, 504],
                                callback=partial(self.retry_callback, request_retry_limit))
        adapter = TimeoutHTTPAdapter(max_retries=retries, timeout=request_timeout)
        self.http = sessions.BaseUrlSession(base_url=self.base_url)
        self.http.mount("https://", adapter)

    def retry_callback(self, request_retry_limit, total):

        logger.info("Retrying sending data (attempt %d)..." % request_retry_limit - total)

    def validateBaseUrl(self, public=False):

        result = pattern.match(self.base_url)

        if not public:
            return result

        return result and not any(
            (result.groupdict().get(key) for key in ('private_ip', 'private_host'))
        )

    def validateApiKey(self):

        # Split token
        token_parts = self.api_key.split('.')

        if not token_parts or len(token_parts) < 2:

            logger.error('API key is not valid JWT.')

            raise Exception('API key is not valid JWT.')

        # Get the first part
        first_part = token_parts[1]

        # Add padding characters
        padded_first_part = first_part + "=" * divmod(len(first_part), 4)[1]

        # Convert token to string
        token_str = base64.b64decode(bytes(padded_first_part, 'utf-8')).decode('utf-8')

        token_json = None

        # Parse token string
        try:

            token_json = json.loads(token_str)

        except:

            logger.error('API key is not valid JWT.')

            raise Exception('API key is not valid JWT.')

        # Check if channel field exists
        if token_json is None or 'channel' not in token_json:

            logger.error('API key is missing a channel claim.')

            raise Exception('API key is missing a channel claim.')

        # Check if channel field matches
        if token_json['channel'] != self.channel:

            logger.error('API key does not match the client channel.')

            raise Exception('API key does not match the client channel.')

    def send_messages(self, messages=None):

        # Sanity check
        if messages is None or len(messages) == 0:

            logger.debug('Message array is empty, ignoring send request...')

            return

        # Create messages dict
        request_body_dict = dict()

        request_body_dict['messages'] = messages

        # Create a request body
        request_json = json.dumps(request_body_dict)

        headers = {}

        headers['Authorization'] = 'Bearer ' + self.api_key

        headers['Content-Type'] = 'application/json'

        headers['X-Botanalytics-Client-Id'] = 'python'

        headers['X-Botanalytics-Client-Version'] = __version__

        self.http.post('messages',
                       data=request_json,
                       headers=headers,
                       allow_redirects=False,
                       hooks={'response': self.response_hook})

    def response_hook(self, response, *args, **kwargs):

        try:

            response.raise_for_status()

        except requests.HTTPError as e:

            # Log error
            logger.error(e)

        if not requests.codes.ok <= response.status_code <= requests.codes.permanent_redirect:

            if response.status_code == requests.codes.bad_request:

                logger.warning('Request considered invalid by the API server.')

            elif response.status_code == requests.codes.unauthorized:

                logger.warning('Request considered unauthorized by the API server.')

            try:

                response_json = response.json()

                if 'errors' in response_json:
                    for error_message in response_json['errors']:
                        logger.error('Received error: %s' % error_message)

                if 'warnings' in response_json:
                    for warning_message in response_json['warnings']:
                        logger.error('Received warning: %s' % warning_message)
            except:

                logger.warning('API server responded but we failed to parse the response body.')

        elif response.status_code == requests.codes.request_timeout:

            logger.warning('Request failed due to timeout.')

        elif response.status_code == requests.codes.ok:

            try:


                data = response.json()

                # Log request ID if available
                if 'request_id' in data:
                    logger.debug('Message(s) successfully sent with the request ID \'%s\'.' % data['request_id'])

            except:

                logger.warning('API server responded but we failed to parse the response body.')
        else:

            logger.warning('Request failed due to an underlying network problem.')
