from __future__ import print_function
import requests
import re
import json

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


# validators url
def valid_url(url, public=False):
    result = pattern.match(url)

    if not public:
        return result

    return result and not any(
        (result.groupdict().get(key) for key in ('private_ip', 'private_host'))
    )


def is_valid(base_payload, t, name, *args):
    if base_payload is None:
        return {
            'ok' : False,
            'reason' : 'None is not accepted',
            'err' : BaseException('Payload is None!')
        }
    if args:
        key_path = ''
        temp = None
        try:
            for arg in args:
                if temp:
                    temp = temp[arg]
                    key_path += arg
                else:
                    temp = base_payload[arg]
                    key_path += arg
        except KeyError as e:
            return {
                'ok': False,
                'reason': 'Field does not exist!',
                'err': BaseException('Expected field <{}> can not be found in {}'.format(key_path+'.'+str(e)[1:-1] if key_path else str(e)[1:-1], name))
            }

        if isinstance(temp, t):
            return {'ok': True}
        else:
            return {
                'ok': False,
                'reason': 'Unexpected format!',
                'err': BaseException('Expected format for {} is {}, found {}'.format(name, t.__name__, type(temp).__name__))
            }
    else:
        if isinstance(base_payload, t):
            return {'ok': True}
        else:
            return {'ok': False,
                    'reason': 'Unexpected format!',
                    'err': BaseException('Expected format for {} is {}, found {}'.format(name, t.__name__, type(base_payload).__name__))
                    }


class Envoy(object):
    def __init__(self, debug=False, token=None, base_url='https://api.botanalytics.co/v1/',
                 callback=None):
        """
        :param debug: bool
            Enables logging (optional)
        :param token: str
            Botanalytics token (required)
        :param base_url: str
            Endpoint
        :param callback: function
            Error callback (optional)
        """
        self.__debug = debug
        self.__token = token
        self.__base_url = base_url
        self.__callback = callback
        if not valid_url(self.__base_url):
            raise ValueError("Url is not valid!")
        if not self.__token:
            raise ValueError("Token is not provided!")

    # Debug
    def _inform(self, payload):
        """
        log.debug
        :param payload: str or dict
        :return:
        """
        if self.__debug:
            if isinstance(payload, str):
                print("[Botanalytics Debug]: %s" % payload)
                return
            if isinstance(payload, dict):
                print("[Botanalytics Debug]: %s" % json.dumps(payload))

    # Error
    def _fail(self, error, reason, payload=None):
        """
        log.error
        :param error: BaseException
        :param reason: str
        :param payload: dict
        :return:
        """
        if self.__callback is not None:
            self.__callback(error, reason, payload)
        else:
            print("[Botanalytics Error]: {}, {}...\n {}".format(reason, str(error), payload))

    # Sends messages
    def _submit(self, parchment, destination="messages/generic/", word=None):
        try:
            path = self.__base_url + destination
            headers = {'Authorization': 'Token ' + self.__token}
            r = requests.post(path, headers=headers, json=parchment)
            if r.status_code == 200 or r.status_code == 201:
                if word is not None:
                    self._inform(word)
                else:
                    self._inform('Successfully logged message(s)...')
                return True
            else:
                self._fail(BaseException('Message(s) can not be logged!'), r.json(), parchment)
                return False
        except BaseException as e:
            self._fail(e, '', parchment)
            return False
