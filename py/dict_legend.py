def citizen_dict(key_string):
    return {
        "1": "U.S. Citizen",
        "2": "Resident/Legal Alien",
        "3": "Illegal Alien",
        "4": "Not a U.S. Citizen/Alien Status",
        "5": "Extradited Alien",
        "ꞏ": "Missing or Indeterminable"
    }.get(key_string, "Unknown")

def monrace_dict(key_string):
    return {
        "1": "White/Caucasian",
        "2": "Black/African American",
        "3": "American Indian\\Alaskan Native",
        "4": "Asian or Pacific Islander",
        "5": "Multi-racial",
        "7": "Other",
        "8": "Info on Race Not Available in Docs (This code only available in FY07 and on)",
        "9": "Non-US American Indians",
        "10": "American Indians Citizenship Unknown",
        "ꞏ": "Missing, Indeterminable, or Inapplicable"
        }.get(key_string, "Unknown")

def monsex_dict(key_string):
    return {
    "0": "Male",
    "1": "Female",
    "2": "Other (Added in FY2024)",
    "ꞏ": "Missing, Indeterminable, or Inapplicable"
    }.get(key_string, "Unknown")

def neweduc_dict(key_string):
    return {
        "1": "No HS Diploma/GED",
        "2": "HS Diploma/GED",
        "3": "Some College",
        "4": "Bachelor's Degree",
        "5": "Graduate Degree",
        "ꞏ": "Missing, Indeterminable, or Inapplicable"
    }.get(key_string, "Unknown")

def hisporig_dict(key_string):
    return {
        "0": "Information on Hispanic Origin Not Available",
        "1": "Non-Hispanic",
        "2": "Hispanic",
        "ꞏ": "Missing, Indeterminable, or Inapplicable"
    }.get(key_string, "Unknown")

def rangept_dict(key_string):
    return {
        "1": "Guideline Minimum",
        "2": "Lower Half of Range",
        "3": "Midpoint of Range",
        "4": "Upper Half of Range",
        "5": "Guideline Maximum",
        "6": "Guideline Min/Max Are Equal",
        "ꞏ": "Missing/Sentenced Outside the Guideline Range/Logical Calculation Issues"
    }.get(key_string, "Unknown")

def offguide_dict(key_string):
    return {
        "1": "Administration of Justice",
        "2": "Antitrust",
        "3": "Arson",
        "4": "Assault",
        "5": "Bribery/Corruption",
        "6": "Burglary/Trespass",
        "7": "Child Pornography",
        "8": "Commercialized Vice",
        "9": "Drug Possession",
        "10": "Drug Trafficking",
        "11": "Environmental",
        "12": "Extortion/Racketeering",
        "13": "Firearms",
        "14": "Food and Drug",
        "15": "Forgery/Counter/Copyright",
        "16": "Fraud/Theft/Embezzlement",
        "17": "Immigration",
        "18": "Individual Rights",
        "19": "Kidnapping",
        "20": "Manslaughter",
        "21": "Money Launder",
        "22": "Murder",
        "23": "National Defense",
        "24": "Obscenity/Other Sex Offenses",
        "25": "Prison Offenses",
        "26": "Robbery",
        "27": "Sex Abuse",
        "28": "Stalking/Harassing",
        "29": "Tax",
        "30": "Other",
        ".": "Missing"
    }.get(key_string, "Unknown")

def district_dict(key_string):
    return {
        "0": "Maine",
        "1": "Massachusetts",
        "2": "New Hampshire",
        "3": "Rhode Island",
        "4": "Puerto Rico",
        "5": "Connecticut",
        "6": "New York North",
        "7": "New York East",
        "8": "New York South",
        "9": "New York West",
        "10": "Vermont",
        "11": "Delaware",
        "12": "New Jersey",
        "13": "Penn. East",
        "14": "Penn. Mid",
        "15": "Penn. West",
        "16": "Maryland",
        "17": "N Carolina East",
        "18": "N Carolina Mid",
        "19": "N Carolina West",
        "20": "South Carolina",
        "22": "Virginia East",
        "23": "Virginia West",
        "24": "W Virginia North",
        "25": "W Virginia South",
        "26": "Alabama North",
        "27": "Alabama Mid",
        "28": "Alabama South",
        "29": "Florida North",
        "30": "Florida Mid",
        "31": "Florida South",
        "32": "Georgia North",
        "33": "Georgia Mid",
        "34": "Georgia South",
        "35": "Louisiana East",
        "36": "Louisiana West",
        "37": "Mississippi North",
        "38": "Mississippi South",
        "39": "Texas North",
        "40": "Texas East",
        "41": "Texas South",
        "42": "Texas West",
        "43": "Kentucky East",
        "44": "Kentucky West",
        "45": "Michigan East",
        "46": "Michigan West",
        "47": "Ohio North",
        "48": "Ohio South",
        "49": "Tennessee East",
        "50": "Tennessee Mid",
        "51": "Tennessee West",
        "52": "Illinois North",
        "53": "Illinois Cent",
        "54": "Illinois South",
        "55": "Indiana North",
        "56": "Indiana South",
        "57": "Wisconsin East",
        "58": "Wisconsin West",
        "60": "Arkansas East",
        "61": "Arkansas West",
        "62": "Iowa North",
        "63": "Iowa South",
        "64": "Minnesota",
        "65": "Missouri East",
        "66": "Missouri West",
        "67": "Nebraska",
        "68": "North Dakota",
        "69": "South Dakota",
        "70": "Arizona",
        "71": "California North",
        "72": "California East",
        "73": "California Central",
        "74": "California South",
        "75": "Hawaii",
        "76": "Idaho",
        "77": "Montana",
        "78": "Nevada",
        "79": "Oregon",
        "80": "Washington East",
        "81": "Washington West",
        "82": "Colorado",
        "83": "Kansas",
        "84": "New Mexico",
        "85": "Oklahoma North",
        "86": "Oklahoma East",
        "87": "Oklahoma West",
        "88": "Utah",
        "89": "Wyoming",
        "90": "Dist of Columbia",
        "91": "Virgin Islands",
        "93": "Guam",
        "94": "N Mariana Islands",
        "95": "Alaska",
        "96": "Louisiana Middle"
    }.get(key_string, "Unknown")