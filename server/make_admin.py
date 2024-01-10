import sqlite3
import argparse
from decouple import config
from dotenv import load_dotenv

DB_PATH = config('DB_DB_PATH')

#pass email as argument in order to make user admin

parser = argparse.ArgumentParser()
parser.add_argument("--email", help="email of user to make admin")
args = parser.parse_args()
email = args.email

#modify user permission to admin
def make_admin(email):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE User SET principal = 'admin' WHERE email = '{email}'")
        conn.commit()
        conn.close()
        print(f"User with email: {email} is now an admin")
    except Exception as e:
        print(e)

make_admin(email)

