import ClueDo
from PyInquirer import prompt

players = prompt([{
    'type': 'checkbox',
    'name': 'players',
    'message': 'Which characters are playing?',
    'choices': [{'name': char} for char in ClueDo.ClueGame.characters],
}])

while len(players['players']) < 3:
    players = prompt([{
        'type': 'checkbox',
        'name': 'players',
        'message': 'Please choose between 3 and 6 characters',
        'choices': [{'name': char} for char in ClueDo.ClueGame.characters],
    }])

my_char = prompt([{
    'type': 'list',
    'name': 'my_char',
    'message': 'Which character will I be playing?',
    'choices': [{'name': char} for char in players['players']]
}])

my_cards = prompt([{
    'type': 'checkbox',
    'name': 'my_cards',
    'message': 'What are my cards?',
    'choices': [{'name': char} for char in ClueDo.ClueGame.all_cards]
}])

while len(my_cards['my_cards']) != 3:
    my_cards = prompt([{
        'type': 'checkbox',
        'name': 'my_cards',
        'message': 'Please select exactly 3 cards',
        'choices': [{'name': char} for char in ClueDo.ClueGame.all_cards]
    }])

game_instance = ClueDo.ClueGame(players['players'], my_char['my_char'], my_cards['my_cards'])

game_instance.start_game()