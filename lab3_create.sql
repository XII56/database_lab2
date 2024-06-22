DROP DATABASE if EXISTS lab3;
CREATE DATABASE lab3;
USE lab3;

CREATE Table bank(
    bname VARCHAR(20) PRIMARY KEY,
    address VARCHAR(100),
    phone VARCHAR(20),
    department_num INT DEFAULT 0
);

CREATE TABLE department(
    did CHAR(20) PRIMARY KEY,
    dname VARCHAR(20),
    bank_name VARCHAR(20),
    FOREIGN KEY(bank_name) REFERENCES bank(bname) on delete cascade on update cascade
);

CREATE TABLE employee(
    eid CHAR(20) PRIMARY KEY,
    ename VARCHAR(10),
    gender CHAR(1),
    age INT,
    address VARCHAR(100),
    salary INT,
    position VARCHAR(10),
    ID CHAR(20) UNIQUE,
    phone VARCHAR(20),
    department_id CHAR(20),
    password CHAR(128),
    idphoto VARCHAR(128),
    FOREIGN KEY(department_id) REFERENCES department(did) on delete set null on update cascade
);

CREATE Table customer(
    ID CHAR(20) PRIMARY KEY,
    cname VARCHAR(10),
    age INT,
    address VARCHAR(100),
    gender CHAR(1),
    phone VARCHAR(20)
);

CREATE Table account(
    aid CHAR(20) PRIMARY KEY,
    balance INT,
    password CHAR(20),
    ID CHAR(20),
    bank_name VARCHAR(20),
    FOREIGN KEY(ID) REFERENCES customer(ID) on delete cascade on update cascade,
    FOREIGN KEY(bank_name) REFERENCES bank(bname) on delete cascade on update cascade
);

CREATE Table loan(
    lid CHAR(20) PRIMARY KEY,
    amount INT,
    end_date DATE,
    account_id CHAR(20),
    bank_name VARCHAR(20),
    FOREIGN KEY(account_id) REFERENCES account(aid) on delete cascade on update cascade,
    FOREIGN KEY(bank_name) REFERENCES bank(bname) on delete cascade on update cascade
);

-- 创建维护bank下属部门数量的触发器（插入和删除、修改）
DELIMITER //
CREATE TRIGGER update_department_num_insert AFTER INSERT ON department
FOR EACH ROW
BEGIN
    UPDATE bank SET department_num = department_num + 1 WHERE bname = NEW.bank_name;
END//
CREATE TRIGGER update_department_num_delete AFTER DELETE ON department
FOR EACH ROW
BEGIN
    UPDATE bank SET department_num = department_num - 1 WHERE bname = OLD.bank_name;
END//
CREATE TRIGGER update_department_num_update AFTER UPDATE ON department
FOR EACH ROW
BEGIN
    UPDATE bank SET department_num = department_num + 1 WHERE bname = NEW.bank_name;
    UPDATE bank SET department_num = department_num - 1 WHERE bname = OLD.bank_name;
END//
DELIMITER ;


-- 转账存储过程
DELIMITER //
CREATE PROCEDURE transfer(IN from_id CHAR(20),IN to_id CHAR(20),IN amount INT,OUT state INT)
BEGIN
    DECLARE s INT DEFAULT 0;
    DECLARE a INT;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET s = 1;
    START TRANSACTION;
    select count(*) into a from account where aid = from_id or aid = to_id;
    IF a < 2 THEN
        SET s = 2;
    END IF;
    SELECT balance INTO a FROM account WHERE aid = from_id;
    IF a < amount THEN
        SET s = 3;
    ELSE
        UPDATE account SET balance = balance - amount WHERE aid = from_id;
        UPDATE account SET balance = balance + amount WHERE aid = to_id;
    END IF;
    IF s = 0 THEN
        SET state = 0;
        COMMIT;
    ELSE
        SET state = s;
        ROLLBACK;
    END IF;
END//
DELIMITER ;

-- 办理贷款存储过程
DELIMITER //
CREATE PROCEDURE apply_loan(IN loan_id CHAR(20),IN amount INT,IN end_date CHAR(20),IN account_id CHAR(20),IN bank VARCHAR(20),OUT state INT)
BEGIN
    DECLARE s INT DEFAULT 0;
    DECLARE a INT;
    DECLARE return_date DATE;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET s = 1;
    START TRANSACTION;
    select count(*) into a from loan where lid = loan_id;
    IF a > 0 THEN
        SET s = 2;
    END IF;
    select count(*) into a from account where aid = account_id;
    IF a < 1 THEN
        SET s = 3;
    END IF;
    select COUNT(*) into a from bank where bname = bank;
    IF a < 1 THEN
        SET s = 4;
    END IF;
    SET return_date = STR_TO_DATE(end_date,'%Y-%m-%d');
    IF return_date IS NULL or return_date < CURDATE() THEN
        SET s = 5;
    END IF;
    IF amount < 0 THEN
        SET s = 6;
    END IF;
    IF s = 0 THEN
        INSERT INTO loan VALUES(loan_id,amount,return_date,account_id,bank);
        UPDATE account SET balance = balance + amount WHERE aid = account_id;
        SET state = 0;
        COMMIT;
    ELSE
        SET state = s;
        ROLLBACK;
    END IF;
END//
DELIMITER ;

-- 检测输入字符串是否是合法的日期格式
DELIMITER //
CREATE FUNCTION is_date(date_str CHAR(20)) RETURNS INT No SQL
BEGIN
    DECLARE date_val DATE;
    DECLARE result INT DEFAULT 0;
    SET date_val = STR_TO_DATE(date_str,'%Y-%m-%d');
    IF date_val IS NOT NULL THEN
        SET result = 1;
    END IF;
    RETURN result;
END//

-- 偿还贷款存储过程
DELIMITER //
CREATE PROCEDURE repay_loan(IN loan_id CHAR(20),OUT state INT)
BEGIN
    DECLARE s INT DEFAULT 0;
    DECLARE a INT;
    DECLARE repay_amount INT;
    DECLARE repay_account_id CHAR(20);
    DECLARE repay_balance INT;
    DECLARE continue HANDLER FOR SQLEXCEPTION SET s = 1;
    START TRANSACTION;
    select count(*) into a from loan where lid = loan_id;
    IF a < 1 THEN
        SET s = 2;
    END IF;
    SELECT amount,account_id INTO repay_amount,repay_account_id FROM loan WHERE lid = loan_id;
    SELECT balance INTO repay_balance FROM account WHERE aid = repay_account_id;
    IF repay_balance < repay_amount THEN
        SET s = 3;
    END IF;
    IF s = 0 THEN
        UPDATE account SET balance = balance - repay_amount WHERE aid = repay_account_id;
        DELETE FROM loan WHERE lid = loan_id;
        SET state = 0;
        COMMIT;
    ELSE
        SET state = s;
        ROLLBACK;
    END IF;
END//
DELIMITER ;

-- 计算客户贷款偿还能力函数
DELIMITER //
CREATE FUNCTION get_loan_state(customer_id CHAR(20)) RETURNS INT Reads SQL data
BEGIN
    DECLARE total_balance INT;
    DECLARE total_loan INT;
    declare rest INT;
    SELECT SUM(balance) INTO total_balance FROM account WHERE ID = customer_id;
    SELECT SUM(amount) INTO total_loan FROM loan,account WHERE loan.account_id = account.aid AND account.ID = customer_id;
    IF total_balance IS NULL THEN
        SET total_balance = 0;
    END IF;
    IF total_loan IS NULL THEN
        SET total_loan = 0;
    END IF;
    SET rest = total_balance - total_loan;

    RETURN rest;
END//
    



-- 插入银行数据  
INSERT INTO bank (bname, address, phone) VALUES   
('Bank of A', '123 Main St, CityA', '123-456-7890'),  
('Bank of B', '456 Elm St, CityB', '987-654-3210'),  
('Bank of C', '789 Oak St, CityC', '111-222-3333');  
  
-- 插入部门数据  
INSERT INTO department (did, dname, bank_name) VALUES   
('D001', 'Dep 1', 'Bank of A'),  
('D002', 'Dep 2', 'Bank of B'),  
('D003', 'Dep 3', 'Bank of C');  
  
-- 插入员工数据  
INSERT INTO employee (eid, ename, gender, age, address, salary, position, ID, phone, department_id, password) VALUES   
('E001', 'John', 'M', 30, '101 First St, CityA', 50000, 'Manager', 'C12345', '555-1234', 'D001', 'password1'),  
('E002', 'Lisa', 'F', 28, '202 Second St, CityB', 40000, 'Staff', 'C67890', '555-5678', 'D002', 'password2'),  
('E003', 'Mike', 'M', 35, '303 Third St, CityC', 60000, 'Senior', 'C24680', '555-1357', 'D003', 'password3');  
  
-- 插入顾客数据  
INSERT INTO customer (ID, cname, age, address, gender, phone) VALUES   
('C12345', 'Alice', 32, '401 Fourth St, CityA', 'F', '111-2222'),  
('C67890', 'Bob', 24, '502 Fifth St, CityB', 'M', '333-4444'),  
('C24680', 'Eve', 35, '603 Sixth St, CityC', 'F', '555-6666');  
  
-- 插入账户数据  
INSERT INTO account (aid, balance, password, ID, bank_name) VALUES   
('A001', 1000, 'passA', 'C12345', 'Bank of A'),  
('A002', 2500, 'passB', 'C67890', 'Bank of B'),  
('A003', 500, 'passC', 'C24680', 'Bank of C');  
  
-- 插入贷款数据  
INSERT INTO loan (lid, amount, end_date, account_id, bank_name) VALUES   
('L001', 500, '2024-12-31', 'A001', 'Bank of A'),  
('L002', 1000, '2024-11-30', 'A002', 'Bank of B'),  
('L003', 2000, '2024-10-31', 'A003', 'Bank of C');  




