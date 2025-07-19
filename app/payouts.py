"""
Payout calculation for parimutuel betting system.

This module handles calculating payouts for winners in each market:
- Advance bets: Winners split the advance pool
- Win bets: Winners split the win pool  
- Prop bets: Winners split their respective yes/no pools

All calculations apply the 3% house take.
"""

from sqlalchemy import select, func
from .models import AdvanceBet, WinBet, PropBet, Player, PropUniverse
import os

# House take percentage (3%)
HOUSE_TAKE = float(os.getenv("HOUSE_TAKE", "0.03"))

def calculate_advance_payouts(session, winning_player_ids):
    """
    Calculate payouts for advance market winners.
    
    Args:
        session: Database session
        winning_player_ids: List of player IDs who advanced
    
    Returns:
        dict: {bettor_email: payout_amount}
    """
    if not winning_player_ids:
        return {}
    
    # Get total pool for advance bets
    total_pool = session.scalar(select(func.sum(AdvanceBet.amount))) or 0.0
    if total_pool <= 0:
        return {}
    
    # Apply house take
    payout_pool = total_pool * (1.0 - HOUSE_TAKE)
    
    # Get total stake on winning players
    winning_stake = session.scalar(
        select(func.sum(AdvanceBet.amount))
        .where(AdvanceBet.player_id.in_(winning_player_ids))
    ) or 0.0
    
    if winning_stake <= 0:
        return {}
    
    # Calculate payouts for each bettor
    payouts = {}
    
    # Get all bets on winning players
    winning_bets = session.execute(
        select(AdvanceBet.bettor_email, AdvanceBet.amount)
        .where(AdvanceBet.player_id.in_(winning_player_ids))
    ).fetchall()
    
    for bettor_email, bet_amount in winning_bets:
        # Payout = (bet_amount / total_winning_stake) * payout_pool
        payout = (bet_amount / winning_stake) * payout_pool
        payouts[bettor_email] = payouts.get(bettor_email, 0.0) + payout
    
    return {email: round(amount, 2) for email, amount in payouts.items()}

def calculate_win_payouts(session, winning_player_id):
    """
    Calculate payouts for win market winner.
    
    Args:
        session: Database session
        winning_player_id: Player ID who won the overall event
    
    Returns:
        dict: {bettor_email: payout_amount}
    """
    if not winning_player_id:
        return {}
    
    # Get total pool for win bets
    total_pool = session.scalar(select(func.sum(WinBet.amount))) or 0.0
    if total_pool <= 0:
        return {}
    
    # Apply house take
    payout_pool = total_pool * (1.0 - HOUSE_TAKE)
    
    # Get total stake on winning player
    winning_stake = session.scalar(
        select(func.sum(WinBet.amount))
        .where(WinBet.player_id == winning_player_id)
    ) or 0.0
    
    if winning_stake <= 0:
        return {}
    
    # Calculate payouts for each bettor
    payouts = {}
    
    # Get all bets on winning player
    winning_bets = session.execute(
        select(WinBet.bettor_email, WinBet.amount)
        .where(WinBet.player_id == winning_player_id)
    ).fetchall()
    
    for bettor_email, bet_amount in winning_bets:
        # Payout = (bet_amount / total_winning_stake) * payout_pool
        payout = (bet_amount / winning_stake) * payout_pool
        payouts[bettor_email] = payouts.get(bettor_email, 0.0) + payout
    
    return {email: round(amount, 2) for email, amount in payouts.items()}

def calculate_prop_payouts(session, prop_results):
    """
    Calculate payouts for prop bet winners.
    
    Args:
        session: Database session
        prop_results: dict {prop_id: True/False} where True=Yes won, False=No won
    
    Returns:
        dict: {bettor_email: payout_amount}
    """
    if not prop_results:
        return {}
    
    payouts = {}
    
    for prop_id, yes_won in prop_results.items():
        # Get total pool for this prop (both yes and no sides)
        total_pool = session.scalar(
            select(func.sum(PropBet.amount))
            .where(PropBet.prop_id == prop_id)
        ) or 0.0
        
        if total_pool <= 0:
            continue
        
        # Apply house take
        payout_pool = total_pool * (1.0 - HOUSE_TAKE)
        
        # Get total stake on winning side
        winning_stake = session.scalar(
            select(func.sum(PropBet.amount))
            .where(PropBet.prop_id == prop_id, PropBet.side_yes == yes_won)
        ) or 0.0
        
        if winning_stake <= 0:
            continue
        
        # Get all bets on winning side
        winning_bets = session.execute(
            select(PropBet.bettor_email, PropBet.amount)
            .where(PropBet.prop_id == prop_id, PropBet.side_yes == yes_won)
        ).fetchall()
        
        for bettor_email, bet_amount in winning_bets:
            # Payout = (bet_amount / total_winning_stake) * payout_pool
            payout = (bet_amount / winning_stake) * payout_pool
            payouts[bettor_email] = payouts.get(bettor_email, 0.0) + payout
    
    return {email: round(amount, 2) for email, amount in payouts.items()}

def calculate_all_payouts(session, results):
    """
    Calculate all payouts across all markets.
    
    Args:
        session: Database session
        results: dict with keys:
            - 'advance_winners': list of player IDs who advanced
            - 'win_winner': player ID who won overall
            - 'prop_results': dict {prop_id: True/False} for prop outcomes
    
    Returns:
        dict: {bettor_email: total_payout_amount}
    """
    all_payouts = {}
    
    # Calculate advance payouts
    if 'advance_winners' in results:
        advance_payouts = calculate_advance_payouts(session, results['advance_winners'])
        for email, amount in advance_payouts.items():
            all_payouts[email] = all_payouts.get(email, 0.0) + amount
    
    # Calculate win payouts
    if 'win_winner' in results:
        win_payouts = calculate_win_payouts(session, results['win_winner'])
        for email, amount in win_payouts.items():
            all_payouts[email] = all_payouts.get(email, 0.0) + amount
    
    # Calculate prop payouts
    if 'prop_results' in results:
        prop_payouts = calculate_prop_payouts(session, results['prop_results'])
        for email, amount in prop_payouts.items():
            all_payouts[email] = all_payouts.get(email, 0.0) + amount
    
    return {email: round(amount, 2) for email, amount in all_payouts.items()}

def get_payout_summary(session, results):
    """
    Get a summary of all payouts with breakdown by market.
    
    Args:
        session: Database session
        results: dict with results (same as calculate_all_payouts)
    
    Returns:
        dict: Summary with total pools, payouts, and breakdowns
    """
    summary = {
        'total_payouts': {},
        'market_breakdown': {},
        'house_take': HOUSE_TAKE
    }
    
    # Advance market summary
    if 'advance_winners' in results:
        total_advance_pool = session.scalar(select(func.sum(AdvanceBet.amount))) or 0.0
        advance_payouts = calculate_advance_payouts(session, results['advance_winners'])
        summary['market_breakdown']['advance'] = {
            'total_pool': round(total_advance_pool, 2),
            'payout_pool': round(total_advance_pool * (1.0 - HOUSE_TAKE), 2),
            'winners': results['advance_winners'],
            'payouts': advance_payouts
        }
        for email, amount in advance_payouts.items():
            summary['total_payouts'][email] = summary['total_payouts'].get(email, 0.0) + amount
    
    # Win market summary
    if 'win_winner' in results:
        total_win_pool = session.scalar(select(func.sum(WinBet.amount))) or 0.0
        win_payouts = calculate_win_payouts(session, results['win_winner'])
        summary['market_breakdown']['win'] = {
            'total_pool': round(total_win_pool, 2),
            'payout_pool': round(total_win_pool * (1.0 - HOUSE_TAKE), 2),
            'winner': results['win_winner'],
            'payouts': win_payouts
        }
        for email, amount in win_payouts.items():
            summary['total_payouts'][email] = summary['total_payouts'].get(email, 0.0) + amount
    
    # Prop market summary
    if 'prop_results' in results:
        total_prop_pool = session.scalar(select(func.sum(PropBet.amount))) or 0.0
        prop_payouts = calculate_prop_payouts(session, results['prop_results'])
        summary['market_breakdown']['props'] = {
            'total_pool': round(total_prop_pool, 2),
            'payout_pool': round(total_prop_pool * (1.0 - HOUSE_TAKE), 2),
            'results': results['prop_results'],
            'payouts': prop_payouts
        }
        for email, amount in prop_payouts.items():
            summary['total_payouts'][email] = summary['total_payouts'].get(email, 0.0) + amount
    
    # Round all totals
    summary['total_payouts'] = {email: round(amount, 2) for email, amount in summary['total_payouts'].items()}
    
    return summary 