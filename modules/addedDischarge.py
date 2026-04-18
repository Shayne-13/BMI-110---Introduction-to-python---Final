import getpass
import bcrypt
import keyring
import json

service = 'BMI Login'

# Usernames and passwords for the 3 different nurses'
keyring.set_password(service, 'Tolkin', 'BMI15fun')
keyring.set_password(service, 'Alagory', 'BMI15notFUN')
keyring.set_password(service, 'Shakira', 'BMI15fine')

# List to make it easier to log in instead of doing a log IF/Else statement
nurse_usernames = ['Tolkin', 'Alagory', 'Shakira']

patients = {}

def load_patients():
    global patients
    try:
        with open('patients.json', 'r') as f:
            patients = json.load(f)
    except FileNotFoundError:
        patients = {}

def save_patients():
    with open('patients.json', 'w') as f:
        json.dump(patients, f, indent=4)

# Nurse Class and everything that it needs to log in and work.
class Nurses:

    # Username and password encryption
    def __init__(self, username, password):
        self.username = username
        encrypted_password = password.encode('utf-8')
        hashing = bcrypt.gensalt(rounds=10)
        self.password_hash = bcrypt.hashpw(encrypted_password, hashing)

    def password_verification(self, password):
        encrypted_password = password.encode('utf-8')
        return bcrypt.checkpw(encrypted_password, self.password_hash)

    def __repr__(self):
        return f"Nurse: {self.username}"

    # Allows the nurse to create a new patient in the system.
    def create_patient(self):
        print(f'\n    Create New Patient    ')
        patient_id = input(f'Enter Patient ID: ')
        if patient_id in patients:
            print(f'A patient with that ID already exists.')
            return
        name = input(f'Enter Patient Name: ')
        age = input(f'Enter Patient Age: ')
        gender = input(f'Enter Patient Gender: ')
        diagnosis = input(f'Enter Diagnosis: ')

        patients[patient_id] = {
            'name': name,
            'age': age,
            'gender': gender,
            'diagnosis': diagnosis,
            'labs': [],
            'medications': [],
            'discharged': False,
            'created_by': self.username
        }
        print(f'\nPatient "{name}" successfully created with ID: {patient_id}')
        save_patients()

    # Allows the nurses to view all available patients
    def view_patients(self):
        print(f'\n    All Patients    ')
        if not patients:
            print(f'No patients on record.')
            return
        for patient_id, details in patients.items():
            print(f"""
Patient ID  : {patient_id}
Name        : {details['name']}
Age         : {details['age']}
Gender      : {details['gender']}
Diagnosis   : {details['diagnosis']}
Labs        : {details['labs'] if details['labs'] else 'None ordered'}
Medications : {details['medications'] if details['medications'] else 'None prescribed'}
Discharged  : {'Yes' if details['discharged'] else 'No'}
Created By  : {details['created_by']}
{'-' * 30}""")

    def order_labs(self):
        print(f'Access Denied: Nurses are not authorized to order labs.')

    def prescribe_meds(self):
        print(f'Access Denied: Nurses are not authorized to prescribe medications.')

    def discharge_patient(self):
        from datetime import datetime
        with open("patients.json", "r") as jsonFile:
            data = json.load(jsonFile)

            now = datetime.now()
        
        while True:
            patientID = input("Please input ID of discharged patient.")
            
            if patientID in data:
                patient = data[patientID]

                name = input("Please confirm patients name.")

                if name == patient["name"]:
                    print("Patient Verified")

                    txtFileName = F"{patient["name"]}_discharged_{now.strftime("%Y-%m-%d")}.txt"

                    with open(txtFileName, "w") as txtFile:
                        txtFile.write(f"Patient ID: {patientID}\n")
                        for key, value in patient.items():
                            txtFile.write(f"{key}: {value}\n")

                    del patients[patientID]

                    with open("patients.json", "w") as jsonFile:
                        json.dump(data, jsonFile, indent=4)

                    print("Patient discharged successful!")
                    print(f"Saved to {txtFileName}")
                    return
                    
                else:
                    print("Name incorrect. Try again.")
                    continue
            else:
                print("Patient ID not found. Try again.")
                continue


nurse_list = []
for username in nurse_usernames:
    password = keyring.get_password(service, username)
    if password:
        nurse_list.append(Nurses(username, password))

# The login prompt that allows the nurses to login
def login():
    print(f'\n=== Nurse Login ===')
    username = input(f'Enter Username: ')
    password = getpass.getpass(f'Enter Password: ')

    for nurse in nurse_list:
        if nurse.username.lower() == username.lower():
            if nurse.password_verification(password):
                print(f"\nWelcome, {nurse.username}!")
                return nurse
            else:
                print(f'Incorrect password.')
                return None

    print(f'Username not found.')
    return None

# The menu that nurses see when they are logged in
def nurse_menu(nurse):
    while True:
        print(f"""
=== Nurse Module | Logged in as: {nurse.username} ===
1. Create Patient
2. View All Patients
3. Order Labs       (Restricted)
4. Prescribe Meds   (Restricted)
5. Discharge Patient
6. Logout
""")
        choice = input(f'Select an option: ').strip()

        if choice == '1':
            nurse.create_patient()
        elif choice == '2':
            nurse.view_patients()
        elif choice == '3':
            nurse.order_labs()
        elif choice == '4':
            nurse.prescribe_meds()
        elif choice == '5':
            nurse.discharge_patient()
        elif choice == '6':
            print(f"Goodbye, {nurse.username}!")
            break
        else:
            print(f'Invalid option. Please select 1-6.')

load_patients()
current_nurse = login()
if current_nurse:
    nurse_menu(current_nurse)
