from . import Base

__channel__ = "rasa"


class Rasa(Base):

    def __init__(self, debug=None, api_key=None, base_url=None, is_async=None,
                 thread_workers=0, **kwargs):
        """
        :param bool debug: Enables logging (optional)
        :param str api_key: Botanalytics api key (required)
        :param str base_url: URL of the api/botanalytics server (required)
        :param bool is_async: Whether client use async workers (optional)
        :param thread_workers: The number of workers the client (optional)
        """
        super(Rasa, self).__init__(debug, api_key=api_key, base_url=base_url, channel=__channel__,
                                   is_async=is_async, thread_workers=thread_workers, **kwargs)

    @classmethod
    async def from_endpoint_config(
            cls, broker_config
    ):
        if broker_config is None:
            return None
        return cls(**broker_config.kwargs)

    def publish(self, event):

        # Create messages list
        messages = list()

        message_dict = dict()

        message_dict['message'] = event

        messages.append(message_dict)

        if self.is_async:

            self.pool.submit(self.send_messages, messages)
        else:

            self.send_messages(messages)
