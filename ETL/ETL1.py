import os
import hashlib
import requests
from typing import List
from dotenv import load_dotenv
from datetime import datetime
from models.data_types import Post
from sqlalchemy import text, inspect
from core.session import Session, engine

load_dotenv()

def load_date()->List[Post]:
    '''
    Sends a GET request to the source REST API and retrieves raw JSON data. 
    The function uses the SOURCE URL environment variable to access the external API endpoint.

    Returns:
        List[Post]:
            A list of dictionaries containing
            posts data received from the API.

    Raises:
        ValueError:
            If SOURCE_URL is not specified
            in environment variables.
        
        requests.HTTPError:
            If the HTTP request returns
            an unsuccessful status code.

        requests.RequestsException:
            For network-related errors during
            the request execution.
    '''
    source_url = os.getenv('SOURCE_URL')
    if source_url is None:
        raise ValueError('SOURCE_URL is not configured')
    response = requests.get(url=source_url)
    response.raise_for_status()
    return response.json()

def hashing(value: str)->str:
    '''
    Generates a SHA-256 hash for the given string value.

    The function encodes the input string into UTF-8
    bytes and returns its hexadecimal hash representation.

    Args:
        value (str):
            Input string to be hashed.

    Returns:
        str:
            SHA-256 hash in hexadecimal format.
    '''
    return hashlib.sha256(value.encode()).hexdigest()

def load_to_stg(data: List[Post])->None:
    '''
    Loads raw post data into the STG layer.

    The function performs the following operations:
        - checks whether the STG table exists;
        - creates the table using DDL if it does not exist;
        - generates a hash for each record;
        - inserts source data into the staging table.

    Args:
        data (List[Post]):
            A list of post records received
            from the source REST API.

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError:
            If an error occurs during SQL execution
            or transaction processing.

        FileNotFoundError:
            If the STG DDL file cannot be found.

        Exception:
            Re-raises any database-related exception
            after rolling back the transaction.
    '''
    inspector = inspect(engine)
    if not inspector.has_table('post_stg', schema='stg'):
        with open('DDL/STG.sql', 'r', encoding='utf-8') as f:
            ddl_sql = f.read()
        with Session() as session:
            try:
                session.execute(text(ddl_sql))
                session.commit()
            except Exception as e:
                session.rollback()

    load_dttm = datetime.now()
    insert_query = text("""
        INSERT INTO stg.post_stg (
            load_dttm,
            source_system,
            post_id,
            user_id,
            title,
            body,
            record_hash
        )
        VALUES (
            :load_dttm,
            :source_system,
            :post_id,
            :user_id,
            :title,
            :body,
            :record_hash
        )
    """)
    with Session() as session:
        try:
            for row in data:
                record_hash = hashing(f"{row['id']}_{row['userId']}_{row['title']}_{row['body']}")
                session.execute(
                    insert_query,
                    {
                        "load_dttm": load_dttm,
                        "source_system": os.getenv('SOURCE_SYSTEM'),
                        "post_id": row['id'],
                        "user_id": row["userId"],
                        "title": row["title"],
                        "body": row["body"],
                        "record_hash": record_hash
                    }
                )
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

if __name__ == "__main__":
    date = load_date()
    load_to_stg(data=date)