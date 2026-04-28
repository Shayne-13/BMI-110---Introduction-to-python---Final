"""
Homebrew HIS - Hospital Information System
Author: Troy W, Shayne W, Gabriel R
Course: CPI 110 Final Project

This program provides a graphical user interface for managing hospital staff,
patients, lab orders, and billing using Python's built-in Tkinter library.
All data is saved locally using JSON files so records persist between sessions.
"""

import json
import os
import uuid
import tkinter as tk
from tkinter import messagebox, ttk


# This section contains all of the backend logic for the application.
# These classes handle data storage, user authentication, and business rules.
# None of this section deals with the visual interface — it is purely data and logic.

class MedicalInterfaceBackend:
    def __init__(self):
        # We store all staff and patients in dictionaries so we can look them up quickly by ID.
        # Lab orders are kept in a list since we often need to loop through all of them.
        self.doctors = {}
        self.nurses = {}
        self.patients = {}
        self.lab_orders = []

        # These default permissions represent a logged-out user who has no access to anything.
        # They get replaced with real permissions as soon as someone successfully logs in.
        self.currentUserPermissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {"enabled": False, "createsDoctors": False, "createsNurses": False},
            "PatientManagement": {"enabled": False, "createsPatients": False, "readsPatientDetails": False, "writesPatientDetails": False},
            "ClinicalActions": {"enabled": False, "viewsLabTests": False, "ordersLabTests": False},
        }

        self.currentUserCredentials = {"Username": "", "Identification": "", "Password": "", "Role": ""}

    def CreateDoctor(self, strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strSpecialty):
        if strUserIdentification in self.doctors:
            return False, f"Doctor ID '{strUserIdentification}' already exists."
        self.doctors[strUserIdentification] = Doctor(strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strSpecialty)
        return True, f"Doctor '{strUserIdentification}' successfully added."

    def CreateNurse(self, strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strDepartment):
        if strUserIdentification in self.nurses:
            return False, f"Nurse ID '{strUserIdentification}' already exists."
        self.nurses[strUserIdentification] = Nurse(strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strDepartment)
        return True, f"Nurse '{strUserIdentification}' successfully added."

    def CreatePatient(self, strPatientID, strFirstName, strLastName, strDateOfBirth, strPhoneNumber, strAddress, strCauseOfVisit="", strCreatedBy=""):
        if strPatientID in self.patients:
            return False, f"Patient ID '{strPatientID}' already exists."
        self.patients[strPatientID] = Patient(strPatientID, strFirstName, strLastName, strDateOfBirth, strPhoneNumber, strAddress, strCauseOfVisit, None, strCreatedBy)
        return True, f"Patient '{strPatientID}' successfully added."

    def CreateLabOrder(self, strPatientID, strOrderingDoctorID, strTestName, strNotes, fPrice=0.0):
        if strPatientID not in self.patients:
            return False, f"Patient '{strPatientID}' not found."
        order = LabOrder(strPatientID, strOrderingDoctorID, strTestName, strNotes, fPrice)
        self.lab_orders.append(order)
        # If a price was provided, we add it as a line item on the patient's bill automatically.
        if float(fPrice) > 0:
            self.patients[strPatientID].bill.append({
                "description": f"Clinical: {strTestName}",
                "amount": float(fPrice)
            })
        return True, f"Lab order '{order.order_id}' created for patient '{strPatientID}'."

    def GetLabOrdersForPatient(self, strPatientID):
        return [o for o in self.lab_orders if o.patient_id == strPatientID]

    def GetAllLabOrders(self):
        return list(self.lab_orders)

    def Login(self, strRole, strIdentification, strPassword):
        import copy
        if strRole == "Doctor":
            found = self.doctors.get(strIdentification)
            if found and found._Doctor__password == strPassword:
                self.currentUserCredentials["Role"] = "Doctor"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = copy.deepcopy(found.permissions)
                return found
        elif strRole == "Nurse":
            found = self.nurses.get(strIdentification)
            if found and found._Nurse__password == strPassword:
                self.currentUserCredentials["Role"] = "Nurse"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = copy.deepcopy(found.permissions)
                return found
        elif strRole == "Patient":
            found = self.patients.get(strIdentification)
            if found:
                self.currentUserCredentials["Role"] = "Patient"
                self.currentUserCredentials["Identification"] = strIdentification
                self.currentUserPermissions = copy.deepcopy(found.permissions)
                return found
        return False

    def load_all(self):
        # Loads all four data files at startup so the app has the latest saved records.
        self._load_doctors(); self._load_nurses(); self._load_patients(); self._load_lab_orders()

    def save_all(self):
        # Writes all four data sets back to their JSON files after any change is made.
        self._save_doctors(); self._save_nurses(); self._save_patients(); self._save_lab_orders()

    def _load_doctors(self):
        # Reads the doctors JSON file and reconstructs each Doctor object from the saved data.
        # If the file does not exist yet, we simply skip loading and start with an empty dictionary.
        try:
            with open("doctors.json", "r") as f:
                raw = json.load(f)
            for ident, d in raw.items():
                self.doctors[ident] = Doctor(d["_Doctor__user_id"], d["_Doctor__password"], d["firstName"], d["lastName"], d["_Doctor__phone"], d["specialty"])
        except FileNotFoundError:
            pass

    def _load_nurses(self):
        # Same as _load_doctors but for nurse records.
        try:
            with open("nurses.json", "r") as f:
                raw = json.load(f)
            for ident, d in raw.items():
                self.nurses[ident] = Nurse(d["_Nurse__user_id"], d["_Nurse__password"], d["firstName"], d["lastName"], d["_Nurse__phone"], d["department"])
        except FileNotFoundError:
            pass

    def _load_patients(self):
        # Reads patient records from disk. We use .get() with defaults for newer fields
        # like cause_of_visit and bill so that older saved files still load without crashing.
        try:
            with open("patients.json", "r") as f:
                raw = json.load(f)
            for pid, d in raw.items():
                self.patients[pid] = Patient(
                    d["patient_id"], d["firstName"], d["lastName"], d["dateOfBirth"],
                    d["_Patient__phone"], d["_Patient__address"],
                    d.get("cause_of_visit", ""),
                    d.get("bill", None),
                    d.get("created_by", "Unknown"))
        except FileNotFoundError:
            pass

    def _load_lab_orders(self):
        # Lab orders are stored as plain dictionaries in JSON, so we create a blank LabOrder
        # object and then populate its attributes directly from the saved data.
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
        # Converts each Doctor object into a dictionary and writes them all to a JSON file.
        with open("doctors.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.doctors.items()}, f, indent=4)

    def _save_nurses(self):
        # Same as _save_doctors but writes nurse records to nurses.json.
        with open("nurses.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.nurses.items()}, f, indent=4)

    def _save_patients(self):
        # Saves all patient records including their billing history to patients.json.
        with open("patients.json", "w") as f:
            json.dump({k: v.__dict__ for k, v in self.patients.items()}, f, indent=4)

    def _save_lab_orders(self):
        # Saves every lab order as a list of dictionaries in lab_orders.json.
        with open("lab_orders.json", "w") as f:
            json.dump([o.__dict__ for o in self.lab_orders], f, indent=4)


# The Doctor class represents a physician on staff. Doctors have full access to
# the system including the ability to create other staff members and order lab tests.
class Doctor:
    def __init__(self, strIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strSpecialty):
        self.__user_id = strIdentification
        self.__password = strPassword
        self.__phone = strPhoneNumber
        self.firstName = strFirstName
        self.lastName = strLastName
        self.role = "Doctor"
        self.specialty = strSpecialty
        # Doctors are given full permissions across the entire system.
        self.permissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {"enabled": True, "createsDoctors": True, "createsNurses": True},
            "PatientManagement": {"enabled": True, "createsPatients": True, "readsPatientDetails": True, "writesPatientDetails": True},
            "ClinicalActions": {"enabled": True, "viewsLabTests": True, "ordersLabTests": True},
        }

    def GetInfo(self):
        return (f"ID:        {self.__user_id}\n"
                f"Name:      {self.firstName} {self.lastName}\n"
                f"Phone:     {self.__phone}\n"
                f"Specialty: {self.specialty}\n"
                f"Role:      {self.role}")


# The Nurse class represents a nursing staff member. Nurses can manage patients
# and view lab orders, but they cannot create other staff or order new lab tests.
class Nurse:
    def __init__(self, strIdentification, strPassword, strFirstName, strLastName, strPhoneNumber, strDepartment):
        self.__user_id = strIdentification
        self.__password = strPassword
        self.__phone = strPhoneNumber
        self.firstName = strFirstName
        self.lastName = strLastName
        self.role = "Nurse"
        self.department = strDepartment
        # Nurses have limited permissions — they can work with patients but not manage staff.
        self.permissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {"enabled": False, "createsDoctors": False, "createsNurses": False},
            "PatientManagement": {"enabled": True, "createsPatients": True, "readsPatientDetails": True, "writesPatientDetails": False},
            "ClinicalActions": {"enabled": True, "viewsLabTests": True, "ordersLabTests": False},
        }

    def GetInfo(self):
        return (f"ID:         {self.__user_id}\n"
                f"Name:       {self.firstName} {self.lastName}\n"
                f"Phone:      {self.__phone}\n"
                f"Department: {self.department}\n"
                f"Role:       {self.role}")


# The Patient class stores all information about a person receiving care.
# Patients can only log in to view their own information and billing details.
class Patient:
    def __init__(self, strPatientID, strFirstName, strLastName, strDateOfBirth, strPhoneNumber, strAddress, strCauseOfVisit="", bill=None, strCreatedBy=""):
        self.patient_id = strPatientID
        self.firstName = strFirstName
        self.lastName = strLastName
        self.dateOfBirth = strDateOfBirth
        self.__phone = strPhoneNumber
        self.__address = strAddress
        self.cause_of_visit = strCauseOfVisit
        # We store who registered this patient so there is always a clear record of accountability.
        self.created_by = strCreatedBy
        # Every new patient automatically starts with a $25.00 activation fee on their bill.
        # Additional charges are added later when clinical actions are performed.
        self.bill = bill if bill is not None else [{"description": "Activation Fee", "amount": 25.00}]
        self.role = "Patient"
        # Nurses have limited permissions — they can work with patients but not manage staff.
        # Patients are restricted to viewing only their own information.
        # They have no access to staff management or clinical ordering features.
        self.permissions = {
            "readsOwnUserDetails": True,
            "StaffManagement": {"enabled": False, "createsDoctors": False, "createsNurses": False},
            "PatientManagement": {"enabled": False, "createsPatients": False, "readsPatientDetails": False, "writesPatientDetails": False},
            "ClinicalActions": {"enabled": False, "viewsLabTests": False, "ordersLabTests": False},
        }

    def GetInfo(self):
        return (f"ID:             {self.patient_id}\n"
                f"Name:           {self.firstName} {self.lastName}\n"
                f"Date of Birth:  {self.dateOfBirth}\n"
                f"Phone:          {self.__phone}\n"
                f"Address:        {self.__address}\n"
                f"Cause of Visit: {self.cause_of_visit}")


# The LabOrder class represents a single clinical test ordered by a doctor for a patient.
# Each order gets a unique ID generated automatically using the uuid module.
class LabOrder:
    def __init__(self, strPatientID, strOrderingDoctorID, strTestName, strNotes, fPrice=0.0):
        self.order_id = str(uuid.uuid4())[:8].upper()
        self.patient_id = strPatientID
        self.ordering_doctor_id = strOrderingDoctorID
        self.test_name = strTestName
        self.notes = strNotes
        self.price = float(fPrice)
        self.status = "Pending"

    def GetInfo(self):
        return (f"Order ID: {self.order_id}  |  Patient: {self.patient_id}  |  "
                f"Doctor: {self.ordering_doctor_id}  |  Test: {self.test_name}  |  "
                f"Notes: {self.notes}  |  Status: {self.status}")


# This section contains everything related to the visual interface.
# Each screen in the app is built as a Tkinter Frame class so they can be
# swapped in and out without rebuilding the entire window each time.

# We define all our colors in one place so it is easy to update the theme later
# without having to hunt through every widget definition in the file.
COLORS = {
    "bg": "#f0f4f8",
    "sidebar": "#1a3a5c",
    "sidebar_btn": "#2a5080",
    "sidebar_btn_hover": "#3a6090",
    "accent": "#2196F3",
    "danger": "#e53935",
    "success": "#43a047",
    "text": "#212121",
    "text_light": "#ffffff",
    "card": "#ffffff",
    "border": "#cfd8dc",
}

# Font definitions are stored as tuples that Tkinter can use directly.
# Keeping them here makes it simple to change sizes or families in one spot.
FONT_TITLE  = ("Helvetica", 18, "bold")
FONT_HEADER = ("Helvetica", 13, "bold")
FONT_BODY   = ("Helvetica", 11)
FONT_SMALL  = ("Helvetica", 9)


def make_label_entry(parent, label_text, row, secret=False):
    """Creates a label and text entry pair side by side in a grid layout.
    The secret parameter hides the typed characters, which we use for password fields."""
    tk.Label(parent, text=label_text, font=FONT_BODY, bg=COLORS["card"],
             fg=COLORS["text"], anchor="w").grid(row=row, column=0, sticky="w", pady=4, padx=8)
    var = tk.StringVar()
    show = "*" if secret else ""
    entry = tk.Entry(parent, textvariable=var, font=FONT_BODY, show=show,
                     relief="solid", bd=1, width=30)
    entry.grid(row=row, column=1, sticky="ew", pady=4, padx=8)
    return var


def styled_button(parent, text, command, color=None, fg=None, width=18):
    """Creates a flat, colored button with a hover effect. This is used throughout
    the app so every button has a consistent look without repeating the same code."""
    color = color or COLORS["accent"]
    fg = fg or COLORS["text_light"]
    btn = tk.Button(parent, text=text, command=command, bg=color, fg=fg,
                    font=FONT_BODY, relief="flat", activebackground=color,
                    activeforeground=fg, cursor="hand2", width=width, pady=6)
    btn.bind("<Enter>", lambda e: btn.config(bg=_darken(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _darken(hex_color):
    """Takes a hex color string and returns a slightly darker version of it.
    We use this to create the hover effect on buttons throughout the interface."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (max(0, int(h[i:i+2], 16) - 20) for i in (0, 2, 4))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


# The App class is the main application window. It inherits from tk.Tk which means
# it IS the window itself. All other screens are loaded inside it.
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Homebrew HIS")
        self.geometry("950x650")
        self.minsize(800, 550)
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)

        self.backend = MedicalInterfaceBackend()
        self.backend.load_all()

        # If no doctor records exist yet, we create a default admin doctor so the
        # system has at least one account to log into on the very first run.
        if not self.backend.doctors:
            self.backend.CreateDoctor("chief", "123", "Andrew", "Jordan", "4808121294", "Pediatric")
            self.backend.save_all()

        self.current_user = None

        # Container for all pages
        self.container = tk.Frame(self, bg=COLORS["bg"])
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def _clear(self):
        # Removes all widgets from the container so a fresh screen can be loaded in.
        for w in self.container.winfo_children():
            w.destroy()

    def show_login(self):
        # Clears the window and loads the login screen.
        self._clear()
        LoginPage(self.container, self)

    def show_main_menu(self):
        # Clears the window and loads the main menu after a successful login.
        self._clear()
        MainMenuPage(self.container, self)

    def show_page(self, PageClass, **kwargs):
        self._clear()
        PageClass(self.container, self, **kwargs)

    def logout(self):
        # Saves all data before logging out so nothing is lost, then returns to the login screen.
        self.backend.save_all()
        self.current_user = None
        self.show_login()


# The LoginPage is the first screen the user sees. It shows three role buttons
# and then slides into a credential form once a role has been selected.
class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.pack(fill="both", expand=True)
        self.app = app
        self.selected_role = None

        # Centered card
        self.card = tk.Frame(self, bg=COLORS["card"], relief="flat", bd=0,
                             highlightbackground=COLORS["border"], highlightthickness=1)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=380)

        tk.Label(self.card, text="🏥 Homebrew HIS", font=FONT_TITLE,
                 bg=COLORS["card"], fg=COLORS["sidebar"]).pack(pady=(30, 5))
        self.subtitle = tk.Label(self.card, text="Select your role to continue",
                                 font=FONT_SMALL, bg=COLORS["card"], fg="gray")
        self.subtitle.pack(pady=(0, 25))

        # ── Step 1: Role buttons ──
        self.role_frame = tk.Frame(self.card, bg=COLORS["card"])
        self.role_frame.pack(pady=10)

        role_configs = [
            ("🩺  Doctor",  "Doctor",  "#1a3a5c"),
            ("💉  Nurse",   "Nurse",   "#2e7d32"),
            ("🧑  Patient", "Patient", "#6a1b9a"),
        ]
        for label, role, color in role_configs:
            btn = tk.Button(
                self.role_frame, text=label, width=22,
                bg=color, fg=COLORS["text_light"],
                font=("Helvetica", 12, "bold"), relief="flat",
                activebackground=_darken(color), activeforeground=COLORS["text_light"],
                cursor="hand2", pady=12,
                command=lambda r=role, c=color: self.show_credentials(r, c)
            )
            btn.pack(pady=6)
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=_darken(c)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

        # ── Step 2: Credentials form (hidden initially) ──
        self.cred_frame = tk.Frame(self.card, bg=COLORS["card"])
        self.err_label  = tk.Label(self.card, text="", font=FONT_SMALL,
                                   bg=COLORS["card"], fg=COLORS["danger"])

    def show_credentials(self, role, color):
        """Hides the role selection buttons and shows the username and password
        fields for whichever role the user clicked on."""
        self.selected_role = role
        self.role_frame.pack_forget()

        for w in self.cred_frame.winfo_children():
            w.destroy()
        self.cred_frame.pack(fill="x", padx=30)

        # Back button
        tk.Button(self.cred_frame, text="← Back", bg=COLORS["card"], fg="gray",
                  font=FONT_SMALL, relief="flat", cursor="hand2",
                  command=self.show_roles).pack(anchor="w", pady=(0, 8))

        # Role badge
        tk.Label(self.cred_frame, text=f"Logging in as  {role}",
                 font=("Helvetica", 11, "bold"), bg=color,
                 fg=COLORS["text_light"], padx=10, pady=4).pack(anchor="w", pady=(0, 14))

        form = tk.Frame(self.cred_frame, bg=COLORS["card"])
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        # Field labels differ by role
        if role == "Patient":
            self.id_var   = make_label_entry(form, "Patient ID", 0)
            self.pass_var = make_label_entry(form, "Name", 1)
        else:
            self.id_var   = make_label_entry(form, "Username", 0)
            self.pass_var = make_label_entry(form, "Password", 1, secret=True)

        btn_frame = tk.Frame(self.cred_frame, bg=COLORS["card"])
        btn_frame.pack(pady=16)
        styled_button(btn_frame, "Login", self.do_login, color=color, width=20).pack()

        self.err_label.pack()
        self.bind_all("<Return>", lambda e: self.do_login())

    def show_roles(self):
        """Hides the credential form and brings the role selection buttons back
        so the user can choose a different role if they made a mistake."""
        self.cred_frame.pack_forget()
        self.err_label.pack_forget()
        self.err_label.config(text="")
        self.role_frame.pack(pady=10)
        self.unbind_all("<Return>")

    def do_login(self):
        ident = self.id_var.get().strip()
        pw    = self.pass_var.get().strip()
        if not ident:
            self.err_label.config(text="Please fill in all fields.")
            return
        result = self.app.backend.Login(self.selected_role, ident, pw)
        if result:
            self.app.current_user = result
            # Ensure credentials and permissions are explicitly set
            self.app.backend.currentUserCredentials["Role"] = self.selected_role
            self.app.backend.currentUserCredentials["Identification"] = ident
            self.app.show_main_menu()
        else:
            self.err_label.config(text="Invalid credentials. Please try again.")


# The MainMenuPage is the central hub of the application. It builds a sidebar
# with navigation buttons that are shown or hidden based on the logged-in user's role.
class MainMenuPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.pack(fill="both", expand=True)
        self.app = app

        # Read directly from the logged-in user object for reliability
        perms = app.current_user.permissions
        ident = app.backend.currentUserCredentials.get("Identification", "")
        role  = app.backend.currentUserCredentials.get("Role", "")
        # Fallback: if role is empty, derive from user object
        if not role:
            role = getattr(app.current_user, "role", "")
            app.backend.currentUserCredentials["Role"] = role

        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # App title block
        tk.Label(sidebar, text="🏥", font=("Helvetica", 22),
                 bg=COLORS["sidebar"], fg=COLORS["text_light"]).pack(pady=(24, 0))
        tk.Label(sidebar, text="Homebrew HIS", font=("Helvetica", 14, "bold"),
                 bg=COLORS["sidebar"], fg=COLORS["text_light"]).pack()
        tk.Label(sidebar, text="CPI 110 Final", font=("Helvetica", 8),
                 bg=COLORS["sidebar"], fg="#7a9bbf").pack(pady=(0, 12))

        # User badge
        badge = tk.Frame(sidebar, bg="#142d47")
        badge.pack(fill="x", padx=14, pady=(0, 14))

        # Role-based avatar icon
        avatar_icons = {"Doctor": "🩺", "Nurse": "💉", "Patient": "🧑"}
        avatar = avatar_icons.get(role, "👤")
        tk.Label(badge, text=avatar, font=("Helvetica", 26),
                 bg="#142d47", fg=COLORS["text_light"]).pack(pady=(10, 4))
        tk.Label(badge, text=ident, font=("Helvetica", 11, "bold"),
                 bg="#142d47", fg=COLORS["text_light"]).pack()
        tk.Label(badge, text=role, font=("Helvetica", 9),
                 bg="#142d47", fg="#7a9bbf").pack(pady=(2, 10))

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=14, pady=(0, 10))

        def sidebar_btn(label, cmd):
            btn = tk.Button(sidebar, text=label, command=cmd,
                            bg=COLORS["sidebar_btn"], fg=COLORS["text_light"],
                            font=("Helvetica", 10, "bold"), relief="flat",
                            activebackground=COLORS["sidebar_btn_hover"],
                            activeforeground=COLORS["text_light"], cursor="hand2",
                            anchor="w", padx=18, pady=11,
                            wraplength=220, justify="left")
            btn.pack(fill="x", padx=14, pady=3)
            btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["sidebar_btn_hover"]))
            btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["sidebar_btn"]))

        if perms.get("readsOwnUserDetails"):
            sidebar_btn("👤   My Information", self.show_my_info)

        patient_perms = perms.get("PatientManagement", {})
        if patient_perms.get("enabled"):
            sidebar_btn("🧑   Patient Management", self.show_patient_mgmt)

        staff_perms = perms.get("StaffManagement", {})
        if staff_perms.get("enabled"):
            sidebar_btn("👥   Staff Management", self.show_staff_mgmt)

        clinical_perms = perms.get("ClinicalActions", {})
        if clinical_perms.get("enabled"):
            sidebar_btn("🧪   Clinical Actions", self.show_clinical)

        # Logout at bottom
        tk.Frame(sidebar, bg=COLORS["sidebar"]).pack(fill="y", expand=True)
        logout_btn = tk.Button(sidebar, text="⬅   Logout", command=app.logout,
                               bg=COLORS["danger"], fg=COLORS["text_light"],
                               font=("Helvetica", 10, "bold"), relief="flat",
                               activebackground=_darken(COLORS["danger"]),
                               activeforeground=COLORS["text_light"],
                               cursor="hand2", pady=11)
        logout_btn.pack(fill="x", padx=14, pady=20)
        logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg=_darken(COLORS["danger"])))
        logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=COLORS["danger"]))

        # ── Content area ──
        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self.show_welcome()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_welcome(self):
        # Displays a simple greeting in the content area when the user first logs in.
        self._clear_content()
        ident = self.app.backend.currentUserCredentials.get("Identification", "")
        role  = self.app.backend.currentUserCredentials.get("Role", "")
        tk.Label(self.content, text=f"Welcome, {ident}",
                 font=FONT_TITLE, bg=COLORS["bg"], fg=COLORS["sidebar"]).pack(pady=(80, 10))
        tk.Label(self.content, text=f"Logged in as {role}. Select an option from the sidebar.",
                 font=FONT_BODY, bg=COLORS["bg"], fg="gray").pack()

    def show_my_info(self):
        # Displays the logged-in user's personal information in a centered profile card.
        # The fields shown differ depending on whether the user is a Doctor, Nurse, or Patient.
        # Patient names are partially masked for privacy, and patients also see their bill.
        self._clear_content()
        card = self._card("My Information")
        user = self.app.current_user
        role = self.app.backend.currentUserCredentials.get("Role", "")

        # Build field list depending on role
        if role == "Doctor":
            fields = [
                ("🆔", "ID",        user._Doctor__user_id),
                ("👤", "Name",      f"{user.firstName} {user.lastName}"),
                ("📞", "Phone",     user._Doctor__phone),
                ("🩺", "Specialty", user.specialty),
                ("🏷", "Role",      user.role),
            ]
            accent = "#1a3a5c"
        elif role == "Nurse":
            fields = [
                ("🆔", "ID",         user._Nurse__user_id),
                ("👤", "Name",       f"{user.firstName} {user.lastName}"),
                ("📞", "Phone",      user._Nurse__phone),
                ("🏥", "Department", user.department),
                ("🏷", "Role",       user.role),
            ]
            accent = "#2e7d32"
        else:
            def mask(name):
                return name[0] + "*" * (len(name) - 1) if len(name) > 1 else name
            masked_name = f"{mask(user.firstName)} {mask(user.lastName)}"
            fields = [
                ("🆔", "Patient ID",     user.patient_id),
                ("👤", "Name",           masked_name),
                ("🎂", "Date of Birth",  user.dateOfBirth),
                ("📞", "Phone",          user._Patient__phone),
                ("🏠", "Address",        user._Patient__address),
                ("🤕", "Cause of Visit", getattr(user, "cause_of_visit", "N/A") or "N/A"),
                ("✍️", "Registered By", getattr(user, "created_by", "Unknown") or "Unknown"),
                ("🏷", "Role",           user.role),
            ]
            accent = "#6a1b9a"

        # Centered profile card inside the card frame
        outer = tk.Frame(card, bg=COLORS["card"])
        outer.pack(fill="both", expand=True)

        # Scrollable inner frame
        canvas = tk.Canvas(outer, bg=COLORS["card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS["card"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Centering wrapper
        center_wrap = tk.Frame(scroll_frame, bg=COLORS["card"])
        center_wrap.pack(fill="both", expand=True, pady=20)
        center_wrap.columnconfigure(0, weight=1)

        inner = tk.Frame(center_wrap, bg=COLORS["card"])
        inner.pack(anchor="center")

        # Avatar block
        avatar_frame = tk.Frame(inner, bg=accent, width=80, height=80)
        avatar_frame.pack(pady=(0, 10))
        avatar_frame.pack_propagate(False)
        tk.Label(avatar_frame, text="👤", font=("Helvetica", 32),
                 bg=accent, fg="white").place(relx=0.5, rely=0.5, anchor="center")

        display_name = masked_name if role == "Patient" else f"{user.firstName} {user.lastName}"
        tk.Label(inner, text=display_name,
                 font=("Helvetica", 16, "bold"), bg=COLORS["card"],
                 fg=COLORS["sidebar"]).pack(anchor="center")
        tk.Label(inner, text=f"  {role}  ",
                 font=("Helvetica", 9, "bold"), bg=accent,
                 fg="white", padx=8, pady=3).pack(pady=(2, 16), anchor="center")

        # Info rows
        info_card = tk.Frame(inner, bg=COLORS["card"],
                             highlightbackground=COLORS["border"], highlightthickness=1)
        info_card.pack(pady=4, ipadx=10)

        for i, (icon, label, value) in enumerate(fields):
            row_bg = COLORS["card"] if i % 2 == 0 else "#f7f9fb"
            row = tk.Frame(info_card, bg=row_bg)
            row.pack(fill="x")
            tk.Label(row, text=f"{icon}  {label}", font=("Helvetica", 10, "bold"),
                     bg=row_bg, fg="#555", width=16, anchor="w",
                     padx=16, pady=10).pack(side="left")
            tk.Frame(row, bg=COLORS["border"], width=1).pack(side="left", fill="y", pady=4)
            tk.Label(row, text=value, font=("Helvetica", 10),
                     bg=row_bg, fg=COLORS["text"],
                     padx=16, pady=10, anchor="w").pack(side="left", fill="x", expand=True)

        # ── Bill section (Patient only) ──
        if role == "Patient":
            bill = getattr(user, "bill", [])
            total = sum(item.get("amount", 0) for item in bill)

            tk.Label(inner, text="💳  Your Bill", font=("Helvetica", 13, "bold"),
                     bg=COLORS["card"], fg=COLORS["sidebar"]).pack(anchor="w", pady=(20, 6))

            bill_card = tk.Frame(inner, bg=COLORS["card"],
                                 highlightbackground=COLORS["border"], highlightthickness=1)
            bill_card.pack(fill="x", ipadx=10)

            if not bill:
                tk.Label(bill_card, text="No charges on file.", font=FONT_BODY,
                         bg=COLORS["card"], fg="gray", padx=16, pady=10).pack(anchor="w")
            else:
                for i, item in enumerate(bill):
                    row_bg = COLORS["card"] if i % 2 == 0 else "#f7f9fb"
                    row = tk.Frame(bill_card, bg=row_bg)
                    row.pack(fill="x")
                    tk.Label(row, text=f"  {item.get('description', 'Charge')}",
                             font=("Helvetica", 10), bg=row_bg, fg=COLORS["text"],
                             padx=12, pady=8, anchor="w").pack(side="left", fill="x", expand=True)
                    tk.Label(row, text=f"${item.get('amount', 0):.2f}",
                             font=("Helvetica", 10, "bold"), bg=row_bg, fg=COLORS["text"],
                             padx=12, pady=8).pack(side="right")

                # Total row
                total_row = tk.Frame(bill_card, bg="#1a3a5c")
                total_row.pack(fill="x")
                tk.Label(total_row, text="  Total Due",
                         font=("Helvetica", 11, "bold"), bg="#1a3a5c",
                         fg="white", padx=12, pady=10).pack(side="left")
                tk.Label(total_row, text=f"${total:.2f}",
                         font=("Helvetica", 11, "bold"), bg="#1a3a5c",
                         fg="#90caf9", padx=12, pady=10).pack(side="right")

    def show_patient_mgmt(self):
        # Shows the patient management screen with a live search bar and a full patient table.
        # Doctors and nurses can double-click any row to open a detailed patient profile popup.
        self._clear_content()
        perms = self.app.current_user.permissions.get("PatientManagement", {})

        # Build header buttons based on permissions
        header_btns = []
        if perms.get("createsPatients"):
            header_btns.append(("➕  Create Patient", self.show_create_patient, COLORS["success"]))

        card = self._card("Patient Management", header_btns)

        # Search bar row
        toolbar = tk.Frame(card, bg=COLORS["card"])
        toolbar.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(toolbar, text="🔍", font=("Helvetica", 12), bg=COLORS["card"]).pack(side="left")
        search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=search_var, font=FONT_BODY,
                                relief="solid", bd=1, width=28)
        search_entry.pack(side="left", padx=6)
        tk.Label(toolbar, text="Search by ID or name", font=FONT_SMALL,
                 bg=COLORS["card"], fg="gray").pack(side="left")

        # Table area
        table_frame = tk.Frame(card, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        all_patients = list(self.app.backend.patients.values())
        all_rows = [(p.patient_id, p.firstName, p.lastName, p.dateOfBirth,
                     getattr(p, "cause_of_visit", "") or "N/A")
                    for p in all_patients]

        role = self.app.backend.currentUserCredentials.get("Role", "")
        can_view_details = role in ("Doctor", "Nurse")

        def discharge_patient(patient_id, popup):
            # Handles the full discharge workflow. It generates a formatted text report,
            # saves it to the Discharged Patients folder, removes the patient from the
            # live system, and refreshes the patient table automatically.
            import os, datetime
            p = self.app.backend.patients.get(patient_id)
            if not p:
                return

            # Confirmation dialog
            confirm = tk.Toplevel(self.app)
            confirm.title("Confirm Discharge")
            confirm.geometry("360x160")
            confirm.configure(bg=COLORS["bg"])
            confirm.resizable(False, False)
            confirm.grab_set()
            confirm.lift()

            tk.Label(confirm, text="⚠️  Discharge Patient",
                     font=("Helvetica", 13, "bold"), bg=COLORS["bg"],
                     fg=COLORS["danger"]).pack(pady=(20, 6))
            tk.Label(confirm, text=f"Would you like to discharge {p.firstName} {p.lastName}?",
                     font=FONT_BODY, bg=COLORS["bg"], fg=COLORS["text"],
                     wraplength=320).pack()

            btn_frame = tk.Frame(confirm, bg=COLORS["bg"])
            btn_frame.pack(pady=16)

            def do_discharge():
                # Gather all data
                now = datetime.datetime.now()
                date_str = now.strftime("%B %d, %Y at %I:%M %p")
                discharged_by = self.app.backend.currentUserCredentials.get("Identification", "Unknown")
                discharged_by_role = self.app.backend.currentUserCredentials.get("Role", "Staff")
                bill = getattr(p, "bill", [])
                total = sum(item.get("amount", 0) for item in bill)
                orders = self.app.backend.GetLabOrdersForPatient(p.patient_id)

                # Build the discharge report text
                sep  = "=" * 54
                thin = "-" * 54
                lines = [
                    sep,
                    "        HOMEBREW HIS — PATIENT DISCHARGE REPORT",
                    "                     CPI 110 Final",
                    sep,
                    "",
                    f"  Date of Discharge : {date_str}",
                    f"  Discharged By     : {discharged_by} ({discharged_by_role})",
                    "",
                    thin,
                    "  PATIENT INFORMATION",
                    thin,
                    f"  Patient ID        : {p.patient_id}",
                    f"  Full Name         : {p.firstName} {p.lastName}",
                    f"  Date of Birth     : {p.dateOfBirth}",
                    f"  Phone             : {p._Patient__phone}",
                    f"  Address           : {p._Patient__address}",
                    f"  Cause of Visit    : {getattr(p, 'cause_of_visit', 'N/A') or 'N/A'}",
                    f"  Registered By     : {getattr(p, 'created_by', 'Unknown') or 'Unknown'}",
                    "",
                    thin,
                    "  BILLING SUMMARY",
                    thin,
                ]
                if not bill:
                    lines.append("  No charges on file.")
                else:
                    for item in bill:
                        desc = item.get("description", "Charge")
                        amt  = item.get("amount", 0)
                        lines.append(f"  {desc:<36} ${amt:>8.2f}")
                    lines.append(thin)
                    lines.append(f"  {'TOTAL DUE':<36} ${total:>8.2f}")

                lines += [
                    "",
                    thin,
                    "  CLINICAL ORDERS",
                    thin,
                ]
                if not orders:
                    lines.append("  No lab orders on file.")
                else:
                    for o in orders:
                        price_str = f"  ${o.price:.2f}" if hasattr(o, "price") and o.price > 0 else ""
                        lines.append(f"  [{o.status}] {o.test_name} — Dr. {o.ordering_doctor_id}{price_str}")
                        if o.notes:
                            lines.append(f"         Notes: {o.notes}")

                lines += [
                    "",
                    sep,
                    "         This record was generated automatically by",
                    "         Homebrew HIS. Retain for medical records.",
                    sep,
                    "",
                ]
                report = "\n".join(lines)

                # We create the discharge folder automatically if it does not already exist
                # so the user never has to set anything up manually.
                folder = "Discharged Patients"
                os.makedirs(folder, exist_ok=True)
                safe_name = f"{p.firstName.lower()}{p.lastName.lower()}_discharged_{now.strftime('%Y%m%d')}"
                filepath = os.path.join(folder, f"{safe_name}.txt")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report)

                # Remove the patient from the active records and delete all of their
                # associated lab orders so nothing is left behind in the system.
                del self.app.backend.patients[p.patient_id]
                self.app.backend.lab_orders = [
                    o for o in self.app.backend.lab_orders if o.patient_id != p.patient_id
                ]
                self.app.backend.save_all()

                confirm.destroy()
                popup.destroy()
                self.show_patient_mgmt()
                messagebox.showinfo("Patient Discharged",
                    f"{p.firstName} {p.lastName} has been discharged.\n\nReport saved to:\n{filepath}")

            styled_button(btn_frame, "Yes, Discharge", do_discharge,
                          color=COLORS["danger"], width=16).pack(side="left", padx=8)
            styled_button(btn_frame, "Cancel", confirm.destroy,
                          color=COLORS["sidebar"], width=10).pack(side="left", padx=8)

        def show_patient_popup(patient_id):
            p = self.app.backend.patients.get(patient_id)
            if not p:
                return

            popup = tk.Toplevel(self.app)
            popup.title(f"Patient — {p.firstName} {p.lastName}")
            popup.geometry("460x580")
            popup.configure(bg=COLORS["bg"])
            popup.resizable(True, True)
            popup.grab_set()

            # ── Fixed header ──
            header = tk.Frame(popup, bg="#6a1b9a")
            header.pack(fill="x")
            tk.Label(header, text="🧑", font=("Helvetica", 28),
                     bg="#6a1b9a", fg="white").pack(pady=(14, 2))
            tk.Label(header, text=f"{p.firstName} {p.lastName}",
                     font=("Helvetica", 14, "bold"), bg="#6a1b9a", fg="white").pack()
            tk.Label(header, text="Patient", font=("Helvetica", 9),
                     bg="#6a1b9a", fg="#d1a8f0").pack(pady=(0, 10))

            # ── Scrollable body ──
            body_frame = tk.Frame(popup, bg=COLORS["bg"])
            body_frame.pack(fill="both", expand=True)

            canvas = tk.Canvas(body_frame, bg=COLORS["bg"], highlightthickness=0)
            vscroll = ttk.Scrollbar(body_frame, orient="vertical", command=canvas.yview)
            scroll_content = tk.Frame(canvas, bg=COLORS["bg"])
            scroll_content.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scroll_content, anchor="nw")
            canvas.configure(yscrollcommand=vscroll.set)
            canvas.pack(side="left", fill="both", expand=True)
            vscroll.pack(side="right", fill="y")

            # We bind the mouse wheel to the canvas so the user can scroll through
            # long patient records without needing to click the scrollbar.
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            popup.protocol("WM_DELETE_WINDOW", lambda: [canvas.unbind_all("<MouseWheel>"), popup.destroy()])

            # ── Info rows ──
            fields = [
                ("🆔", "Patient ID",     p.patient_id),
                ("🎂", "Date of Birth",  p.dateOfBirth),
                ("📞", "Phone",          p._Patient__phone),
                ("🏠", "Address",        p._Patient__address),
                ("🤕", "Cause of Visit", getattr(p, "cause_of_visit", "") or "N/A"),
                ("✍️", "Registered By",  getattr(p, "created_by", "Unknown") or "Unknown"),
            ]
            tk.Label(scroll_content, text="📋  Patient Info",
                     font=("Helvetica", 11, "bold"), bg=COLORS["bg"],
                     fg=COLORS["sidebar"]).pack(anchor="w", padx=20, pady=(14, 4))
            info_card = tk.Frame(scroll_content, bg=COLORS["card"],
                                 highlightbackground=COLORS["border"], highlightthickness=1)
            info_card.pack(fill="x", padx=20, pady=(0, 10))
            for i, (icon, label, value) in enumerate(fields):
                row_bg = COLORS["card"] if i % 2 == 0 else "#f7f9fb"
                row = tk.Frame(info_card, bg=row_bg)
                row.pack(fill="x")
                tk.Label(row, text=f"{icon}  {label}", font=("Helvetica", 10, "bold"),
                         bg=row_bg, fg="#555", width=16, anchor="w",
                         padx=12, pady=9).pack(side="left")
                tk.Frame(row, bg=COLORS["border"], width=1).pack(side="left", fill="y", pady=4)
                tk.Label(row, text=value, font=("Helvetica", 10),
                         bg=row_bg, fg=COLORS["text"],
                         padx=12, pady=9, anchor="w").pack(side="left", fill="x", expand=True)

            # ── Bill section ──
            bill = getattr(p, "bill", [])
            total = sum(item.get("amount", 0) for item in bill)
            tk.Label(scroll_content, text="💳  Bill",
                     font=("Helvetica", 11, "bold"), bg=COLORS["bg"],
                     fg=COLORS["sidebar"]).pack(anchor="w", padx=20, pady=(6, 4))
            bill_frame = tk.Frame(scroll_content, bg=COLORS["card"],
                                  highlightbackground=COLORS["border"], highlightthickness=1)
            bill_frame.pack(fill="x", padx=20, pady=(0, 10))
            if not bill:
                tk.Label(bill_frame, text="No charges on file.", font=FONT_SMALL,
                         bg=COLORS["card"], fg="gray", padx=12, pady=6).pack(anchor="w")
            else:
                for i, item in enumerate(bill):
                    row_bg = COLORS["card"] if i % 2 == 0 else "#f7f9fb"
                    brow = tk.Frame(bill_frame, bg=row_bg)
                    brow.pack(fill="x")
                    tk.Label(brow, text=f"  {item.get('description', 'Charge')}",
                             font=FONT_SMALL, bg=row_bg, fg=COLORS["text"],
                             padx=10, pady=7, anchor="w").pack(side="left", fill="x", expand=True)
                    tk.Label(brow, text=f"${item.get('amount', 0):.2f}",
                             font=("Helvetica", 9, "bold"), bg=row_bg,
                             fg=COLORS["text"], padx=10, pady=7).pack(side="right")
                total_row = tk.Frame(bill_frame, bg="#1a3a5c")
                total_row.pack(fill="x")
                tk.Label(total_row, text="  Total Due",
                         font=("Helvetica", 10, "bold"), bg="#1a3a5c",
                         fg="white", padx=10, pady=8).pack(side="left")
                tk.Label(total_row, text=f"${total:.2f}",
                         font=("Helvetica", 10, "bold"), bg="#1a3a5c",
                         fg="#90caf9", padx=10, pady=8).pack(side="right")

            # ── Lab orders ──
            orders = self.app.backend.GetLabOrdersForPatient(p.patient_id)
            tk.Label(scroll_content, text="🧪  Lab Orders",
                     font=("Helvetica", 11, "bold"), bg=COLORS["bg"],
                     fg=COLORS["sidebar"]).pack(anchor="w", padx=20, pady=(6, 4))
            if not orders:
                tk.Label(scroll_content, text="No lab orders on file.", font=FONT_SMALL,
                         bg=COLORS["bg"], fg="gray", padx=20).pack(anchor="w", pady=(0, 10))
            else:
                for i, o in enumerate(orders):
                    row_bg = COLORS["card"] if i % 2 == 0 else "#f7f9fb"
                    lf = tk.Frame(scroll_content, bg=row_bg,
                                  highlightbackground=COLORS["border"], highlightthickness=1)
                    lf.pack(fill="x", padx=20, pady=2)
                    price_str = f"   ${o.price:.2f}" if hasattr(o, "price") and o.price > 0 else ""
                    tk.Label(lf, text=f"  [{o.status}]  {o.test_name}  —  Dr. {o.ordering_doctor_id}{price_str}",
                             font=FONT_SMALL, bg=row_bg, fg=COLORS["text"],
                             padx=10, pady=7, anchor="w").pack(side="left", fill="x", expand=True)
                    if o.notes:
                        tk.Label(lf, text=f"  Notes: {o.notes}",
                                 font=FONT_SMALL, bg=row_bg, fg="gray",
                                 padx=10, pady=2, anchor="w").pack(fill="x")

            # ── Action buttons ──
            btn_row = tk.Frame(scroll_content, bg=COLORS["bg"])
            btn_row.pack(fill="x", padx=20, pady=16)
            styled_button(btn_row, "🏥  Discharge Patient",
                          lambda: discharge_patient(patient_id, popup),
                          color=COLORS["danger"], width=20).pack(side="left", padx=(0, 8))
            styled_button(btn_row, "Close", popup.destroy,
                          color=COLORS["sidebar"], width=10).pack(side="left")

        def refresh_table(rows):
            for w in table_frame.winfo_children():
                w.destroy()
            self._show_table(table_frame,
                columns=("ID", "First Name", "Last Name", "DOB", "Cause of Visit"),
                rows=rows,
                on_click=show_patient_popup if can_view_details else None,
                click_col=0)

        def on_search(*args):
            q = search_var.get().strip().lower()
            if not q:
                refresh_table(all_rows)
            else:
                filtered = [r for r in all_rows if q in r[0].lower() or q in r[1].lower() or q in r[2].lower()]
                refresh_table(filtered)

        search_var.trace_add("write", on_search)
        refresh_table(all_rows)

    def show_create_patient(self):
        # Displays a form for creating a new patient record. A $25 activation fee
        # is added to the patient's bill automatically when the record is saved.
        self._clear_content()
        card = self._card("Create New Patient",
                          [("← Back to Patients", self.show_patient_mgmt, COLORS["sidebar"])])
        form = tk.Frame(card, bg=COLORS["card"]); form.pack(padx=20, pady=10)
        form.columnconfigure(1, weight=1)
        pid   = make_label_entry(form, "Patient ID", 0)
        first = make_label_entry(form, "First Name", 1)
        last  = make_label_entry(form, "Last Name", 2)
        dob   = make_label_entry(form, "Date of Birth (YYYY-MM-DD)", 3)
        phone = make_label_entry(form, "Phone Number", 4)
        addr  = make_label_entry(form, "Address", 5)
        cause = make_label_entry(form, "Cause of Visit", 6)
        status = tk.Label(card, text="", font=FONT_SMALL, bg=COLORS["card"])
        status.pack()

        def submit():
            creator = self.app.backend.currentUserCredentials.get("Identification", "Unknown")
            creator_role = self.app.backend.currentUserCredentials.get("Role", "")
            ok, msg = self.app.backend.CreatePatient(
                pid.get().strip(), first.get().strip(), last.get().strip(),
                dob.get().strip(), phone.get().strip(), addr.get().strip(),
                cause.get().strip(), f"{creator} ({creator_role})")
            if ok:
                self.app.backend.save_all()
                self.show_patient_mgmt()
            else:
                status.config(text=msg, fg=COLORS["danger"])

        styled_button(card, "Save Patient", submit, color=COLORS["success"]).pack(pady=10)

    def show_staff_mgmt(self):
        # Shows a table of all current doctors and nurses on staff.
        # Only doctors have the buttons available to add new staff members.
        self._clear_content()
        perms = self.app.current_user.permissions.get("StaffManagement", {})

        header_btns = []
        if perms.get("createsNurses"):
            header_btns.append(("➕  Create Nurse", self.show_create_nurse, "#2e7d32"))
        if perms.get("createsDoctors"):
            header_btns.append(("➕  Create Doctor", self.show_create_doctor, COLORS["accent"]))

        card = self._card("Staff Management", header_btns)

        # All staff rows
        rows = []
        for d in self.app.backend.doctors.values():
            rows.append((d._Doctor__user_id, d.firstName, d.lastName, "Doctor", d.specialty))
        for n in self.app.backend.nurses.values():
            rows.append((n._Nurse__user_id, n.firstName, n.lastName, "Nurse", n.department))

        self._show_table(card,
            columns=("ID", "First Name", "Last Name", "Role", "Specialty/Dept"),
            rows=rows)

    def show_create_doctor(self):
        # Displays a form where a doctor can create a new physician account in the system.
        self._clear_content()
        card = self._card("Create New Doctor",
                          [("← Back to Staff", self.show_staff_mgmt, COLORS["sidebar"])])
        form = tk.Frame(card, bg=COLORS["card"]); form.pack(padx=20, pady=10)
        form.columnconfigure(1, weight=1)
        ident     = make_label_entry(form, "Doctor ID / Username", 0)
        password  = make_label_entry(form, "Password", 1, secret=True)
        first     = make_label_entry(form, "First Name", 2)
        last      = make_label_entry(form, "Last Name", 3)
        phone     = make_label_entry(form, "Phone Number", 4)
        specialty = make_label_entry(form, "Specialty", 5)
        status = tk.Label(card, text="", font=FONT_SMALL, bg=COLORS["card"]); status.pack()

        def submit():
            ok, msg = self.app.backend.CreateDoctor(
                ident.get().strip(), password.get().strip(), first.get().strip(),
                last.get().strip(), phone.get().strip(), specialty.get().strip())
            if ok:
                self.app.backend.save_all()
                self.show_staff_mgmt()
            else:
                status.config(text=msg, fg=COLORS["danger"])

        styled_button(card, "Save Doctor", submit, color=COLORS["success"]).pack(pady=10)

    def show_create_nurse(self):
        # Displays a form where a doctor can create a new nurse account in the system.
        self._clear_content()
        card = self._card("Create New Nurse",
                          [("← Back to Staff", self.show_staff_mgmt, COLORS["sidebar"])])
        form = tk.Frame(card, bg=COLORS["card"]); form.pack(padx=20, pady=10)
        form.columnconfigure(1, weight=1)
        ident      = make_label_entry(form, "Nurse ID / Username", 0)
        password   = make_label_entry(form, "Password", 1, secret=True)
        first      = make_label_entry(form, "First Name", 2)
        last       = make_label_entry(form, "Last Name", 3)
        phone      = make_label_entry(form, "Phone Number", 4)
        department = make_label_entry(form, "Department", 5)
        status = tk.Label(card, text="", font=FONT_SMALL, bg=COLORS["card"]); status.pack()

        def submit():
            ok, msg = self.app.backend.CreateNurse(
                ident.get().strip(), password.get().strip(), first.get().strip(),
                last.get().strip(), phone.get().strip(), department.get().strip())
            if ok:
                self.app.backend.save_all()
                self.show_staff_mgmt()
            else:
                status.config(text=msg, fg=COLORS["danger"])

        styled_button(card, "Save Nurse", submit, color=COLORS["success"]).pack(pady=10)

    def show_clinical(self):
        # Shows all lab orders in a searchable table. Doctors can also place new orders
        # from this screen using the button in the top right corner.
        self._clear_content()
        perms = self.app.current_user.permissions.get("ClinicalActions", {})

        header_btns = []
        if perms.get("ordersLabTests"):
            header_btns.append(("🧪  Order Lab Test", self.show_order_lab, COLORS["accent"]))

        card = self._card("Clinical Actions", header_btns)

        # Search bar for patient lab orders
        toolbar = tk.Frame(card, bg=COLORS["card"])
        toolbar.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(toolbar, text="🔍", font=("Helvetica", 12), bg=COLORS["card"]).pack(side="left")
        pid_var = tk.StringVar()
        tk.Entry(toolbar, textvariable=pid_var, font=FONT_BODY,
                 relief="solid", bd=1, width=24).pack(side="left", padx=6)
        tk.Label(toolbar, text="Search by Patient ID", font=FONT_SMALL,
                 bg=COLORS["card"], fg="gray").pack(side="left")

        table_frame = tk.Frame(card, bg=COLORS["card"])
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        all_orders = self.app.backend.GetAllLabOrders()
        all_rows = [(o.order_id, o.patient_id, o.ordering_doctor_id, o.test_name, o.status)
                    for o in all_orders]

        def refresh_table(rows):
            for w in table_frame.winfo_children():
                w.destroy()
            self._show_table(table_frame,
                columns=("Order ID", "Patient", "Doctor", "Test", "Status"),
                rows=rows)

        def on_search(*args):
            q = pid_var.get().strip().lower()
            if not q:
                refresh_table(all_rows)
            else:
                filtered = [r for r in all_rows if q in r[1].lower()]
                refresh_table(filtered)

        pid_var.trace_add("write", on_search)
        refresh_table(all_rows)

    def show_order_lab(self):
        # Displays a form for placing a new lab order for a selected patient.
        # An optional charge amount can be entered which will be added to that patient's bill.
        self._clear_content()
        card = self._card("Order Lab Test",
                          [("← Back to Clinical", self.show_clinical, COLORS["sidebar"])])

        if not self.app.backend.patients:
            tk.Label(card, text="No patients on record. Please create a patient first.",
                     font=FONT_BODY, bg=COLORS["card"], fg=COLORS["danger"]).pack(padx=20, pady=20)
            return

        form = tk.Frame(card, bg=COLORS["card"]); form.pack(padx=20, pady=10)
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Patient", font=FONT_BODY, bg=COLORS["card"],
                 fg=COLORS["text"], anchor="w").grid(row=0, column=0, sticky="w", pady=6, padx=8)
        patient_ids = list(self.app.backend.patients.keys())
        pid_var = tk.StringVar(value=patient_ids[0] if patient_ids else "")
        ttk.Combobox(form, textvariable=pid_var, values=patient_ids,
                     state="readonly", font=FONT_BODY, width=27).grid(row=0, column=1, sticky="ew", pady=6, padx=8)

        test_var  = make_label_entry(form, "Test Name", 1)
        notes_var = make_label_entry(form, "Notes / Indication", 2)
        price_var = make_label_entry(form, "Charge Amount ($)", 3)
        status = tk.Label(card, text="", font=FONT_SMALL, bg=COLORS["card"]); status.pack()

        def submit():
            doctor_id = self.app.backend.currentUserCredentials["Identification"]
            try:
                price = float(price_var.get().strip() or "0")
            except ValueError:
                status.config(text="Invalid price. Please enter a number.", fg=COLORS["danger"])
                return
            ok, msg = self.app.backend.CreateLabOrder(
                pid_var.get().strip(), doctor_id,
                test_var.get().strip(), notes_var.get().strip(), price)
            if ok:
                self.app.backend.save_all()
                self.show_clinical()
            else:
                status.config(text=msg, fg=COLORS["danger"])

        styled_button(card, "Place Order", submit, color=COLORS["success"]).pack(pady=10)

    # ── Helpers ───────────────────────────────────────

    def _card(self, title, header_widgets=None):
        """Builds a titled section header and a white card beneath it in the content area.
        Any buttons passed through header_widgets will appear in the top right of the header."""
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill="x", padx=20, pady=(20, 5))
        tk.Label(header, text=title, font=FONT_TITLE,
                 bg=COLORS["bg"], fg=COLORS["sidebar"]).pack(side="left")
        if header_widgets:
            for (label, cmd, color) in reversed(header_widgets):
                btn = tk.Button(header, text=label, command=cmd,
                                bg=color, fg=COLORS["text_light"],
                                font=("Helvetica", 9, "bold"), relief="flat",
                                activebackground=_darken(color),
                                activeforeground=COLORS["text_light"],
                                cursor="hand2", padx=12, pady=6)
                btn.pack(side="right", padx=4)
                btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=_darken(c)))
                btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        card = tk.Frame(self.content, bg=COLORS["card"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return card

    def _show_table(self, parent, columns, rows, on_click=None, click_col=0):
        """Renders a styled data table using ttk.Treeview. If on_click is provided,
        double-clicking a row will call that function with the value in click_col."""
        frame = tk.Frame(parent, bg=COLORS["card"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                         background=COLORS["card"], foreground=COLORS["text"],
                         rowheight=30, fieldbackground=COLORS["card"], font=FONT_BODY)
        style.configure("Custom.Treeview.Heading",
                         background=COLORS["sidebar"], foreground=COLORS["text_light"],
                         font=FONT_HEADER)
        style.map("Custom.Treeview", background=[("selected", COLORS["accent"])])

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                             style="Custom.Treeview")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor="w")

        for row in rows:
            tree.insert("", "end", values=row)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if on_click:
            hint = tk.Label(parent, text="Double-click a row to view full details",
                            font=FONT_SMALL, bg=COLORS["card"], fg="gray")
            hint.pack(pady=(0, 4))
            def on_double_click(event):
                item = tree.focus()
                if item:
                    val = tree.item(item, "values")
                    if val:
                        on_click(val[click_col])
            tree.bind("<Double-1>", on_double_click)

        if not rows:
            tk.Label(parent, text="No records found.", font=FONT_BODY,
                     bg=COLORS["card"], fg="gray").pack(pady=10)


# This block runs only when the script is executed directly, not when it is imported.
# It creates the main application window and starts the Tkinter event loop.
if __name__ == "__main__":
    app = App()
    app.mainloop()
