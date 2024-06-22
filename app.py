from flask import Flask,url_for,render_template,request,redirect,flash,session
from datetime import datetime
import pymysql
import os
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

def is_valid_date(input_string):  
    try:  
        datetime.strptime(input_string, '%Y-%m-%d')  
        return True  
    except ValueError:  
        return False  

app	= Flask(__name__)
app.secret_key = 'dev'
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.getcwd(), "idphoto")
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)

class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, u'只能上传图片！'), 
        FileRequired(u'文件未选择！')])
    submit = SubmitField(u'上传')


database = pymysql.connect(host="127.0.0.1", user="root", password="lcf667808", database="lab3", port=3306) 

@app.route('/',methods=['GET','POST'])
def	login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']

        if not userid or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        cursor = database.cursor()
        cursor.execute('select * from Employee where eid = %s',userid)
        user = cursor.fetchone()
        if user is None:
            flash('Invalid userid.')
            return redirect(url_for('login'))
        if user[10] == password:
            session['user_id'] = user[0]
            session['password'] = user[10]
            return redirect(url_for('bank'))
        flash('Invalid password.')
        return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/bank',methods=['GET','POST'])
def bank():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from bank')
        banks = cursor.fetchall()
        return render_template('bank.html',banks=banks)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        bank_name = request.form['bank_name']
        bank_address = request.form['bank_address']
        bank_phone = request.form['bank_phone']
        bank_department_num = request.form['bank_department_num']

        if 'add' in request.form:
            if not bank_name:
                flash('Invalid input.')
                return redirect(url_for('bank'))
            cursor = database.cursor()
            cursor.execute('select bname from bank where bname = %s',bank_name)
            if cursor.fetchone():
                flash('Bank already exists.')
                return redirect(url_for('bank'))
            cursor.execute('insert into bank(bname,address,phone) values(%s,%s,%s)',(bank_name,bank_address,bank_phone))
            database.commit()
            flash('Bank added.')
            return redirect(url_for('bank'))
        elif 'search' in request.form:
            query = "SELECT * FROM bank WHERE 1=1"  
            params = []  
            if bank_name:  
                query += " AND bname = %s"  
                params.append(bank_name)  
            if bank_address:  
                query += " AND address = %s"  
                params.append(bank_address)  
            if bank_phone:  
                query += " AND phone = %s"  
                params.append(bank_phone)
            if bank_department_num:
                try:
                    bank_department_num = int(bank_department_num)
                except ValueError:
                    flash('Invalid department number.')
                    return redirect(url_for('bank'))
                query += " AND department_num = %s"
                params.append(bank_department_num)
            cursor = database.cursor()
            cursor.execute(query, params) 
            banks = cursor.fetchall()
            return render_template('bank.html',banks=banks)

@app.route('/bank/update/<bank_name>',methods=['GET','POST'])
def bank_edit(bank_name):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    cursor = database.cursor()
    cursor.execute('select * from bank where bname = %s',bank_name)
    bank = cursor.fetchone()
    if request.method == 'POST':
        new_bank_name = request.form['bank_name']
        new_bank_address = request.form['bank_address']
        new_bank_phone = request.form['bank_phone']
        if new_bank_name != bank_name:
            cursor.execute('select bname from bank where bname = %s',new_bank_name)
            if cursor.fetchone():
                flash('Bankname already exists.')
                return redirect(url_for('bank'))
        cursor.execute('update bank set bname = %s,address = %s,phone = %s where bname = %s',(new_bank_name,new_bank_address,new_bank_phone,bank_name))
        database.commit()
        flash('Bank updated.')
        return redirect(url_for('bank'))
    return render_template('bank_edit.html',bank=bank)

@app.route('/bank/delete/<bank_name>',methods=['POST'])
def bank_delete(bank_name):
    cursor = database.cursor()
    cursor.execute('delete from bank where bname = %s',bank_name)
    database.commit()
    flash('Bank deleted.')
    return redirect(url_for('bank'))

@app.route('/department',methods=['GET','POST'])
def department():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from department')
        departments = cursor.fetchall()
        return render_template('department.html',departments=departments)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        department_id = request.form['department_id']
        department_name = request.form['department_name']
        department_bank = request.form['department_bank']

        if 'add' in request.form:
            if not department_id or not department_bank:
                flash('Invalid input.')
                return redirect(url_for('department'))
            cursor = database.cursor()
            cursor.execute('select did from department where did = %s',department_id)
            if cursor.fetchone():
                flash('Department already exists.')
                return redirect(url_for('department'))
            cursor.execute('select bname from bank where bname = %s',department_bank)
            if not cursor.fetchone():
                flash('Bank does not exist.')
                return redirect(url_for('department'))
            cursor.execute('insert into department(did,dname,bank_name) values(%s,%s,%s)',(department_id,department_name,department_bank))
            database.commit()
            flash('Department added.')
            return redirect(url_for('department'))
        elif 'search' in request.form:
            query = "SELECT * FROM department WHERE 1=1"  
            params = []  
            if department_id:  
                query += " AND did = %s"  
                params.append(department_id)  
            if department_name:  
                query += " AND dname = %s"  
                params.append(department_name)  
            if department_bank:  
                query += " AND bank_name = %s"  
                params.append(department_bank)  
            cursor = database.cursor()
            cursor.execute(query, params) 
            departments = cursor.fetchall()
            return render_template('department.html',departments=departments)
        
@app.route('/department/update/<department_id>',methods=['GET','POST'])
def department_edit(department_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    cursor = database.cursor()
    cursor.execute('select * from department where did = %s',department_id)
    department = cursor.fetchone()
    if request.method == 'POST':
        new_department_id = request.form['department_id']
        new_department_name = request.form['department_name']
        new_department_bank = request.form['department_bank']
        if new_department_id != department_id:
            cursor.execute('select did from department where did = %s',new_department_id)
            if cursor.fetchone():
                flash('Department already exists.')
                return redirect(url_for('department'))
        cursor.execute('select bname from bank where bname = %s',new_department_bank)
        if not cursor.fetchone():
            flash('Bank does not exist.')
            return redirect(url_for('department'))
        cursor.execute('update department set did = %s,dname = %s,bank_name = %s where did = %s',(new_department_id,new_department_name,new_department_bank,department_id))
        database.commit()
        flash('Department updated.')
        return redirect(url_for('department'))
    return render_template('department_edit.html',department=department)

@app.route('/department/delete/<department_id>',methods=['POST'])
def department_delete(department_id):
    cursor = database.cursor()
    cursor.execute('delete from department where did = %s',department_id)
    database.commit()
    flash('Department deleted.')
    return redirect(url_for('department'))

@app.route('/employee',methods=['GET','POST'])
def employee():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from Employee')
        employees = cursor.fetchall()
        return render_template('employee.html',employees=employees)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        employee_eid = request.form['employee_eid']
        employee_name = request.form['employee_name']
        employee_gender = request.form['employee_gender']
        employee_age = request.form['employee_age']
        employee_address = request.form['employee_address']
        employee_salary = request.form['employee_salary']
        employee_position = request.form['employee_position']
        employee_id = request.form['employee_id']
        employee_phone = request.form['employee_phone']
        employee_department = request.form['employee_department']
        employee_password = request.form['employee_password']

        if not employee_age:
            employee_age = None
        else:
            try:
                employee_age = int(employee_age)
            except ValueError:
                flash('Invalid age.')
                return redirect(url_for('employee'))
            
        if not employee_salary:
            employee_salary = None
        else:
            try:
                employee_salary = int(employee_salary)
            except ValueError:
                flash('Invalid salary.')
                return redirect(url_for('employee'))
            

        if 'add' in request.form:
            if not employee_eid or not employee_department:
                flash('Invalid input.')
                return redirect(url_for('employee'))
            cursor = database.cursor()
            cursor.execute('select eid from Employee where eid = %s',employee_eid)
            if cursor.fetchone():
                flash('Employeeid already exists.')
                return redirect(url_for('employee'))
            
            cursor.execute('select did from department where did = %s',employee_department)
            if not cursor.fetchone():
                flash('Department does not exist.')
                return redirect(url_for('employee'))
            
            cursor.execute('select ID from Employee where ID = %s',employee_id)
            if cursor.fetchone():
                flash('ID already exists.')
                return redirect(url_for('employee'))

            cursor.execute('insert into Employee(eid,ename,gender,age,address,salary,position,ID,phone,department_id,password) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(employee_eid,employee_name,employee_gender,employee_age,employee_address,employee_salary,employee_position,employee_id,employee_phone,employee_department,employee_password)) 
            database.commit()
            flash('Employee added.')
            return redirect(url_for('employee'))
        elif 'search' in request.form:
            query = "SELECT * FROM Employee WHERE 1=1"  
            params = []  
            if employee_eid:  
                query += " AND eid = %s"  
                params.append(employee_eid)  
            if employee_name:  
                query += " AND ename = %s"  
                params.append(employee_name)
            if employee_gender:
                query += " AND gender = %s"
                params.append(employee_gender)
            if employee_age:
                query += " AND age = %s"
                params.append(employee_age)
            if employee_address:
                query += " AND address = %s"
                params.append(employee_address)
            if employee_salary:
                query += " AND salary = %s"
                params.append(employee_salary)
            if employee_position:
                query += " AND position = %s"
                params.append(employee_position)
            if employee_id:
                query += " AND ID = %s"
                params.append(employee_id)
            if employee_phone:
                query += " AND phone = %s"
                params.append(employee_phone)
            if employee_department:
                query += " AND department_id = %s"
                params.append(employee_department)
            cursor = database.cursor()
            cursor.execute(query, params)
            employees = cursor.fetchall()
            return render_template('employee.html',employees=employees)
        
@app.route('/employee/update/<employee_eid>',methods=['GET','POST'])
def employee_edit(employee_eid):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    form = UploadForm()
    cursor = database.cursor()
    cursor.execute('select * from Employee where eid = %s',employee_eid)
    employee = cursor.fetchone()
    file_url = None
    if employee[11]:
        file_url = photos.url(employee[11])
    if request.method == 'POST':
        if 'information' in request.form:
            new_employee_eid = request.form['employee_eid']
            new_employee_name = request.form['employee_name']
            new_employee_gender = request.form['employee_gender']
            new_employee_age = request.form['employee_age']
            new_employee_address = request.form['employee_address']
            new_employee_salary = request.form['employee_salary']
            new_employee_position = request.form['employee_position']
            new_employee_id = request.form['employee_id']
            new_employee_phone = request.form['employee_phone']
            new_employee_department = request.form['employee_department']
            new_employee_password = request.form['employee_password']

            if not new_employee_age or new_employee_age == 'None':
                new_employee_age = None
            else:
                try:
                    new_employee_age = int(new_employee_age)
                except ValueError:
                    flash('Invalid age.')
                    return redirect(url_for('employee'))
            
            if not new_employee_salary or new_employee_salary == 'None':
                new_employee_salary = None
            else:
                try:
                    new_employee_salary = int(new_employee_salary)
                except ValueError:
                    flash('Invalid salary.')
                    return redirect(url_for('employee'))

            if new_employee_eid != employee_eid:
                cursor.execute('select eid from Employee where eid = %s',new_employee_eid)
                if cursor.fetchone():
                    flash('Employeeid already exists.')
                    return redirect(url_for('employee'))
                
            if new_employee_id != employee[7]:
                cursor.execute('select ID from Employee where ID = %s',new_employee_id)
                if cursor.fetchone():
                    flash('ID already exists.')
                    return redirect(url_for('employee'))

            cursor.execute('select did from department where did = %s',new_employee_department)
            if not cursor.fetchone():
                flash('Department does not exist.')
                return redirect(url_for('employee'))
            cursor.execute('update Employee set eid = %s,ename = %s,gender = %s,age = %s,address = %s,salary = %s,position = %s,ID = %s,phone = %s,department_id = %s,password = %s where eid = %s',(new_employee_eid,new_employee_name,new_employee_gender,new_employee_age,new_employee_address,new_employee_salary,new_employee_position,new_employee_id,new_employee_phone,new_employee_department,new_employee_password,employee_eid))
            database.commit()
            flash('Employee updated.')
            return redirect(url_for('employee'))
        elif form.validate_on_submit():
            if file_url:
                file_path = photos.path(employee[11])
                os.remove(file_path)
            filename = photos.save(form.photo.data)
            file_url = photos.url(filename)
            cursor.execute('update Employee set idphoto = %s where eid = %s',(filename,employee_eid))
            database.commit()
            flash('Photo updated.')
            return redirect(url_for('employee_edit',employee_eid=employee_eid))
    return render_template('employee_edit.html',employee=employee,form=form,file_url=file_url)

@app.route('/employee/delete/<employee_eid>',methods=['POST'])
def employee_delete(employee_eid):
    cursor = database.cursor()
    cursor.execute('select idphoto from Employee where eid = %s',employee_eid)
    photo = cursor.fetchone()[0]
    if photo:
        file_path = photos.path(photo)
        os.remove(file_path)
    cursor.execute('delete from Employee where eid = %s',employee_eid)
    database.commit()
    flash('Employee deleted.')
    return redirect(url_for('employee'))

@app.route('/customer',methods=['GET','POST'])
def customer():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from Customer')
        customers = cursor.fetchall()
        return render_template('customer.html',customers=customers)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        customer_id = request.form['customer_id']
        customer_name = request.form['customer_name']
        customer_age = request.form['customer_age']
        customer_address = request.form['customer_address']
        customer_gender = request.form['customer_gender']
        customer_phone = request.form['customer_phone']

        if not customer_age:
            customer_age = None
        else:
            try:
                customer_age = int(customer_age)
            except ValueError:
                flash('Invalid age.')
                return redirect(url_for('customer'))
            
        if 'add' in request.form:
            if not customer_id:
                flash('Invalid input.')
                return redirect(url_for('customer'))
            cursor = database.cursor()
            cursor.execute('select ID from Customer where ID = %s',customer_id)
            if cursor.fetchone():
                flash('Customerid already exists.')
                return redirect(url_for('customer'))
            cursor.execute('insert into Customer(ID,cname,age,address,gender,phone) values(%s,%s,%s,%s,%s,%s)',(customer_id,customer_name,customer_age,customer_address,customer_gender,customer_phone))
            database.commit()
            flash('Customer added.')
            return redirect(url_for('customer'))
        elif 'search' in request.form:
            query = "SELECT * FROM Customer WHERE 1=1"  
            params = []  
            if customer_id:  
                query += " AND ID = %s"  
                params.append(customer_id)  
            if customer_name:  
                query += " AND cname = %s"  
                params.append(customer_name)
            if customer_age:
                query += " AND age = %s"
                params.append(customer_age)
            if customer_address:
                query += " AND address = %s"
                params.append(customer_address)
            if customer_gender:
                query += " AND gender = %s"
                params.append(customer_gender)
            if customer_phone:
                query += " AND phone = %s"
                params.append(customer_phone)
            cursor = database.cursor()
            cursor.execute(query, params)
            customers = cursor.fetchall()
            return render_template('customer.html',customers=customers)
        
@app.route('/customer/update/<customer_id>',methods=['GET','POST'])
def customer_edit(customer_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    cursor = database.cursor()
    cursor.execute('select * from Customer where ID = %s',customer_id)
    customer = cursor.fetchone()
    if request.method == 'POST':
        new_customer_id = request.form['customer_id']
        new_customer_name = request.form['customer_name']
        new_customer_age = request.form['customer_age']
        new_customer_address = request.form['customer_address']
        new_customer_gender = request.form['customer_gender']
        new_customer_phone = request.form['customer_phone']

        if not new_customer_age or new_customer_age == 'None':
            new_customer_age = None
        else:
            try:
                new_customer_age = int(new_customer_age)
            except ValueError:
                flash('Invalid age.')
                return redirect(url_for('customer'))

        if new_customer_id != customer_id:
            cursor.execute('select ID from Customer where ID = %s',new_customer_id)
            if cursor.fetchone():
                flash('Customerid already exists.')
                return redirect(url_for('customer'))

        cursor.execute('update Customer set ID = %s,cname = %s,age = %s,address = %s,gender = %s,phone = %s where ID = %s',(new_customer_id,new_customer_name,new_customer_age,new_customer_address,new_customer_gender,new_customer_phone,customer_id))
        database.commit()
        flash('Customer updated.')
        return redirect(url_for('customer'))
    return render_template('customer_edit.html',customer=customer)

@app.route('/customer/delete/<customer_id>',methods=['POST'])
def customer_delete(customer_id):
    cursor = database.cursor()
    cursor.execute('delete from Customer where ID = %s',customer_id)
    database.commit()
    flash('Customer deleted.')
    return redirect(url_for('customer'))   

@app.route('/customer/loan_state/<customer_id>',methods=['POST'])
def customer_loan_state(customer_id):
    cursor = database.cursor()
    cursor.execute('select get_loan_state(%s) as result',customer_id)
    result = cursor.fetchone()[0]
    flash("偿还贷款后剩余余额: " + str(result))
    return redirect(url_for('customer'))
    

@app.route('/account',methods=['GET','POST'])
def account():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from Account')
        accounts = cursor.fetchall()
        return render_template('account.html',accounts=accounts)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        account_id = request.form['account_id']
        account_balance = request.form['account_balance']
        account_password = request.form['account_password']
        account_ownerid = request.form['account_ownerid']
        account_bank = request.form['account_bank']

        if not account_balance:
            account_balance = None
        else:
            try:
                account_balance = int(account_balance)
            except ValueError:
                flash('Invalid balance.')
                return redirect(url_for('account'))
            
        if 'add' in request.form:
            if not account_id or not account_ownerid or not account_bank:
                flash('Invalid input.')
                return redirect(url_for('account'))
            cursor = database.cursor()
            cursor.execute('select aid from Account where aid = %s',account_id)
            if cursor.fetchone():
                flash('Accountid already exists.')
                return redirect(url_for('account'))
            cursor.execute('select ID from Customer where ID = %s',account_ownerid)
            if not cursor.fetchone():
                flash('Customer does not exist.')
                return redirect(url_for('account'))
            cursor.execute('select bname from bank where bname = %s',account_bank)
            if not cursor.fetchone():
                flash('Bank does not exist.')
                return redirect(url_for('account'))
            cursor.execute('insert into Account(aid,balance,password,ID,bank_name) values(%s,%s,%s,%s,%s)',(account_id,account_balance,account_password,account_ownerid,account_bank))
            database.commit()
            flash('Account added.')
            return redirect(url_for('account'))
        elif 'search' in request.form:
            query = "SELECT * FROM Account WHERE 1=1"  
            params = []  
            if account_id:  
                query += " AND aid = %s"  
                params.append(account_id)  
            if account_balance:
                query += " AND balance = %s"
                params.append(account_balance)
            if account_password:
                query += " AND password = %s"
                params.append(account_password)
            if account_ownerid:
                query += " AND ID = %s"
                params.append(account_ownerid)
            if account_bank:
                query += " AND bank_name = %s"
                params.append(account_bank)
            cursor = database.cursor()
            cursor.execute(query, params)
            accounts = cursor.fetchall()
            return render_template('account.html',accounts=accounts)
        
@app.route('/account/update/<account_id>',methods=['GET','POST'])
def account_edit(account_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    cursor = database.cursor()
    cursor.execute('select * from Account where aid = %s',account_id)
    account = cursor.fetchone()
    if request.method == 'POST':
        if 'information' in request.form:
            new_account_id = request.form['account_id']
            new_account_password = request.form['account_password']
            new_account_ownerid = request.form['account_ownerid']

            if new_account_id != account_id:
                cursor.execute('select aid from Account where aid = %s',new_account_id)
                if cursor.fetchone():
                    flash('Accountid already exists.')
                    return redirect(url_for('account'))
            
            cursor.execute('select ID from Customer where ID = %s',new_account_ownerid)
            if not cursor.fetchone():
                flash('Customer does not exist.')
                return redirect(url_for('account'))
            
            cursor.execute('update Account set aid = %s,password = %s,ID = %s where aid = %s',(new_account_id,new_account_password,new_account_ownerid,account_id))
            database.commit()
            flash('Account updated.')
            return redirect(url_for('account'))
        elif 'deposit' in request.form:
            deposit = request.form['account_amount']
            if not deposit:
                flash('Invalid input.')
                return redirect(url_for('account'))
            try:
                deposit = int(deposit)
            except ValueError:
                flash('Invalid amount.')
                return redirect(url_for('account'))
            cursor.execute('update Account set balance = balance + %s where aid = %s',(deposit,account_id))
            database.commit()
            flash('Deposit succeeded.')
            return redirect(url_for('account'))
        elif 'withdraw' in request.form:
            withdraw = request.form['account_amount']
            if not withdraw:
                flash('Invalid input.')
                return redirect(url_for('account'))
            try:
                withdraw = int(withdraw)
            except ValueError:
                flash('Invalid amount.')
                return redirect(url_for('account'))
            cursor.execute('select balance from Account where aid = %s',account_id)
            balance = cursor.fetchone()[0]
            if balance < withdraw:
                flash('Insufficient balance.')
                return redirect(url_for('account'))
            cursor.execute('update Account set balance = balance - %s where aid = %s',(withdraw,account_id))
            database.commit()
            flash('Withdraw succeeded.')
            return redirect(url_for('account'))
        elif 'transfer' in request.form:
            amount = request.form['account_amount']
            target = request.form['goal_account']
            if not amount or not target:
                flash('Invalid input.')
                return redirect(url_for('account'))
            try:
                amount = int(amount)
            except ValueError:
                flash('Invalid amount.')
                return redirect(url_for('account'))
            cursor.callproc('transfer',(account_id,target,amount,0))
            cursor.execute('select @_transfer_3')
            result = cursor.fetchone()
            if result[0] == 0:
                database.commit()
                flash('Transfer succeeded.')
                return redirect(url_for('account'))
            else:
                flash('Transfer failed.')
                return redirect(url_for('account'))
    return render_template('account_edit.html',account=account)

@app.route('/account/delete/<account_id>',methods=['POST'])
def account_delete(account_id):
    cursor = database.cursor()
    cursor.execute('delete from Account where aid = %s',account_id)
    database.commit()
    flash('Account deleted.')
    return redirect(url_for('account'))

@app.route('/loan',methods=['GET','POST'])
def loan():
    if request.method == 'GET':
        cursor = database.cursor()
        cursor.execute('select * from Loan')
        loans = cursor.fetchall()
        return render_template('loan.html',loans=loans)
    else:
        if not session.get('user_id'):
            return redirect(url_for('login'))
        loan_id = request.form['loan_id']
        loan_amount = request.form['loan_amount']
        loan_enddate = request.form['loan_enddate']
        loan_accountid = request.form['loan_accountid']
        loan_bank = request.form['loan_bank']

        if not loan_amount:
            loan_amount = None
        else:
            try:
                loan_amount = int(loan_amount)
            except ValueError:
                flash('Invalid amount.')
                return redirect(url_for('loan'))
            
        if 'add' in request.form:
            if not loan_id or not loan_accountid or not loan_bank or not loan_enddate or not loan_amount:
                flash('Invalid input.')
                return redirect(url_for('loan'))
            cursor = database.cursor()
            cursor.callproc('apply_loan',(loan_id,loan_amount,loan_enddate,loan_accountid,loan_bank,0))
            cursor.execute('select @_apply_loan_5')
            result = cursor.fetchone()
            if result[0] == 0:
                database.commit()
                flash('Loan applied.')
                return redirect(url_for('loan'))
            else:
                flash('Loan failed.')
                return redirect(url_for('loan'))
        elif 'search' in request.form:
            query = "SELECT * FROM Loan WHERE 1=1"  
            params = []  
            cursor = database.cursor()
            if loan_id:  
                query += " AND lid = %s"  
                params.append(loan_id)
            if loan_amount:
                query += " AND amount = %s"
                params.append(loan_amount)
            if loan_enddate:
                is_valid_date(loan_enddate)
                if not is_valid_date(loan_enddate):
                    flash('Invalid date.')
                    return redirect(url_for('loan'))
                query += " AND end_date = STR_TO_DATE(%s,'%%Y-%%m-%%d')"
                params.append(loan_enddate)
            if loan_accountid:
                query += " AND account_id = %s"
                params.append(loan_accountid)
            if loan_bank:
                query += " AND bank_name = %s"
                params.append(loan_bank)
            cursor.execute(query, params)
            loans = cursor.fetchall()
            return render_template('loan.html',loans=loans)
        
@app.route('/loan/update/<loan_id>',methods=['GET','POST'])
def loan_edit(loan_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    cursor = database.cursor()
    cursor.execute('select * from Loan where lid = %s',loan_id)
    loan = cursor.fetchone()
    if request.method == 'POST':
        new_loan_amount = request.form['loan_amount']
        new_loan_enddate = request.form['loan_enddate']
        new_loan_accountid = request.form['loan_accountid']

        
        try:
            new_loan_amount = int(new_loan_amount)
        except ValueError:
            flash('Invalid amount.')
            return redirect(url_for('loan'))
        if new_loan_amount <= 0:
            flash('Invalid amount.')
            return redirect(url_for('loan'))
        
        if not is_valid_date(new_loan_enddate):
            flash('Invalid date.')
            return redirect(url_for('loan'))
        
        cursor.execute('select aid from Account where aid = %s',new_loan_accountid)
        if not cursor.fetchone():
            flash('Account does not exist.')

        cursor.execute("update Loan set amount = %s,end_date = STR_TO_DATE(%s,'%%Y-%%m-%%d'),account_id = %s where lid = %s",(new_loan_amount,new_loan_enddate,new_loan_accountid,loan_id))
        database.commit()
        flash('Loan updated.')
        return redirect(url_for('loan'))
    return render_template('loan_edit.html',loan=loan)

@app.route('/loan/delete/<loan_id>',methods=['POST'])
def loan_delete(loan_id):
    cursor = database.cursor()
    cursor.callproc('repay_loan',(loan_id,0))
    cursor.execute('select @_repay_loan_1')
    result = cursor.fetchone()
    if result[0] == 0:
        database.commit()
        flash('Loan repaid.')
        return redirect(url_for('loan'))
    else:
        flash('Loan repayment failed.')
        return redirect(url_for('loan'))
    

