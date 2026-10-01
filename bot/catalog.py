"""Static catalogue choices: base colours and destination countries."""

# key -> display name. Keys are used in callback data (must stay short and stable).
BASE_COLORS: dict[str, str] = {
    "ral7016": "Anthracite RAL7016",
    "rr32": "Dark Brown RR32",
}

COUNTRIES: dict[str, str] = {
    "lv": "Latvia",
    "ee": "Estonia",
    "lt": "Lithuania",
}

OTHER_COUNTRY = "Other Country"

# key -> English name for the admin card. Keys are used in callback data.
PAYMENT_METHODS: dict[str, str] = {
    "cash": "Cash",
    "transfer": "Bank transfer",
}
