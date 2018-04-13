from .util import Envoy, is_valid
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import threading



class AmazonAlexa(Envoy):

    def __init__(self, debug=False, token=None, base_url='https://api.botanalytics.co/v1/',
                 callback=None):
        """
        :param debug: bool
            (default False)
        :param token: str
            Botanalytics token
        :param base_url: str
        :param call_back: function
            Error callback function of format (err, reason, payload)
        """
        super(AmazonAlexa, self).__init__(debug, token, base_url, callback)
        self.__path = 'messages/amazon-alexa/'
        self._inform("Logging enabled for AmazonAlexa...")
        self.__number_of_workers = multiprocessing.cpu_count()
        if self.__number_of_workers == 0:
            self.__number_of_workers = 3
        self.__executor_service = ThreadPoolExecutor(max_workers=self.__number_of_workers)

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
            self.__executor_service.submit(self._submit, payload, self.__path)
        else:
            payload = {'request': req, 'response': resp}
            self._fail(validation['err'], validation['reason'], payload)

    @staticmethod
    def __validate(req, resp):
        """
        :param req:dict
            User Payload
        :param resp: dict
            Skill Payload
        :return: dict
            Validation Result
        """
        pv = is_valid(req, dict, 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, dict, 'request', 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'context', 'System', 'user', 'userId')
        if not pv['ok']:
            return pv
        pv = is_valid(resp, dict, 'response')
        if not pv['ok']:
            return pv
        return is_valid(resp, dict, 'response', 'response')

class AmazonAlexaLambda(Envoy):

    def __init__(self, debug=False, token=None, base_url='https://api.botanalytics.co/v1/',
                 async_logging=False):
        """
        :param debug: bool
            (default False)
        :param token: str
            Botanalytics token
        :param base_url: str

        :param async_logging : bool
            Log async
        """
        super(AmazonAlexaLambda, self).__init__(debug, token, base_url)
        self.__path = 'messages/amazon-alexa/'
        self._inform("Logging enabled for AmazonAlexa...")
        self.__number_of_workers = multiprocessing.cpu_count()
        self.__async_logging = async_logging

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
            if self.__async_logging:
                t = threading.Thread(target=self._submit, args=(payload, self.__path), daemon=False)
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
            Skill Payload
        :return: dict
            Validation Result
        """
        pv = is_valid(req, dict, 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, dict, 'request', 'request')
        if not pv['ok']:
            return pv
        pv = is_valid(req, str, 'request', 'context', 'System', 'user', 'userId')
        if not pv['ok']:
            return pv
        pv = is_valid(resp, dict, 'response')
        if not pv['ok']:
            return pv
        return is_valid(resp, dict, 'response', 'response')

