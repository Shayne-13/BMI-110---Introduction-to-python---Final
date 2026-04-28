# patient module

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
        # basic patient info
        self.patient_id = strPatientID
        self.firstName = strFirstName
        self.lastName = strLastName
        self.dateOfBirth = strDateOfBirth
        self.__phone = strPhoneNumber
        self.__address = strAddress
        self.role = "Patient"
# display patient information 
    def DisplayInfo(self):
        print(
            f"\n--- Patient Info ---"
            f"\nID: {self.patient_id}"
            f"\nName: {self.firstName} {self.lastName}"
            f"\nDOB: {self.dateOfBirth}"
            f"\nPhone: {self.__phone}"
            f"\nAddress: {self.__address}\n"
        )

    def UpdateContact(self, newPhone, newAddress):
        # update phone and address
        self.__phone = newPhone
        self.__address = newAddress
        print("Patient info updated")
