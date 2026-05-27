"""
# Install Python MySQL connector
pip3 install mysql-connector-python
# Install MySQL using Homebrew
brew install mysql
# Start MySQL
brew services start mysql
# Check MySQL version
mysql --version
# Stop MySQL
brew services stop mysql
# Delete old/broken MySQL local data
rm -rf /opt/homebrew/var/mysql
# Initialize fresh MySQL with no root password
mysqld --initialize-insecure --user=$(whoami) --datadir=/opt/homebrew/var/mysql
# Start MySQL again
brew services start mysql
# Login to MySQL as root
mysql -uroot

Then inside MySQL:
ALTER USER 'root'@'localhost' IDENTIFIED BY 'rootpassword';

CREATE DATABASE IF NOT EXISTS cs122a;

CREATE USER IF NOT EXISTS 'test'@'localhost'
IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON cs122a.* TO 'test'@'localhost';

FLUSH PRIVILEGES;

exit;


# Test the project database user
mysql -utest -p cs122a # password is "password"
"""

import mysql.connector
import sys
import csv
import os

def get_sql_connection():
    """Establish the database connection"""
    return mysql.connector.connect(user='test', password='password', database='cs122a')

def import_data(folderName):
    """Delete existing tables, and create new tables. Then read the csv files in the given folder
    and import data into the database. You can assume that the folder always contains all
    the necessary CSV files and the files are correct.

    Input:
        python3 project.py import [folderName:str]

    Output:
        Boolean
    """

    print(f"Importing from: {folderName}")

    con = get_sql_connection()
    cursor = con.cursor()

    try:

        # Start with a clean database. Drop child tables first
        cursor.execute("DROP TABLE IF EXISTS Approval")
        cursor.execute("DROP TABLE IF EXISTS Hosting")
        cursor.execute("DROP TABLE IF EXISTS Slot")
        cursor.execute("DROP TABLE IF EXISTS OnCampus")
        cursor.execute("DROP TABLE IF EXISTS OffCampus")
        cursor.execute("DROP TABLE IF EXISTS Event")
        cursor.execute("DROP TABLE IF EXISTS Organizer")
        cursor.execute("DROP TABLE IF EXISTS Participant")
        cursor.execute("DROP TABLE IF EXISTS Administrator")
        cursor.execute("DROP TABLE IF EXISTS Venue")
        cursor.execute("DROP TABLE IF EXISTS User")

        ### DDL from HW 2 ###

        # User
        cursor.execute("""
        CREATE TABLE User (
            uid INT,
            email TEXT NOT NULL,
            username TEXT NOT NULL,
            joined DATE NOT NULL,
            PRIMARY KEY (uid)
        );
        """)

        # Organizer
        cursor.execute("""
        CREATE TABLE Organizer (
            uid INT,
            department TEXT NOT NULL,
            experience INT NOT NULL,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        );
        """)

        # Participant
        cursor.execute("""
        CREATE TABLE Participant (
            uid INT,
            type TEXT,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        );
        """)

        # Administrator
        cursor.execute("""
        CREATE TABLE Administrator (
            uid INT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            PRIMARY KEY (uid),
            FOREIGN KEY (uid) REFERENCES User(uid) ON DELETE CASCADE
        );
        """)
        
        # Event
        cursor.execute("""
        CREATE TABLE Event (
            eid INT,
            creator_uid INT NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            datetime DATETIME NOT NULL,
            PRIMARY KEY (eid),
            FOREIGN KEY (creator_uid) REFERENCES Organizer(uid) ON DELETE CASCADE
        );
        """)

        # Slot
        cursor.execute("""
        CREATE TABLE Slot (
            eid INT,
            snum INT NOT NULL,
            is_reserved BOOLEAN NOT NULL,
            uid INT,
            PRIMARY KEY (eid, snum),
            FOREIGN KEY (eid) REFERENCES Event(eid) ON DELETE CASCADE,
            FOREIGN KEY (uid) REFERENCES Participant(uid) ON DELETE CASCADE
        );
        """)

        # Venue
        cursor.execute("""
        CREATE TABLE Venue (
            vid INT,
            street TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            PRIMARY KEY (vid)
        );
        """)

        # OnCampus
        cursor.execute("""
        CREATE TABLE OnCampus (
            vid INT,
            code TEXT NOT NULL,
            PRIMARY KEY (vid),
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        );
        """)

        # OffCampus
        cursor.execute("""
        CREATE TABLE OffCampus (
            vid INT,
            distance INT NOT NULL,
            PRIMARY KEY (vid),
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        );
        """)

        # Hosting
        cursor.execute("""
        CREATE TABLE Hosting (
            eid INT NOT NULL,
            vid INT NOT NULL,
            is_primary BOOLEAN NOT NULL,
            PRIMARY KEY (eid, vid),
            FOREIGN KEY (eid) REFERENCES Event(eid) ON DELETE CASCADE,
            FOREIGN KEY (vid) REFERENCES Venue(vid) ON DELETE CASCADE
        );
        """)

        # Approval
        cursor.execute("""
        CREATE TABLE Approval (
            uid INT NOT NULL,
            vid INT NOT NULL,
            valid_from DATE NOT NULL,
            valid_until DATE NOT NULL,
            PRIMARY KEY (uid, vid),
            FOREIGN KEY (uid) REFERENCES Administrator(uid) ON DELETE CASCADE,
            FOREIGN KEY (vid) REFERENCES OffCampus(vid) ON DELETE CASCADE
        );
        """)

        ### Import data from CSV files into correct table ###
        tables = ["User", "Organizer", "Participant", "Administrator", "Event", "Slot", "Venue", "OnCampus", "OffCampus", "Hosting", "Approval"]
        for table in tables:
            file_path = os.path.join(folderName, f"{table}.csv")
            with open(file_path, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    # If the input is NULL, treat it as the None type in Python
                    for i in range(len(row)):
                        if row[i] == "NULL":
                            row[i] = None
                    placeholders = ", ".join(["%s"] * len(row))
                    sql = f"INSERT INTO {table} VALUES ({placeholders})"
                    cursor.execute(sql, row)
        
        con.commit()
        print("Success")

    except:
        print("Fail")

    finally:
        cursor.close()
        con.close()
    

def insert_admin():
    pass

def add_venue():
    pass

def reserve_slot():
   pass

def cancel_reservation():
   pass

def update_event():
    pass

def delete_organizer():
    pass

def available_events():
    pass

def popular_event_types():
   pass
def participant_schedule():
    pass

def organizer_stats():
   pass

def venue_events():
    pass


def main():
    function_name = sys.argv[1]

    if function_name == "import":
        import_data(sys.argv[2])

if __name__ == "__main__":
    main()