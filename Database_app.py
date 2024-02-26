#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 10:47:12 2023

@author: jaiafoster
"""

import sqlite3
from fuzzywuzzy import fuzz

# Database setup functions
def create_players_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS Players (
                        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        rating INTEGER DEFAULT 1200
                      );''')

def create_matches_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            player1_id INTEGER,
            player2_id INTEGER,
            winner_id INTEGER,
            loser_id INTEGER,
            scores_csv TEXT,
            suggested_play_order INTEGER,
            status INTEGER DEFAULT 0,
            FOREIGN KEY (player1_id) REFERENCES Players (player_id),
            FOREIGN KEY (player2_id) REFERENCES Players (player_id),
            FOREIGN KEY (winner_id) REFERENCES Players (player_id),
            FOREIGN KEY (loser_id) REFERENCES Players (player_id)
        );
    ''')

def create_aliases_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS PlayerAliases (
                        alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_id INTEGER,
                        alias_name TEXT NOT NULL,
                        FOREIGN KEY (player_id) REFERENCES Players (player_id)
                      );''')

# Initialize the database
def initialize_database():
    conn = sqlite3.connect('tournament_database.db')
    cursor = conn.cursor()
    create_players_table(cursor)
    create_matches_table(cursor)
    create_aliases_table(cursor)
    conn.commit()
    conn.close()

def add_player(conn, player_id=None, name=None, rating=1200):
    """
    Add a player to the database. Checks if a player with the same ID or a similar name exists.
    Adds a new player only if neither exists.
    """
    if name is None or name.strip() == '':
        print(f"Invalid name provided. Skipping addition.")
        return None

    cursor = conn.cursor()

    # Check for existing player with a similar name
    cursor.execute("SELECT player_id, name FROM Players")
    for existing_player_id, existing_name in cursor.fetchall():
        if is_name_match(name, existing_name):
            print(f"Found matching player {existing_name} for {name}. Using existing player ID {existing_player_id}.")
            return existing_player_id

    # If no match found, add new player
    cursor.execute("INSERT INTO Players (name, rating) VALUES (?, ?)", (name, rating))
    conn.commit()
    return cursor.lastrowid

def add_match(conn, match_id, tournament_id, player1_id, player2_id, winner_id, loser_id, scores_csv, suggested_play_order):
    """
    Add a match to the database with player IDs. Only adds if the match doesn't already exist.
    """
    
    # Check if match already exists
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Matches WHERE match_id = ?", (match_id,))
    if cursor.fetchone()[0] > 0:
        print(f"Match {match_id} is already in the database. Skipping addition.")
        return None

    # Add match
    sql = """
    INSERT INTO Matches (match_id, tournament_id, player1_id, player2_id, winner_id, loser_id, scores_csv, suggested_play_order) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (match_id, tournament_id, player1_id, player2_id, winner_id, loser_id, scores_csv, suggested_play_order)
    
    try:
        cursor.execute(sql, values)
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding match to database: {e}")
        return None

def get_player_rating(conn, player_id):
    cursor = conn.cursor()
    cursor.execute("SELECT rating FROM Players WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()
    #print(f"Rating for player {player_id}: {result}")  # Debugging line
    
    return result[0] if result else None

def update_player_rating(conn, player_id, new_rating):
    """
    Update the ELO rating of a player in the database.
    """
    cursor = conn.cursor()
    cursor.execute("UPDATE Players SET rating = ? WHERE player_id = ?", (new_rating, player_id))
    conn.commit()

def fetch_rankings(conn):
    """
    Fetches and returns player rankings from the database.

    :param conn: The SQLite database connection.
    :return: A list of tuples containing player names and their ratings, sorted by ratings in descending order.
    """
    cursor = conn.cursor()

    # SQL query to select player names and ratings, sorted by ratings in descending order
    query = "SELECT name, rating FROM Players ORDER BY rating DESC"

    try:
        cursor.execute(query)
        rankings = cursor.fetchall()
        return rankings
    except Exception as e:
        print(f"An error occurred while fetching rankings: {e}")
        return []
    
def remove_matches_by_tournament_id(conn, tournament_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Matches WHERE tournament_id = ?", (tournament_id,))
    conn.commit()


def is_name_match(name1, name2, threshold=85):
    """
    Check if two names are a match based on a similarity threshold.
    """
    similarity_score = fuzz.ratio(name1.lower(), name2.lower())
    return similarity_score >= threshold 
    
def add_player_alias(conn, participant_id, alias_name, manual_player_id=None):
    """
    Add an alias for a player in the PlayerAliases table.
    Optionally, manually specify the player ID if automatic matching fails.
    """
    cursor = conn.cursor()

    if manual_player_id is not None:
        # Check if the manually provided player_id exists in the Players table
        cursor.execute("SELECT COUNT(*) FROM Players WHERE player_id = ?", (manual_player_id,))
        if cursor.fetchone()[0] == 0:
            print(f"No player found with ID {manual_player_id}. Cannot add alias.")
            return

        # Directly use the provided player ID
        cursor.execute("INSERT INTO PlayerAliases (participant_id, alias_name, player_id) VALUES (?, ?, ?)", 
                       (participant_id, alias_name, manual_player_id))
        print(f"Manually added alias {alias_name} for player ID {manual_player_id}")
    else:
        # Fetch all existing aliases and their associated player IDs
        cursor.execute("SELECT alias_name, player_id FROM PlayerAliases")
        aliases = cursor.fetchall()

        matched_player_id = None
        for existing_alias, player_id in aliases:
            if is_name_match(alias_name, existing_alias):
                matched_player_id = player_id
                break

        if matched_player_id:
            # A matching alias was found, link the new alias to the existing player ID
            cursor.execute("INSERT INTO PlayerAliases (participant_id, alias_name, player_id) VALUES (?, ?, ?)", 
                           (participant_id, alias_name, matched_player_id))
            print(f"Alias {alias_name} matched with existing player ID {matched_player_id}")
        else:
            # No matching alias found, handle as new player or ask for user input
            print(f"No matching alias found for {alias_name}. Further action needed.")

    conn.commit()

