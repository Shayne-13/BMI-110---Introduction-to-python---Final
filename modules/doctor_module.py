# Troy Wilson
import json
import os
import getpass
from time import sleep
from subprocess import call


class MedicalInterfaceBackend:
    def __init__(self):
        self.doctors = {}
        self.nurses = {}
        self.patients = {}

        self.currentUserPermissions = {
            "readsOwnUserDetails": True,
            "Staff Management": False,
            "Patient Management": False,
            "Clinical Actions": False,
        }

        self.currentUserCredentials = {
            "Username": "",  # unimplemented
            "Identification": "",
            "Password": "",  # unimplemented for patients and nurses
            "Role": "",
        }

    def CreateDoctor(
        self,
        strUserIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strSpecialty,
    ):
        new_doctor = Doctor(
            strUserIdentification,
            strPassword,
            strFirstName,
            strLastName,
            strPhoneNumber,
            strSpecialty,
        )

        self.doctors[strUserIdentification] = new_doctor

        print(f"'{strUserIdentification}' succesfully added to doctor list.")

    def Login(self, strRole, strIdentification, strPassword):
        if strRole == "Patient":
            if self.patients.get(strIdentification):  # unimplemented
                self.currentUserCredentials["Role"] = "Patient"
                self.currentUserCredentials["Password"] = strPassword
                return True
        elif strRole == "Nurse":
            if self.nurses.get(strIdentification):  # unimplemented
                self.currentUserCredentials["Role"] = "Nurse"
                self.currentUserCredentials["Password"] = strPassword
                return True
        elif strRole == "Doctor":
            found_doctor = self.doctors.get(strIdentification)
            if found_doctor and found_doctor._Doctor__password == strPassword:
                self.currentUserCredentials["Role"] = "Doctor"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = found_doctor.permissions
                return found_doctor
        return False

    def load_patients(self):
        global patients
        try:
            with open("patients.json", "r") as f:
                self.patients = json.load(f)
        except FileNotFoundError:
            pass

    def load_nurses(self):
        global nurses
        try:
            with open("nurses.json", "r") as f:
                self.nurses = json.load(f)
        except FileNotFoundError:
            pass

    def load_doctors(self):
        global doctors
        try:
            with open("doctors.json", "r") as f:
                self.doctors = json.load(f)
        except FileNotFoundError:
            pass

    def save_nurses(self):
        with open("nurses.json", "w") as f:
            json.dump(self.nurses, f, indent=4)

    def save_patients(self):
        with open("patients.json", "w") as f:
            json.dump(self.patients, f, indent=4)

    def save_doctors(self):
        with open("doctors.json", "w") as f:
            json.dump(self.doctors, f, indent=4)


class Doctor:
    def __init__(
        self,
        strIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strSpecialty,
    ):
        self.__user_id = strIdentification
        self.__password = strPassword
        self.__phone = strPhoneNumber

        self.firstName = strFirstName
        self.lastName = strLastName

        self.role = "Doctor"
        self.specialty = strSpecialty

        self.permissions = {
            "readsOwnUserDetails": True,
            "Staff Management": {
                "enabled": True,
                "createsDoctors": True,
                "createsNurses": True,
            },
            "PatientManagement": {
                "enabled": True,
                "createsPatients": True,
                "readsPatientDetails": True,
                "writesPatientDetails": True,
            },
            "ClinicalActions": {
                "enabled": True,
                "viewsLabTests": True,
                "ordersLabTests": True,
            },
        }

    def DisplayInfo(self):

        full_name = f"{self.firstName} {self.lastName}"

        print(
            f"ID: {self.__user_id}\nFull Name: Role: {self.role}\n{full_name}\nPhone: {self.__phone}\nRole:"
        )

    def UpdateInformation(self, strIdentification, needsPassword, strPassword):

        if needsPassword and not strPassword == self.__password:
            return (False, "Password of this doctor is required to update information.")

        self.__user_id = strIdentification
        self.__password = strPassword

        return (True, "Updated doctor informaton.")


def clear_console(intTimeout):
    if intTimeout:
        sleep(intTimeout)
    call("clear" if os.name == "posix" else "cls")


def user_login():
    clear_console(0)
    while True:
        role = input("Enter role(Patient/Nurse/Doctor): ").strip()
        if role not in ("Patient", "Nurse", "Doctor"):
            print("Invalid type. Please try again.")
            clear_console(1)
        else:
            break

    while True:
        identification = input("Enter Username: ").strip()
        password = getpass.getpass("Enter Password: ")

        roleObject = clinicalBackend.Login(role, identification, password)

        if roleObject:
            clear_console(1)
            print(f"Login successfull as {role}. Welcone, {identification}")
            clear_console(1)
            return roleObject
        else:
            print(f"Invalid {role} login, check username and password.")
            clear_console(1)


def blankFunction():  # for menu options not requiring action
    clear_console(0)
    return


def userMenu(currentUserRoleObject):
    clear_console(0)
    print(
        f"Welcome, {clinicalBackend.currentUserCredentials.get('Role')} {clinicalBackend.currentUserCredentials.get('Identification')} select from options:"
    )
    possibleOptions = {0: ("Exit Program", blankFunction)}
    optionNumber = 1

    if clinicalBackend.currentUserPermissions.get("readsOwnUserDetails"):
        possibleOptions[optionNumber] = (
            "Display your user information.",
            currentUserRoleObject.DisplayInfo,
        )
        optionNumber += 1

    if clinicalBackend.currentUserPermissions.get("PatientManagement"):
        possibleOptions[optionNumber] = ("Patient Database", blankFunction)
        optionNumber += 1

    if clinicalBackend.currentUserPermissions.get("StaffManagement"):
        possibleOptions[optionNumber] = ("Staff Magagement", blankFunction)
        optionNumber += 1

    if clinicalBackend.currentUserPermissions.get("ClinicalActions"):
        possibleOptions[optionNumber] = ("Clinical Actions", blankFunction)
        optionNumber += 1

    for key, (label, _) in possibleOptions.items():
        print(f"({key}) - {label}")

    userOption = input("-> ").strip()


"""
        self.currentUserPermissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {
                "enabled": False,
                "createsDoctors": False,
                "createsNurses": False,
            },
            "PatientManagement": {
                "enabled": False,
                "createsPatients": False,
                "readsPatientDetails": False,
                "writesPatientDetails": False,
            },
            "Clinical Actions": {
                "enabled": False,
                "viewsLabTests": False,
                "ordersLabTests": False,
            },
        }
"""

clinicalBackend = MedicalInterfaceBackend()
clinicalBackend.CreateDoctor(
    "chief", "123", "Andrew", "Jordan", "4808121294", "Pediatric"
)

roleObject = user_login()
userMenu(roleObject)
