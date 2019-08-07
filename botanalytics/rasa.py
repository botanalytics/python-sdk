from .util import Envoy, is_valid
import multiprocessing
from concurrent.futures import ThreadPoolExecutor


class Rasa(Envoy):

    def __init__(self, debug=False, token=None, base_url='http://localhost:8080/v1/',
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
        super(Rasa, self).__init__(debug, token, base_url, callback)
        self.__path = "rasa/messages/"
        self.__async = async
        self._inform("Debugging enabled for Rasa...")
        self.last_action_dict = {}
        self.last_slot_dict = {}
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
        self._inform('Logging message...')
        self._inform(payload)
        if self.__async:
            self.__executor_service.submit(self._submit, payload, self.__path)
        else:
            self._submit(payload, self.__path)
            



    @classmethod
    def from_endpoint_config(
        cls, broker_config
    ):
        if broker_config is None:
            return None
        return cls(token=broker_config.kwargs.pop("api_token"),**broker_config.kwargs)

    def publish(self, event):
        if event['event'] == 'user':
            if event['sender_id'] in self.last_slot_dict:
                event['slot'] = self.last_slot_dict[event['sender_id']] 
                self.last_slot_dict.pop(event['sender_id'], None)
            self.log(event)
        elif event['event'] == 'bot':
            if event['sender_id'] in self.last_action_dict:
                event['action'] = self.last_action_dict[event['sender_id']]
                self.last_action_dict.pop(event['sender_id'], None)
            self.log(event)
        elif event['event'] == 'agent':
            self.log(event)
        elif event['event'] == 'action':
            self.last_action_dict[event['sender_id']] = event
        elif event['event'] == 'slot':
            self.last_slot_dict[event['sender_id']] = event
