import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlite3

from sqlite_models import Impression, DataCampaign

DATABASE_URL = "sqlite:///./mab.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def print_tables(db_path="mab.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", [t[0] for t in tables])

    # Dump contents of each table
    for (table_name,) in tables:
        print(f"\n--- {table_name} ---")
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print(columns)

        # Print rows
        for row in rows:
            print(row)

    conn.close()

if __name__ == "__main__":
    import sys

    db = SessionLocal()

    def clear_impressions_all():
        deleted = db.query(Impression).delete()
        print(f"Deleted {deleted} impressions.")

    def clear_impressions_campaign(campaign_id):
        deleted = db.query(Impression).filter(Impression.data_campaign_id == campaign_id).delete()
        print(f"Deleted {deleted} impressions for data_campaign_id={campaign_id}.")

    def clear_data_campaigns_all():
        # Clear impressions first, then data campaigns
        clear_impressions_all()
        deleted = db.query(DataCampaign).delete()
        print(f"Deleted {deleted} data campaigns.")

    def clear_data_campaign_campaign(campaign_id):
        clear_impressions_campaign(campaign_id)
        deleted = db.query(DataCampaign).filter(DataCampaign.id == campaign_id).delete()
        print(f"Deleted {deleted} data campaigns with id={campaign_id}.")

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == "print":
            print_tables()

        elif cmd == "clear":
            if len(sys.argv) < 3:
                print("Please specify what to clear: 'imp' or 'camp'")
            else:
                subcmd = sys.argv[2].lower()

                if subcmd == "imp":
                    if len(sys.argv) == 4:
                        # clear impressions for campaign
                        try:
                            campaign_id = int(sys.argv[3])
                            confirm = input(f"Clear impressions for data_campaign_id={campaign_id}? (yes/no): ").strip().lower()
                            if confirm == "yes":
                                clear_impressions_campaign(campaign_id)
                                db.commit()
                            else:
                                print("Aborted.")
                        except ValueError:
                            print("Invalid campaign ID.")
                    else:
                        # clear all impressions
                        confirm = input("Clear ALL impressions? (yes/no): ").strip().lower()
                        if confirm == "yes":
                            clear_impressions_all()
                            db.commit()
                        else:
                            print("Aborted.")

                elif subcmd == "camp":
                    if len(sys.argv) == 4:
                        # clear specific data campaign and impressions
                        try:
                            campaign_id = int(sys.argv[3])
                            confirm = input(f"Clear data campaign id={campaign_id} AND its impressions? (yes/no): ").strip().lower()
                            if confirm == "yes":
                                clear_data_campaign_campaign(campaign_id)
                                db.commit()
                            else:
                                print("Aborted.")
                        except ValueError:
                            print("Invalid campaign ID.")
                    else:
                        # clear all data campaigns and impressions
                        confirm = input("Clear ALL data campaigns AND impressions? (yes/no): ").strip().lower()
                        if confirm == "yes":
                            clear_data_campaigns_all()
                            db.commit()
                        else:
                            print("Aborted.")
                else:
                    print("Unknown clear command. Use 'imp' or 'camp'.")

        else:
            print("Unknown command. Usage:")
            print("  python db_utils.py print")
            print("  python db_utils.py clear imp [<data_campaign_id>]  <= Clears All Impressions or the impressions for one data campaign")
            print("  python db_utils.py clear camp [<data_campaign_id>]  <= Clears All DataCampaigns or a single campaign, and its impressions")
    else:
        print("No command provided. Usage:")
        print("  python db_utils.py print")
        print("  python db_utils.py clear imp [<data_campaign_id>] <= Clears All Impressions or the impressions for one data campaign" )
        print("  python db_utils.py clear camp [<data_campaign_id>]  <= Clears All DataCampaigns or a single campaign, and its impressions")
    db.close()
