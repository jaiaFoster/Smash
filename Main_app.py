#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 11:44:52 2023

@author: jaiafoster
"""

import sqlite3
import requests
from Database_app import fetch_rankings, add_match, create_players_table,  create_matches_table, add_player
from ELO_app import process_tournament_matches
import traceback
# Constants
API_KEY = "KLZZ126tKidHVOVx7tbKFm62stnqzlHCe3GfMjgd"
#tournament_id = '12509421'

def fetch_tournament_details(tournament_code):
    """
    Fetches tournament details and data from the Challonge API.
    """
    url = f"https://api.challonge.com/v1/tournaments/{tournament_code}.json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Include both matches and participants in the response
    params = {'api_key': API_KEY, 'include_matches': 1, 'include_participants': 1}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            #print("API Response:", data)
            return data
        else:
            print(f"Error fetching data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def fetch_all_tournaments():
    """
    Fetches all tournaments from the Challonge API and returns a dictionary with tournament IDs as keys and details as values.
    """
    url = "https://api.challonge.com/v1/tournaments.json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    params = {'api_key': API_KEY}
    
    tournaments_info = {}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            tournaments_data = response.json()
            for index, tournament in enumerate(tournaments_data, start=1):
                tournament_details = tournament['tournament']
                print(f"{index}. Name: {tournament_details['name']}, Code: {tournament_details['url']}, Tournament ID: {tournament_details['id']}")
                tournaments_info[tournament_details['id']] = {
                    'name': tournament_details['name'],
                    'code': tournament_details['url']
                }
        else:
            print(f"Error fetching tournaments: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    return tournaments_info

def get_tournament_matches(tournament_data):
    """
    Extracts match details from the tournament data.
    :param tournament_data: The 'tournament' part of the JSON response from the Challonge API.
    :return: List of matches.
    """
    matches = tournament_data.get('matches', [])
    return [match['match'] for match in matches]

def parse_participants(participants_data):
    participants = {}
    for p in participants_data:
        participant = p['participant']
        pid = participant['id']
        name = participant['name']
        participants[pid] = name
    return participants

def parse_matches(match_data, participants):
    """
    Parses match data into a more usable format.x
    :param match_data: List of match data from the API.
    :return: List of parsed match data.
    """
    parsed_matches = []
    for match in match_data:
        match_info = {
            'match_id': match['id'],
            'tournament_id': match['tournament_id'],
            'player1_id': match['player1_id'],
            'player2_id': match['player2_id'],
            'player1_name': participants.get(match['player1_id'], "Unknown"),
            'player2_name': participants.get(match['player2_id'], "Unknown"),
            'winner_id': match['winner_id'],
            'loser_id': match['loser_id'],
            'scores_csv': match['scores_csv'],
            'suggested_play_order': match['suggested_play_order']
        }
        parsed_matches.append(match_info)
    return parsed_matches

def fetch_parse_add(tournament_code,conn):
    """
    fetches the tournament data, parses it, then passses it into the database

    """
    
    tournament_response = fetch_tournament_details(tournament_code)
    
    if tournament_response:
        try:
            matches = get_tournament_matches(tournament_response['tournament'])
            participants_data = tournament_response['tournament']['participants']
            # Parsing participants
            participants = parse_participants(participants_data)
            # Parsing matches with the participants data
            parsed_matches = parse_matches(matches, participants)
            # Assuming parsed_matches is generated from the matches data
            # Add the logic for parsing matches here if not already present
    
            for match_data in parsed_matches:
                # Debugging: Print each argument being passed
                #print("Match Data:", match_data)
    
                try:
                    add_match(conn, 
                          match_data['match_id'],
                          match_data['tournament_id'],
                          match_data['player1_id'], 
                          match_data['player2_id'], 
                          match_data['winner_id'], 
                          match_data['loser_id'], 
                          match_data.get('scores_csv', '2-0'),
                          match_data['suggested_play_order']
                          
                          )
                except KeyError as e:
                    print(f"Missing key in match data: {e}")
                    traceback.print_exc()
            print("Match data added successfully")
            
            try:
                
                for player_id, name in participants.items():
                    add_player(conn, player_id, name)
                
            except Exception as e:
                print(f"An error occurred processing the player data: {e}")
                traceback.print_exc()
            
            print("Player data added successfully")
            
        except Exception as e:
            print(f"An error occurred processing the tournament: {e}")
            traceback.print_exc()

def main():
    # Database connection setup
    conn = sqlite3.connect('tournament_database.db')
    cursor = conn.cursor()

    # Create tables if they don't exist
    create_players_table(cursor)
    create_matches_table(cursor)

    try:
        while True:
            print("\nTournament ELO Ranking System", flush=True)
            print("1. Fetch and process tournament data", flush=True)
            print("2. Update ELO rankings", flush=True)
            print("3. Display Rankings", flush=True)
            print("4. Exit", flush=True)
            choice = input("\nEnter your choice: ")
        
            if choice == '1':
                tournaments_info = fetch_all_tournaments()
                tournament_ids = list(tournaments_info.keys())
            
                if tournament_ids:  # Check if there are any tournaments
                    print("\nChoose a tournament by entering the corresponding number.", flush=True)
                    while True:
                        try:
                            user_input = int(input(f"Enter a number (1-{len(tournament_ids)}): "))
                            if 1 <= user_input <= len(tournament_ids):
                                selected_tournament_id = tournament_ids[user_input - 1]
                                tournament_code = tournaments_info[selected_tournament_id]['code']
                                print(f"You have selected: {tournaments_info[selected_tournament_id]['name']}", flush=True)
                                fetch_parse_add(tournament_code, conn)
                                break
                            else:
                                print(f"Please enter a number between 1 and {len(tournament_ids)}.", flush=True)
                        except ValueError:
                            print("Invalid input. Please enter a number.", flush=True)
                else:
                    print("No tournaments available.", flush=True)
            
            elif choice == '2':
                tournaments_info = fetch_all_tournaments()
                tournament_ids = list(tournaments_info.keys())
            
                if tournament_ids:  # Check if there are any tournaments
                    print("\nChoose a tournament by entering the corresponding number.", flush=True)
                    while True:
                        try:
                            user_input = int(input(f"Enter a number (1-{len(tournament_ids)}): "))
                            if 1 <= user_input <= len(tournament_ids):
                                selected_tournament_id = tournament_ids[user_input - 1]
                                print(f"You have selected: {tournaments_info[selected_tournament_id]['name']}", flush=True)
                                process_tournament_matches(selected_tournament_id, conn)
                                print("ELO rankings updated.", flush=True)
                                break
                            else:
                                print(f"Please enter a number between 1 and {len(tournament_ids)}.", flush=True)
                        except ValueError:
                            print("Invalid input. Please enter a number.", flush=True)
                else:
                    print("No tournaments available.", flush=True)

            elif choice == '3':
                rankings = fetch_rankings(conn)
                print("\nPlayer Rankings:")
                for rank, (name, rating) in enumerate(rankings, start=1):
                    print(f"{rank}. {name} - {rating}")
        
            elif choice == '4':
                print("Exiting the application.")
                break
                
            else:
                print("Invalid choice. Please try again.")

    finally:
        # This will always execute, ensuring the database connection is closed properly
        conn.close()

if __name__ == '__main__':
    main()
    
    
    