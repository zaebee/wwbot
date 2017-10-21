import logging
from django.conf import settings

from eventchat.vk import VKChat
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run(*args):
    """
    """
    chat = VKChat()
    gen = chat.observe_chat()
    logger.debug('run vk bot')
    while True:
        # TODO catch TimeoutError
        try:
            next(gen)
        except StopIteration:
            gen = chat.observe_chat()
            next(gen)
