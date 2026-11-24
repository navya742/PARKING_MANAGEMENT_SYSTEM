CREATE DATABASE IF NOT EXISTS neww_parking_management_db;
USE neww_parking_management_db;

CREATE TABLE owner (
    Owner_ID INT AUTO_INCREMENT PRIMARY KEY,
    Owner_Name VARCHAR(100) NOT NULL,
    Contact VARCHAR(15) UNIQUE NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE vehicle (
    Vehicle_ID INT AUTO_INCREMENT PRIMARY KEY,
    Owner_ID INT NOT NULL,
    Vehicle_Number VARCHAR(20) UNIQUE NOT NULL,
    Vehicle_Type ENUM('Two-Wheeler', 'Sedan', 'SUV', 'EV', 'Truck') NOT NULL,
    FOREIGN KEY (Owner_ID) REFERENCES owner(Owner_ID) ON DELETE CASCADE
);


CREATE TABLE parking_slot (
    Slot_ID INT AUTO_INCREMENT PRIMARY KEY,
    Slot_Number VARCHAR(15) UNIQUE NOT NULL,
    Slot_Type ENUM('Two-Wheeler', 'Four-Wheeler', 'EV-Charging', 'Handicapped') NOT NULL,
    Status ENUM('AVAILABLE', 'OCCUPIED', 'RESERVED', 'MAINTENANCE') DEFAULT 'AVAILABLE' NOT NULL
);


CREATE TABLE parking_record (
    Record_ID INT AUTO_INCREMENT PRIMARY KEY,
    Vehicle_ID INT NOT NULL,
    Slot_ID INT NOT NULL,
    Entry_Time DATETIME NOT NULL,
    Exit_Time DATETIME DEFAULT NULL,
    Duration DECIMAL(6, 2) DEFAULT NULL, -- in hours
    Fee DECIMAL(8, 2) DEFAULT NULL,
    FOREIGN KEY (Vehicle_ID) REFERENCES vehicle(Vehicle_ID),
    FOREIGN KEY (Slot_ID) REFERENCES parking_slot(Slot_ID)
);


CREATE TABLE reservation (
    Reservation_ID INT AUTO_INCREMENT PRIMARY KEY,
    Vehicle_ID INT NOT NULL,
    Slot_ID INT NOT NULL,
    Reservation_Time DATETIME NOT NULL,
    Status ENUM('CONFIRMED', 'CANCELLED', 'COMPLETED') DEFAULT 'CONFIRMED' NOT NULL,
    FOREIGN KEY (Vehicle_ID) REFERENCES vehicle(Vehicle_ID),
    FOREIGN KEY (Slot_ID) REFERENCES parking_slot(Slot_ID)
);

CREATE TABLE payment (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Record_ID INT NOT NULL,
    Amount DECIMAL(8, 2) NOT NULL CHECK (Amount >= 0),
    Payment_Date DATETIME NOT NULL,
    Payment_Status ENUM('PAID', 'PENDING', 'FAILED', 'REFUNDED') DEFAULT 'PENDING' NOT NULL,
    FOREIGN KEY (Record_ID) REFERENCES parking_record(Record_ID)
);


CREATE TABLE violation (
    Violation_ID INT AUTO_INCREMENT PRIMARY KEY,
    Vehicle_ID INT NOT NULL,
    Violation_Type VARCHAR(100) NOT NULL,
    Fine DECIMAL(8, 2) NOT NULL CHECK (Fine >= 0),
    Violation_Date DATE NOT NULL,
    Status ENUM('UNPAID', 'PAID', 'DISPUTED') DEFAULT 'UNPAID' NOT NULL,
    FOREIGN KEY (Vehicle_ID) REFERENCES vehicle(Vehicle_ID)
);
-- 1. Insert Owners
INSERT INTO owner (Owner_Name, Contact, Email) VALUES
('Aarav Sharma', '9876543210', 'aarav.sharma@example.com'),
('Isha Verma', '9812345678', 'isha.verma@example.com'),
('Rohan Mehta', '9988776655', 'rohan.mehta@example.com');


INSERT INTO vehicle (Owner_ID, Vehicle_Number, Vehicle_Type) VALUES
(1, 'DL-01-AB-1234', 'Sedan'),
(2, 'UP-16-CD-5678', 'SUV'),
(3, 'DL-04-EF-9012', 'Two-Wheeler');

INSERT INTO parking_slot (Slot_Number, Slot_Type, Status) VALUES
('S-101', 'Four-Wheeler', 'AVAILABLE'),
('S-102', 'Four-Wheeler', 'AVAILABLE'),
('S-103', 'Four-Wheeler', 'AVAILABLE'),
('S-104', 'Four-Wheeler', 'AVAILABLE'),
('S-105', 'Four-Wheeler', 'AVAILABLE'),
('T-201', 'Two-Wheeler', 'AVAILABLE'),
('T-202', 'Two-Wheeler', 'AVAILABLE'),
('T-203', 'Two-Wheeler', 'AVAILABLE'),
('T-204', 'Two-Wheeler', 'AVAILABLE'),
('T-205', 'Two-Wheeler', 'AVAILABLE'),
('E-301', 'EV-Charging', 'AVAILABLE'),
('E-302', 'EV-Charging', 'AVAILABLE'),
('E-303', 'EV-Charging', 'AVAILABLE'),
('E-304', 'EV-Charging', 'AVAILABLE'),
('E-305', 'EV-Charging', 'AVAILABLE'),
('H-401', 'Handicapped', 'AVAILABLE'),
('H-402', 'Handicapped', 'AVAILABLE');
DELIMITER $$
CREATE PROCEDURE RecordVehicleEntry(
    IN p_Vehicle_ID INT,
    IN p_Slot_ID INT
)
BEGIN
    DECLARE slot_curr_status VARCHAR(20);

    START TRANSACTION;
    
    
    SELECT Status INTO slot_curr_status 
    FROM parking_slot 
    WHERE Slot_ID = p_Slot_ID FOR UPDATE;

    IF slot_curr_status = 'AVAILABLE' THEN
        INSERT INTO parking_record (Vehicle_ID, Slot_ID, Entry_Time)
        VALUES (p_Vehicle_ID, p_Slot_ID, NOW());

        UPDATE parking_slot 
        SET Status = 'OCCUPIED' 
        WHERE Slot_ID = p_Slot_ID;

        COMMIT;
    ELSE
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Slot is not available for assignment.';
    END IF;
END $$
DELIMITER ;
DELIMITER $$
CREATE PROCEDURE RecordVehicleExit(
    IN p_Record_ID INT,
    IN p_HourlyRate DECIMAL(8, 2)
)
BEGIN
    DECLARE v_Entry_Time DATETIME;
    DECLARE v_Exit_Time DATETIME;
    DECLARE v_Duration_Hours DECIMAL(6, 2);
    DECLARE v_CalculatedFee DECIMAL(8, 2);
    DECLARE v_Slot_ID INT;

    START TRANSACTION;

    SELECT Entry_Time, Slot_ID INTO v_Entry_Time, v_Slot_ID 
    FROM parking_record 
    WHERE Record_ID = p_Record_ID AND Exit_Time IS NULL FOR UPDATE;

    IF v_Entry_Time IS NOT NULL THEN
        SET v_Exit_Time = NOW();
        
        SET v_Duration_Hours = ROUND(TIMESTAMPDIFF(MINUTE, v_Entry_Time, v_Exit_Time) / 60.0, 2);
        
        
        IF v_Duration_Hours < 1.00 THEN
            SET v_Duration_Hours = 1.00;
        END IF;

        SET v_CalculatedFee = ROUND(v_Duration_Hours * p_HourlyRate, 2);

        UPDATE parking_record 
        SET Exit_Time = v_Exit_Time,
            Duration = v_Duration_Hours,
            Fee = v_CalculatedFee
        WHERE Record_ID = p_Record_ID;

        UPDATE parking_slot 
        SET Status = 'AVAILABLE' 
        WHERE Slot_ID = v_Slot_ID;

        COMMIT;
    ELSE
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Active record not found or already closed.';
    END IF;
END $$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER trg_AfterExit_CreatePayment
AFTER UPDATE ON parking_record
FOR EACH ROW
BEGIN
    IF OLD.Exit_Time IS NULL AND NEW.Exit_Time IS NOT NULL THEN
        INSERT INTO payment (Record_ID, Amount, Payment_Date, Payment_Status)
        VALUES (NEW.Record_ID, NEW.Fee, NOW(), 'PENDING');
    END IF;
END $$
DELIMITER ;
CREATE VIEW vw_LiveOccupancy AS
SELECT 
    ps.Slot_Number,
    ps.Slot_Type,
    ps.Status,
    v.Vehicle_Number,
    o.Owner_Name,
    o.Contact,
    pr.Entry_Time
FROM parking_slot ps
LEFT JOIN parking_record pr ON ps.Slot_ID = pr.Slot_ID AND pr.Exit_Time IS NULL
LEFT JOIN vehicle v ON pr.Vehicle_ID = v.Vehicle_ID
LEFT JOIN owner o ON v.Owner_ID = o.Owner_ID;
CREATE VIEW vw_DailyFinancialAudit AS
SELECT 
    DATE(p.Payment_Date) AS Audit_Date,
    COUNT(p.Payment_ID) AS Total_Transactions,
    SUM(CASE WHEN p.Payment_Status = 'PAID' THEN p.Amount ELSE 0 END) AS Collected_Parking_Revenue,
    SUM(CASE WHEN p.Payment_Status = 'PENDING' THEN p.Amount ELSE 0 END) AS Pending_Parking_Revenue
FROM payment p
GROUP BY DATE(p.Payment_Date);
CALL RecordVehicleEntry(1, 1);

-- 5. Test Entry Procedure (Vehicle 2 takes Slot 2)
CALL RecordVehicleEntry(2, 2);

-- 6. Insert Violations
INSERT INTO violation (Vehicle_ID, Violation_Type, Fine, Violation_Date, Status) VALUES
(3, 'Unauthorized Parking in Fire Lane', 500.00, CURDATE(), 'UNPAID');

-- Verify Live Occupancy View (Slot S-101 and S-102 should be OCCUPIED)
SELECT * FROM vw_LiveOccupancy;

-- 7. Test Exit Procedure (Record_ID 1 exits, hourly rate 50.00)
CALL RecordVehicleExit(1, 50.00);

-- Verify Slot S-101 is now AVAILABLE again
SELECT Slot_Number, Status FROM parking_slot WHERE Slot_ID = 1;

-- Verify Trigger created a pending payment row automatically
SELECT * FROM payment;

UPDATE payment SET Payment_Status = 'PAID' WHERE Record_ID = 1;

-- Check Daily Financial Audit View
SELECT * FROM vw_DailyFinancialAudit;
