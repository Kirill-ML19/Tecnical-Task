import os
import hashlib
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import inspect, text

from core.session import Session, engine


load_dotenv()


def hashing(value: str) -> str:
    '''
    Generates a SHA-256 hash from the given string.

    The function encodes the input string using UTF-8
    and returns a hexadecimal hash representation.

    Args:
        value (str):
            Input value to hash.

    Returns:
        str:
            SHA-256 hash as a hexadecimal string.
    '''
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def check_table() -> None:
    '''
    Checks whether all required DDS tables exist.

    The function:
        - retrieves the list of existing tables from the DDS schema;
        - compares them with the required table set;
        - executes the DDS DDL script if one or more tables are missing.

    Required DDS tables:
        - hub_user
        - hub_post
        - link_user_post
        - sat_post_details

    Returns:
        None

    Raises:
        FileNotFoundError:
            If the DDS.sql file cannot be found.

        sqlalchemy.exc.SQLAlchemyError:
            If an error occurs during SQL execution.

        Exception:
            Re-raises any exception after rolling
            back the current transaction.
    '''
    inspector = inspect(engine)

    required_tables = {
        "hub_user",
        "hub_post",
        "link_user_post",
        "sat_post_details"
    }

    existing_tables = set(
        inspector.get_table_names(schema="dds")
    )

    if not required_tables.issubset(existing_tables):

        with open(
            file="DDL/DDS.sql",
            mode="r",
            encoding="utf-8"
        ) as f:
            ddl_sql = f.read()

        with Session() as session:
            try:
                session.execute(text(ddl_sql))
                session.commit()

            except Exception as e:
                session.rollback()
                raise e


def load_to_dds() -> None:
    '''
    Loads transformed data from the STG layer
    into the DDS layer using the Data Vault 2.0 model.

    The function performs the following operations:

    1. Loads unique users into HUB_USER.
    2. Loads unique posts into HUB_POST.
    3. Loads relationships between users and posts
       into LINK_USER_POST.
    4. Loads descriptive post attributes into
       SAT_POST_DETAILS.

    Tables affected:
        - dds.hub_user
        - dds.hub_post
        - dds.link_user_post
        - dds.sat_post_details

    Returns:
        None

    Raises:
        sqlalchemy.exc.SQLAlchemyError:
            If an error occurs during SQL execution
            or transaction handling.

        Exception:
            Re-raises any exception after performing
            transaction rollback.

    Notes:
        - HUB tables store business keys.
        - LINK tables store relationships between hubs.
        - SATELLITE tables store descriptive attributes.
    '''
    load_dttm = datetime.now()

    source_system = os.getenv("SOURCE_SYSTEM")

    with Session() as session:

        try:

            users_query = text("""
                SELECT DISTINCT user_id
                FROM stg.post_stg
            """)

            users = session.execute(
                users_query
            ).fetchall()

            hub_user_insert = text("""
                INSERT INTO dds.hub_user (
                    hub_user_hash_key,
                    user_id,
                    load_dttm,
                    record_source
                )
                SELECT
                    :hub_user_hash_key,
                    :user_id,
                    :load_dttm,
                    :record_source
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dds.hub_user
                    WHERE hub_user_hash_key = :hub_user_hash_key
                )
            """)

            for user in users:

                user_id = user.user_id

                hub_user_hash_key = hashing(
                    str(user_id)
                )

                session.execute(
                    hub_user_insert,
                    {
                        "hub_user_hash_key": hub_user_hash_key,
                        "user_id": user_id,
                        "load_dttm": load_dttm,
                        "record_source": source_system
                    }
                )

            posts_query = text("""
                SELECT DISTINCT post_id
                FROM stg.post_stg
            """)

            posts = session.execute(
                posts_query
            ).fetchall()

            hub_post_insert = text("""
                INSERT INTO dds.hub_post (
                    hub_post_hash_key,
                    post_id,
                    load_dttm,
                    record_source
                )
                SELECT
                    :hub_post_hash_key,
                    :post_id,
                    :load_dttm,
                    :record_source
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dds.hub_post
                    WHERE hub_post_hash_key = :hub_post_hash_key
                )
            """)

            for post in posts:

                post_id = post.post_id

                hub_post_hash_key = hashing(
                    str(post_id)
                )

                session.execute(
                    hub_post_insert,
                    {
                        "hub_post_hash_key": hub_post_hash_key,
                        "post_id": post_id,
                        "load_dttm": load_dttm,
                        "record_source": source_system
                    }
                )

            links_query = text("""
                SELECT DISTINCT
                    user_id,
                    post_id
                FROM stg.post_stg
            """)

            links = session.execute(
                links_query
            ).fetchall()

            links_insert = text("""
                INSERT INTO dds.link_user_post (
                    link_user_post_hash_key,
                    hub_user_hash_key,
                    hub_post_hash_key,
                    load_dttm,
                    record_source
                )
                SELECT
                    :link_user_post_hash_key,
                    :hub_user_hash_key,
                    :hub_post_hash_key,
                    :load_dttm,
                    :record_source
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dds.link_user_post
                    WHERE link_user_post_hash_key = :link_user_post_hash_key
                )
            """)

            for link in links:

                user_id = link.user_id
                post_id = link.post_id

                hub_user_hash_key = hashing(
                    str(user_id)
                )

                hub_post_hash_key = hashing(
                    str(post_id)
                )

                link_user_post_hash_key = hashing(
                    f"{user_id}|{post_id}"
                )

                session.execute(
                    links_insert,
                    {
                        "link_user_post_hash_key": link_user_post_hash_key,
                        "hub_user_hash_key": hub_user_hash_key,
                        "hub_post_hash_key": hub_post_hash_key,
                        "load_dttm": load_dttm,
                        "record_source": source_system
                    }
                )

            satellite_query = text("""
                SELECT
                    post_id,
                    title,
                    body
                FROM stg.post_stg
            """)

            satellite_rows = session.execute(
                satellite_query
            ).fetchall()

            satellite_insert = text("""
                INSERT INTO dds.sat_post_details (
                    hub_post_hash_key,
                    title,
                    body,
                    hash_diff,
                    load_dttm,
                    record_source
                )
                SELECT
                    :hub_post_hash_key,
                    :title,
                    :body,
                    :hash_diff,
                    :load_dttm,
                    :record_source
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dds.sat_post_details
                    WHERE hub_post_hash_key = :hub_post_hash_key
                      AND hash_diff = :hash_diff
                )
            """)

            for row in satellite_rows:

                post_id = row.post_id

                title = row.title
                body = row.body

                hub_post_hash_key = hashing(
                    str(post_id)
                )

                hash_diff = hashing(
                    f"{title or ''}|{body or ''}"
                )

                session.execute(
                    satellite_insert,
                    {
                        "hub_post_hash_key": hub_post_hash_key,
                        "title": title,
                        "body": body,
                        "hash_diff": hash_diff,
                        "load_dttm": load_dttm,
                        "record_source": source_system
                    }
                )

            session.commit()

        except Exception as e:

            session.rollback()

            raise e


if __name__ == "__main__":

    check_table()

    load_to_dds()