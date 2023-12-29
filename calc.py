import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

domain = 'https://kingscross.f-rpg.me'
subforums = [10,11,9]
user_name = 'Raphael'
cookie = {'mybb_ru': ''}
time = '2023-11-01 20:14:00'
before = 100
currency_dict = {
    "one": "билет",
    "two": "билета",
    "five": "билетов",
    "pricelist": [{
        "min": 0,
        "max": 5000,
        "price": 1
    },
{
        "min": 5001,
        "max": 10000,
        "price": 2
    },
{
        "min": 10001,
        "max": 15000,
        "price": 3
    },
{
        "min": 15001,
        "price": 4
    }]
}

def find_last_page(domain, subforum, user_name, cookie):
    url = domain + '/search.php?action=search&keywords=&author=' + user_name + '&forum=' + str(
        subforum) + '&search_in=0&sort_dir=DESC&show_as=posts&topics=&p=1'
    html = requests.get(url, cookies=cookie)
    soup = BeautifulSoup(html.text, 'html.parser')
    last_page = 1
    links = soup.find("div", {"class": "pagelink"})
    if links is None:
        return last_page

    links = links.find_all('a')
    for link in links:
        t = link.text
        if t.isnumeric() and int(t) > last_page:
            last_page = int(t)
    return last_page


def get_posts(domain, subforums, user_name, cookie, start_time_str, currency_dict):
    format = '%Y-%m-%d %H:%M:%S'
    topics = {}
    posts = []
    start_time = datetime.strptime(start_time_str, format)

    for subforum in subforums:
        last_page = find_last_page(domain, subforum, user_name, cookie)

        for n in range(1, (last_page + 1)):
            url = domain + '/search.php?action=search&keywords=&author=' + user_name + '&forum=' + str(subforum) + '&search_in=0&sort_dir=DESC&show_as=posts&topics=&p=' + str(n)
            html = requests.get(url, cookies=cookie)
            soup = BeautifulSoup(html.text, 'html.parser')
            for post in soup.find_all('div', {'class': 'post'}):
                header_links = post.find('h3').find_all('a')

                href = header_links[2]['href']
                topic_title = header_links[1].text

                post_time = datetime.strptime(convert_date_string(header_links[2].text), format)
                if post_time < start_time:
                    break

                topic_id = int(header_links[1]['href'].split('=')[1])
                if topic_id not in topics:
                    topics[topic_id] = get_topic_start_post(domain, topic_id)

                post_id = int(header_links[2]['href'].split('#p')[1])
                if post_id != topics[topic_id]:

                    text = post.find('div', {'class': 'post-content'}).text
                    number, price, currency = calculate_currency(text, currency_dict)

                    posts.append({
                        'topic_id': topic_id,
                        'post_id': post_id,
                        'number':  number,
                        'href': href,
                        'topic_title': topic_title,
                        'price': price,
                        'currency': currency
                    })
    return posts

def get_topic_start_post(domain, topic_id):
    url = domain+'/api.php?method=topic.get&topic_id='+str(topic_id)+'&fields=init_post'
    text = requests.get(url, cookies=cookie).text
    j = json.loads(text)
    return int(j['response'][0]['init_id'])


def convert_date_string(date_string):
    if 'Сегодня' in date_string:
        today = datetime.today().strftime('%Y-%m-%d')
        date_string = date_string.replace('Сегодня', today)

    if 'Вчера' in date_string:
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        date_string = date_string.replace('Вчера', yesterday)
    return date_string


def calculate_currency(text, currency_dict):
    number = len(text)

    for p in currency_dict['pricelist']:
        if 'max' not in p:
            p['max'] = 1000000000000000000
        if p['min'] < number < p['max']:
            price = p['price']

    if price % 10 == 1:
        currency = currency_dict['one']
    else:
        if 1 < price % 10 < 5:
            currency = currency_dict['two']
        else:
            currency = currency_dict['five']
    return number, price, currency


def format_message(posts, before):
    message = ''
    total = 0
    for post in posts:
        total += post['price']
        message += 'пост '+str(post['number'])+' символов — '+str(post['price']) + ' ' + post['currency'] +' [[url='+post['href']+']'+post['topic_title']+'[/url]]'+"\n"
    new_total = before + total
    message += 'Итого в профиле: '+str(before)+' + '+str(total)+' = ' + str(new_total)
    return message



posts = get_posts(domain, subforums, user_name, cookie, time, currency_dict)
print(format_message(posts, before))
