# Centralised Vehicle Parking and Audit Management System

A relational database and interactive Python CLI application designed to automate vehicle parking allocation, real-time occupancy tracking, hourly fee calculation, violation logging, and financial auditing.

---

## Key Features

* **Owner & Vehicle Registration:** Atomic multi-table inserts linking owners (`owner`) to registered vehicles (`vehicle`) with `ON DELETE CASCADE` support.
* **Concurrency-Safe Slot Assignment:** Uses the `RecordVehicleEntry` stored procedure with row-level locking (`SELECT ... FOR UPDATE`) to prevent double-booking of slots.
* **Automated Billing & Fee Calculation:** Computes parking duration (with a 1-hour minimum billing rule) and dynamically frees slots upon exit via `RecordVehicleExit`.
* **Event-Driven Payment Generation:** An `AFTER UPDATE` trigger (`trg_AfterExit_CreatePayment`) automatically generates pending billing records in the `payment` table as soon as a vehicle exits.
* **Compliance & Violation Tracking:** Logs unauthorized parking incidents and unpaid fines per vehicle.
* **Real-Time Operational & Audit Views:** Uses SQL views (`vw_LiveOccupancy` and `vw_DailyFinancialAudit`) to monitor live slot status and daily collected vs. pending revenue.
* **Interactive Python CLI:** Menu-driven terminal interface built with `mysql-connector-python` and `tabulate` for end-to-end management.

---

## Tech Stack

* **Database:** MySQL 8.0+
* **Backend / CLI:** Python 3.x
* **Python Libraries:** `mysql-connector-python`, `tabulate`

---

## Database Architecture

The database (`final_parking_management_db`) is normalized to 3NF and comprises **7 relational tables**:

| Table | Description |
| :--- | :--- |
| `owner` | Stores vehicle owner contact details (`Owner_ID`, `Owner_Name`, `Contact`, `Email`). |
| `vehicle` | Stores registered vehicles linked to owners (`Vehicle_ID`, `Owner_ID`, `Vehicle_Number`, `Vehicle_Type`). |
| `parking_slot` | Tracks individual parking spaces, types (`Two-Wheeler`, `Four-Wheeler`, `EV-Charging`, `Handicapped`), and live status. |
| `parking_record` | Logs active and historical entry/exit timestamps, billed duration, and calculated fees. |
| `reservation` | Manages advance slot bookings (`CONFIRMED`, `CANCELLED`, `COMPLETED`). |
| `payment` | Tracks generated invoices and payment statuses (`PAID`, `PENDING`, `FAILED`, `REFUNDED`). |
| `violation` | Records parking infractions, fine amounts, and payment statuses (`UNPAID`, `PAID`, `DISPUTED`). |

### Stored Procedures, Triggers & Views
* **Procedures:** `RecordVehicleEntry(p_Vehicle_ID, p_Slot_ID)`, `RecordVehicleExit(p_Record_ID, p_HourlyRate)`
* **Trigger:** `trg_AfterExit_CreatePayment`
* **Views:** `vw_LiveOccupancy`, `vw_DailyFinancialAudit`

---

## Project Structure

```text
├── schema.sql        # Complete DDL, sample data, stored procedures, trigger, and views
├── app.py            # Interactive Python CLI application
└── README.md         # Project documentation
