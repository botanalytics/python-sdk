from .util import Envoy, is_valid
from concurrent.futures import ThreadPoolExecutor
import threading
import multiprocessing

class GoogleAssistant(Envoy):

    def __init__(self, debug=False, token=None, base_url='https://api.botanalytics.co/v1/',
                 callback=None, async = False):
        """
        :param debug: bool
            (default False)
        :param token: str
            Botanalytics token
        :param base_url: str
        :param callback: function
            Error callback function of format (err, reason, payload)
        """
        super(GoogleAssistant, self).__init__(debug, token, base_url, callback)
        self.__path = 'messages/google-assistant/'
        self._inform("Logging enabled for GoogleAssistant...")
        self.__async = async
        if self.__async:
            self.__number_of_workers = multiprocessing.cpu_count() * 2
            if self.__number_of_workers == 0:
                self.__number_of_workers = 2
            self.__executor_service = ThreadPoolExecutor(max_workers=self.__number_of_workers)
            self._inform("Mode: Async...")

    def log(self, req, resp):
        """
        :param req: dict
            User Payload
        :param resp: dict
            Action Payload
        :return:
        """
        validation = self.__validate(req, resp)
        if validation['ok']:
            payload = {'request': req, 'response': resp}
            self._inform('Logging messages...')
            self._inform(payload)
            if self.__async:
                self.__executor_service.submit(self._submit, payload, self.__path)
            else:
                self._submit(payload, self.__path)
        else:
            payload = {'request': req, 'response': resp}
            self._fail(validation['err'], validation['reason'], payload)

    @staticmethod
    def __validate(req, resp):
        """
        :param req:dict
            User Payload
        :param resp: dict
            Action Payload
        :return: dict
            Validation Result
        """

        pv = is_valid(req, dict, 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'user', 'userId')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'conversation', 'conversationId')
        if not pv['ok']:
            return pv
        pv = is_valid(resp, dict, 'response')
        if not pv['ok']:
            return pv
        try:
            if resp['expectUserResponse']:
                return is_valid(resp, list, 'response', 'expectedInputs')

            else:
                return is_valid(resp, dict, 'response', 'finalResponse')

        except BaseException as e:
            return {'ok': False,
                    'reason': 'Invalid response payload, expected fields are not found!',
                    'err': e
                    }

class GoogleAssistantCloudFunctions(Envoy):

    def __init__(self, debug=False, token=None, base_url='https://api.botanalytics.co/v1/',
                 async=False):
        """
        :param debug: bool
            (default False)
        :param token: str
            Botanalytics token
        :param base_url: str
        :param async: function
            Error callback function of format (err, reason, payload)
        """
        super(GoogleAssistantCloudFunctions, self).__init__(debug, token, base_url)
        self.__path = 'messages/google-assistant/'
        self._inform("Logging enabled for GoogleAssistant...")
        self.__async = async
        if self.__async:
            self._inform("Mode: Async...")

    def log(self, req, resp):
        """
        :param req: dict
            User Payload
        :param resp: dict
            Action Payload
        :return:
        """
        validation = self.__validate(req, resp)
        if validation['ok']:
            payload = {'request': req, 'response': resp}
            self._inform('Logging messages...')
            self._inform(payload)
            if self.__async:
                t = threading.Thread(target=self._submit, args=(payload, self.__path), daemon=True)
                t.start()
            else:
                self._submit(payload, self.__path)
        else:
            payload = {'request': req, 'response': resp}
            self._fail(validation['err'], validation['reason'], payload)

    @staticmethod
    def __validate(req, resp):
        """
        :param req:dict
            User Payload
        :param resp: dict
            Action Payload
        :return: dict
            Validation Result
        """

        pv = is_valid(req, dict, 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'user', 'userId')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'conversation', 'conversationId')
        if not pv['ok']:
            return pv
        pv = is_valid(resp, dict, 'response')
        if not pv['ok']:
            return pv
        try:
            if resp['expectUserResponse']:
                return is_valid(resp, list, 'response', 'expectedInputs')

            else:
                return is_valid(resp, dict, 'response', 'finalResponse')

        except BaseException as e:
            return {'ok': False,
                    'reason': 'Invalid response payload, expected fields are not found!',
                    'err': e
                    }

