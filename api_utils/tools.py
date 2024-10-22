import sys
from concurrent.futures import ThreadPoolExecutor
import json
import asyncio
import redis
from secrets import token_hex
import time
import os



ISO_file = os.path.join(os.path.dirname(__file__), '..', 'api_utils', 'ISO 3166-2.json')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def connect_to_redis():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)


def create_token(size: int = 8) -> str:
    return token_hex(size)


def save_user_token(user_id, expire: bool = True):
    r = connect_to_redis()
    token = create_token()
    key = f"{user_id}_{token}"
    r.set(key, user_id)
    if expire:
        r.expire(key, 600)
    return token


def delete_user_tokens(token: str) -> bool:
    # Connect to Redis
    redis_client = connect_to_redis()

    # Search for keys matching the pattern
    keys_to_delete = list(redis_client.scan_iter(match=f"*_{token}"))

    # Check if any keys were found
    if not keys_to_delete:
        # No keys found, return False
        redis_client.close()
        return False

    # Delete keys one by one
    for key in keys_to_delete:
        redis_client.delete(key)

    # Close Redis connection (optional in this context since it's synchronous)
    redis_client.close()
    return True


def find_user_id_by_token(token):
    r = connect_to_redis()
    keys = r.keys(f"*_{token}")
    if keys:
        user_id_key = keys[0]
        user_id = r.get(user_id_key)
        return user_id
    else:
        return None


def count_records_by_user_id(user_id):
    r = connect_to_redis()
    keys = r.keys(f"{user_id}_*")
    count = len(keys)
    return count


def open_file(add: str):
    file = open(add, errors='ignore')
    body = json.load(file)

    return body


async def find_country_code(country: str, is_country: bool = True, city: str = None):
    country_dict = {
        "Afghanistan": "AF", "Albania": "AL", "Algeria": "DZ", "American Samoa": "AS", "Andorra": "AD",
        "Angola": "AO", "Anguilla": "AI", "Antigua and Barbuda": "AG", "Argentina": "AR", "Armenia": "AM",
        "Aruba": "AW", "Australia": "AU", "Austria": "AT", "Azerbaijan": "AZ", "Bahamas": "BS", "Bahrain": "BH",
        "Bangladesh": "BD", "Barbados": "BB", "Belarus": "BY", "Belgium": "BE", "Belize": "BZ", "Benin": "BJ",
        "Bermuda": "BM", "Bhutan": "BT", "Bolivia": "BO", "Bosnia and Herzegovina": "BA", "Botswana": "BW",
        "Brazil": "BR", "British Virgin Islands": "VG", "Brunei Darussalam": "BN", "Bulgaria": "BG",
        "Burkina Faso": "BF", "Burundi": "BI", "Cambodia": "KH", "Cameroon": "CM", "Canada": "CA",
        "Cape Verde": "CV", "Central African Republic": "CF", "Chad": "TD", "Chile": "CL", "China": "CN",
        "Hong Kong": "HK", "Macao": "MO", "Colombia": "CO", "Comoros": "KM", "Congo": "CG", "Costa Rica": "CR",
        "Côte d'Ivoire": "CI", "Croatia": "HR", "Cuba": "CU", "Cyprus": "CY", "Czech Republic": "CZ",
        "Denmark": "DK", "Djibouti": "DJ", "Dominica": "DM", "Dominican Republic": "DO", "Ecuador": "EC",
        "Egypt": "EG", "El Salvador": "SV", "Equatorial Guinea": "GQ", "Eritrea": "ER", "Estonia": "EE",
        "Ethiopia": "ET", "European Union": "EU", "Faroe Islands": "FO", "Fiji": "FJ", "Finland": "FI",
        "France": "FR", "French Guiana": "GF", "French Polynesia": "PF", "Gabon": "GA", "Gambia": "GM",
        "Georgia": "GE", "Germany": "DE", "Ghana": "GH", "Greece": "GR", "Greenland": "GL", "Grenada": "GD",
        "Guadeloupe": "GP", "Guam": "GU", "Guatemala": "GT", "Guinea-Bissau": "GW", "Haiti": "HT",
        "Honduras": "HN", "Hungry": "HU", "Iceland": "IS", "India": "IN", "Indonesia": "ID",
        "Iran (Islamic Republic of)": "IR", "Iraq": "IQ", "Ireland": "IE", "Israel": "IL", "Italy": "IT",
        "Japan": "JP", "Jordan": "JO", "Kazakhstan": "KZ", "Kenya": "KE", "Kiribati": "KI", "Korea": "KR",
        "Kuwait": "KW", "Kyrgyzstan": "KG", "Lao PDR": "LA", "Latvia": "LV", "Lebanon": "LB", "Lesotho": "LS",
        "Liberia": "LR", "Libya": "LY", "Liechtenstein": "LI", "Lithuania": "LT", "Luxembourg": "LU",
        "Madagascar": "MG", "Malawi": "MW", "Malaysia": "MY", "Maldives": "MV", "Mali": "ML", "Malta": "MT",
        "Marshall Islands": "MH", "Martinique": "MQ", "Mauritania": "MR", "Mauritius": "MU", "Mexico": "MX",
        "Micronesia, Federated States of": "FM", "Moldova": "MD", "Monaco": "MC", "Mongolia": "MN",
        "Montenegro": "ME", "Montserrat": "MS", "Morocco": "MA", "Mozambique": "MZ", "Myanmar": "MM",
        "Namibia": "NA", "Nauru": "NR", "Nepal": "NP", "Netherlands": "NL", "Netherlands Antilles": "AN",
        "New Caledonia": "NC", "New Zealand": "NZ", "Nicaragua": "NI", "Niger": "NE", "Nigeria": "NG",
        "Northern Mariana Islands": "MP", "Norway": "NO", "Oman": "OM", "Pakistan": "PK", "Palau": "PW",
        "Palestinian Territory": "PS", "Panama": "PA", "Papua New Guinea": "PG", "Paraguay": "PY", "Peru": "PE",
        "Philippines": "PH", "Pitcairn": "PN", "Poland": "PL", "Portugal": "PT", "Puerto Rico": "PR",
        "Qatar": "QA", "Réunion": "RE", "Romania": "RO", "Russian Federation": "RU", "Rwanda": "RW",
        "Saint Kitts and Nevis": "KN", "Saint Lucia": "LC", "Saint Vincent and Grenadines": "VC", "Samoa": "WS",
        "San Marino": "SM", "Sao Tome and Principe": "ST", "Saudi Arabia": "SA", "Senegal": "SN", "Serbia": "RS",
        "Seychelles": "SC", "Sierra Leone": "SL", "Singapore": "SG", "Slovakia": "SK", "Slovenia": "SI",
        "Solomon Islands": "SB", "Somalia": "SO", "South Africa": "ZA", "Spain": "ES", "Sri Lanka": "LK",
        "Sudan": "SD", "Suriname": "SR", "Swaziland": "SZ", "Sweden": "SE", "Switzerland": "CH",
        "Syrian Arab Republic": "SY", "Taiwan (Province of China)": "TW", "Tajikistan": "TJ", "Tanzania": "TZ",
        "Thailand": "TH", "Timor-Leste": "TL", "Togo": "TG", "Tonga": "TO", "Trinidad and Tobago": "TT",
        "Tunisia": "TN", "Turkey": "TR", "Turkmenistan": "TM", "Tuvalu": "TV", "Uganda": "UG", "Ukraine": "UA",
        "United Arab Emirates": "AE", "United Kingdom": "GB", "United States of America": "US", "Uruguay": "UY",
        "Uzbekistan": "UZ", "Vanuatu": "VU", "Venezuela": "VE", "Viet Nam": "VN", "Virgin Islands, US": "VI",
        "Yemen": "YE", "Zambia": "ZM", "Zimbabwe": "ZW"
    }
    if is_country is True:
        return country_dict.get(country, "")
    loop = asyncio.get_running_loop()
    body = await loop.run_in_executor(ThreadPoolExecutor(), open_file, ISO_file)

    country_code = body[country]
    for i in country_code:
        country_name = country_code[i]['name']
        if country_name == city:
            return country_code[i]['parentCode'] , country_code[i]['type']
    return None
