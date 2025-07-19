#!/usr/bin/env python3
"""
Database migration script to add the users table
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app.models import Base, User

load_dotenv()

def migrate():
    """Add users table to existing database"""
    DATABASE_URL = os.environ["DATABASE_URL"]
    engine = create_engine(DATABASE_URL, future=True, echo=True)
    
    # Create the users table
    User.__table__.create(engine, checkfirst=True)
    
    print("Migration completed successfully!")
    print("Users table has been created.")

if __name__ == "__main__":
    migrate() 