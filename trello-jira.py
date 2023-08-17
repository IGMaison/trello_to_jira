import copy

import requests, json, pprint, re
from pathlib import Path
import datetime
import pytz
import data_tj
from dateutil import parser as dparser
from requests_oauthlib import OAuth1Session
import urllib.parse
from functools import reduce


with open('keys.json', 'r') as file:
    keys = json.load(file)

key = keys['key']
secret_key = keys['secret_key']
token = keys['token']

params_key_and_token = {'key': key, 'token': token}
board_id = '5d6e0372de8d2f14fc4b24f9'   # id доски в Трелло
path = 'D:/Sensum/Export/trello-jira/'  # Рабочая папка
path_attach = path + 'Attachments/'  # папка для приложений
t_json_file = path + 'trello_json.json'     # Файл данных, получаемых или уже полученных из Трелло
date_format = '%d/%b/%y %I:%M %p %z'
max_exist_issue_key = 0


def get_trello_info(keys, req_params={}, board_id='5d6e0372de8d2f14fc4b24f9', card_id=''):
    url = req_params.get('url', '').replace('{board_id}', board_id).replace('{board_id}', board_id).replace(
        '{card_id}', card_id)
    return requests.request('GET', url, params=keys, headers=req_params.get('headers'),
                            data=req_params.get('arguments'))


def save_req(path, req, file_name):
    with open(path + file_name, 'w') as out:
        out.write(req.text)


def get_members(trello_members: []):
    import data_tj as trd

    author: [(int, str)] = []
    executor: [(int, str)] = []
    tester: [(int, str)] = []

    for member_id in trello_members:
        if member_id in trd.author:
            author.append((trd.author[member_id], member_id))
        if member_id in trd.executor:
            executor.append((trd.executor[member_id], member_id))
        if member_id in trd.tester:
            tester.append((trd.tester[member_id], member_id))

    author.sort()
    executor.sort()
    tester.sort()

    return {'author': author[0][1] if author else '',
            'executor': executor[0][1] if executor else '',
            'tester': tester[0][1] if tester else ''}


def get_labels(trello_labels: [{}]) -> [str]:

    labels: [str] = []

    for label in trello_labels:
        labels.append(label['name'])

    return labels


def get_attachments(card_id: str) -> [{}]:
    import data_tj as trd
    attachments = get_trello_info(params_key_and_token, trd.req_params.get('attachments'),
                                  card_id=card_id).json()

    temp_attachm = {}
    for attachment in attachments:
        if attachment.get('id'):
            temp_attachm[attachment.get('id')] = attachment

    return copy.deepcopy(temp_attachm)


def get_comments(card_id: str) -> [{}]:
    import data_tj as trd
    comments = get_trello_info(params_key_and_token, trd.req_params.get('comments'),
                               card_id=card_id)
    return comments.json()


def get_actions(card_id: str) -> [{}]:
    import data_tj as trd
    return get_trello_info(params_key_and_token, trd.req_params.get('actions'),
                           card_id=card_id).json()


def create_jira_attach_file_name__(attachment_dict):

    file_extension = ''
    re_file_ext = r'.*\.(\w+$)'
    if re.match(re_file_ext, attachment_dict.get('url', '')) and attachment_dict.get('name'):

        if not re.match(re_file_ext, attachment_dict.get('name', '')) \
                or re.match(re_file_ext, attachment_dict.get('url', '')).group(1) \
                != re.match(re_file_ext, attachment_dict.get('name', '')).group(1):

            file_extension = re.match(re_file_ext, attachment_dict.get('url', '')).group(1)

    return attachment_dict.get('id', '') + \
        ('_' + attachment_dict.get('name', '').replace(' ', '_') if attachment_dict.get('fileName') else '') + \
           (file_extension and '.') + file_extension


def create_jira_attach_file_name(attachment_dict):

    return attachment_dict.get('id', '') + '_' \
           + (urllib.parse.unquote(attachment_dict.get('fileName', '')) if attachment_dict.get('fileName') else '')


def handle_card_text(text, card={}, card_relationships={}) -> str:

    for link in card.get('Link Relates', []):
        link_re = rf'\[{link}.*?]\(.+?inline\"\)'
        text = re.sub(link_re,
                      card_relationships[link],
                      text,
                      0,
                      re.UNICODE | re.MULTILINE
                      )

    for attachment_id in card.get('Вложения в тексте', []):
        if card['Вложение'].get(attachment_id) and card['Вложение'][attachment_id].get('id'):
            attachment_re = rf'!\[[^\[\]\n]*\]\(https://trello\.com/1/cards/\w+/attachments/{attachment_id}/download/.+?\.\w+\)'
            text = re.sub(attachment_re,
                          '!' + create_jira_attach_file_name(card['Вложение'][attachment_id]) + '|thumbnail!',
                          text,
                          0,
                          re.UNICODE | re.MULTILINE
                          )

    attachment_re = r'\]\(https://trello\.com/1/cards/(\w+)/attachments/(\w+)/download/.+?\.\w+(?:\)| \"‌\")'
    for attachment_id in re.finditer(attachment_re, text, re.UNICODE | re.MULTILINE):

        temp_card = None
        if card.get('Вложение', {}).get(attachment_id[2]):
            temp_card = card

        elif trello_json:
            for tj_card in trello_json:
                if tj_card.get('id', '') == attachment_id[1]:
                    temp_card = tj_card
                    break

        if temp_card and temp_card.get('Вложение', {}).get(attachment_id[2]):
            text = re.sub(attachment_re,
                          '|' + 'file://trello/' +
                          temp_card.get('shortLink', '') + ('/' if temp_card.get('shortLink', '') else '') +
                          create_jira_attach_file_name(temp_card['Вложение'][attachment_id[2]]) + ']',
                          text,
                          0,
                          re.UNICODE | re.MULTILINE
                          )

    link_re = r'(?<!\|)(https:\/\/trello\.com\/c\/\w{8})\b'
    for link in re.finditer(link_re, text, re.UNICODE | re.MULTILINE):
        text = re.sub(link_re,
                      ' ' + card_relationships[link[1]] + ' ',
                      text,
                      0,
                      re.UNICODE | re.MULTILINE
                      )

    # Списки
    if re.search(r'^>- ', text, re.UNICODE | re.MULTILINE):

        re_pars = {'^>>>>- ': '**** ', '^>>>- ': '*** ', '^>>- ': '** ', '^>- ': '* '}
        for re_par in re_pars:
            if not re.search(re_par, text, re.MULTILINE):
                continue
                
            text = re.sub(re_par,
                          re_pars[re_par],
                          text,
                          0,
                          re.UNICODE | re.MULTILINE
                          )
    # Зачёркнутый текст
    crossed_re = r'(~~ *?)([\s\S]*?)( *?~~)'
    for _ in re.findall(crossed_re,text,re.UNICODE | re.MULTILINE):
        text = re.sub(r'~~ *?',
                      '-',
                      text,
                      1,
                      re.UNICODE | re.MULTILINE
                      )
        text = re.sub(r' *?~~',
                      '-',
                      text,
                      1,
                      re.UNICODE | re.MULTILINE
                      )
    return text


def get_links_and_attachs_from_text(text) -> dict:

    attachments = {}
    links = {}

    found = re.finditer(
        r'(https://trello\.com/c/\w{8})|(?:\(https://trello\.com/1/cards/\w+/attachments/(\w+)/download/(.+?\.\w+))(?:\))',
        text,
        re.UNICODE | re.MULTILINE,
        )

    for _ in found:
        if re.match(r'(https://trello\.com/c/\w{8})', _[0], re.UNICODE | re.MULTILINE):
            links[_[0]] = ''
        else:
            attachments[_[2]] = _[3]

    return {'text': text, 'links': links, 'attachments': attachments}


def parse_labels(labels: [str]) -> (str, []):
    filtered_labels = ' '.join(map(lambda x: x.strip().replace(' ', '_'), filter(lambda x: not 'Релиз' in x, labels)))
    sprints = list(map(lambda x: x.strip().replace(' ', '_'), filter(lambda x: 'Релиз' in x, labels)))
    return filtered_labels, sprints


def get_time_by_id(_id: str) -> datetime:
    timestamp = int(_id[0:8], 16)
    return str(datetime.datetime.fromtimestamp(timestamp, tz=pytz.utc))


def create_cards_relationships(cards_json, max_exist_issue_key, proj_key='TE'):
    card_relationships = {}
    issue_key = max_exist_issue_key

    for card in cards_json:
        issue_key += 1
        card_relationships[card['shortUrl']] = proj_key + '-' + str(issue_key)

    return card_relationships


# noinspection SpellCheckingInspection
def create_jira_import_json_by_trello_data(cards):
    jira_json: [{}] = []
    print('Получение информации из карт (' + str(len(cards)) + 'шт.)...')
    cnt = 1
    arch = 0

    card: dict
    for card in cards:

        print(cnt, 'из', len(cards), '-', card['name'])
        jira_card = {}
        jira_members = get_members(card['idMembers'])
        trello_card_actions = get_actions(card['id'])

        change_date = None
        if len(trello_card_actions):
            change_date = dparser.parse(trello_card_actions[0].get('date'))
        if not change_date:
            change_date = dparser.parse(card.get('dateLastActivity', ''))
        change_date = str(change_date) if change_date else None

        jira_card['id'] = card['id']
        jira_card['shortUrl'] = card['shortUrl']
        jira_card['shortLink'] = card['shortLink']
        jira_card['closed'] = card['closed']
        jira_card['dateLastActivity'] = str(dparser.parse(card.get('dateLastActivity', '')))
        jira_card['Тема'] = card['name']
        jira_card['Ключ запроса'] = ''
        jira_card['Тип задачи'] = 'Задача'
        jira_card['Статус'] = data_tj.status.get(card['idList'], '')
        if not jira_card['Статус']:
            arch += 1
            jira_card['Статус'] = card['idList']
            print('!!!', card['name'],  jira_card['Статус'])
        jira_card['Приоритет'] = 'Medium'
        jira_card['Создатель'] = jira_members['author'] if jira_members['author'] else 'admin'
        jira_card['Автор'] = jira_card['Создатель']
        jira_card['Исполнитель'] = jira_members['executor']
        jira_card['Пользовательское поле (Тестировщик)'] = jira_members['tester']
        jira_card['Дата создания'] = get_time_by_id(card['id'])
        jira_card['Дата изменения'] = change_date if change_date else jira_card['Дата создания']
        jira_card['Метки'] = get_labels(card['labels'])
        jira_card['Описание'] = 'Эта карта импортирована из [Трелло|' + card['shortUrl'] + ']\n\n' + card['desc']
        jira_card['Вложение'] = get_attachments(card['id'])

        links_and_attachs_from_text = get_links_and_attachs_from_text(card['desc'])
        jira_card['Link Relates'] = list(links_and_attachs_from_text['links'])
        jira_card['Вложения в тексте'] = list(links_and_attachs_from_text['attachments'])

        if int(card['badges']['comments']) > 0:
            jira_card['Комментировать содержание'] = get_comments(card['id'])
            for comment in jira_card.get('Комментировать содержание', {}):
                links_and_attachs_from_text = get_links_and_attachs_from_text(
                    comment.get('data', {}).get('text', ''))
                jira_card['Link Relates'] += list(links_and_attachs_from_text['links'])
                jira_card['Вложения в тексте'] += list(links_and_attachs_from_text['attachments'])

        jira_json.append(copy.deepcopy(jira_card))
        cnt += 1

    print('arch = ', arch)

    return jira_json


def create_csv_for_jira(trello_json, max_exist_issue_key):
    # card = get_trello_info(params_key_and_token, data_tj.req_params.get('card'),  # todo off
    #                        card_id='621cba6c6cf0af216fd31d2b').json()
    # r = create_jira_import_json_by_trello_data([card])

    # with open('trello_json+.json', 'r') as file:
    #     trello_json = json.load(file)

    # for card in trello_json: # todo off
    #     for comment in card.get('Комментировать содержание', {}):
    #         links_and_attachs_from_text = get_links_and_attachs_from_text(
    #             comment.get('data', {}).get('text', ''))
    #         card['Link Relates'] += list(links_and_attachs_from_text['links'])
    #         card['Вложения в тексте'] += list(links_and_attachs_from_text['attachments'])
    #
    # with open(t_json_file, 'w') as file:
    #     json.dump(trello_json, file)

    cards_relationships = create_cards_relationships(trello_json, max_exist_issue_key)

    cnt_attach = 0
    cnt_link_relates = 0
    cnt_comments = 0
    cnt_sprints = 0
    sprints_found = set()

    # count some fields
    for card in trello_json:
        card_labels, card_sprints = parse_labels(card.get('Метки', ''))
        sprints_found.update(card_sprints)
        cnt_sprints = max(cnt_sprints, len(card_sprints))
        cnt_attach = max(cnt_attach, len(card.get('Вложение', '')))
        cnt_link_relates = max(cnt_link_relates, len(card.get('Link Relates', '')))
        cnt_comments = max(cnt_comments, len(card.get('Комментировать содержание', '')))
        card['Ключ запроса'] = cards_relationships[card['shortUrl']]

    # check that sprint lists are right
    if sprints_found - set(data_tj.sprints):
        print('Не хватает этих спринтов в таблице соответствия data_tj.sprints:')
        print(*(sprints_found - set(data_tj.sprints)), sep='\n')
        input('Выполнение прервано')
        exit()

    csv_for_jira = []
    jira_string = \
        ['Тема',
         'Ключ запроса',
         'Тип задачи',
         'Статус',
         'Приоритет',
         # 'Создатель',
         'Автор',
         'Исполнитель',
         'Пользовательское поле (Тестировщик)',
         'Дата создания',
         'Дата изменения',
         'Метки'] + \
        ['Sprint'] * cnt_sprints + \
        ['Описание'] + \
        ['Вложение'] * cnt_attach + \
        ['Link Relates'] * cnt_link_relates + \
        ['Комментировать содержание'] * cnt_comments +\
        ['Исправить в версии'] * cnt_sprints

    jira_string = '"' + '","'.join(map(str, jira_string)) + '"'
    csv_for_jira.append(jira_string)
    cnt = 0
    for card in trello_json:
        # cnt += 1
        # if cnt not in range(1800, 1810):   #todo off
        #     continue

        labels, sprints = parse_labels(card.get('Метки', ''))

        jira_string = \
            [handle_card_text(card['Тема']),
             card['Ключ запроса'],
             card['Тип задачи'],
             card['Статус'],
             card['Приоритет'],
             # data_tj.members.get(card.get('Создатель', ''), ''),
             data_tj.members.get(card.get('Автор', ''), ''),
             data_tj.members.get(card.get('Исполнитель', ''), ''),
             data_tj.members.get(card.get('Пользовательское поле (Тестировщик)', ''), ''),
             dparser.parse(card['Дата создания']).strftime(date_format),
             dparser.parse(card['Дата изменения']).strftime(date_format),
             labels] + \
            list(map(lambda x: data_tj.sprints.get(x, ''), sprints)) + [''] * (cnt_sprints - len(sprints)) + \
            [handle_card_text(card['Описание'], card, cards_relationships)] + \
            list(map(lambda x: dparser.parse(card.get('Вложение', {}).get(x, {}).get('date', '')).strftime(  # Вложение
                date_format) + ';' +
                               str(data_tj.members.get(card.get('Вложение', {}).get(x, {}).get('idMember', ''),
                                                       '')) + ';' +
                               create_jira_attach_file_name(card.get('Вложение', {}).get(x, {})) + ';' +
                               'file://trello/' +
                               str(card.get('shortLink', '')) + ('/' if card.get('shortLink', '') else '') +
                               create_jira_attach_file_name(card.get('Вложение', {}).get(x, {})),
                     list(card.get('Вложение', {})))) + \
            [''] * (cnt_attach - len(card.get('Вложение', ''))) + \
            list(map(lambda x: cards_relationships.get(x, ''), card.get('Link Relates', ['']))) + [''] * (  # Link Relates
                    cnt_link_relates - len(card.get('Link Relates', ''))) + \
            list(map(lambda x: dparser.parse(x.get('date', '')).strftime(date_format) + ';' +               # Комменты
                               data_tj.members.get(x.get('idMemberCreator', ''), '') + ';' +
                               handle_card_text(x.get('data', {}).get('text', ''), card, cards_relationships),
                     card.get('Комментировать содержание', []))) \
            + [''] * (cnt_comments - len(card.get('Комментировать содержание', ''))) + \
            sprints + [''] * (cnt_sprints - len(sprints))   # Исправить в версии

        jira_string = '"' + '","'.join(map(lambda x: str(x).replace('"', '""'), jira_string)) + '"'
        csv_for_jira.append(jira_string)

    return csv_for_jira


def save_attachment_file(binary_file_content, full_file_name):
    with open(full_file_name, 'wb') as out:
        out.write(binary_file_content)


def download_card_attachment(card, path_attach=path_attach):

    print('\nСкачивание', len(card['Вложение']), 'приложений карты:', card['Тема'])
    file_path = path_attach + 'trello/' + card['shortLink'] + '/'
    if not Path(path_attach + 'trello/').exists():
        Path.mkdir(Path(path_attach + 'trello/'))
    if not Path(path_attach + 'trello/' + card['shortLink']).exists():
        Path.mkdir(Path((path_attach + 'trello/' + card['shortLink'])))

    err = {'cnt': 0}
    for attachment_id in card['Вложение']:

        attachment = card['Вложение'][attachment_id]
        end_file_name = create_jira_attach_file_name(attachment)
        file_name = file_path + end_file_name

        if not Path(file_name).exists():
            try:
                save_attachment_file(get_attachment_file(attachment['url']), file_name)
                print(end_file_name)
                err['cnt'] += 1
            except Exception as e:
                print('!!! - ошибка:', str(e), '\nНе удалось записать вложение', end_file_name)
                err[attachment_id] = '!!! - ошибка:', str(e), '\nНе удалось записать вложение', file_name
        else: print(end_file_name, '---- уже есть.')

    return err


def get_attachment_file(url):
    return OAuth1Session(key, secret_key, token).get(url).content


def actualise_trello_json(trello_json, fresh_cards):
    t_json_ids: dict = {}
    new_cards = []
    for card in trello_json:
        t_json_ids[card['id']] = dparser.parse(card.get('dateLastActivity', ''))
    for card in fresh_cards:
        if not t_json_ids.get(card.get('id'), ''):
            new_cards.append(card)
        elif dparser.parse(card.get('dateLastActivity', '')) > t_json_ids.get(card.get('id')):
            new_cards.append(card)

    new_cards = create_jira_import_json_by_trello_data(new_cards)

    for new_card in new_cards:
        used = False
        for card in range(len(trello_json)):
            if trello_json[card]['id'] == new_card['id']:
                trello_json[card] = new_card
                used = True
                break
        if not used:
            trello_json.append(new_card)


def save_trello_json(trello_json, t_json_file=t_json_file):

    print('Идёт запись...')
    try:
        with open(t_json_file, 'w') as file:
            json.dump(trello_json, file)
            print('Записано!')
    except Exception as e:
        print(t_json_file, str(e))
    try:
        with open('text_trello_json.json', 'w') as file:
            file.write(str(trello_json))
            print('Записано!')
    except Exception as e:
        print('text_trello_json.json не удалось сохранить', str(e))


if __name__ == '__main__':

    # comments = get_trello_info(params_key_and_token, data_tj.req_params.get('comments')).json()

    # Скачивание информации для сопоставления
    # labels = get_trello_info(params_key_and_token, data_tj.req_params.get('labels'))
    # save_req(path, labels, 'labels')
    # members = get_trello_info(params_key_and_token, data_tj.req_params.get('members'))
    # save_req(path, members, 'members')
    # lists = get_trello_info(params_key_and_token, data_tj.req_params.get('lists'))
    # save_req(path, lists, 'lists')

    print('Получение данных из скачанного ранее файла...')
    trello_json = None

    if Path(t_json_file).exists():
        try:
            with open(t_json_file, 'r') as file:
                trello_json = json.load(file)
        except:
            print('Проблема с файлом ', t_json_file)

    else:
        print('\nФайл не найден!')

    if not trello_json or input('\nПолучить карты из трелло (иначе будут взяты из ранее скачанного файла)? (Да - любой символ) >'):

        print('Получение списка карт...\n')
        cards = get_trello_info(params_key_and_token, data_tj.req_params.get('cards')).json()

        if not trello_json or trello_json and input('\nАктуализировать имеющийся файл или скачать всё заново? (Заново - любой символ) >'):
            if not trello_json:
                print('Так как файл данных не найден, производится полная закачка данных.')

            trello_json = create_jira_import_json_by_trello_data(cards)
        else:
            actualise_trello_json(trello_json, cards)

        if input('\nCохранить информацию с карт трелло в файл trello_json.json? (Да - любой символ) >'):
            save_trello_json(trello_json)

    if not trello_json:
        print('Не удалось получить данные!')
        exit()

    if input('\nПроизвести закачку всех приложений из карт? (Да - любой символ) >'):

        if not Path(path_attach).exists():
            Path.mkdir(Path(path_attach))
            print('Создана папка для файлов приложений', Path(path_attach).absolute())
        else:
            print('Файлы приложений будут помещены в папку', Path(path_attach).absolute())

        cnt_at = 0
        cnt_dnl_at = 0
        at_errs = {}
        for card in trello_json:
            print('\nКарта', cnt_at, 'из', len(trello_json), ':')

            if len(card['Вложение']):
                at_err = download_card_attachment(card)
                if at_err:
                    at_errs |= at_err
                    cnt_dnl_at += at_err.get('cnt', 0)
            cnt_at += 1

        at_errs.pop('cnt', None)
        print('\n=============================   Файлов:', cnt_at)
        print('\n=============================   Из них дополнительно скачано:', cnt_dnl_at)
        print('\n=============================   Ошибки при сохранении файлов: \n')
        pprint.pprint(at_errs)

    print('\nФормирование csv файла для Jira...')
    csv_for_jira = create_csv_for_jira(trello_json, max_exist_issue_key)

    if input("\nСохранить в " + path + "csv_for_jira? (Да - лбюбой символ) >"):

        print('\nНачалось сохранение....')

        with open(path + 'csv_for_jira.csv', 'w', encoding='utf-8') as file:
            file.write('\n'.join(csv_for_jira))

        print('\nГотово!')

    else:
        pprint.pprint(csv_for_jira)
