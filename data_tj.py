status = {
    '5e2ad1a2f5a41f5ca3888468': 'To Do',  # 'BackLog'
    '5d6e03dc865b3b65237b5db8': 'To Do',  # 'To Do'
    '5d6e03e9cf2a230f9f9cc201': 'In Progress',  # 'In Progress'
    '62f6590646e42f475f623935': 'CodeReview',  # 'Review'
    '5d6e03f58d5c810e4ec2d5e9': 'Testing',  # 'Test'
    '5d6e04358dfe3537badeba79': 'ReadyForTesting',  # 'ReadyForRealese'
    '624d732e0f740d03d18d81bc': 'Done (Готово)',  # 'Realese

    '5d6e043bb00f7c3c33526ca9': 'Done (Готово)',  # 'Done',
    '602428d3cf33e43a01c653b2': 'Done (Готово)',  # 'Done',
    '60561771f7f21c0649776658': 'To Do',  # 'ToDoPlan',
    '6023ff7093faf76153171a74': 'To Do',   # 'HOTFIX',
    '605e0f225f607c0898bd1ef4': 'CodeReview',  # 'Debug',
    '5d6e0419649bc147f8993568': 'CodeReview',  # 'Debug',
    '624d72f5293c060377656c8c': 'Done (Готово)',  # 'Actualize TD',
    '602bc3cbf3598f5b12c9831f': 'Testing',    # 'RealeseTest'
}

members = {
    '61658c63c981d14347d12b5a': 'lina', 
    '5efef6a12c2fcc71dffe4a75': 'igor9561', 

}

author = {
    '5fb377e424a99d4ad95deac3': 1,  # 'smirnov'
    '63a1b0898d421501b4150a8a': 2,  # 'Issak'
}

executor = {
    '5fb377e424a99d4ad95deac3': 1,  # 'smirnov'
    '63a1b0898d421501b4150a8a': 2,  # 'Issak'
}

tester = {
    '5fb377e424a99d4ad95deac3': 1,  # 'smirnov'
    '63a1b0898d421501b4150a8a': 2,  # 'Issak'
}

sprints = {
    'Релиз_21.01.2022': 178,
    'Релиз_13.01.2023': 148,
}

headers = {
    "Accept": "application/json",
}

req_params = {
    'comments-': {
        'type': 'comments',
        'url': 'https://trello.com/1/boards/{board_id}/actions?filter=commentCard&limit=1000',
        'headers': headers,
        'argument----s': {'fields': ['data']}
    },
    'comments': {
        'type': 'comments',
        'url': 'https://api.trello.com/1/cards/{card_id}/actions?filter=commentCard',
        'headers': headers,
        'arguments': {'fields': ['id', 'date', 'data', 'idMemberCreator']}
    },
    'cards': {
        'type': 'cards',
        'url': 'https://api.trello.com/1/boards/{board_id}/cards/all',
        'headers': headers,
        'arguments': {'fields': ["id", 'idShort', 'name', 'dateLastActivity', 'shortUrl', 'desc', 'idList', 'idMembers',
                                 "labels", 'shortLink', 'badges', 'closed']}
    },
    'card': {
        'type': 'card',
        'url': 'https://api.trello.com/1/cards/{card_id}/',
        'headers': headers,
        'arguments': {'fields': ["id", 'idShort', 'name', 'dateLastActivity', 'shortUrl', 'desc', 'idList', 'idMembers',
                                 "labels", 'shortLink', 'badges', 'closed']}
    },
    'actions': {
        'type': 'card',
        'url': 'https://api.trello.com/1/cards/{card_id}/actions',
        'headers': headers,
    },
    'labels': {
        'type': 'labels',
        'url': 'https://api.trello.com/1/boards/{board_id}/labels?limit=1000',
        'headers': headers,
        'arguments': {'fields': ["name"]}
    },
    'members': {
        'type': 'members',
        'url': 'https://api.trello.com/1/boards/{board_id}/members',
        'headers': headers
    },
    'lists': {
        'type': 'lists',
        'url': 'https://api.trello.com/1/boards/{board_id}/lists/all',
        'headers': headers,
        'arguments': {'fields': ["name"]}
    },
    'attachments': {
        'type': 'attachments',
        'url': "https://api.trello.com/1/cards/{card_id}/attachments",
        'headers': headers,
        'arguments': {'fields': ['id', 'date', 'idMember', 'name', 'fileName', 'url']}
    }
}
