import numpy as np
import time
import networkx as nx
import os
from PyInquirer import prompt
from Board_graph import board_graph

class ClueGame:
    
    characters = {'Colonel Mustard', 'Miss Scarlett', 'Mrs Peacock', 'Dr Orchid', 'Rev Green', 'Prof Plum'}
    weapons = {'Rope', 'Dagger', 'Wrench', 'Revolver', 'Candlestick', 'Lead Pipe'}
    locations = {'Kitchen', 'Dining Room', 'Lounge', 'Hall', 'Study', 'Library', 'Billiard Room', 'Conservatory', 'Ballroom'}
    secret_passage_locations = {'Lounge', 'Conservatory', 'Study', 'Kitchen'}
    non_secret_passage_locations = {'Dining Room', 'Hall', 'Library', 'Billiard Room', 'Ballroom'}
    all_cards = characters.union(weapons, locations)
    char_starting_positions = {'Colonel Mustard': 66, 'Miss Scarlett': 4, 'Mrs Peacock': 145, 'Dr Orchid': 196, 'Rev Green':95, 'Prof Plum': 28}
    room_locations = {'Kitchen': 194, 'Dining Room': 87, 'Lounge': 5, 'Hall': 3, 'Study': 1, 'Library': 82, 'Billiard Room': 109, 'Conservatory': 186, 'Ballroom': 190}
    possible_clue_cards = {'Specific card reveal', 'Choice card reveal', 'Secret passage', 'Player movement', 'Positional reveal', 'All reveal', 'Choice player reveal'}

    # initialize with a set of characters, my character, and the cards we are dealt
    def __init__(self, players, my_char, my_cards):
        assert all([player in ClueGame.characters for player in players])
        self.players = players
        self.my_char = my_char
        self.other_players = [player for player in players if player != my_char]
        self.my_cards = my_cards
        # dictionary for storing knowledge about other players' cards: -1 means they do not have the card, 1 means they do, 0 is ambiguous
        self.game_state = {player: {card: 1 if card in self.my_cards and player == my_char
                                    else -1 if card in self.my_cards and player != my_char
                                    else 0 for card in ClueGame.all_cards} 
                           for player in self.players}
        # dictionary for tracking possible cards for each player in each round, based on what they show
        self.possible_cards = {player: {} for player in self.players}
        # location on the board
        self.position = ClueGame.char_starting_positions[self.my_char]
        # cards that could be inside of the envelope
        self.possible_characters = ClueGame.characters
        self.possible_weapons = ClueGame.weapons
        self.possible_locations = ClueGame.locations
        # turn tracker
        self.current_turn = 0
        self.current_round = 0
        self.game_is_active = True
        # update possible guesses to start the game
        self.update_possible_guesses()
        
    # function that asks for input and loops until the input is present in the viable card list
    @staticmethod
    def card_input(viable_card_list, input_message, error_message):
        input = prompt({
            'type': 'list',
            'name': 'selection',
            'message': input_message,
            'choices': [{'name': card} for card in viable_card_list],
            'validate': lambda answer: error_message if answer not in viable_card_list else True
        })
        card = input['selection']
        return card
        
    # function that returns false if we know that any player has the card
    def is_card_possible(self, card):
        card_scores = [self.game_state[player][card] for player in self.game_state]
        return all([score != 1 for score in card_scores])
            
    # function for scoring a card based on current knowledge (i.e. how many players do not hold it for certain)
    def score_card(self, card):
        card_scores = [self.game_state[player][card] for player in self.game_state]
        return sum(card_scores)
    
    # use score_card to find best card from a list
    def find_best_card(self, card_list):
        card_scores = {card: self.score_card(card) for card in card_list if self.is_card_possible(card)}
        best_card = min(card_scores, key = lambda card: card_scores[card])
        return best_card
    
    # functin for updating the game state after we know that a player has a card
    def rule_out_card(self, player, card):
        for single_player in self.game_state:
            self.game_state[single_player][card] = 1 if single_player == player else -1
        if player == self.my_char:
            self.my_cards.remove(card)
            
    # function for making a suggestion on our turn
    def get_top_suggestions(self):
        
        char_scores = {}
        weapon_scores = {}
        location_scores = {}
        
        # for each card of each type, score the card and save to the dictionary
        for character in ClueGame.characters:
            if self.is_card_possible(character):
                char_scores[character] = self.score_card(character)
        
        for weapon in ClueGame.weapons:
            if self.is_card_possible(weapon):
                weapon_scores[weapon] = self.score_card(weapon)
        
        for location in ClueGame.locations:
            if self.is_card_possible(location):
                location_scores[location] = self.score_card(location)
                 
        # find the card(s) in each category with the minimum score
        top_char = min(char_scores, key = lambda char: char_scores[char])
        top_weapon = min(weapon_scores, key = lambda weapon: weapon_scores[weapon])
        top_location = min(location_scores, key = lambda location: location_scores[location])
        
        return top_char, top_weapon, top_location
    
    # function for calculating distances to each room from current position
    def get_path_lengths(self):
        
        path_lengths =  {room: nx.shortest_path_length(board_graph, self.position, ClueGame.room_locations[room]) for room in ClueGame.room_locations}  
        return path_lengths
    
    # function for moving on the board, towards or into the best room 
    def move_on_board(self, dice_roll):

        # Calculate distances to each room from current position
        path_lengths = self.get_path_lengths()
        
        # Get scores for each room 
        room_scores = {room: self.score_card(room) for room in ClueGame.locations if self.is_card_possible(room)}
   
        # Filter rooms further away than dice roll
        possible_rooms = [key for key in room_scores if path_lengths[key] <= dice_roll]

        # If no rooms are reachable in this turn, move to a square on the way to closest room
        if len(possible_rooms) == 0:
            
            # Find the rooms that are still uneliminated, and return those that are closest
            dist_to_closest_viable_room = min([path_lengths[key] for key in room_scores])
            possible_rooms = [key for key in room_scores if path_lengths[key] == dist_to_closest_viable_room]
            # Pick one of these close and viable rooms at random and move to it
            # by finding shortest path to closest room and moving as far along it as dice roll will allow
            closest_room = np.random.choice(possible_rooms,size=1)[0]
            new_location = nx.shortest_path(board_graph, self.position, self.room_locations[closest_room])[dice_roll]
            return new_location, closest_room

        # If more than one possible, close room same distance apart, pick one at random and move to it
        elif len(possible_rooms) > 1:
            
            best_possible_room_score = min([room_scores[room] for room in possible_rooms])
            best_possible_rooms = [room for room in possible_rooms if room_scores[room] == best_possible_room_score]
            # Move to closest room at random
            room = np.random.choice(best_possible_rooms, size=1)[0]
            new_location = self.room_locations[room]
            return new_location, room

        # If only one room available, move to it
        else:
            room = possible_rooms[0]
            new_location = self.room_locations[possible_rooms[0]]
            return new_location, room
        
    def which_player_showed_card(self, card):
        
        character = prompt([{
            'type': 'list',
            'name': 'selection',
            'message': 'Which player showed the card? If none, select None',
            'choices': [{'name': card} for card in self.other_players + ['None']],
        }])
        if character['selection'] == 'None':
            if card in self.players:
                self.possible_characters = {card}
            elif card in self.weapons:
                self.possible_weapons = {card}
            elif card in self.locations:
                self.possible_locations = {card}
        else:
            self.rule_out_card(character['selection'], card)
            self.update_possible_cards(character['selection'])
        
    def clue_card(self, whose_turn, dice_roll):
            
        # get the type of clue card being shown
        clue_card_type = ClueGame.card_input(ClueGame.possible_clue_cards, 'Please choose which type of clue card has been shown.',
                                             'That\'s not a valid type of clue card. Trust me, we looked through all of them.')
        # if it is a specific card reveal, take in the specific card and update the game state
        if clue_card_type == 'Specific card reveal':
            card_shown = ClueGame.card_input(self.all_cards, 'Please enter which card is to be revealed.', 'That doesn\'t look like anything to me...')
            if card_shown in self.my_cards:
                if card_shown in ClueGame.characters:
                    print('Here is {}'.format(card_shown))
                    time.sleep(3)
                else:
                    print('Here is the {}.'.format(card_shown))
                    time.sleep(3)
                self.rule_out_card(self.my_char, card_shown)
            else:
                self.which_player_showed_card(card_shown)
            
        # if the card says to choose a card to reveal, choose the top card   
        elif clue_card_type == 'Choice card reveal':
            if whose_turn == self.my_char:
                type_of_choice_reveal = ClueGame.card_input({'Suspect', 'Weapon', 'Location'}, 'Please enter which type of card is to be revealed.', 'That is not a valid type of card')
                print('Hmmm, what\'s the best card to choose...')
                if type_of_choice_reveal == 'Suspect':
                    best_card = self.find_best_card(ClueGame.characters)
                elif type_of_choice_reveal == 'Weapon':
                    best_card = self.find_best_card(ClueGame.weapons)
                elif type_of_choice_reveal == 'Location':
                    best_card = self.find_best_card(ClueGame.locations)
                time.sleep(1)
                print('If anyone has {}, please show it.'.format(best_card))
                time.sleep(5)
                self.which_player_showed_card(best_card)
            else:
                suggested_card = ClueGame.card_input(self.all_cards, 'Please enter which card was suggested.', 'That doesn\'t look like anything to me...')
                self.which_player_showed_card(suggested_card)    
                
        # if the card is a secret passage card       
        elif clue_card_type == 'Secret passage':
            # if it's our turn, make a passage to the lowest scoring room
            if whose_turn == self.my_char:
                # if we are in a room with a secret passage
                if self.position in [loc for room, loc in ClueGame.room_locations.items() if room in ClueGame.secret_passage_locations]:
                    # find best room that does not have a passage
                    best_room = self.find_best_card(ClueGame.non_secret_passage_locations)
                # if we are not in a room with a secret passage
                elif self.position in [loc for room, loc in ClueGame.room_locations.items() if room not in ClueGame.secret_passage_locations]:
                    # make a passage from the current room
                    best_room = ClueGame.room_locations[self.position]
                # if we are not in a room, find possible rooms
                elif self.position not in [loc for room, loc in ClueGame.room_locations.items()]:
                    path_lengths = self.get_path_lengths()
                    # Get scores for each room 
                    room_scores = {room: self.score_card(room) for room in ClueGame.locations if self.is_card_possible(room)}
                    possible_rooms = [room for room in room_scores if path_lengths[room] <= dice_roll]
                    # if any possible rooms are secret passage rooms, make a passage to the room with the best score
                    if any([room in ClueGame.secret_passage_locations for room in possible_rooms]):
                        best_room = self.find_best_card(ClueGame.non_secret_passage_locations)
                    # else if all possible rooms are not secret passage locations (and there are possible rooms), find the best one
                    elif len(possible_rooms) >= 1:
                        best_room = self.find_best_card(possible_rooms)
                    # else if there are not any possible rooms, choose to put the passage in the closest room that could still be in the envelope
                    else:
                        path_lengths_non_passage_rooms = {room: path_length for room, path_length in path_lengths.items() if room in ClueGame.non_secret_passage_locations and self.is_card_possible(room)}
                        print(path_lengths_non_passage_rooms)
                        best_room = min(path_lengths_non_passage_rooms, key = lambda room: path_lengths_non_passage_rooms[room])
                print('Let\'s make a passage through the {}'.format(best_room))
                for secret_passage_room in ClueGame.secret_passage_locations:
                    board_graph.add_edge(ClueGame.room_locations[secret_passage_room], ClueGame.room_locations[best_room])
            else:
                chosen_room = ClueGame.card_input(ClueGame.locations, 'Please enter which room {} would like to connect to the secret passages.'.format(whose_turn)
                                                  , 'That\'s not a valid room.')
                for secret_passage_room in ClueGame.secret_passage_locations:
                    board_graph.add_edge(ClueGame.room_locations[secret_passage_room], ClueGame.room_locations[chosen_room])
        
        elif clue_card_type == 'Player movement':
            # find best-scoring room out of all the rooms and move to it
            best_room = self.find_best_card(ClueGame.locations)
            self.position = ClueGame.room_locations[best_room]
            print('I have moved to the {}.'.format(best_room))
            
        elif clue_card_type == 'Positional reveal':
            # take as input the card that was shown
            our_index = self.players.index(self.my_char)
            player_to_our_right = self.players[our_index-1] if our_index > 0 else self.players[-1]
            shown_card = self.card_input(ClueGame.all_cards, 'Which card would you like to show me, {}?'.format(player_to_our_right), 'That\'s not a valid card')
            self.rule_out_card(player_to_our_right, shown_card)
            self.update_possible_cards(player_to_our_right)
            
            # show a card to the player to our left
            player_to_our_left = self.players[our_index+1] if our_index < len(self.players)-1 else self.players[0]
            random_card = np.random.choice([card for card in self.my_cards], size = 1)[0]
            print('I have a card to show {}...'.format(player_to_our_left))
            time.sleep(3)
            print('My card is: {}. This message will self-destruct in 5 seconds'.format(random_card))
            time.sleep(5)
            os.system('cls')
            self.rule_out_card(self.my_char, random_card)
            
        elif clue_card_type == 'All reveal':
            for player in self.players:
                if player == self.my_char:
                    # take a random card
                    random_card = np.random.choice([card for card in self.my_cards], size = 1)[0]
                    print('My card is: {}.'.format(random_card))
                    self.rule_out_card(self.my_char, random_card)
                else:    
                    shown_card = ClueGame.card_input(ClueGame.all_cards, 'Please enter which card {} showed.'.format(player), 'That\'s not a real card. Please don\'t waste my time, I spent so long on this fucking bot.')
                    self.rule_out_card(player, shown_card)
                    self.update_possible_cards(player)
            
        elif clue_card_type == 'Choice player reveal':
            if whose_turn == self.my_char:
                player_scores = {}
                # score each player based on our knowledge of their hand - i.e. how many cards we know they have for sure
                for player in self.game_state:
                    player_scores[player] = np.count_nonzero([self.game_state[player][item] == 1 for item in self.game_state[player]])
                # best player has the least number of 1s in the game state (minimum score)
                best_player = min(player_scores, key = lambda player: player_scores[player])
                print('I would like {} to reveal a card'.format(best_player))
                hidden_cards = [card for card in ClueGame.all_cards if self.is_card_possible(card)]
                shown_card = ClueGame.card_input(hidden_cards, 'Please enter which card {} showed.'.format(best_player), 'Please don\'t waste my time, I spent so long on this fucking bot.')
                time.sleep(1)
                self.rule_out_card(best_player, shown_card)
                self.update_possible_cards(best_player)
            else:
                player_to_reveal_card = ClueGame.card_input(self.players, 'Please enter which player was chosen by {} to reveal a card.'.format(whose_turn), 'That\'s not a valid player. Please don\'t waste my time, I spent so long on this fucking bot.')
                if player_to_reveal_card == self.my_char:
                    random_card = np.random.choice([card for card in self.my_cards], size = 1)[0]
                    print('Ready to show my card, but only to {}...'.format(whose_turn))
                    time.sleep(3)
                    print('My card is {}'.format(random_card))
                    self.rule_out_card(self.my_char, random_card)
                else:
                    card_revealed = ClueGame.card_input(ClueGame.all_cards, 'Please enter which card was revealed by {}.'.format(player_to_reveal_card), 'That\'s not a valid card.')
                    self.rule_out_card(player_to_reveal_card, card_revealed)
                    self.update_possible_cards(player_to_reveal_card)                             
                                                                 
    # function for taking our turn
    def our_turn(self):
        
        # Enter dice roll value for movement
        dice_roll = int(input('Please Enter Dice Roll.\n'))
        while type(dice_roll) != int or dice_roll > 12 or dice_roll < 2:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            dice_roll = int(input('Please Enter Dice Roll.\n'))
            
        n_clue_cards = int(input('Please enter number of clue cards shown.\n'))
        while type(n_clue_cards) != int or n_clue_cards > 2 or n_clue_cards < 0:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            n_clue_cards = int(input('Please enter number of clue cards shown.\n'))
        
        # If we have a clue card, have person enter result
        for i in range(n_clue_cards):
            self.clue_card(whose_turn = self.my_char, dice_roll = dice_roll)
        
        # Complete room movement
        self.position, room = self.move_on_board(dice_roll)
        
        # If we have moved to a new room, make a suggestion
        if self.position in ClueGame.room_locations.values():
            print('I have moved to the {}'.format(room))
            top_char, top_weapon, top_location = self.get_top_suggestions()
            time.sleep(1)
            print('Hm... what should I suggest...')
            time.sleep(5)
            print('I suggest {} did it with the {} in the {}'.format(top_char, top_weapon, room))
            which_player = ClueGame.card_input(self.other_players + ['None'], 'If a player showed a card, please enter which one. If not, select None.', 'That\'s not a valid player.')
            if which_player:
                which_card = ClueGame.card_input([top_char, top_weapon, room], 'Please enter which card {} showed.'.format(which_player), 'That\'s not one of the cards I suggested.')
                self.rule_out_card(which_player, which_card)
                self.update_possible_cards(which_player)
            else:
                self.possible_characters = {top_char}
                self.possible_weapons = {top_weapon}
                self.possible_locations = {room}
        # If we have not moved to a new room, make our way to a room
        else:
            time.sleep(1)
            print('Just moved to square {}'.format(self.position))
            print('I am on my way to the {}'.format(room))
            
        # Update possible guesses after clue card is shown
        self.update_possible_guesses()
        
        if len(self.possible_characters) == 1 and len(self.possible_weapons) == 1 and len(self.possible_locations) == 1:
            character = list(self.possible_characters)[0]
            weapon = list(self.possible_weapons)[0]
            location = list(self.possible_locations)[0]
            print('I accuse {} of doing the crime, with the {} in the {}'.format(character, weapon, location))
            self.game_is_active = False
       
    # update attribute for possible cards (cards that could be in the envelope) in each category
    def update_possible_guesses(self):
        
        impossible_characters = []
        for char in self.possible_characters:
            if not self.is_card_possible(char):
                impossible_characters.append(char)
                
        self.possible_characters = self.possible_characters.difference(set(impossible_characters))
                
        impossible_weapons = []    
        for weapon in self.possible_weapons:
            if not self.is_card_possible(weapon):
                impossible_weapons.append(weapon)
                
        self.possible_weapons = self.possible_weapons.difference(set(impossible_weapons))
         
        impossible_locations = []
        for location in self.possible_locations:
            if not self.is_card_possible(location):
                impossible_locations.append(location)
                
        self.possible_locations = self.possible_locations.difference(set(impossible_locations))        
                
    # function for updating the possible cards each player has in each round
    def update_possible_cards(self, player):
        
        # only need to update if the input player is a different player
        if player != self.my_char:
            
            # cards that the player cannot have
            impossible = {card for card in self.game_state[player] if self.game_state[player][card] == -1}
            
            # loop through their possible cards
            for previous_round in self.possible_cards[player]:
                set_of_possible_cards = self.possible_cards[player][previous_round]
                # check if any of the cards in the impossible list are in the set of possible cards for each previous round
                if any([impossible_card in set_of_possible_cards for impossible_card in impossible]):
                    # if so, take the difference between the sets
                    impossible_cards_in_set = {card for card in impossible if card in set_of_possible_cards}
                    self.possible_cards[player][previous_round] = self.possible_cards[player][previous_round].difference(impossible_cards_in_set)
                # if there is only one possible card, set the game state variable to reflect that
                if len(self.possible_cards[player][previous_round]) == 1:
                    card = list(self.possible_cards[player][previous_round])[0]
                    self.rule_out_card(player, card)
                
    # turn for other players
    def other_turn(self, player):

        print('It\'s {}\'s turn.'.format(player))

        n_clue_cards = int(input('Please enter number of clue cards shown.\n'))
        while type(n_clue_cards) != int or n_clue_cards > 2 or n_clue_cards < 0:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            n_clue_cards = int(input('Please enter number of clue cards shown.\n'))
        
        # If we have a clue card, have person enter result
        for i in range(n_clue_cards):
            self.clue_card(whose_turn = player, dice_roll = False)
        
        make_suggestion = ClueGame.card_input(['Yes', 'No'],
                                              'Would {} like to make a suggestion?'.format(player),
                                              'That\'s not a valid choice')

        if make_suggestion == 'Yes':
                               
            # take inputs for the suggestion
            sug_character = ClueGame.card_input([char for char in self.players if char != player] + ['None'], 'Please enter the character being accused.', 'I don\'t know that person.')
            sug_weapon = ClueGame.card_input(ClueGame.weapons, 'Please enter the weapon that was suggested.', 'Please choose a valid weapon.')
            sug_location =  ClueGame.card_input(ClueGame.locations, 'Please enter the location that was suggested.', 'Please choose a valid location.')
           
            suggestions = [sug_character, sug_weapon, sug_location]
            player_position = self.players.index(player)
            
            # if we are the suggested character, update our current position to suggested room
            if sug_character == self.my_char:
                self.position = self.room_locations[sug_location]
                print("I guess I'm moving to the {} then...".format(sug_location))
            
            # loop through other players positions
            for pos in range(player_position+1, player_position+len(self.players)):
                
                current_player = self.players[pos % len(self.players)]
                
                # if it is our turn, and we have one of the suggested cards, show it
                if current_player == self.my_char:
                    time.sleep(1)
                    if any(np.isin(self.my_cards, suggestions)):
                        matching_cards = np.array(self.my_cards)[np.isin(self.my_cards, suggestions)]
                        matching_card = np.random.choice(matching_cards, size = 1)[0] if len(matching_cards) > 1 else matching_cards[0]
                        print('I have a card to show {}...'.format(current_player))
                        time.sleep(3)
                        print('My card is: {}. This message will self-destruct in 5 seconds.'.format(matching_card))
                        time.sleep(5)
                        os.system('cls')
                        break
                    else: 
                        print('I have no cards to show.')
                # if it is not our turn, tell the computer whether each character showed a card
                else:
                    status = ClueGame.card_input(['Yes', 'No'], 'Did {} show a card?'.format(current_player), 'That\'s not a valid choice')
                    # if the player showed a card, let the computer know and figure out which of the cards the player could have possibly showed
                    if status:
                        impossible = [suggestion for suggestion in suggestions if self.game_state[current_player][suggestion] == -1]
                        possible = {suggestion for suggestion in suggestions if suggestion not in impossible}
                        self.possible_cards[current_player][self.current_round] = possible
                        self.update_possible_cards(current_player)
                        break
                    else:
                        self.game_state[current_player][sug_character] = -1
                        self.game_state[current_player][sug_weapon] = -1
                        self.game_state[current_player][sug_location] = -1    
                        self.update_possible_cards(current_player)
                        
            self.update_possible_guesses()
                          
        making_an_accusation = ClueGame.card_input(['Yes', 'No'], 'Would {} like to make an accusation?'.format(player),
                                                   'That\'s not a valid choice')

        if making_an_accusation == 'Yes':
            # check if accusation was correct
            accusation_correct = ClueGame.card_input(['Yes', 'No'], 'Was {}\'s accusation correct?'.format(player),
                                                     'That\'s not a valid choice')
            if accusation_correct == 'Yes':
                self.game_is_active = False
                 
        self.current_turn += 1  
        
        if self.current_turn % len(self.players) == 0:
            self.current_round = int(self.current_turn / len(self.players))
            
    def start_game(self):
        
        player_going_first = ClueGame.card_input(self.players, 'Please enter which player is going first.', 'That\'s not a valid player')

        player_order = ['Miss Scarlett', 'Colonel Mustard', 'Dr Orchid', 'Rev Green', 'Mrs Peacock', 'Prof Plum']

        players = [player for player in player_order if player in self.players]

        player_index = players.index(player_going_first)
        our_index = players.index(self.my_char)

        while self.game_is_active:

            if player_index == 0 and player_going_first == self.my_char:
                self.our_turn()
            elif player_index % our_index == 0 and player_index != 0:
                self.our_turn()
            else:
                self.other_turn(player = players[player_index % len(players)])

            player_index += 1