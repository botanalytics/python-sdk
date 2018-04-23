from .util import Envoy, is_valid
import multiprocessing
from concurrent.futures import ThreadPoolExecutor


class Generic(Envoy):

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
        super(Generic, self).__init__(debug, token, base_url, callback)
        self._inform("Logging enabled for Generic...")
        self.__async = async
        if self.__async:
            self.__number_of_workers = multiprocessing.cpu_count() * 2
            if self.__number_of_workers == 0:
                self.__number_of_workers = 2
            self.__executor_service = ThreadPoolExecutor(max_workers=self.__number_of_workers)
            self._inform("Mode: Async...")

    def log(self, payload):
        """
        :param payload: dict
                 Payload
        :return:
        """
        validation = self.__validate(payload)
        if validation['ok']:
            self._inform('Logging message...')
            self._inform(payload)
            if self.__async:
                self.__executor_service.submit(self._submit, payload)
            else:
                self._submit(payload)
        else:
            self._fail(validation['err'], validation['reason'], payload)

    @staticmethod
    def __validate(payload):
        """
        :param payload:dict
            payload
        :return: dict
            Validation Result
        """

        pv = is_valid(payload, dict, 'payload')
        if not pv['ok']:
            return pv
        pv = is_valid(payload, bool, 'payload', 'is_sender_bot')
        if not pv['ok']:
            return pv
        pv = is_valid(payload, str, 'payload', 'user', 'id')
        if not pv['ok']:
            return pv
        pv = is_valid(payload, str, 'payload', 'user', 'name')
        if not pv['ok']:
            return pv
        pv = is_valid(payload, str, 'payload', 'message', 'text')
        if not pv['ok']:
            return pv
        return is_valid(payload, int, 'payload', 'message', 'timestamp')
