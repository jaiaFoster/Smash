#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 12:39:12 2023

@author: jaiafoster
"""

from Database_app import add_player, get_player_rating, update_player_rating
import traceback
import sqlite3

# ELO Calculation Constants
BASE_ELO_K_FACTOR = 32
DEFAULT_ELO_RATING = 1200

def calculate_elo_change(winner_rating, loser_rating, k_factor=BASE_ELO_K_FACTOR):
    """
    Calculate the ELO rating change for both winner and loser.
    """
    expected_score_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    elo_change = round(k_factor * (1 - expected_score_winner))
    return elo_change

def update_elo_ratings(winner_id, loser_id, conn):
    
    # Now fetch their ratings
    winner_rating = get_player_rating(conn, winner_id)
    loser_rating = get_player_rating(conn, loser_id)

    if winner_rating is None or loser_rating is None:
        print(f"Error: Rating not found for player IDs {winner_id} or {loser_id}")
        return  # Exit the function if ratings are not found

    elo_change = calculate_elo_change(winner_rating, loser_rating)
    
    update_player_rating(conn, winner_id, winner_rating + elo_change)
    update_player_rating(conn, loser_id, loser_rating - elo_change)

def apply_tournament_placement_bonus(tournament_id, conn):
    """
    Apply additional ELO points based on players' tournament placements.
    """
    # Placeholder: Fetch tournament placement data and apply bonuses
    # This will depend on how you store and retrieve tournament placement data
    # Example: update_player_rating(conn, player_id, new_rating)

def get_player_name(conn, player_id):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Players WHERE player_id = ?", (player_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def process_tournament_matches(tournament_id, conn):
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM Matches WHERE tournament_id = ? AND status = 0", (tournament_id,))
        matches = cursor.fetchall()

        for match in matches:
            player1_name = get_player_name(conn, match['player1_id'])
            player2_name = get_player_name(conn, match['player2_id'])

            # Check if player names are found
            if not player1_name or not player2_name:
                print(f"Player names not found for match ID {match['match_id']}. Skipping.")
                continue

            player1_id = add_player(conn, name=player1_name)
            player2_id = add_player(conn, name=player2_name)
            # Determine winner and loser IDs
            winner_id = player1_id if match['winner_id'] == player1_id else player2_id
            loser_id = player2_id if winner_id == player1_id else player1_id

            # Update ELO ratings
            update_elo_ratings(winner_id, loser_id, conn)

            # Update match status as processed
            cursor.execute("UPDATE Matches SET status = 1 WHERE match_id = ?", (match['match_id'],))

        conn.commit()

    except Exception as e:
        print("An error occurred: ", e)
        traceback.print_exc()

    finally:
        cursor.close()


