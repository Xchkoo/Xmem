#!/usr/bin/env python3
"""初始化数据库表结构"""
import asyncio
import os
import sys

# Ensure we can import app modules
sys.path.append(os.getcwd())

from sqlalchemy import inspect
from app.db import engine, Base
# Import models to ensure they are registered with Base.metadata
from app import models 

async def init():
    print("Checking database state...")
    try:
        async with engine.begin() as conn:
            # Check if users table exists using run_sync
            def check_users(connection):
                inspector = inspect(connection)
                return inspector.has_table("users")

            exists = await conn.run_sync(check_users)
            
            if not exists:
                print("Database is empty. Initializing tables from models...")
                await conn.run_sync(Base.metadata.create_all)
                print("Tables created successfully.")
                return True
            else:
                print("Tables already exist. Skipping initialization.")
                return False
    except Exception as e:
        print(f"Error checking/initializing database: {e}")
        raise

if __name__ == "__main__":
    try:
        should_stamp = asyncio.run(init())
        if should_stamp:
            print("Stamping alembic to head...")
            # We assume alembic is installed and in path
            result = os.system("alembic stamp head")
            if result != 0:
                print("Error: Failed to stamp alembic head.")
                sys.exit(1)
            print("Alembic stamped to head.")
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)