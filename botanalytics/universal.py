from . import Base

__channel__ = "universal"


class Universal(Base):

    def __init__(self, debug=None, api_key=None, base_url=None, is_async=None,
                 thread_workers=0, **kwargs):
        """
        :param bool debug: Enables logging (optional)
        :param str api_key: Botanalytics api key (required)
        :param str base_url: URL of the api/botanalytics server (required)
        :param bool is_async: Whether client use async workers (optional)
        :param thread_workers: the number of workers the client (optional)
        """
        super(Universal, self).__init__(debug, api_key=api_key, base_url=base_url, channel=__channel__,
                                        is_async=is_async, thread_workers=thread_workers, **kwargs)

    def log_message(self, message):

        self.log_messages([message])

    def log_messages(self, messages):

        if self.is_async:

            self.pool.submit(self.send_messages, messages)
        else:

            self.send_messages(messages=messages)
