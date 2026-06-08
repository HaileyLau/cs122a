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
from datetime import datetime

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
            FOREIGN KEY (uid) REFERENCES Participant(uid) ON DELETE SET NULL
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
    

def insert_admin(uid, email, username, joined, firstname, lastname):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "INSERT INTO User (uid, email, username, joined) VALUES (%s, %s, %s, %s)",
            (uid, email, username, joined)
        )

        cursor.execute(
            "INSERT INTO Administrator (uid, firstname, lastname) VALUES (%s, %s, %s)",
            (uid, firstname, lastname)
        )

        con.commit()

        print("Success")
    except Exception:
        print("Fail")
    finally:
        cursor.close()
        con.close()
 

def add_venue(eid, vid, is_primary):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        if is_primary:
            cursor.execute(
                "SELECT COUNT(*) FROM Hosting WHERE eid = %s AND is_primary = TRUE",
                (eid,)
            )

            count = cursor.fetchone()[0]

            if count > 0:
                print("Fail")
                return
 
        cursor.execute(
            "INSERT INTO Hosting (eid, vid, is_primary) VALUES (%s, %s, %s)",
            (eid, vid, is_primary)
        )

        con.commit()

        print("Success")
    except Exception:
        print("Fail")
    finally:
        cursor.close()
        con.close()

def reserve_slot(eid, snum, uid):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "SELECT is_reserved FROM Slot WHERE eid = %s AND snum = %s",
            (eid, snum)
        )

        row = cursor.fetchone()

        if row is None or row[0]:  # not found or already reserved
            print("Fail")
            return
 
        cursor.execute(
            "UPDATE Slot SET is_reserved = TRUE, uid = %s WHERE eid = %s AND snum = %s",
            (uid, eid, snum)
        )

        con.commit()
        
        print("Success")
    except Exception:
        print("Fail")
    finally:
        cursor.close()
        con.close()

def cancel_reservation(eid, snum, uid):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM Slot WHERE eid = %s AND snum = %s AND uid = %s)",
            (eid, snum, uid)
        )

        participant_reserved = cursor.fetchone()

        # Slot is not reserved by given participant
        if not participant_reserved or participant_reserved[0] == 0:
            print("Fail")
            return False
        
        # Mark slot as unreserved and remove participant
        cursor.execute(
            "UPDATE Slot SET is_reserved = FALSE, uid = NULL WHERE eid = %s AND snum = %s",
            (eid, snum)
        )

        con.commit()

        print("Success")
        return True
    except Exception:
        print("Fail")
        return False
    finally:
        cursor.close()
        con.close()

def update_event(eid, title, datetime):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM Event WHERE eid = %s)",
            (eid,)
        )

        event_exists = cursor.fetchone()

        # Event with given eid does not exist
        if not event_exists or event_exists[0] == 0:
            print("Fail")
            return False
        
        # Update the title and datetime of event
        cursor.execute(
            "UPDATE Event SET title = %s, datetime = %s WHERE eid = %s",
            (title, datetime, eid)
        )

        con.commit()

        print("Success")
        return True
    except Exception:
        print("Fail")
        return False
    finally:
        cursor.close()
        con.close()

def delete_organizer(uid):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "DELETE FROM Organizer WHERE uid = %s",
            (uid,)
        )

        # Organizer with given uid does not exist
        if cursor.rowcount == 0:
            print("Fail")
            return False

        con.commit()

        print("Success")
        return True
    except Exception:
        print("Fail")
        return False
    finally:
        cursor.close()
        con.close()

def available_events():
    pass

def popular_event_types():
   pass
def participant_schedule():
    pass

def organizer_stats(n):
    con = get_sql_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            "SELECT o.uid, u.username, o.department, COUNT(e.eid) FROM Organizer o " \
            "JOIN User u ON o.uid = u.uid JOIN Event e ON o.uid = e.creator_uid " \
            "GROUP BY o.uid, u.username, o.department " \
            "HAVING COUNT(e.eid) >= %s ORDER BY COUNT(e.eid) DESC, o.uid ASC",
            (n,)
        )

        organizers = cursor.fetchall()

        for row in organizers:
            print(f"{row[0]},{row[1]},{row[2]},{row[3]}")

        return organizers
    except Exception:
        return None
    finally:
        cursor.close()
        con.close()

def venue_events():
    pass


def main():
    function_name = sys.argv[1]

    if function_name == "import":
        import_data(sys.argv[2])
    elif function_name == "insertAdmin":
        insert_admin(
            int(sys.argv[2]),   # uid
            sys.argv[3],        # email
            sys.argv[4],        # username
            sys.argv[5],        # joined (YYYY-MM-DD)
            sys.argv[6],        # firstname
            sys.argv[7]         # lastname
        )
    elif function_name == "addVenue":
        is_primary = sys.argv[4].lower() == "true"
        
        # eid vid is_primary
        add_venue(int(sys.argv[2]), int(sys.argv[3]), is_primary)
    elif function_name == "reserveSlot":
        # eid snum uid
        reserve_slot(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif function_name == "cancelReservation":
        # eid snum uid
        cancel_reservation(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif function_name == "updateEvent":
        # eid title datetime
        update_event(int(sys.argv[2]), str(sys.argv[3]), datetime.strptime(sys.argv[4], "%Y-%m-%d %H:%M:%S"))
    elif function_name == "deleteOrganizer":
        # uid
        delete_organizer(int(sys.argv[2]))
    elif function_name == "organizerStats":
        # n
        organizer_stats(int(sys.argv[2]))

if __name__ == "__main__":
    main()