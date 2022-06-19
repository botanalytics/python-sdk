import jwt
import random
import string
import unittest

from botanalytics import Base
from botanalytics.rasa import __channel__ as __rasa_channel__
from botanalytics.universal import __channel__ as __universal_channel__

__default_base_url__ = 'https://api.botanalytics.co'

__random_secret__ = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

__api_key_with_rasa_channel__ = jwt.encode({"channel": __rasa_channel__}, __random_secret__, algorithm="HS256")

__api_key_without_channel__ = jwt.encode({}, __random_secret__, algorithm="HS256")

__api_key_with_universal_channel__ = jwt.encode({"channel": __universal_channel__}, __random_secret__, algorithm="HS256")

class BaseTest(unittest.TestCase):

    def test_missing_channel(self):

        with self.assertRaises(Exception) as context:
            Base()

        self.assertTrue('Please set channel by passing parameters' in str(context.exception))

    def test_missing_api_key(self):

        with self.assertRaises(Exception) as context:
            Base(channel=__rasa_channel__)

        self.assertTrue("Please set api key either via environment variables "
                            "(`BA_API_KEY`) or by passing parameters "
                            "`api_key`" in str(context.exception))

    def test_api_key_is_not_valid_jwt(self):

        with self.assertRaises(Exception) as context:
            Base(channel=__rasa_channel__, api_key=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)))

        self.assertTrue("API key is not valid JWT." in str(context.exception))

    def test_base_url_is_not_valid(self):

        with self.assertRaises(Exception) as context:
            Base(channel=__rasa_channel__, api_key=__api_key_with_rasa_channel__, base_url=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)))

        self.assertTrue('Base Url is not valid.' in str(context.exception))

    def test_api_key_is_missing_channel_claim(self):

        with self.assertRaises(Exception) as context:
            Base(channel=__rasa_channel__, api_key=__api_key_without_channel__)

        self.assertTrue('API key is missing a channel claim.' in str(context.exception))

    def test_api_key_does_not_match_with_client_channel(self):

        with self.assertRaises(Exception) as context:
            Base(channel=__rasa_channel__, api_key=__api_key_with_universal_channel__)

        self.assertTrue('API key does not match the client channel.' in str(context.exception))

if __name__ == '__main__':
    unittest.main()