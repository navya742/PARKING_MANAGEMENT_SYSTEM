import sys
import mysql.connector
from mysql.connector import Error
from tabulate import tabulate

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Parampara@110",
    "database": "neww_parking_management_db"
}

def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as err:
        print(f"\n[!] Database Connection Error: {err}")
        return None

def register_vehicle():
    print("\n--- 1. Register Owner & Vehicle ---")
    name = input("Owner Name: ").strip()
    contact = input("Contact Number: ").strip()
    email = input("Email Address: ").strip()
    veh_num = input("Vehicle Registration Number: ").strip()
    print("Types: Two-Wheeler, Sedan, SUV, EV, Truck")
    veh_type = input("Vehicle Type: ").strip()

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute(
            "INSERT INTO owner (Owner_Name, Contact, Email) VALUES (%s, %s, %s)",
            (name, contact, email)
        )
        owner_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO vehicle (Owner_ID, Vehicle_Number, Vehicle_Type) VALUES (%s, %s, %s)",
            (owner_id, veh_num, veh_type)
        )
        conn.commit()
        print(f"[+] Registration successful! Assigned Vehicle ID: {cursor.lastrowid}")
    except Error as e:
        conn.rollback()
        print(f"[!] Error registering vehicle: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def view_slots():
    print("\n--- 2. Parking Slot Status ---")
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT Slot_ID, Slot_Number, Slot_Type, Status FROM parking_slot")
        rows = cursor.fetchall()
        if rows:
            print(tabulate(rows, headers="keys", tablefmt="grid"))
        else:
            print("No slots registered.")
    except Error as e:
        print(f"[!] Query failed: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def vehicle_entry():
    print("\n--- 3. Record Vehicle Entry ---")
    try:
        veh_id = int(input("Enter Vehicle ID: "))
        slot_id = int(input("Enter Slot ID to Assign: "))
    except ValueError:
        print("[!] Invalid integer ID provided.")
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.callproc("RecordVehicleEntry", [veh_id, slot_id])
        conn.commit()
        print(f"[+] Vehicle {veh_id} successfully parked in Slot {slot_id}.")
    except Error as e:
        print(f"[!] Entry transaction failed: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def vehicle_exit():
    print("\n--- 4. Record Vehicle Exit ---")
    try:
        veh_id = int(input("Enter Vehicle ID: "))
        rate = float(input("Enter Hourly Rate (Default 50.00): ") or 50.00)
    except ValueError:
        print("[!] Invalid inputs.")
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT Record_ID FROM parking_record WHERE Vehicle_ID = %s AND Exit_Time IS NULL LIMIT 1",
            (veh_id,)
        )
        record = cursor.fetchone()

        if not record:
            print(f"[!] No active parking record found for Vehicle ID {veh_id}.")
            return

        rec_id = record[0]

        cursor.callproc("RecordVehicleExit", [rec_id, rate])
        conn.commit()
        
        cursor.execute("SELECT Duration, Fee FROM parking_record WHERE Record_ID = %s", (rec_id,))
        result = cursor.fetchone()
        if result:
            print(f"[+] Exit processed for Vehicle ID {veh_id}! Billed Duration: {result[0]} hrs | Total Fee: Rs. {result[1]}")
    except Error as e:
        conn.rollback()
        print(f"[!] Exit transaction failed: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def manage_payments():
    print("\n--- 5. Payment Management ---")
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT Payment_ID, Record_ID, Amount, Payment_Date, Payment_Status FROM payment WHERE Payment_Status = 'PENDING'"
        )
        pending = cursor.fetchall()
        if not pending:
            print("No pending payments found.")
            return

        print(tabulate(pending, headers="keys", tablefmt="grid"))
        pay_id = input("\nEnter Payment ID to mark as PAID (or hit Enter to skip): ").strip()
        if pay_id:
            cursor.execute("UPDATE payment SET Payment_Status = 'PAID' WHERE Payment_ID = %s", (int(pay_id),))
            conn.commit()
            print(f"[+] Payment ID {pay_id} updated to PAID.")
    except ValueError:
        print("[!] Invalid Payment ID.")
    except Error as e:
        print(f"[!] Payment error: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def record_violation():
    print("\n--- 6. Record Violation ---")
    try:
        veh_id = int(input("Enter Vehicle ID: "))
        v_type = input("Violation Description: ").strip()
        fine = float(input("Fine Amount: "))
    except ValueError:
        print("[!] Invalid input.")
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO violation (Vehicle_ID, Violation_Type, Fine, Violation_Date, Status) VALUES (%s, %s, %s, CURDATE(), 'UNPAID')",
            (veh_id, v_type, fine)
        )
        conn.commit()
        print(f"[+] Violation logged with ID: {cursor.lastrowid}")
    except Error as e:
        print(f"[!] Failed to log violation: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def view_audit_reports():
    print("\n--- 7. Reports & Audit ---")
    print("1. Live Occupancy Dashboard")
    print("2. Daily Financial Summary")
    print("0. Back to Main Menu")
    choice = input("Select report: ").strip()

    if choice == "0":
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    try:
        if choice == "1":
            cursor.execute("SELECT * FROM vw_LiveOccupancy")
            rows = cursor.fetchall()
            print(tabulate(rows, headers="keys", tablefmt="grid"))
        elif choice == "2":
            cursor.execute("SELECT * FROM vw_DailyFinancialAudit")
            rows = cursor.fetchall()
            print(tabulate(rows, headers="keys", tablefmt="grid"))
        else:
            print("Invalid report selection.")
    except Error as e:
        print(f"[!] Report generation error: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def delete_vehicle():
    print("\n--- 8. Delete Vehicle Record ---")
    veh_num = input("Enter Vehicle Registration Number to delete (or 0 to go back): ").strip()
    if not veh_num or veh_num == "0":
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT v.Vehicle_ID, v.Vehicle_Number, v.Vehicle_Type, o.Owner_ID, o.Owner_Name
            FROM vehicle v
            JOIN owner o ON v.Owner_ID = o.Owner_ID
            WHERE v.Vehicle_Number = %s
        """, (veh_num,))
        vehicle = cursor.fetchone()

        if not vehicle:
            print(f"[!] No vehicle found with registration number '{veh_num}'.")
            return

        print(f"\nFound: {vehicle['Vehicle_Number']} ({vehicle['Vehicle_Type']}) | Owner: {vehicle['Owner_Name']}")
        confirm = input("Are you sure you want to permanently delete this vehicle and all its history? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("[-] Deletion cancelled.")
            return

        veh_id = vehicle["Vehicle_ID"]
        owner_id = vehicle["Owner_ID"]

        conn.start_transaction()

        cursor.execute("""
            UPDATE parking_slot ps
            JOIN parking_record pr ON ps.Slot_ID = pr.Slot_ID
            SET ps.Status = 'AVAILABLE'
            WHERE pr.Vehicle_ID = %s AND pr.Exit_Time IS NULL
        """, (veh_id,))

        cursor.execute("""
            DELETE p FROM payment p
            JOIN parking_record pr ON p.Record_ID = pr.Record_ID
            WHERE pr.Vehicle_ID = %s
        """, (veh_id,))
        cursor.execute("DELETE FROM parking_record WHERE Vehicle_ID = %s", (veh_id,))
        cursor.execute("DELETE FROM reservation WHERE Vehicle_ID = %s", (veh_id,))
        cursor.execute("DELETE FROM violation WHERE Vehicle_ID = %s", (veh_id,))

        cursor.execute("DELETE FROM vehicle WHERE Vehicle_ID = %s", (veh_id,))

        cursor.execute("SELECT COUNT(*) AS cnt FROM vehicle WHERE Owner_ID = %s", (owner_id,))
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute("DELETE FROM owner WHERE Owner_ID = %s", (owner_id,))

        conn.commit()
        print(f"[+] Vehicle '{veh_num}' and its associated records have been deleted.")

    except Error as e:
        conn.rollback()
        print(f"[!] Failed to delete vehicle: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def add_parking_slot():
    print("\n--- 9. Add New Parking Slot ---")
    slot_num = input("Enter Slot Number (e.g., S-106, T-206, E-306): ").strip().upper()
    if not slot_num:
        print("[!] Slot Number cannot be empty.")
        return

    print("Slot Types: Four-Wheeler, Two-Wheeler, EV-Charging, Handicapped")
    slot_type = input("Enter Slot Type: ").strip()

    valid_types = ("Four-Wheeler", "Two-Wheeler", "EV-Charging", "Handicapped")
    if slot_type not in valid_types:
        print(f"[!] Invalid Slot Type. Choose from: {', '.join(valid_types)}")
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO parking_slot (Slot_Number, Slot_Type, Status) VALUES (%s, %s, 'AVAILABLE')",
            (slot_num, slot_type)
        )
        conn.commit()
        print(f"[+] Slot '{slot_num}' ({slot_type}) added! Assigned Slot ID: {cursor.lastrowid}")
    except Error as e:
        conn.rollback()
        print(f"[!] Failed to add slot: {e.msg}")
    finally:
        cursor.close()
        conn.close()

def main_menu():
    while True:
        print("\n" + "="*50)
        print("  CENTRALISED PARKING & AUDIT MANAGEMENT SYSTEM")
        print("="*50)
        print("1. Register Vehicle & Owner")
        print("2. View Parking Slots")
        print("3. Record Vehicle Entry")
        print("4. Record Vehicle Exit & Calculate Fee")
        print("5. Manage Pending Payments")
        print("6. Record Parking Violation")
        print("7. View Reports & Financial Audits")
        print("8. Delete Vehicle Record")
        print("9. Add Parking Slot")
        print("0. Exit Application")
        
        choice = input("\nEnter choice [0-9]: ").strip()
        if choice == "1":
            register_vehicle()
        elif choice == "2":
            view_slots()
        elif choice == "3":
            vehicle_entry()
        elif choice == "4":
            vehicle_exit()
        elif choice == "5":
            manage_payments()
        elif choice == "6":
            record_violation()
        elif choice == "7":
            view_audit_reports()
        elif choice == "8":
            delete_vehicle()
        elif choice == "9":
            add_parking_slot()
        elif choice == "0":
            print("\nExiting system. Goodbye!")
            sys.exit(0)
        else:
            print("\n[!] Invalid selection, please try again.")

if __name__ == "__main__":
    main_menu()