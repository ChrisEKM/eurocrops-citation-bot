import logging
import time
from dataclasses import dataclass
from typing import Optional

import yaml
from telegram import update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


from citation_counter import BASE_URL, get_latest_citation_count
from keys import TELEGRAM_BOT_SECRET


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


INTERVAL_S = 3600 * 4
USER_CONFIG_PATH = "user_config.yml"


@dataclass
class UserConfig():
    username = 'username'
    first_name = 'first_name'
    is_subscribed = 'is_subscribed'
    last_cite_count = 'last_cite_count'
    last_notified = 'last_notified'


def get_subscribed_users() -> dict:
    """
    Retrieves the users currently subscribed to the bot

    Returns
    -------
    dict
        dict of subscribed users
    """
    with open(USER_CONFIG_PATH, 'r') as config:
        res = yaml.safe_load(config)
    return res if res else dict()


def add_new_user_to_config(user: "TelegramUserObject") -> None:
    """
    Adds the newly subscribed user to the user config

    Parameters
    ----------
    user_id
        uuid of the newly subscribed user
    """
    new_user_data = {
        UserConfig.username: user['username'],
        UserConfig.first_name: user['first_name'],
        UserConfig.is_subscribed: True,
        UserConfig.last_cite_count: 0,
        UserConfig.last_notified: 0
    }
    existing_users = get_subscribed_users()
    with open(USER_CONFIG_PATH, 'w') as config:
        existing_users[user['id']] = new_user_data
        yaml.dump(existing_users, config)
        logger.info(f"Added new user {user['id']} to config")


def check_citations(context: CallbackContext) -> None:
    """
    Fetches the latest citation count and, if necessary, sends a message to the relevant 
    subscribed user

    Parameters
    ----------
    context
        telegram CallbackContext
    """
    users = get_subscribed_users()
    job = context.job
    cites = get_latest_citation_count(BASE_URL)
    logger.info(users)

    for user in users.keys():
        logger.info(f"Attempting to fetch citations for {user}")
        if (
            users.get(user).get(UserConfig.is_subscribed) and 
            cites > users.get(user).get(UserConfig.last_cite_count)
        ):
            context.bot.send_message(job.context, "Your citation count changed!!")
            context.bot.send_message(job.context, f"Latest citation count: {cites}")
            logger.info(f"Updated citation count for user: '{user}' - new count: {cites}")
        else:
            logger.info(f"No change to citation count for user: '{user}'")



def start_callback(update: Updater, context: CallbackContext) -> None:
    """
    Entry-point for the bot. When a new user calls the relevant command, adds them to the
    subscribed users and sends them a welcome message.

    Parameters
    ----------
    update
        telegram Updater object

    context
        telegram CallbackContext
    """
    user = update.message.from_user
    logger.info(f"User requested start: {user.first_name}")
    logger.info(user)
    current_users = get_subscribed_users()
    if current_users:
        is_existing_user = user['id'] in current_users.keys()

    msg = f"Welcome back {user.first_name}! I'll let you know when you get any new citations"
    if not current_users or not is_existing_user:
        msg = f"Hallo {user.first_name}! Let me fetch a first citation count for you.."
        add_new_user_to_config(user)
    update.message.reply_text(msg)
    add_user_job(update, context)


def cancel_callback(update: Updater, context: CallbackContext) -> None:
    """
    Callback that removes both the job from the queue and the user from receiving messages

    Parameters
    ----------
    update
        telegram Updater object
    context
        telegram CallbackContext
    """
    # TODO: This looks to remove the job, and NOT the user. Should probably update this just
    # to update the relevant config
    user = update.message.from_user
    logger.info(f"User '{user}' cancelled the subscription")
    remove_job_if_exists(update.message.chat_id, context)
    update.message.reply_text(f"You've unsubscribed :(")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """
    Removes a job with the given name
    """
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def add_user_job(update: Updater, context: CallbackContext) -> None:
    """Add a polling job to the queue."""
    chat_id = update.message.chat_id

    job_removed = remove_job_if_exists(str(chat_id), context)
    if not job_removed:
        context.job_queue.run_once(check_citations, 5, context=chat_id, name=str(chat_id) + "_now")
    context.job_queue.run_repeating(check_citations, INTERVAL_S, context=chat_id, name=str(chat_id))
    logger.info(f"Successfully added job for {chat_id}")


def run():
    CURRENT_CITATION_COUNT = 0
    updater = Updater(TELEGRAM_BOT_SECRET)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('citeme', start_callback))
    dispatcher.add_handler(CommandHandler('cancel', cancel_callback))
    updater.start_polling()
    updater.idle()

