# Troy Wilson


class Doctor:
    def __init__(
        self, strIdentification, strPassword, strFirstName, strLastName, strPhoneNumber
    ):
        self.__user_id = strIdentification
        self.__password = strPassword

        self.firstName = strFirstName
        self.lastName = strLastName
        self.__phone = strPhoneNumber

        self.role = "Doctor"

    def GetPermissions(self):
        doctorPermissions = {
            "Staff Management": {"createsDoctors": True, "createsNurses": True},
            "Patient Management": {
                "createsPatients": True,
                "readsPatientDetails": True,
                "writesPatientDetails": True,
            },
            "Clinical Actions": {"ordersLabTests": True},
        }

        return doctorPermissions

    def DisplayInfo(self):

        full_name = f"{self.firstName} {self.lastName}"

        print(
            f"ID: {self.__user_id}\nName: {full_name}\nPhone: {self.__phone}\nRole: {self.role}"
        )

    def GetID(self):
        return self.__user_id

    def UpdateInformation(self, strIdentification, needsPassword, strPassword):

        if needsPassword and not strPassword == self.__password:
            return (False, "Password of this doctor is required to update information.")

        self.__user_id = strIdentification
        self.__password = strPassword

        return (True, "Updated doctor informaton.")


Clinic = {
    "Doctors": [],  # FORMAT: [ {doctorIdNumber, Doctor }    ]
    "Nurses": [],
    "Patients": [],
}


def CreateDoctor(
    strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber
):
    new_doctor = Doctor(
        strUserIdentification, strPassword, strFirstName, strLastName, strPhoneNumber
    )
    Clinic["Doctors"].append({strUserIdentification: new_doctor})

    print(f"'{strUserIdentification}' succesfully added to doctor list.")


CreateDoctor("chief", "123", "Andrew", "Jordan", "480123123")
