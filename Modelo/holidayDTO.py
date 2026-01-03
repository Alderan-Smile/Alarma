class holidayDTO:
    date: str
    localName: str
    name: str
    countryCode: str
    year: int

    def __init__(self, date: str, localName: str, name: str, countryCode: str, year: int):
        self.date = date
        self.localName = localName
        self.name = name
        self.countryCode = countryCode
        self.year = year

    def to_dict(self):
        return {
            "date": self.date,
            "localName": self.localName,
            "name": self.name,
            "countryCode": self.countryCode,
            "year": self.year
        }