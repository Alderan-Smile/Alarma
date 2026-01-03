class countryDTO:
    countryCode: str
    name: str

    def __init__(self, countryCode: str, name: str):
        self.countryCode = countryCode
        self.name = name
    
    def to_dict(self):
        return {
            "countryCode": self.countryCode,
            "name": self.name
        }