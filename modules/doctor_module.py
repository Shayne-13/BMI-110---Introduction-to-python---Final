# Troy Wilson
import json
import os
import getpass
import uuid
from time import sleep
from subprocess import call


class MedicalInterfaceBackend:
    """Central backend managing doctors, nurses, patients, lab orders, and authentication."""

    def __init__(self):
        self.doctors = {}
        self.nurses = {}
        self.patients = {}
        self.lab_orders = []

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
        """Register a new doctor. Returns False if the ID already exists."""
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
        """Register a new nurse. Returns False if the ID already exists."""
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
        """Register a new patient. Returns False if the ID already exists."""
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
        """Create a lab order for a patient. Returns False if the patient ID is not found."""
        if strPatientID not in self.patients:
            print(f"Patient '{strPatientID}' not found.")
            return False
        order = LabOrder(strPatientID, strOrderingDoctorID, strTestName, strNotes)
        self.lab_orders.append(order)
        print(f"Lab order '{order.order_id}' created for patient '{strPatientID}'.")
        return True

    def GetLabOrdersForPatient(self, strPatientID):
        """Return all lab orders for a given patient ID."""
        return [o for o in self.lab_orders if o.patient_id == strPatientID]

    def GetAllLabOrders(self):
        """Return all lab orders in the system."""
        return list(self.lab_orders)

    def Login(self, strRole, strIdentification, strPassword):
        """Authenticate a user and load their permissions. Returns the role object or False."""
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
        """Load all data from disk."""
        self._load_doctors()
        self._load_nurses()
        self._load_patients()
        self._load_lab_orders()

    def save_all(self):
        """Persist all data to disk."""
        self._save_doctors()
        self._save_nurses()
        self._save_patients()
        self._save_lab_orders()

    def _load_doctors(self):
        """Load doctors from doctors.json."""
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
        """Load nurses from nurses.json."""
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
        """Load patients from patients.json."""
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
        """Load lab orders from lab_orders.json."""
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
        """Save doctors to doctors.json."""
        with open("doctors.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.doctors.items()}, f, indent=4)

    def _save_nurses(self):
        """Save nurses to nurses.json."""
        with open("nurses.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.nurses.items()}, f, indent=4)

    def _save_patients(self):
        """Save patients to patients.json."""
        with open("patients.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.patients.items()}, f, indent=4)

    def _save_lab_orders(self):
        """Save lab orders to lab_orders.json."""
        with open("lab_orders.json", "w") as f:
            json.dump([o.__dict__ for o in self.lab_orders], f, indent=4)


class Doctor:
    """A doctor with full staff, patient, and clinical permissions."""

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
        """Print the doctor's profile to the console."""
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
        """Update profile after verifying current password. Returns a (bool, message) tuple."""
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
    """A nurse with patient-read and lab-view permissions, but no staff management."""

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
        """Print the nurse's profile to the console."""
        print(
            f"\n--- Nurse Info ---"
            f"\nID:         {self.__user_id}"
            f"\nName:       {self.firstName} {self.lastName}"
            f"\nPhone:      {self.__phone}"
            f"\nDepartment: {self.department}"
            f"\nRole:       {self.role}\n"
        )


class Patient:
    """A patient with read-only access to their own profile."""

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
        """Print the patient's profile to the console."""
        print(
            f"\n--- Patient Info ---"
            f"\nID:            {self.patient_id}"
            f"\nName:          {self.firstName} {self.lastName}"
            f"\nDate of Birth: {self.dateOfBirth}"
            f"\nPhone:         {self.__phone}"
            f"\nAddress:       {self.__address}\n"
        )


class LabOrder:
    """A lab test order with an auto-generated ID and a default status of Pending."""

    def __init__(self, strPatientID, strOrderingDoctorID, strTestName, strNotes):
        self.order_id = str(uuid.uuid4())[:8].upper()
        self.patient_id = strPatientID
        self.ordering_doctor_id = strOrderingDoctorID
        self.test_name = strTestName
        self.notes = strNotes
        self.status = "Pending"

    def Display(self):
        """Print the lab order's details to the console."""
        print(
            f"\n  Order ID: {self.order_id}"
            f"\n  Patient:  {self.patient_id}"
            f"\n  Doctor:   {self.ordering_doctor_id}"
            f"\n  Test:     {self.test_name}"
            f"\n  Notes:    {self.notes}"
            f"\n  Status:   {self.status}"
        )


# Helper stuff:
def ClearConsole(intTimeout=0):
    """Clear the terminal, optionally after a delay in seconds."""
    if intTimeout:
        sleep(intTimeout)
    call("clear" if os.name == "posix" else "cls")


def prompt(label, secret=False):
    """Prompt for user input. Pass secret=True to hide input (for passwords)."""
    if secret:
        return getpass.getpass(f"{label}: ")
    return input(f"{label}: ").strip()


def pause():
    """Wait for the user to press Enter."""
    input("\nPress Enter to continue...")


def run_menu(title, options):
    """Display a numbered menu and dispatch selections. Option 0 returns to the previous menu."""
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


# Staff Management


def ViewStaffScreen():
    """Display all doctors and nurses in the system."""
    ClearConsole()
    print("\n--- Staff Database ---")
    if not clinicalBackend.doctors and not clinicalBackend.nurses:
        print("No Staff on record.")
    if clinicalBackend.doctors:
        for patient in clinicalBackend.doctors.values():
            patient.DisplayInfo()
    if clinicalBackend.nurses:
        for patient in clinicalBackend.nurses.values():
            patient.DisplayInfo()
    pause()


def CreateDoctorScreen():
    """Prompt for new doctor details and register them."""
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
    """Prompt for new nurse details and register them."""
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
    """Staff management submenu, filtered by the current user's permissions."""
    options = [("View Staff Database", ViewStaffScreen)]
    if staffPerms.get("createsDoctors"):
        options.append(("Create Doctor", CreateDoctorScreen))
    if staffPerms.get("createsNurses"):
        options.append(("Create Nurse", CreateNurseScreen))
    run_menu("Staff Management", options)


# Patient Management


def CreatePatientScreen():
    """Prompt for new patient details and register them."""
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
    """Display all patients in the system."""
    ClearConsole()
    print("\n--- Patient Database ---")
    if not clinicalBackend.patients:
        print("No patients on record.")
    else:
        for patient in clinicalBackend.patients.values():
            patient.DisplayInfo()
    pause()


def ViewPatientByIDScreen():
    """Prompt for a patient ID and display that patient's info."""
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
    """Patient management submenu, filtered by the current user's permissions."""
    options = []
    if patientPerms.get("createsPatients"):
        options.append(("Create Patient", CreatePatientScreen))
    if patientPerms.get("readsPatientDetails"):
        options.append(("View All Patients", ViewAllPatientsScreen))
        options.append(("View Patient by ID", ViewPatientByIDScreen))
    run_menu("Patient Management", options)


# Clinical Actions


def OrderLabTestScreen():
    """Prompt the logged-in doctor to order a lab test for a patient."""
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
    """Display all lab orders in the system."""
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
    """Prompt for a patient ID and display their lab orders."""
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
    """Clinical actions submenu, filtered by the current user's permissions."""
    options = []
    if clinicalPerms.get("ordersLabTests"):
        options.append(("Order Lab Test", OrderLabTestScreen))
    if clinicalPerms.get("viewsLabTests"):
        options.append(("View All Lab Orders", ViewAllLabOrdersScreen))
        options.append(("View Lab Orders by Patient", ViewLabOrdersByPatientScreen))
    run_menu("Clinical Actions", options)


# Login Things


def CredentialsMenu(role):
    """Prompt for credentials and authenticate, retrying on failure."""
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
    """Prompt the user to select a role and log in."""
    ClearConsole()
    while True:
        role = prompt("Enter role (Patient/Nurse/Doctor)")
        if role not in ("Patient", "Nurse", "Doctor"):
            print("Invalid role. Please enter Patient, Nurse, or Doctor.")
            sleep(1)
        else:
            return CredentialsMenu(role)


# main menu


def userMenu(currentUserRoleObject):
    """Main menu loop. Shows only options permitted for the logged-in user."""
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


# I had to do this so it would play nice with the pydoc tool
if __name__ == "__main__":
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
