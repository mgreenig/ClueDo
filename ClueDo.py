import numpy as np
from Board_graph import board_graph

class ClueGame:
    
    characters = {'Colonel Mustard', 'Miss Scarlett', 'Mrs Peacock', 'Dr Orchid', 'Rev Green', 'Prof Plum'}
    weapons = {'Rope', 'Dagger', 'Wrench', 'Revolver', 'Candlestick', 'Lead Pipe'}
    locations = {'Kitchen', 'Dining Room', 'Lounge', 'Hall', 'Study', 'Library', 'Billiard Room', 'Conservatory', 'Ballroom'}
    board_graph = board_graph
    char_starting_positions = {'Colonel Mustard': 66, 'Miss Scarlett': 4, 'Mrs Peacock': 145, 'Dr Orchid': 196, 'Rev Green':95, 'Prof Plum': 28}
    room_locations = {'Kitchen': 194, 'Dining Room': 87, 'Lounge': 5, 'Hall': 3, 'Study': 1, 'Library': 82, 'Billiard Room': 109, 'Conservatory': 186, 'Ballroom': 190}
  
    # initialize with a set of characters, my character, and the cards we are dealt
    def __init__(self, players, my_char, my_cards):
        assert all([player in ClueGame.characters for player in players])
        self.players = players
        self.my_char = my_char
        self.my_cards = my_cards
        # update the character list to disclude characters not playing
        self.characters = set(players).intersection(self.characters)
        self.all_cards = self.characters.union(self.weapons, self.locations)
        # dictionary for storing knowledge about other players' cards: -1 means they do not have the card, 1 means they do, 0 is ambiguous
        self.game_state = {player: {item: 1 if item in self.my_cards and player == my_char
                                    else -1 if item in self.my_cards and player != my_char
                                    else 0 for item in self.characters.union(self.weapons, self.locations)} 
                           for player in self.players}
        # dictionary for tracking possible cards for each player in each round, based on what they show
        self.possible_cards = {player: {} for player in self.players}
        # location on the board
        self.location = ClueGame.char_starting_positions[self.my_char]
        self.possible_characters = self.characters
        self.possible_weapons = self.weapons
        self.possible_locations = self.locations
        self.current_turn = 0
        self.current_round = 0
        
    def move_on_board(self, dice_roll):

        # Calculate distances to each room from current position
        path_lengths = {'Kitchen': 0, 'Dining Room': 0, 'Lounge': 0, 'Hall': 0, 'Study': 0, 'Library': 0, 
                        'Billiard Room': 0, 'Conservatory': 0, 'Ballroom': 0}
        for room in room_locations:
            path_lengths[room] = nx.shortest_path_length(board_graph, self.position, room_locations[room])
            
            # Filter rooms further away than dice roll
            possible_rooms = [key for key in path_lengths if path_lengths[key] <= dice_roll]
            
            # If no rooms are reachable in this turn, move to a square on the way to closest room
            if len(possible_rooms) == 0:
                possible_rooms = [key for key in room_locations if path_lengths[key] == min(path_lengths.values())]
                closest_room_key = np.random.choice(possible_rooms,size=1)[0]   
                # Find shortest path to closest room and move as far along it as dice roll will allow
                return mx.shortest_path(board_graph, self.position, room_locations[closest_room_key])[dice_roll], closest_room_key

            # If more than one room same distance apart, pick one at random and move to it
            elif len(possible_rooms) > 1:
                # Find the list of close rooms
                possible_rooms = [key for key in possible_rooms if path_lengths[key] == min(path_lengths.values())]
                # Move to closest room at random
                room_key = np.random.choice(possible_rooms,size=1)[0]
                return board_graph[room_locations[room_key]], room_key
            
            # If only one room available, move to it
            else:
                return board_graph[room_locations[possible_rooms[0]]], room_key
            
    def score_item(self, item):
       
        item_scores = []
        for player in self.game_state:
            item_scores.append(self.game_state[player][item])
        if any([score == 1 for score in item_scores]):
            return False
        else: 
            return sum(item_scores)
            
    def make_suggestion(self):
        
        char_scores = {}
        weapon_scores = {}
        location_scores = {}
        
        for character in self.characters:
            if score_item(character):
                char_scores[character] = score_item(character)
        
        for weapon in self.weapons:
            if score_item(weapon):
                weapon_scores[weapon] = score_item(weapon)
        
        for location in self.locations:
            if score_item(location):
                location_scores[location] = score_item(location)
                
        top_characters = [character for character in char_scores if char_scores[character] == min(char_scores.values())]
        top_weapons = [weapon for weapon in weapon_scores if weapon_scores[weapon] == min(weapon_scores.values())]
        top_locations = [location for location in location_scores if location_scores[location] == min(location_scores.values())]
        
        top_char = np.random.choice(top_characters, size=1)
        

    def our_turn(self):
        dice_roll = input('Please Enter Dice Roll')
        assert type(dice_roll) == int, "Uh... that ain't a number tho"

        self.position, room = self.move_on_board(dice_roll)
        room_locations_inv = {loc: room for room, loc in room_locations.items()}
    
        if self.position in room_locations_inv.keys():
            print('I have moved to {}'.format(room))
        else:
            print('I am on my way to {}'.format(room))
        

    # function for updating the possible cards each player has in each round
    def update_possible_cards(self, player):
        
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
                card = ''.join([str(card) for card in self.possible_cards[player][previous_round]])
                for single_player in self.game_state:
                    self.game_state[single_player][card] = 1 if single_player == player else -1
                    
    # turn for other players
    def other_turn(self, player, make_suggestion = True):
        
        assert player in self.players
        
        if make_suggestion:
            # assert inputs are correct
            sug_character = input('Please enter the character being accused.')
            assert sug_character in self.character, 'Please choose a valid character.'
            sug_weapon = input('Please enter the weapon that was used.')
            assert sug_weapon in self.weapons, 'Please choose a valid weapon.'
            sug_location = input('Please enter the location of the crime.')
            assert sug_location in self.locations, 'Please choose a valid location.'
            
            suggestions = [sug_character, sug_weapon, sug_location]
            player_position = self.players.index(player)
            
            # if we are the suggested character, update our current position to suggested room
            if sug_character == self.mychar:
                self.position = room_locations[sug_location]
                print("I guess I'm moving to {} then...".format(sug_location))
            
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
                                 
        self.current_turn += 1  
        
        if self.current_turn % len(self.players) == 0:
            self.current_round = int(self.current_turn / len(self.players)) 
