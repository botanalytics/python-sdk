from .util import Envoy, is_valid
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import time
import requests


class SlackRTMApi(Envoy):
    def __init__(self, debug=False, token=None, slack_client_instance=None, base_url='https://api.botanalytics.co/v1/',
                 callback=None):
        """
        :param debug: bool
            Enables logging
        :param token: str
            Botanalytics token
        :param slack_client_instance:
            Slack client instance
        :param base_url:

        :param callback:
        """
        super(SlackRTMApi, self).__init__(debug=debug, token=token, base_url=base_url, callback=callback)
        self.__base_url = base_url
        self.__path = 'messages/slack/'
        self.__initialize_path = 'bots/slack/initialize/'
        self.__activeUserId = None
        self.__activeTeamId = None
        self.__executor_service = ThreadPoolExecutor(max_workers=2)
        self._inform('Logging enabled for SlackRTMApi...')
        if slack_client_instance is None:
            raise ValueError('Slack instance is not provided!')
        self.__slack_client = slack_client_instance
        # Start fetching
        self.__executor_service.submit(self.__initialize)

    def __initialize(self):
        wait_interval = 2
        update_interval = 3600
        form = {'token': self.__slack_client.token}
        while True:
            try:
                r = requests.post('https://slack.com/api/rtm.start', data=form)
                if r.status_code == 200 or r.status_code == 201:
                    data = r.json()
                    if not data['ok']:
                        time.sleep(wait_interval)
                        wait_interval += 3
                        continue
                    self.__activeUserId = data['self']['id']
                    self.__activeTeamId = data['team']['id']
                    if not self._submit(data, self.__initialize_path, "Successfully updated bot '{}' info...".format(data['self']['name'])):
                        time.sleep(wait_interval)
                        wait_interval += 3
                    else:
                        time.sleep(update_interval)
                        wait_interval = 2
            except BaseException as e:
                self._fail(e, 'Unknown. Bot could not be initialized.')

    def log_incoming(self, payload):
        """
        :param payload: dict
            Message payload

        :return:
        """
        if self.__activeTeamId is None or self.__activeUserId is None:
            self._fail(BaseException('team and bot'), 'Missing info')
            return

        validation = self.__validate(payload)
        if validation['ok']:
            self._inform('Logging message...')
            payload['is_bot'] = False
            payload['team'] = self.__activeTeamId
            self._inform(payload)
            self.__executor_service.submit(self._submit, payload, self.__path)
        else:
            self._inform("Message does not contain 'type' field. Ignoring...")
            self._inform(payload)

    def log_outgoing(self, channel, message, thread=None, reply_broadcast=None, msg_payload=None):

        if self.__activeTeamId is None or self.__activeUserId is None:
            self._fail(BaseException('team and bot'), 'Missing info')
            return

        if msg_payload is not None:
            if self.__activeTeamId is None or self.__activeUserId is None:
                self._fail(BaseException('team and bot'), 'Missing info')
            if not isinstance(msg_payload, dict):
                self._fail(BaseException('Expected format for msg_payload is dict found {}'.format(type(msg_payload).__name__)),
                           'Unexpected payload format!')
                return
            msg = msg_payload.copy()
            validation = self.__validate(msg)
            if validation['ok']:
                msg['is_bot'] = True
                msg['ts'] = str(int(time.time() * 1000) / 1000)
                msg['team'] = self.__activeTeamId
                msg['user'] = self.__activeUserId
                self._inform('Logging message...')
                self._inform(msg)
                self.__executor_service.submit(self._submit, message, self.__path)
            else:
                self._inform("Message does not contain 'type' field. Ignoring...")
                self._inform(msg_payload)
                return
        found_channel = self.__slack_client.server.channels.find(channel)
        channel_id = found_channel.id if found_channel else channel
        payload = {"type": "message", "channel": channel_id, "text": message}
        if thread is not None:
            payload["thread_ts"] = thread
            if reply_broadcast:
                payload['reply_broadcast'] = True
        payload['is_bot'] = True
        payload['ts'] = str(int(time.time()*1000)/1000)
        payload['team'] = self.__activeTeamId
        payload['user'] = self.__activeUserId
        self._inform('Logging message...')
        self._inform(payload)
        self.__executor_service.submit(self._submit, payload, self.__path)

    @staticmethod
    def __validate(payload):
        return is_valid(payload, str, 'msg_payload', 'type')


class SlackEventApi(Envoy):
    def __init__(self, debug=False, token=None, slack_token=None, base_url='https://api.botanalytics.co/v1/',
                 callback=None):
        """
        :param debug: bool
            Enables logging
        :param token: str
            Botanalytics token
        :param slack_token:
            Slack token
        :param base_url:

        :param callback:
        """
        super(SlackEventApi, self).__init__(debug=debug, token=token, base_url=base_url, callback=callback)
        self.__path = 'messages/slack/event/'
        self.__initialize_path = 'bots/slack/initialize/'
        self.__interactive_path = 'messages/slack/interactive/'
        self.__number_of_workers = multiprocessing.cpu_count()
        if self.__number_of_workers == 0:
            # +1 for initialize update
            self.__number_of_workers = 3
        self.__executor_service = ThreadPoolExecutor(max_workers=self.__number_of_workers)
        self._inform('Logging enabled for SlackEventApi...')
        if slack_token is None:
            raise ValueError('Slack token is not provided!')
        self.__slack_token = slack_token
        # Start fetching
        self.__executor_service.submit(self.__initialize)

    def __initialize(self):
        wait_interval = 2
        update_interval = 3600
        form = {'token': self.__slack_token}
        while True:
            try:
                r = requests.post('https://slack.com/api/rtm.start', data=form)
                if r.status_code == 200 or r.status_code == 201:
                    data = r.json()
                    if not data['ok']:
                        time.sleep(wait_interval)
                        wait_interval += 3
                        continue
                    self.__activeUserId = data['self']['id']
                    self.__activeTeamId = data['team']['id']
                    if not self._submit(data, self.__initialize_path, "Successfully updated bot '{}' info...".format(data['self']['name'])):
                        time.sleep(wait_interval)
                        wait_interval += 3
                    else:
                        time.sleep(update_interval)
                        wait_interval = 2
            except BaseException as e:
                self._fail(e, 'Unknown. Bot could not be initialized.')

    def log(self, payload):
        """
        :param payload: dict
            Message payload

        :return:
        """
        try:
            if payload['challenge']:
                return
        except BaseException:
            pass

        validation = self.__validate(payload)
        if validation['ok']:
            self._inform('Logging message...')
            self._inform(payload)
            type_name = payload['type']
            if type_name == "interactive_message":
                self.__executor_service.submit(self._submit, payload, self.__interactive_path)
            elif type_name == "event_callback":
                self.__executor_service.submit(self._submit, payload, self.__path)
            else:
                self._fail(
                    BaseException('Expected types, [interactive_message, event_callback] but found {}'.format(type_name)),
                    'New event type, contact us < tech@botanalytics.co >',
                    payload
                )
        else:
            self._inform("Message does not contain 'type' field. Ignoring...")

    @staticmethod
    def __validate(payload):
        return is_valid(payload, str, 'payload', 'type')
