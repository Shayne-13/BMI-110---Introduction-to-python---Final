# Troy Wilson
import json
import os
import getpass
import uuid
from time import sleep
from subprocess import call


class MedicalInterfaceBackend:
    """
    Central backend for the medical interface system.

    Manages all staff (doctors, nurses), patients, and lab orders.
    Handles login/authentication, role-based permission enforcement,
    and JSON-based persistence to disk.

    Attributes:
        doctors (dict): Maps doctor ID strings to Doctor objects.
        nurses (dict): Maps nurse ID strings to Nurse objects.
        patients (dict): Maps patient ID strings to Patient objects.
        lab_orders (list): List of all LabOrder objects in the system.
        currentUserPermissions (dict): Permission flags for the currently logged-in user.
        currentUserCredentials (dict): Credentials/metadata for the currently logged-in user.
    """

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
        """
        Register a new doctor in the system.

        Args:
            strUserIdentification (str): Unique doctor ID / username.
            strPassword (str): Login password.
            strFirstName (str): Doctor's first name.
            strLastName (str): Doctor's last name.
            strPhoneNumber (str): Contact phone number.
            strSpecialty (str): Medical specialty (e.g. "Pediatric").

        Returns:
            bool: True if the doctor was created successfully, False if the ID already exists.
        """
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
        """
        Register a new nurse in the system.

        Args:
            strUserIdentification (str): Unique nurse ID / username.
            strPassword (str): Login password.
            strFirstName (str): Nurse's first name.
            strLastName (str): Nurse's last name.
            strPhoneNumber (str): Contact phone number.
            strDepartment (str): Department the nurse belongs to (e.g. "ICU").

        Returns:
            bool: True if the nurse was created successfully, False if the ID already exists.
        """
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
        """
        Register a new patient in the system.

        Args:
            strPatientID (str): Unique patient ID.
            strFirstName (str): Patient's first name.
            strLastName (str): Patient's last name.
            strDateOfBirth (str): Date of birth in YYYY-MM-DD format.
            strPhoneNumber (str): Contact phone number.
            strAddress (str): Home address.

        Returns:
            bool: True if the patient was created successfully, False if the ID already exists.
        """
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
        """
        Create a new lab order for a patient.

        Args:
            strPatientID (str): ID of the patient the order is for.
            strOrderingDoctorID (str): ID of the doctor placing the order.
            strTestName (str): Name of the lab test (e.g. "CBC", "Urinalysis").
            strNotes (str): Clinical notes or indication for the test.

        Returns:
            bool: True if the order was created, False if the patient ID was not found.
        """
        if strPatientID not in self.patients:
            print(f"Patient '{strPatientID}' not found.")
            return False
        order = LabOrder(strPatientID, strOrderingDoctorID, strTestName, strNotes)
        self.lab_orders.append(order)
        print(f"Lab order '{order.order_id}' created for patient '{strPatientID}'.")
        return True

    def GetLabOrdersForPatient(self, strPatientID):
        """
        Retrieve all lab orders associated with a specific patient.

        Args:
            strPatientID (str): ID of the patient to filter by.

        Returns:
            list[LabOrder]: A list of LabOrder objects belonging to the patient.
                            Returns an empty list if none are found.
        """
        return [o for o in self.lab_orders if o.patient_id == strPatientID]

    def GetAllLabOrders(self):
        """
        Retrieve every lab order in the system.

        Returns:
            list[LabOrder]: A shallow copy of the full lab orders list.
        """
        return list(self.lab_orders)

    def Login(self, strRole, strIdentification, strPassword):
        """
        Authenticate a user and load their permissions into the session.

        Patients are not password-authenticated — any patient ID is accepted.
        On success, updates ``currentUserCredentials`` and ``currentUserPermissions``
        with the authenticated user's data.

        Args:
            strRole (str): Role to authenticate as. Must be "Doctor", "Nurse", or "Patient".
            strIdentification (str): The user's ID / username.
            strPassword (str): The user's password (ignored for Patient logins).

        Returns:
            Doctor | Nurse | Patient | bool: The authenticated role object on success,
                                             or False if authentication fails.
        """
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
        """Load all data from disk. Calls individual loaders for each entity type."""
        self._load_doctors()
        self._load_nurses()
        self._load_patients()
        self._load_lab_orders()

    def save_all(self):
        """Persist all in-memory data to disk. Calls individual savers for each entity type."""
        self._save_doctors()
        self._save_nurses()
        self._save_patients()
        self._save_lab_orders()

    def _load_doctors(self):
        """
        Load doctors from ``doctors.json`` into memory.
        Silently skips if the file does not exist.
        """
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
        """
        Load nurses from ``nurses.json`` into memory.
        Silently skips if the file does not exist.
        """
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
        """
        Load patients from ``patients.json`` into memory.
        Silently skips if the file does not exist.
        """
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
        """
        Load lab orders from ``lab_orders.json`` into memory.
        Uses ``__new__`` to reconstruct LabOrder objects without calling ``__init__``,
        then restores state via ``__dict__``. Silently skips if the file does not exist.
        """
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
        """Serialize all Doctor objects to ``doctors.json``."""
        with open("doctors.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.doctors.items()}, f, indent=4)

    def _save_nurses(self):
        """Serialize all Nurse objects to ``nurses.json``."""
        with open("nurses.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.nurses.items()}, f, indent=4)

    def _save_patients(self):
        """Serialize all Patient objects to ``patients.json``."""
        with open("patients.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.patients.items()}, f, indent=4)

    def _save_lab_orders(self):
        """Serialize all LabOrder objects to ``lab_orders.json``."""
        with open("lab_orders.json", "w") as f:
            json.dump([o.__dict__ for o in self.lab_orders], f, indent=4)


class Doctor:
    """
    Represents a doctor in the medical system.

    Doctors have full permissions: they can manage staff, manage patients,
    and perform all clinical actions including ordering lab tests.

    Attributes:
        firstName (str): Doctor's first name.
        lastName (str): Doctor's last name.
        role (str): Always "Doctor".
        specialty (str): Medical specialty (e.g. "Pediatric").
        permissions (dict): Full permission set granted to all doctors.
    """

    def __init__(
        self,
        strIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strSpecialty,
    ):
        """
        Initialize a Doctor instance.

        Args:
            strIdentification (str): Unique doctor ID / username.
            strPassword (str): Login password (stored as a private attribute).
            strFirstName (str): Doctor's first name.
            strLastName (str): Doctor's last name.
            strPhoneNumber (str): Contact phone number (stored as a private attribute).
            strSpecialty (str): Medical specialty.
        """
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
        """Print the doctor's profile information to the console."""
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
        """
        Update the doctor's profile after verifying their current password.

        Args:
            strIdentification (str): New doctor ID / username.
            strFirstName (str): New first name.
            strLastName (str): New last name.
            strPhoneNumber (str): New phone number.
            strSpecialty (str): New medical specialty.
            strNewPassword (str): New password to set.
            strCurrentPassword (str): Current password for verification.

        Returns:
            tuple[bool, str]: A (success, message) tuple.
                - (False, error message) if the current password is incorrect.
                - (True, success message) if the update completed.
        """
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
    """
    Represents a nurse in the medical system.

    Nurses have limited permissions: they can create and view patients,
    view lab tests, but cannot manage staff or order lab tests.

    Attributes:
        firstName (str): Nurse's first name.
        lastName (str): Nurse's last name.
        role (str): Always "Nurse".
        department (str): Department the nurse belongs to.
        permissions (dict): Restricted permission set granted to all nurses.
    """

    def __init__(
        self,
        strIdentification,
        strPassword,
        strFirstName,
        strLastName,
        strPhoneNumber,
        strDepartment,
    ):
        """
        Initialize a Nurse instance.

        Args:
            strIdentification (str): Unique nurse ID / username.
            strPassword (str): Login password (stored as a private attribute).
            strFirstName (str): Nurse's first name.
            strLastName (str): Nurse's last name.
            strPhoneNumber (str): Contact phone number (stored as a private attribute).
            strDepartment (str): Department the nurse belongs to.
        """
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
        """Print the nurse's profile information to the console."""
        print(
            f"\n--- Nurse Info ---"
            f"\nID:         {self.__user_id}"
            f"\nName:       {self.firstName} {self.lastName}"
            f"\nPhone:      {self.__phone}"
            f"\nDepartment: {self.department}"
            f"\nRole:       {self.role}\n"
        )


class Patient:
    """
    Represents a patient in the medical system.

    Patients have minimal permissions: they can only view their own
    profile. They cannot access staff, other patients, or clinical data.

    Attributes:
        patient_id (str): Unique patient ID.
        firstName (str): Patient's first name.
        lastName (str): Patient's last name.
        dateOfBirth (str): Date of birth in YYYY-MM-DD format.
        role (str): Always "Patient".
        permissions (dict): Minimal permission set granted to all patients.
    """

    def __init__(
        self,
        strPatientID,
        strFirstName,
        strLastName,
        strDateOfBirth,
        strPhoneNumber,
        strAddress,
    ):
        """
        Initialize a Patient instance.

        Args:
            strPatientID (str): Unique patient ID.
            strFirstName (str): Patient's first name.
            strLastName (str): Patient's last name.
            strDateOfBirth (str): Date of birth in YYYY-MM-DD format.
            strPhoneNumber (str): Contact phone number (stored as a private attribute).
            strAddress (str): Home address (stored as a private attribute).
        """
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
        """Print the patient's profile information to the console."""
        print(
            f"\n--- Patient Info ---"
            f"\nID:            {self.patient_id}"
            f"\nName:          {self.firstName} {self.lastName}"
            f"\nDate of Birth: {self.dateOfBirth}"
            f"\nPhone:         {self.__phone}"
            f"\nAddress:       {self.__address}\n"
        )


class LabOrder:
    """
    Represents a single lab test order.

    Each order is assigned a unique 8-character ID on creation and
    begins with a status of "Pending".

    Attributes:
        order_id (str): Auto-generated unique 8-character uppercase order ID.
        patient_id (str): ID of the patient the order is for.
        ordering_doctor_id (str): ID of the doctor who placed the order.
        test_name (str): Name of the lab test (e.g. "CBC", "Lipid Panel").
        notes (str): Clinical notes or indication for the test.
        status (str): Current order status. Defaults to "Pending".
    """

    def __init__(self, strPatientID, strOrderingDoctorID, strTestName, strNotes):
        """
        Initialize a LabOrder instance.

        Args:
            strPatientID (str): ID of the patient the order is for.
            strOrderingDoctorID (str): ID of the doctor placing the order.
            strTestName (str): Name of the lab test.
            strNotes (str): Clinical notes or indication.
        """
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


# ---------------------------------------------------------------------------
# Helper / Utility Functions
# ---------------------------------------------------------------------------


def ClearConsole(intTimeout=0):
    """
    Clear the terminal screen, optionally after a delay.

    Args:
        intTimeout (int | float): Seconds to wait before clearing. Defaults to 0 (immediate).
    """
    if intTimeout:
        sleep(intTimeout)
    call("clear" if os.name == "posix" else "cls")


def prompt(label, secret=False):
    """
    Prompt the user for input, with optional hidden input for passwords.

    Args:
        label (str): The prompt label displayed to the user.
        secret (bool): If True, input is hidden (suitable for passwords). Defaults to False.

    Returns:
        str: The user's input, stripped of leading/trailing whitespace.
    """
    if secret:
        return getpass.getpass(f"{label}: ")
    return input(f"{label}: ").strip()


def pause():
    """Pause execution until the user presses Enter."""
    input("\nPress Enter to continue...")


def run_menu(title, options):
    """
    Display a numbered menu and dispatch the selected action in a loop.

    Continues looping until the user selects option 0 to return.

    Args:
        title (str): Title displayed at the top of the menu.
        options (list[tuple[str, callable]]): A list of (label, function) pairs.
            Each function is called with no arguments when selected.
            Option 0 is always implicitly "Return" and exits the loop.
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


# ---------------------------------------------------------------------------
# Staff Management Screens
# ---------------------------------------------------------------------------


def ViewStaffScreen():
    """Display all doctors and nurses currently registered in the system."""
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
    """Prompt for new doctor details and register them in the system."""
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
    """Prompt for new nurse details and register them in the system."""
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
    """
    Display the Staff Management submenu with options filtered by the user's permissions.

    Args:
        staffPerms (dict): The "StaffManagement" slice of the current user's permissions dict.
            Expected keys: "createsDoctors" (bool), "createsNurses" (bool).
    """
    options = []
    options.append(("View Staff Database", ViewStaffScreen))
    if staffPerms.get("createsDoctors"):
        options.append(("Create Doctor", CreateDoctorScreen))
    if staffPerms.get("createsNurses"):
        options.append(("Create Nurse", CreateNurseScreen))
    run_menu("Staff Management", options)


# ---------------------------------------------------------------------------
# Patient Management Screens
# ---------------------------------------------------------------------------


def CreatePatientScreen():
    """Prompt for new patient details and register them in the system."""
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
    """Display all patients currently registered in the system."""
    ClearConsole()
    print("\n--- Patient Database ---")
    if not clinicalBackend.patients:
        print("No patients on record.")
    else:
        for patient in clinicalBackend.patients.values():
            patient.DisplayInfo()
    pause()


def ViewPatientByIDScreen():
    """Prompt for a patient ID and display that patient's information."""
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
    """
    Display the Patient Management submenu with options filtered by the user's permissions.

    Args:
        patientPerms (dict): The "PatientManagement" slice of the current user's permissions dict.
            Expected keys: "createsPatients" (bool), "readsPatientDetails" (bool).
    """
    options = []
    if patientPerms.get("createsPatients"):
        options.append(("Create Patient", CreatePatientScreen))
    if patientPerms.get("readsPatientDetails"):
        options.append(("View All Patients", ViewAllPatientsScreen))
        options.append(("View Patient by ID", ViewPatientByIDScreen))
    run_menu("Patient Management", options)


# ---------------------------------------------------------------------------
# Clinical Actions Screens
# ---------------------------------------------------------------------------


def OrderLabTestScreen():
    """
    Prompt the logged-in doctor to order a lab test for a selected patient.

    Displays all available patients before prompting for input.
    Automatically uses the currently logged-in doctor's ID as the ordering doctor.
    """
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
    """Display all lab orders currently in the system."""
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
    """Prompt for a patient ID and display all lab orders associated with that patient."""
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
    """
    Display the Clinical Actions submenu with options filtered by the user's permissions.

    Args:
        clinicalPerms (dict): The "ClinicalActions" slice of the current user's permissions dict.
            Expected keys: "ordersLabTests" (bool), "viewsLabTests" (bool).
    """
    options = []
    if clinicalPerms.get("ordersLabTests"):
        options.append(("Order Lab Test", OrderLabTestScreen))
    if clinicalPerms.get("viewsLabTests"):
        options.append(("View All Lab Orders", ViewAllLabOrdersScreen))
        options.append(("View Lab Orders by Patient", ViewLabOrdersByPatientScreen))
    run_menu("Clinical Actions", options)


# ---------------------------------------------------------------------------
# Login Screens
# ---------------------------------------------------------------------------


def CredentialsMenu(role):
    """
    Prompt for credentials and authenticate the user, retrying on failure.

    Args:
        role (str): The role to authenticate as ("Doctor", "Nurse", or "Patient").

    Returns:
        Doctor | Nurse | Patient: The authenticated role object on success.
    """
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
    """
    Prompt the user to select a role and log in.

    Loops until a valid role is entered, then delegates to ``CredentialsMenu``.

    Returns:
        Doctor | Nurse | Patient: The authenticated role object.
    """
    ClearConsole()
    while True:
        role = prompt("Enter role (Patient/Nurse/Doctor)")
        if role not in ("Patient", "Nurse", "Doctor"):
            print("Invalid role. Please enter Patient, Nurse, or Doctor.")
            sleep(1)
        else:
            return CredentialsMenu(role)


# ---------------------------------------------------------------------------
# Main User Menu
# ---------------------------------------------------------------------------


def userMenu(currentUserRoleObject):
    """
    Display the main menu for the logged-in user, showing only permitted options.

    Loops until the user selects exit (option 0), at which point all data is saved.

    Args:
        currentUserRoleObject (Doctor | Nurse | Patient): The authenticated user object
            returned by ``LoginMenu``. Used to call ``DisplayInfo`` for the user's own profile.
    """
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


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    clinicalBackend = MedicalInterfaceBackend()
    clinicalBackend.load_all()

    # Seed a default doctor on first run so the system is never locked out
    if not clinicalBackend.doctors:
        clinicalBackend.CreateDoctor(
            "chief", "123", "Andrew", "Jordan", "4808121294", "Pediatric"
        )
        clinicalBackend.save_all()

    roleObject = LoginMenu()
    userMenu(roleObject)
