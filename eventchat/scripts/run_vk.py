import logging
from django.conf import settings

from eventchat.vk import VKChat

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO remove hard coded tokens
VK_ACCESS_TOKEN = '861765b84b9a76c19ddb6d9fbfca27e1d5fb20201ffb33f121cb35e0895f3ddbc87f4b692a71129ec5484'
AI_ACCESS_TOKEN = '490d6a1fb84141cda768a766ab1173a8'
PEER_ID = -155406641


def run(*args):
    """
    Example: `./manage.py runscript run_vk --script-args <peer_id> <vk_token> <dialog_token>`
    """
    if len(args) == 3:
        peer_id = args[0]
        vk_token = args[1]
        ai_token = args[2]
    else:
        peer_id = PEER_ID
        vk_token = VK_ACCESS_TOKEN
        ai_token = AI_ACCESS_TOKEN

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
