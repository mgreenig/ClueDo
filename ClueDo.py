import numpy as np
import time
import networkx as nx
from Board_graph import board_graph

class ClueGame:
    
    characters = {'Colonel Mustard', 'Miss Scarlett', 'Mrs Peacock', 'Dr Orchid', 'Rev Green', 'Prof Plum'}
    weapons = {'Rope', 'Dagger', 'Wrench', 'Revolver', 'Candlestick', 'Lead Pipe'}
    locations = {'Kitchen', 'Dining Room', 'Lounge', 'Hall', 'Study', 'Library', 'Billiard Room', 'Conservatory', 'Ballroom'}
    secret_passage_locations = {'Lounge', 'Conservatory', 'Study', 'Kitchen'}
    non_secret_passage_locations = {'Dining Room', 'Hall', 'Library', 'Billiard Room', 'Ballroom'}
    all_cards = characters.union(weapons, locations)
    board_graph = board_graph
    char_starting_positions = {'Colonel Mustard': 66, 'Miss Scarlett': 4, 'Mrs Peacock': 145, 'Dr Orchid': 196, 'Rev Green':95, 'Prof Plum': 28}
    room_locations = {'Kitchen': 194, 'Dining Room': 87, 'Lounge': 5, 'Hall': 3, 'Study': 1, 'Library': 82, 'Billiard Room': 109, 'Conservatory': 186, 'Ballroom': 190}
    possible_clue_cards = {'Specific card reveal', 'Choice card reveal', 'Secret passage', 'Player movement', 'Positional reveal', 'All reveal', 'Choice player reveal'}

    # initialize with a set of characters, my character, and the cards we are dealt
    def __init__(self, players, my_char, my_cards):
        assert all([player in ClueGame.characters for player in players])
        self.players = players
        self.my_char = my_char
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
        
    # function that asks for input and loops until the input is present in the viable card list
    @staticmethod
    def card_input(viable_card_list, input_message, error_message):
        card = input(input_message)
        while card not in viable_card_list:
            print(error_message)
            time.sleep(1)
            card = input(input_message)
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
        card_scores = {card: self.score_card(card) for card in self.card_list if self.is_card_possible(card)}
        best_card = min(card_scores, key = lambda card: card_scores[card])
        return best_card
    
    # functin for updating the game state after we know that a player has a card
    def rule_out_card(self, player, card):
        for single_player in self.game_state:
            self.game_state[single_player][card] = 1 if single_player == player else -1
        if player == self.my_char:
            self.my_cards = self.my_cards.remove(card)
            
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
        top_characters = [character for character in char_scores if char_scores[character] == min(char_scores.values())]
        top_weapons = [weapon for weapon in weapon_scores if weapon_scores[weapon] == min(weapon_scores.values())]
        top_locations = [location for location in location_scores if location_scores[location] == min(location_scores.values())]
        
        # sample randomly 
        top_char = np.random.choice(top_characters, size=1)[0]
        top_weapon = np.random.choice(top_weapons, size=1)[0]
        top_location = np.random.choice(top_locations, size=1)[0]
        
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
        
        character = input('If a player showed the card, enter their character here. Otherwise, press enter')
        while character not in self.players and character != '':
            print("Who is that? Try again.")
            time.sleep(1)
            character = input('If anyone has {}, please show it. If a player showed the card, enter their character here. Otherwise, press enter'.format(best_card))
        if character == '':
            if card in self.players:
                self.possible_characters = {card}
            elif card in self.weapons:
                self.possible_weapons = {card}
            elif card in self.locations:
                self.possible_locations = {card}
        else:
            self.rule_out_card(character, card) 
            self.update_possible_cards(character)
        
    def clue_card(self, whose_turn, dice_roll):
            
        # get the type of clue card being shown
        clue_card_type = ClueGame.card_input(ClueGame.possible_clue_cards, 'Please choose which type of clue card has been shown: {}'.format(', '.join(list(ClueGame.possible_clue_cards))), 
                                             'That\'s not a valid type of clue card. Trust me, we looked through all of them.')
        # if it is a specific card reveal, take in the specific card and update the game state
        if clue_card_type == 'Specific card reveal':
            card_shown = ClueGame.card_input(self.all_cards, 'Please enter which card was revealed.', 'That doesn\'t look like anything to me...')
            self.which_player_showed_card(card)
            
        # if the card says to choose a card to reveal, choose the top card   
        elif clue_card_type == 'Choice reveal':
            if whose_turn == self.my_char:
                type_of_choice_reveal = ClueGame.card_input({'Suspect', 'Weapon', 'Location'}, 'Please enter which type of card is to be revealed.', 'That is not a valid type of card')
                print('Hmmm, what\'s the best card to choose...')
                if type_of_choice_reveal == 'Suspect':
                    best_card = self.find_best_card(ClueGame.characters)
                elif type_of_choice_reveal == 'Weapon':
                    best_card = self.find_best_card(ClueGame.weapons)
                elif type_of_choice_reveal = 'Location':
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
                    possible_rooms = [room for room in room_scores if path_lengths[key] <= dice_roll]
                    # if any possible rooms are secret passage rooms, make a passage to the room with the best score
                    if any([room in ClueGame.secret_passage_locations for room in possible_rooms]):
                        best_room = self.find_best_card(ClueGame.non_secret_passage_locations)
                    # else if all possible rooms are not secret passage locations (and there are possible rooms), find the best one
                    elif len(possible_rooms) >= 1:
                        best_room = self.find_best_card(possible_rooms)
                    # else if there are not any possible rooms, choose to put the passage in the closest room that could still be in the envelope
                    else:
                        path_lengths_non_passage_rooms = {room: path_length for room, path_length in path_lengths.items() if room in ClueGame.non_secret_passage_locations and self.is_card_possible(room)}
                        best_room = min(path_lengths_non_passage_rooms, key = lambda room: path_lengths_non_passage_rooms[room])
                print('Let\'s make a passage from {} to {}'.format(current_room, top_room))
                for secret_passage_room in ClueGame.secret_passage_locations:
                    board_graph.add_edge(ClueGame.room_locations[secret_passage_room], ClueGame.room_locations[best_room])
            else:
                chosen_room = ClueGame.card_input(ClueGame.locations, 'Please enter which room you would like to connect to the secret passages.', 'That\'s not a valid room.')
                for secret_passage_room in ClueGame.secret_passage_locations:
                    board_graph.add_edge(ClueGame.room_locations[secret_passage_room], ClueGame.room_locations[chosen_room])
        
        elif clue_card_type == 'Player movement':
            # find best-scoring room out of all the rooms and move to it
            best_room = self.find_best_card(ClueGame.locations)
            self.position = ClueGame.room_locations[best_room]
            print('I have moved to the {}.'.format(best_room))
            
        elif clue_card_type == 'Positional reveal':
            # take as input the acrd that was shown
            shown_card = self.card_input(ClueGame.all_cards, 'Which card would you like to show me?', 'That\'s not a valid card')
            our_index = self.players.index(self.my_char)
            player_to_our_right = self.players[our_index-1] if our_index > 0 else self.players[-1]
            self.rule_out_card(player_to_our_right, shown_card)
            self.update_possible_cards(player_to_our_right)
            
        elif clue_card_type == 'All reveal':
            # take the card with the max score 
            random_card = np.random.choice([card for card in self.my_cards], size = 1)[0]
            print('My card is: {}.'.format(random_card))
            self.rule_out_card(self.my_char, random_card)
            for player in self.players:
                shown_card = ClueGame.card_input(ClueGame.all_cards, 'Please enter which card {} showed.'.format(player), 'That\'s not a real card. Please don\'t waste my time, I spent so long on this fucking bot.')
                self.rule_out_card(player, shown_card)
                self.update_possible_cards(player)
            
        elif clue_card_type == 'Choice player reveal':
            player_scores = {}
            # score each player based on our knowledge of their hand - i.e. how many cards we know they have for sure
            for player in self.game_state:
                player_scores[player] = np.count_nonzero([self.game_state[player][item] == 1 for item in self.game_state[player]])
            # best player has the least number of 1s in the game state (minimum score)
            best_player = min(player_scores, key = lambda player: player_scores[player])
            print('I would like {} to reveal a card'.format(best_player))
            shown_card = ClueGame.card_input(ClueGame.all_cards, 'Please enter which card {} showed'.format(best_player), 'That\'s not a real card. Please don\'t waste my time, I spent so long on this fucking bot.')
            self.rule_out_card(best_player, shown_card)
            self.update_possible_cards(best_player)
                                             
                                                                 
    # function for taking our turn
    def our_turn(self):
        
        # Enter dice roll value for movement
        dice_roll = int(input('Please Enter Dice Roll'))
        while type(dice_roll) != int or dice_roll > 12 or dice_roll < 2:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            dice_roll = int(input('Please Enter Dice Roll'))
            
        n_clue_cards = int(input('Please enter number of clue cards shown'))
        while type(n_clue_cards) != int or n_clue_cards > 2 or n_clue_cards < 0:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            n_clue_cards = int(input('Please enter number of clue cards shown'))
        
        # If we have a clue card, have person enter result
        for i in range(n_clue_cards):
            self.clue_card(whose_turn = self.my_player, dice_roll = dice_roll)
        
        # Complete room movement
        self.position, room = self.move_on_board(dice_roll)
        
        # If we have moved to a new room, make a suggestion
        if self.position in ClueGame.room_locations.values():
            print('I have moved to {}'.format(room))
            top_char, top_weapon, top_location = self.get_top_suggestions()
            print('Hm... what should I suggest...')
            time.sleep(5)
            print('I suggest {} did it with the {} in the {}'.format(top_char, top_weapon, top_location))
            which_player = ClueGame.card_input(self.players, 'Please enter the player that showed a card', 'That\'s not a valid player.')
            which_card = ClueGame.card_input([top_char, top_weapon, top_location], 'Please enter which card {} showed'.format(which_player), 'That\'s not one of the cards I suggested.')
            self.rule_out_card(which_player, which_card)
            self.update_possible_cards(which_player)
        # If we have not moved to a new room, make our way to a room
        else:
            print('I am on my way to the {}'.format(room))
            
        # Update possible guesses after clue card is shown
        self.update_possible_guesses()
        
        if len(self.possible_characters) == 1 and len(self.possible_weapons) == 1 and len(self.possible_locations) == 1:
            character = self.possible_characters[0]
            weapon = self.possible_weapons[0]
            location = self.possible_locations[0]
            print('I accuse {} of doing the crime, with the {} in the {}'.format(character, weapon, location))
       
    # update attribute for possible cards (cards that could be in the envelope) in each category
    def update_possible_guesses(self):
        
        for char in self.possible_characters:
            if not self.is_card_possible(char):
                self.possible_characters.remove(char)
                
        for weapon in self.possible_weapons:
            if not self.is_card_possible(weapon):
                self.possible_weapons.remove(weapon)
                
        for location in self.possible_locations:
            if not self.is_card_possible(location):
                self.possible_locations.remove(location)
                
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
                    card = self.possible_cards[player][previous_round]][0]
                    self.rule_out_card(player, card)
                
    # turn for other players
    def other_turn(self):
        
        player = ClueGame.card_input(self.players, 'Please enter which player\'s turn it is', 'Please enter a valid player')
                      
        n_clue_cards = int(input('Please enter number of clue cards shown'))
        while type(n_clue_cards) != int or n_clue_cards > 2 or n_clue_cards < 0:
            print("Uh... I'm gonna need a valid input")
            time.sleep(1)
            n_clue_cards = int(input('Please enter number of clue cards shown'))
        
        # If we have a clue card, have person enter result
        for i in range(n_clue_cards):
            self.clue_card(whose_turn = player, dice_roll = False)
        
        make_suggestion = input('If {} would like to make a suggestion, enter any character and press enter. If not, just press enter.'.format(player))
        
        if len(make_suggestion) > 0:
                               
            # take inputs for the suggestion
            sug_character = ClueGame.card_input(ClueGame.characters, 'Please enter the character being accused.', 'I don\'t know that person.')
            sug_weapon = ClueGame.card_input(ClueGame.weapons, 'Please enter the weapon that was used.', 'Please choose a valid weapon.')
            sug_location =  ClueGame.card_input(ClueGame.locations, 'Please enter the location of the crime.', 'Please choose a valid location.')
           
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
                    if any(np.isin(self.my_cards, suggestions)):
                        matching_cards = np.array(self.my_cards)[np.isin(self.my_cards, suggestions)]
                        matching_card = np.random.choice(matching_cards, size = 1)[0] if len(matching_cards) > 1 else matching_cards[0]
                        print('My card is: {}'.format(matching_card))
                        break
                    else: 
                        print('I have no cards to show.')
                # if it is not our turn, tell the computer whether each character showed a card
                else:
                    status = input('Please type any character if {} showed a card. If not, press enter.'.format(current_player))
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
                                 
        self.current_turn += 1  
        
        if self.current_turn % len(self.players) == 0:
            self.current_round = int(self.current_turn / len(self.players))   
