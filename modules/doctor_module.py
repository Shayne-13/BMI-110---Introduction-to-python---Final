# Troy Wilson
import json
import os
import getpass
import uuid
from time import sleep
from subprocess import call


class MedicalInterfaceBackend:
    def __init__(self):
        self.doctors = {}  # id -> Doctor object
        self.nurses = {}  # id -> Nurse object
        self.patients = {}  # id -> Patient object
        self.lab_orders = []  # list of LabOrder objects

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
            "ClinicalActions": {
                "enabled": False,
                "viewsLabTests": False,
                "ordersLabTests": False,
            },
        }

        self.currentUserCredentials = {
            "Username": "",
            "Identification": "",
            "Password": "",
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
        if strUserIdentification in self.doctors:
            print(f"Doctor ID '{strUserIdentification}' already exists.")
            return False
        self.doctors[strUserIdentification] = Doctor(
            strUserIdentification,
            strPassword,
            strFirstName,
            strLastName,
            strPhoneNumber,
            strSpecialty,
        )
        print(f"Doctor '{strUserIdentification}' successfully added.")
        return True

    def CreateNurse(
        self,
        strUserIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strDepartment,
    ):
        if strUserIdentification in self.nurses:
            print(f"Nurse ID '{strUserIdentification}' already exists.")
            return False
        self.nurses[strUserIdentification] = Nurse(
            strUserIdentification,
            strPassword,
            strFirstName,
            strLastName,
            strPhoneNumber,
            strDepartment,
        )
        print(f"Nurse '{strUserIdentification}' successfully added.")
        return True

    def CreatePatient(
        self,
        strPatientID,
        strFirstName,
        strLastName,
        strDateOfBirth,
        strPhoneNumber,
        strAddress,
    ):
        if strPatientID in self.patients:
            print(f"Patient ID '{strPatientID}' already exists.")
            return False
        self.patients[strPatientID] = Patient(
            strPatientID,
            strFirstName,
            strLastName,
            strDateOfBirth,
            strPhoneNumber,
            strAddress,
        )
        print(f"Patient '{strPatientID}' successfully added.")
        return True

    def CreateLabOrder(self, strPatientID, strOrderingDoctorID, strTestName, strNotes):
        if strPatientID not in self.patients:
            print(f"Patient '{strPatientID}' not found.")
            return False
        order = LabOrder(strPatientID, strOrderingDoctorID, strTestName, strNotes)
        self.lab_orders.append(order)
        print(f"Lab order '{order.order_id}' created for patient '{strPatientID}'.")
        return True

    def GetLabOrdersForPatient(self, strPatientID):
        return [o for o in self.lab_orders if o.patient_id == strPatientID]

    def GetAllLabOrders(self):
        return list(self.lab_orders)

    def Login(self, strRole, strIdentification, strPassword):
        if strRole == "Doctor":
            found = self.doctors.get(strIdentification)
            if found and found._Doctor__password == strPassword:
                self.currentUserCredentials["Role"] = "Doctor"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = found.permissions
                return found
        elif strRole == "Nurse":
            found = self.nurses.get(strIdentification)
            if found and found._Nurse__password == strPassword:
                self.currentUserCredentials["Role"] = "Nurse"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = found.permissions
                return found
        elif strRole == "Patient":
            found = self.patients.get(strIdentification)
            if found:
                self.currentUserCredentials["Role"] = "Patient"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = found.permissions
                return found
        return False

    def load_all(self):
        self._load_doctors()
        self._load_nurses()
        self._load_patients()
        self._load_lab_orders()

    def save_all(self):
        self._save_doctors()
        self._save_nurses()
        self._save_patients()
        self._save_lab_orders()

    def _load_doctors(self):
        try:
            with open("doctors.json", "r") as f:
                raw = json.load(f)
            for ident, d in raw.items():
                self.doctors[ident] = Doctor(
                    d["_Doctor__user_id"],
                    d["_Doctor__password"],
                    d["firstName"],
                    d["lastName"],
                    d["_Doctor__phone"],
                    d["specialty"],
                )
        except FileNotFoundError:
            pass

    def _load_nurses(self):
        try:
            with open("nurses.json", "r") as f:
                raw = json.load(f)
            for ident, d in raw.items():
                self.nurses[ident] = Nurse(
                    d["_Nurse__user_id"],
                    d["_Nurse__password"],
                    d["firstName"],
                    d["lastName"],
                    d["_Nurse__phone"],
                    d["department"],
                )
        except FileNotFoundError:
            pass

    def _load_patients(self):
        try:
            with open("patients.json", "r") as f:
                raw = json.load(f)
            for pid, d in raw.items():
                self.patients[pid] = Patient(
                    d["patient_id"],
                    d["firstName"],
                    d["lastName"],
                    d["dateOfBirth"],
                    d["_Patient__phone"],
                    d["_Patient__address"],
                )
        except FileNotFoundError:
            pass

    def _load_lab_orders(self):
        try:
            with open("lab_orders.json", "r") as f:
                raw = json.load(f)
            for entry in raw:
                o = LabOrder.__new__(LabOrder)
                o.__dict__.update(entry)
                self.lab_orders.append(o)
        except FileNotFoundError:
            pass

    def _save_doctors(self):
        with open("doctors.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.doctors.items()}, f, indent=4)

    def _save_nurses(self):
        with open("nurses.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.nurses.items()}, f, indent=4)

    def _save_patients(self):
        with open("patients.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.patients.items()}, f, indent=4)

    def _save_lab_orders(self):
        with open("lab_orders.json", "w") as f:
            json.dump([o.__dict__ for o in self.lab_orders], f, indent=4)


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
            "StaffManagement": {
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
        print(
            f"\n--- Doctor Info ---"
            f"\nID:        {self.__user_id}"
            f"\nName:      {self.firstName} {self.lastName}"
            f"\nPhone:     {self.__phone}"
            f"\nSpecialty: {self.specialty}"
            f"\nRole:      {self.role}\n"
        )

    def UpdateInformation(
        self,
        strIdentification,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strSpecialty,
        strNewPassword,
        strCurrentPassword,
    ):
        if strCurrentPassword != self.__password:
            return (False, "Current password is incorrect; information not updated.")
        self.__user_id = strIdentification
        self.__password = strNewPassword
        self.firstName = strFirstName
        self.lastName = strLastName
        self.__phone = strPhoneNumber
        self.specialty = strSpecialty
        return (True, "Doctor information updated.")


class Nurse:
    def __init__(
        self,
        strIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strDepartment,
    ):
        self.__user_id = strIdentification
        self.__password = strPassword
        self.__phone = strPhoneNumber
        self.firstName = strFirstName
        self.lastName = strLastName
        self.role = "Nurse"
        self.department = strDepartment
        self.permissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {
                "enabled": False,
                "createsDoctors": False,
                "createsNurses": False,
            },
            "PatientManagement": {
                "enabled": True,
                "createsPatients": True,
                "readsPatientDetails": True,
                "writesPatientDetails": False,
            },
            "ClinicalActions": {
                "enabled": True,
                "viewsLabTests": True,
                "ordersLabTests": False,
            },
        }

    def DisplayInfo(self):
        print(
            f"\n--- Nurse Info ---"
            f"\nID:         {self.__user_id}"
            f"\nName:       {self.firstName} {self.lastName}"
            f"\nPhone:      {self.__phone}"
            f"\nDepartment: {self.department}"
            f"\nRole:       {self.role}\n"
        )


class Patient:
    def __init__(
        self,
        strPatientID,
        strFirstName,
        strLastName,
        strDateOfBirth,
        strPhoneNumber,
        strAddress,
    ):
        self.patient_id = strPatientID
        self.firstName = strFirstName
        self.lastName = strLastName
        self.dateOfBirth = strDateOfBirth
        self.__phone = strPhoneNumber
        self.__address = strAddress
        self.role = "Patient"
        self.permissions = {
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
            "ClinicalActions": {
                "enabled": False,
                "viewsLabTests": False,
                "ordersLabTests": False,
            },
        }

    def DisplayInfo(self):
        print(
            f"\n--- Patient Info ---"
            f"\nID:            {self.patient_id}"
            f"\nName:          {self.firstName} {self.lastName}"
            f"\nDate of Birth: {self.dateOfBirth}"
            f"\nPhone:         {self.__phone}"
            f"\nAddress:       {self.__address}\n"
        )


class LabOrder:
    def __init__(self, strPatientID, strOrderingDoctorID, strTestName, strNotes):
        self.order_id = str(uuid.uuid4())[:8].upper()
        self.patient_id = strPatientID
        self.ordering_doctor_id = strOrderingDoctorID
        self.test_name = strTestName
        self.notes = strNotes
        self.status = "Pending"

    def Display(self):
        print(
            f"\n  Order ID: {self.order_id}"
            f"\n  Patient:  {self.patient_id}"
            f"\n  Doctor:   {self.ordering_doctor_id}"
            f"\n  Test:     {self.test_name}"
            f"\n  Notes:    {self.notes}"
            f"\n  Status:   {self.status}"
        )


# My helper functions:


def ClearConsole(intTimeout=0):
    if intTimeout:
        sleep(intTimeout)
    call("clear" if os.name == "posix" else "cls")


def prompt(label, secret=False):
    if secret:
        return getpass.getpass(f"{label}: ")
    return input(f"{label}: ").strip()


def pause():
    input("\nPress Enter to continue...")


def run_menu(title, options):
    """
    Display a numbered menu and dispatch.
    options: list of (label, callable).
    Option 0 always returns to the previous menu.
    """
    while True:
        ClearConsole()
        print(f"\n=== {title} ===\n")
        print("(0) - Return")
        for i, (label, _) in enumerate(options, 1):
            print(f"({i}) - {label}")
        choice = prompt("\n->")
        try:
            idx = int(choice)
            if idx == 0:
                return
            label, fn = options[idx - 1]
            fn()
        except (ValueError, IndexError):
            print("Invalid option.")
            sleep(1)


# Staff Management:


def CreateDoctorScreen():
    ClearConsole()
    print("\n--- Create New Doctor ---")
    ident = prompt("Doctor ID / Username")
    password = prompt("Password", secret=True)
    first = prompt("First Name")
    last = prompt("Last Name")
    phone = prompt("Phone Number")
    specialty = prompt("Specialty")
    clinicalBackend.CreateDoctor(ident, password, first, last, phone, specialty)
    clinicalBackend.save_all()
    pause()


def CreateNurseScreen():
    ClearConsole()
    print("\n--- Create New Nurse ---")
    ident = prompt("Nurse ID / Username")
    password = prompt("Password", secret=True)
    first = prompt("First Name")
    last = prompt("Last Name")
    phone = prompt("Phone Number")
    department = prompt("Department")
    clinicalBackend.CreateNurse(ident, password, first, last, phone, department)
    clinicalBackend.save_all()
    pause()


def StaffManagementMenu(staffPerms):
    options = []
    if staffPerms.get("createsDoctors"):
        options.append(("Create Doctor", CreateDoctorScreen))
    if staffPerms.get("createsNurses"):
        options.append(("Create Nurse", CreateNurseScreen))
    run_menu("Staff Management", options)


# Patient Management


def CreatePatientScreen():
    ClearConsole()
    print("\n--- Create New Patient ---")
    pid = prompt("Patient ID")
    first = prompt("First Name")
    last = prompt("Last Name")
    dob = prompt("Date of Birth (YYYY-MM-DD)")
    phone = prompt("Phone Number")
    addr = prompt("Address")
    clinicalBackend.CreatePatient(pid, first, last, dob, phone, addr)
    clinicalBackend.save_all()
    pause()


def ViewAllPatientsScreen():
    ClearConsole()
    print("\n--- Patient Database ---")
    if not clinicalBackend.patients:
        print("No patients on record.")
    else:
        for patient in clinicalBackend.patients.values():
            patient.DisplayInfo()
    pause()


def ViewPatientByIDScreen():
    ClearConsole()
    print("\n--- View Patient by ID ---")
    pid = prompt("Enter Patient ID")
    patient = clinicalBackend.patients.get(pid)
    if not patient:
        print(f"Patient '{pid}' not found.")
    else:
        patient.DisplayInfo()
    pause()


def PatientManagementMenu(patientPerms):
    options = []
    if patientPerms.get("createsPatients"):
        options.append(("Create Patient", CreatePatientScreen))
    if patientPerms.get("readsPatientDetails"):
        options.append(("View All Patients", ViewAllPatientsScreen))
        options.append(("View Patient by ID", ViewPatientByIDScreen))
    run_menu("Patient Management", options)


# Clinical Actions:


def OrderLabTestScreen():
    ClearConsole()
    print("\n--- Order Lab Test ---")
    if not clinicalBackend.patients:
        print("No patients on record. Please create a patient first.")
        pause()
        return

    print("Available Patients:")
    for pid, p in clinicalBackend.patients.items():
        print(f"  {pid} - {p.firstName} {p.lastName}")

    pid = prompt("\nPatient ID")
    test_name = prompt("Test Name (e.g. CBC, Lipid Panel, Urinalysis)")
    notes = prompt("Notes / Clinical Indication")
    doctor_id = clinicalBackend.currentUserCredentials["Identification"]

    clinicalBackend.CreateLabOrder(pid, doctor_id, test_name, notes)
    clinicalBackend.save_all()
    pause()


def ViewAllLabOrdersScreen():
    ClearConsole()
    print("\n--- All Lab Orders ---")
    orders = clinicalBackend.GetAllLabOrders()
    if not orders:
        print("No lab orders on record.")
    else:
        for order in orders:
            order.Display()
    pause()


def ViewLabOrdersByPatientScreen():
    ClearConsole()
    print("\n--- Lab Orders by Patient ---")
    pid = prompt("Enter Patient ID")
    orders = clinicalBackend.GetLabOrdersForPatient(pid)
    if not orders:
        print(f"No lab orders found for patient '{pid}'.")
    else:
        print(f"\nLab orders for patient '{pid}':")
        for order in orders:
            order.Display()
    pause()


def ClinicalActionsMenu(clinicalPerms):
    options = []
    if clinicalPerms.get("ordersLabTests"):
        options.append(("Order Lab Test", OrderLabTestScreen))
    if clinicalPerms.get("viewsLabTests"):
        options.append(("View All Lab Orders", ViewAllLabOrdersScreen))
        options.append(("View Lab Orders by Patient", ViewLabOrdersByPatientScreen))
    run_menu("Clinical Actions", options)


# Login


def CredentialsMenu(role):
    ClearConsole()
    while True:
        identification = prompt("Username")
        password = prompt("Password", secret=True)
        roleObject = clinicalBackend.Login(role, identification, password)
        if roleObject:
            ClearConsole()
            print(f"Login successful. Welcome, {identification}!")
            sleep(1)
            return roleObject
        print("Invalid credentials. Please try again.")
        sleep(1)


def LoginMenu():
    ClearConsole()
    while True:
        role = prompt("Enter role (Patient/Nurse/Doctor)")
        if role not in ("Patient", "Nurse", "Doctor"):
            print("Invalid role. Please enter Patient, Nurse, or Doctor.")
            sleep(1)
        else:
            return CredentialsMenu(role)


# Main user menu


def userMenu(currentUserRoleObject):
    while True:
        ClearConsole()
        ident = clinicalBackend.currentUserCredentials.get("Identification")
        print(f"\n=== Main Menu  |  Logged in as: {ident} ===\n")

        options = []

        if clinicalBackend.currentUserPermissions.get("readsOwnUserDetails"):
            options.append(
                ("Display My Information", currentUserRoleObject.DisplayInfo)
            )

        patientPerms = clinicalBackend.currentUserPermissions.get(
            "PatientManagement", {}
        )
        if patientPerms.get("enabled"):
            options.append(
                ("Patient Management", lambda p=patientPerms: PatientManagementMenu(p))
            )

        staffPerms = clinicalBackend.currentUserPermissions.get("StaffManagement", {})
        if staffPerms.get("enabled"):
            options.append(
                ("Staff Management", lambda s=staffPerms: StaffManagementMenu(s))
            )

        clinicalPerms = clinicalBackend.currentUserPermissions.get(
            "ClinicalActions", {}
        )
        if clinicalPerms.get("enabled"):
            options.append(
                ("Clinical Actions", lambda c=clinicalPerms: ClinicalActionsMenu(c))
            )

        print("(0) - Exit Program")
        for i, (label, _) in enumerate(options, 1):
            print(f"({i}) - {label}")

        choice = prompt("\n->")
        try:
            idx = int(choice)
            if idx == 0:
                clinicalBackend.save_all()
                print("Goodbye.")
                break
            label, fn = options[idx - 1]
            fn()
            if "Information" in label:
                pause()
        except (ValueError, IndexError):
            print("Invalid option.")
            sleep(1)


# Entry point

clinicalBackend = MedicalInterfaceBackend()
clinicalBackend.load_all()

# Seed a default doctor on first run
if not clinicalBackend.doctors:
    clinicalBackend.CreateDoctor(
        "chief", "123", "Andrew", "Jordan", "4808121294", "Pediatric"
    )
    clinicalBackend.save_all()

roleObject = LoginMenu()
userMenu(roleObject)
