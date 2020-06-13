import argparse
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import requests
import time
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
key = 'ncaA7h_sFa889VF09J3APCLmamwwTOVzuzzgX6hCGgS'

ifttt_webhook_url = 'https://maker.ifttt.com/trigger/{}/with/key/'+key


def get_latest_bitcoin_price():
    # coinmarketcap api url
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'e95c1590-a40a-4135-8b3e-00469f91eb61',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url)
    # getting the json data
        data = json.loads(response.text)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    print("BTC Price", float(data['data'][0]['quote']['USD']['price']))
    return float(data['data'][0]['quote']['USD']['price'])


# requesting the notification from IFTTT
def post_ifttt_webhook(event, value):
    # The payload that will be sent to IFTTT service
    data = {'value1': value}
    # inserts our desired event
    ifttt_event_url = ifttt_webhook_url.format(event)
    # Sends a HTTP POST request to the webhook URL
    requests.post(ifttt_event_url, json=data)
    print("IFTTT", ifttt_event_url)


def customize_btc_data(bts_data):
    rows = []
    for bit_price in bts_data:
        # Formats the date into a string: '26.03.2020 19:09'
        date = bit_price['date'].strftime('%d.%m.%Y %H:%M')
        new_price = bit_price['price']
        # <b> (bold) tag creates bolded text
        # 26.03.2020 19:09: $<b>6877.4</b>
        row = f'{date}: $<b>{new_price}</b>'
        rows.append(row)

        # Use a <br> (break) tag to create a new line
        # Join the rows delimited by <br> tag: row1<br>row2<br>row3
    return '<br>'.join(rows)


def run(bitcoin_threshold, time_gap, email):
    bts_data = []
    threshold = float(bitcoin_threshold[0])
    intervals = float(time_gap[0])
    while True:
        new_price = get_latest_bitcoin_price()
        date = datetime.now()
        bts_data.append({'date': date, 'price': round(new_price)})
        # for emergency notification
        if new_price < threshold:
            post_ifttt_webhook('bitcoin_price_emergency', round(new_price))
            emergency_update(email, round(new_price))
            # for Telegram notification
        # Once we have 1 items in our list send an update
        if len(bts_data) == 1:
            post_ifttt_webhook('Bitcoin_Price_Update',
                               customize_btc_data(bts_data))
            # Reset the history
            bts_data = []

        # Time gap as you want
        time.sleep(intervals)


# this is is command line utility function, that takes the argument,
# parse it ans then call the run function
def main():
    parser = argparse.ArgumentParser(description="Bitcoin price tracker")
    # command line variable for time gap
    parser.add_argument("-i", "--interval", type=int, nargs=1,
                        metavar="interval", default=[1],
                        help="Time interval in minutes")
    # command line variable for threshold
    parser.add_argument("-t", "--threshold", type=int, nargs=1,
                        metavar="threshold", default=[7000],
                        help="Threshold in USD")
    new_args = parser.parse_args()
    email = input('Enter your email')
    print('Running Application with time interval of ',
          new_args.interval[0], ' and threshold = $',  new_args.threshold[0])
    # calls the run function
    run(new_args.threshold,  new_args.interval, email)


def emergency_update(email, price):
    recipent_email_address = email

    msg = MIMEMultipart()

    password = 'jrzonnwtbdhmpwrh'
    msg['From'] = 'ghimirerahul@gmail.com'
    msg['To'] = recipent_email_address

    message = f"""From:ghimirerahul@gmail.com
To: {email}
Subject:BTC Price Below Threshold
BTC Price crossed below Threshold\n
Current Price: {price} ,\n
Buy Or Sell Now.\n
Regards Rahul Ghimire
"""

    # Stablishing the gmail sever to send mails
    server = smtplib.SMTP('smtp.gmail.com: 587')

    server.starttls()

    # Login using gmail account
    server.login(msg['From'], password)

    # sending the mail
    server.sendmail(msg['From'], msg['To'], message.encode('utf-8'))

    server.quit()

    print('Emergency Update Sent\n\n')


if __name__ == '__main__':
    main()
