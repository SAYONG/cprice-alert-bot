from decimal import Decimal
from telegram.ext import Updater, CommandHandler
import logging
import os

from bx_client import recent_trades

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi! Use /set <THB> to tracking you\'re prefered exchange rate')


def send_rate_notification(bot, job):
    rate = recent_trades()
    tracking_rate = Decimal(job.context['tracking_rate'])
    diff = tracking_rate - rate
    if abs(diff) < 2000:
        chat_id = job.context['chat_id']
        message = 'BEWARE!!! Current exchange rate is {} THB, diff is {} THB'.format(rate, diff)
        bot.send_message(chat_id, text=message)


def set_rate(bot, update, args, job_queue, chat_data):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the interested exchange rate in THB
        rate = args[0]

        # Add job to queue
        context = {'chat_id': chat_id, 'tracking_rate': rate}
        job = job_queue.run_repeating(send_rate_notification, 5, context=context)
        chat_data['job'] = (rate, job)

        update.message.reply_text('Exchange rate now tracking!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <THB>')


def unset(bot, update, chat_data):
    """Remove the job if the user changed their mind."""
    if 'job' not in chat_data:
        update.message.reply_text('You have no tracking exchange rate!')
        return

    _, job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']

    update.message.reply_text('Exchange rate successfully unset!')


def rate(bot, update, chat_data):
    """Get current tracking exchange rate."""
    if 'job' not in chat_data:
        update.message.reply_text('You have no tracking exchange rate!')
        return

    due, _ = chat_data['job']

    reply_message = 'You\'re tracking on ETH with rate {} THB'.format(due)
    update.message.reply_text(reply_message)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Run bot."""
    key = os.getenv('BOT_KEY')
    updater = Updater(key)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("set", set_rate,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))
    dp.add_handler(CommandHandler("rate", rate, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
