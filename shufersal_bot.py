import glob
import gzip
import logging
import os
import shutil
import requests
import xmltodict
from bs4 import BeautifulSoup
from telegram.ext import Updater, MessageHandler, Filters

TOKEN=''
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def download_new_file(delete_xmls=True, store_id='371'):
    if delete_xmls:
        files_to_delete = glob.glob(os.path.join('.', "*.xml"))
        for f in files_to_delete:
            os.remove(f)
            logger.info('deleted ' + f)
    url = "http://prices.shufersal.co.il/FileObject/UpdateCategory?catID=2&storeId=" + store_id
    response = requests.get(url)
    data = response.text

    soup = BeautifulSoup(data, features="html.parser")
    tags = soup.find_all('a', href=True)
    download_link = ''
    for tag in tags:
        if '.gz' in tag.get('href'):
            download_link = tag.get('href')

    logger.info('about to download ' + download_link)
    r = requests.get(download_link)
    gz_file_name = (os.path.basename(download_link.split('?')[0]))
    logger.info('archive name is ' + gz_file_name)
    with open(gz_file_name, 'wb') as f:
        f.write(r.content)

    with gzip.open(gz_file_name, 'rb') as f_in:
        with open(gz_file_name.replace('gz', 'xml'), 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(gz_file_name)


def send_reply(bot, update):
    if update.message.text.isdigit():
        item_code = update.message.text
    else:
        logger.warning('item code must be numbers only')
        return
    for item in list_of_items:
        if item['ItemCode'].endswith(item_code):
            update.message.reply_text('{}\n{}\n{}'.format(item['ItemCode'], item['ItemName'], item['ItemPrice']))
            return
    update.message.reply_text('item not found')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def open_file():
    files_list = (glob.glob('*.xml'))
    if not files_list:
        logger.warning("can't find the xml")
        return
    else:
        file_name = files_list[0]
        logger.info('using ' + file_name)

    with open(file_name, 'r', encoding="utf8") as f:
        xml_string = f.read()
    j = xmltodict.parse(xml_string)
    global list_of_items
    list_of_items = j['root']['Items']['Item']


def main():
    download_new_file()
    open_file()
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text, send_reply))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
