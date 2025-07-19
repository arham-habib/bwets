#!/usr/bin/env python3
"""
Example script showing how to calculate payouts for the betting system.

This script demonstrates how to use the payouts module to calculate
winnings for users based on event results.
"""

import os
from dotenv import load_dotenv
from app.models import SessionLocal
from app.payouts import calculate_all_payouts, get_payout_summary

load_dotenv()

def example_payout_calculation():
    """Example of how to calculate payouts with sample results."""
    
    # Example results - you would replace these with actual event outcomes
    results = {
        # Players who advanced from heats (example player IDs)
        'advance_winners': [
            'player-123',  # Replace with actual player IDs
            'player-456',
            'player-789'
        ],
        
        # Overall winner
        'win_winner': 'player-123',  # Replace with actual winner ID
        
        # Prop bet results (True = Yes won, False = No won)
        'prop_results': {
            'prop-001': True,   # "Will Nir win?" - Yes won
            'prop-002': False,  # "Will Greg advance?" - No won
            'prop-003': True    # "Will Engineering win?" - Yes won
        }
    }
    
    with SessionLocal() as db:
        # Calculate all payouts
        payouts = calculate_all_payouts(db, results)
        
        # Get detailed summary
        summary = get_payout_summary(db, results)
        
        # Print results
        print("🏆 PAYOUT CALCULATION RESULTS")
        print("=" * 50)
        
        print(f"\n💰 Total Payouts by User:")
        for email, amount in payouts.items():
            print(f"  {email}: ${amount:.2f}")
        
        print(f"\n📊 Market Breakdown:")
        
        if 'advance' in summary['market_breakdown']:
            advance = summary['market_breakdown']['advance']
            print(f"\n  🏁 Advance Market:")
            print(f"    Total Pool: ${advance['total_pool']:.2f}")
            print(f"    Payout Pool: ${advance['payout_pool']:.2f}")
            print(f"    Winners: {len(advance['winners'])} players")
            for email, amount in advance['payouts'].items():
                print(f"      {email}: ${amount:.2f}")
        
        if 'win' in summary['market_breakdown']:
            win = summary['market_breakdown']['win']
            print(f"\n  🏆 Win Market:")
            print(f"    Total Pool: ${win['total_pool']:.2f}")
            print(f"    Payout Pool: ${win['payout_pool']:.2f}")
            print(f"    Winner: {win['winner']}")
            for email, amount in win['payouts'].items():
                print(f"      {email}: ${amount:.2f}")
        
        if 'props' in summary['market_breakdown']:
            props = summary['market_breakdown']['props']
            print(f"\n  🎲 Prop Bets:")
            print(f"    Total Pool: ${props['total_pool']:.2f}")
            print(f"    Payout Pool: ${props['payout_pool']:.2f}")
            for email, amount in props['payouts'].items():
                print(f"      {email}: ${amount:.2f}")
        
        print(f"\n🏦 House Take: {summary['house_take']*100:.1f}%")
        
        total_payout = sum(payouts.values())
        print(f"\n💵 Total Payouts: ${total_payout:.2f}")

def calculate_specific_market_payouts():
    """Example of calculating payouts for specific markets only."""
    
    with SessionLocal() as db:
        # Example: Only advance market results
        advance_results = {
            'advance_winners': ['player-123', 'player-456']
        }
        
        from app.payouts import calculate_advance_payouts
        advance_payouts = calculate_advance_payouts(db, advance_results['advance_winners'])
        
        print("\n🏁 Advance Market Payouts Only:")
        for email, amount in advance_payouts.items():
            print(f"  {email}: ${amount:.2f}")

if __name__ == "__main__":
    print("🎲 Betting Payout Calculator")
    print("This script demonstrates payout calculations for the parimutuel betting system.")
    print("\nNote: Replace the example player IDs and prop IDs with actual results from your event.")
    
    try:
        example_payout_calculation()
        calculate_specific_market_payouts()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the database is set up and contains bet data.") 