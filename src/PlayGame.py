import ClueDo
from PyInquirer import prompt

if __name__ == '__main__':

    # input the players participating in the game
    players = prompt([{
        'type': 'checkbox',
        'name': 'players',
        'message': 'Which characters are playing?',
        'choices': [{'name': char} for char in ClueDo.ClueGame.characters],
    }])

    # ensure that 3 or more players are selected
    while len(players['players']) < 3:
        players = prompt([{
            'type': 'checkbox',
            'name': 'players',
            'message': 'Please choose between 3 and 6 characters',
            'choices': [{'name': char} for char in ClueDo.ClueGame.characters],
        }])

    # input which character is to be controlled by the computer
    my_char = prompt([{
        'type': 'list',
        'name': 'my_char',
        'message': 'Which character will I be playing?',
        'choices': [{'name': char} for char in players['players']]
    }])

    # input the cards to be used by the computer
    my_cards = prompt([{
        'type': 'checkbox',
        'name': 'my_cards',
        'message': 'What are my cards?',
        'choices': [{'name': char} for char in ClueDo.ClueGame.all_cards]
    }])

    # ensure that exactly 3 cards are inputted
    while len(my_cards['my_cards']) != 3:
        my_cards = prompt([{
            'type': 'checkbox',
            'name': 'my_cards',
            'message': 'Please select exactly 3 cards',
            'choices': [{'name': char} for char in ClueDo.ClueGame.all_cards]
        }])

    # initialise instance of the class
    game_instance = ClueDo.ClueGame(players['players'], my_char['my_char'], my_cards['my_cards'])

    # begin the game
    game_instance.start_game()