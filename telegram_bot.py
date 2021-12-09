import logging
import time
import yaml
from enum import Enum

from keys import TELEGRAM_BOT_SECRET
from telegram import update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


from citation_counter import get_latest_citation_count


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

INTERVAL_S = 3600 * 2
USER_CONFIG_PATH = "user_config.yml"


class UserConfig(Enum):
    is_subscribed = 'is_subscribed'
    last_cite_count = 'last_cite_count'
    last_notified = 'last_notified'


def get_subscribed_users() -> dict:
    with open(USER_CONFIG_PATH, 'r') as config:
        res = yaml.safe_load(config)
    return res


def add_new_user_to_config(username) -> None:
    new_user_data = {
        UserConfig.is_subscribed: True,
        UserConfig.last_cite_count: 0,
        UserConfig.last_notified: 0
    }
    existing_users = get_subscribed_users()
    with open(USER_CONFIG_PATH, 'w') as config:
        existing_users[username] = new_user_data
        yaml.dump(existing_users, USER_CONFIG_PATH)
        logger.info(f"Added {username} to config")


def check_citations(context: CallbackContext) -> None:
    users = get_subscribed_users()
    job = context.job
    cites = get_latest_citation_count()

    for user in users.keys():
        if (
            user.get(UserConfig.is_subscribed.value) and 
            cites > user.get(UserConfig.last_cite_count.value)
        ):
            context.bot.send_message(job.context, "Your citation count changed!!")
            context.bot.send_message(job.context, f"Latest citation count: {cites}")
            logger.info(f"Updated citation count for user: '{user}' - new count: {cites}")
        else:
            logger.info(f"No change to citation count for user: '{user}'")



def start_callback(update: Updater, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"User requested start: {user.first_name}")
    logger.info(user)
    update.message.reply_text(
        f"Halloooooo {user.first_name}! I'll let you know when you get any new citations!"
    )
    update.message.reply_text(
        f"You can send a `/cancel` to stop me talking :) (But I know you won't do that)"
    )
    add_user_job(update, context)


def cancel_callback(update: Updater, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"User '{user}' cancelled the subscription")
    remove_job_if_exists(update.message.chat_id, context)
    update.message.reply_text(f"You've unsubscribed :(")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
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


if __name__ == '__main__':
    CURRENT_CITATION_COUNT = 0
    updater = Updater(TELEGRAM_BOT_SECRET)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('citeme', start_callback))
    dispatcher.add_handler(CommandHandler('cancel', cancel_callback))
    updater.start_polling()
    updater.idle()

