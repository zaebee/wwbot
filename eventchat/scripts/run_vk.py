import logging
from django.conf import settings

from eventchat.vk import VKChat
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def run(*args):
    """
    Example: `./manage.py runscript run_vk --script-args <peer_id> <vk_token> <dialog_token>`
    """
    if len(args) == 3:
        peer_id = args[0]
        vk_token = args[1]
        ai_token = args[2]

    chat = VKChat(
        peer_id=peer_id,
        vk_token=vk_token,
        ai_token=ai_token
    )
    gen = chat.observe_chat()
    logger.debug('run vk bot')
    while True:
        # TODO catch TimeoutError
        try:
            next(gen)
        except StopIteration:
            gen = chat.observe_chat()
            next(gen)
