from .util import Envoy, is_valid
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import time

class FacebookMessenger(Envoy):
    def __init__(self, debug=False, token=None, fb_token=None, base_url='https://api.botanalytics.co/v1/', callback=None, async = False):
        """
        :param debug: bool
            To enable logging
        :param token: str
            Botanalytics token
        :param fb_token: str
            Facebook token (optional)
        :param base_url: str
        :param callback: function
            Error callback of format (err, reason, payload)
        """
        super(FacebookMessenger, self).__init__(debug, token, base_url, callback)
        self.__fb_token = fb_token
        self.__path = "messages/facebook-messenger/"
        self.__profile_path = "facebook-messenger/users/"
        self.__async = async
        self._inform("Debugging enabled for Facebook...")
        if self.__async:
            self.__number_of_workers = multiprocessing.cpu_count() * 2
            if self.__number_of_workers == 0:
                self.__number_of_workers = 2
            self.__executor_service = ThreadPoolExecutor(max_workers=self.__number_of_workers)
            self._inform("Mode: Async...")

    def log_incoming(self, message):
        """
        Logs incoming message
        :param message: dict
            Incoming message
        :return:
        """
        validation = self.__validate(message, "Incoming message")
        if validation['ok']:
            payload = {
                'recipient': None,
                'timestamp': int(time.time()*1000),
                'message': message
            }
            self._inform("Logging incoming message...")
            self._inform(message)
            if self.__async:
                self.__executor_service.submit(self._submit, payload, self.__path)
            else:
                self._submit(payload, self.__path)
        else:
            self._fail(validation['err'], validation['reason'], message)

    def log_outgoing(self, message, sender_id):
        """
        Logs outgoing message
        :param message: dict
            Outgoing message payload
        :param sender_id: str
            Sender id
        :return:
        """
        validation = self.__validate_outgoing(message, sender_id)
        if validation['ok']:
            payload = {
                'recipient': sender_id,
                'timestamp': int(time.time()*1000),
                'message': message,
                'fb_token': self.__fb_token
            }
            self._inform("Logging outgoing message...")
            self._inform(message)
            if self.__async:
                self.__executor_service.submit(self._submit, payload, self.__path)
            else:
                self._submit(payload, self.__path)
        else:
            self._fail(validation['err'], validation['reason'], message)

    def log_user_profile(self, message):
        """
        Logs user profile
        :param message: dict
            User profile
        :return:
        """
        validation = self.__validate(message, "User profile")
        if validation['ok']:
            self._inform("Logging user profile message...")
            self._inform(message)
            if self.__async:
                self.__executor_service.submit(self._submit, message, self.__profile_path)
            else:
                self._submit(message, self.__profile_path)
        else:
            self._fail(validation['err'], validation['reason'], message)

    @staticmethod
    def __validate(payload, name):
        return is_valid(payload, dict, name)

    @staticmethod
    def __validate_outgoing(message, sender_id):
        mv = is_valid(message, dict, "Outgoing message")
        if not mv['ok']:
            return mv
        return is_valid(sender_id, str, "Sender id")