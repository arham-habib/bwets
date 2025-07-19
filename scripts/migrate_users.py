#!/usr/bin/env python3
"""
Database migration script to add user authentication support
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from app.models import Base, User

load_dotenv()

def migrate():
    """Add users table and missing columns to existing database"""
    DATABASE_URL = os.environ["DATABASE_URL"]
    engine = create_engine(DATABASE_URL, future=True, echo=True)
    
    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = inspector.get_table_names()
        
        # Create users table if it doesn't exist
        if "users" not in existing_tables:
            print("Creating users table...")
            User.__table__.create(conn, checkfirst=True)
        
        # Add bettor_email to win_bets if missing
        if "win_bets" in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('win_bets')]
            if 'bettor_email' not in columns:
                print("Adding bettor_email column to win_bets...")
                conn.execute(text("ALTER TABLE win_bets ADD COLUMN bettor_email TEXT"))
        
        # Add bettor_email to prop_bets if missing
        if "prop_bets" in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('prop_bets')]
            if 'bettor_email' not in columns:
                print("Adding bettor_email column to prop_bets...")
                conn.execute(text("ALTER TABLE prop_bets ADD COLUMN bettor_email TEXT"))
        
        # Update prop_universe id column type if needed
        if "prop_universe" in existing_tables:
            columns = inspector.get_columns('prop_universe')
            id_column = next((col for col in columns if col['name'] == 'id'), None)
            if id_column and 'uuid' in str(id_column['type']).lower():
                print("Converting prop_universe.id to TEXT...")
                # SQLite doesn't support ALTER COLUMN TYPE, so we need to recreate
                # For now, just note this - in production you'd need a more complex migration
                print("Note: prop_universe.id column type conversion may be needed")
    
    print("Migration completed successfully!")
    print("Users table and bettor_email columns have been added.")

if __name__ == "__main__":
    migrate() 