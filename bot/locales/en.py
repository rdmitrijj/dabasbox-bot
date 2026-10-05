"""English texts. Every locale file must define the same keys and the same {placeholders}.

Messages are sent with parse_mode=HTML: keep <b>, <code> tags balanced. Values inserted into
{placeholders} are escaped by the code.
"""

NAME = "🇬🇧 English"

TEXTS: dict[str, str] = {
    # ------------------------------------------------------------------ language
    "language_set": "✅ Language: English",
    # ------------------------------------------------------------------ start / commands
    "welcome": (
        "👋 <b>Welcome to Dabasbox!</b>\n"
        "Here you can order a protective enclosure for your heat pump outdoor unit.\n\n"
        "📏 <b>How to measure your unit</b>\n"
        "Measure the heat pump <b>as installed and connected</b>, in millimetres (mm):\n\n"
        "• <b>Height</b> — from the base of the mounting stand/rack to the top of the heat pump.\n"
        "• <b>Width</b> — including all protruding pipe connection points and fittings.\n"
        "• <b>Depth</b> — from the outer front panel of the heat pump to the building facade "
        "(including the wall clearance).\n\n"
        "Provide the <b>net actual dimensions</b> only. We automatically add a 3–4 cm clearance "
        "on each side during manufacturing for hassle-free assembly.\n\n"
        "You can cancel at any time with /cancel."
    ),
    "tap_when_measured": "When you have measured your unit, tap the button below.",
    "btn_proceed": "Proceed to Enter Dimensions ➡️",
    "help": (
        "This bot takes orders for Dabasbox heat pump enclosures.\n\n"
        "/start — start a new order\n"
        "/cancel — cancel the current order\n"
        "/language — change the language\n"
        "/help — show this message"
    ),
    "cancelled": "❌ Order cancelled. Send /start whenever you want to place a new order.",
    "nothing_to_cancel": "There is no active order. Send /start to place one.",
    "stale_button": "This button is no longer active.",
    "use_start": "Send /start to place a new Dabasbox order.",
    "restart_required": "⚠️ Your order session has expired or is incomplete. Please send /start to begin again.",
    # ------------------------------------------------------------------ dimensions
    "ask_dimensions": (
        "⚠️ <b>IMPORTANT:</b> Enter the <b>NET actual dimensions</b> of your heat pump unit in <b>millimetres (mm)</b> "
        "without adding extra margin. A manufacturing tolerance of 3-4 cm will be added by us.\n\n"
        "Enter dimensions in the format: <code>Height x Width x Depth</code> (e.g., <code>800x950x470</code>)."
    ),
    "dims_line": "📐 Net dimensions: <b>{h} (H) x {w} (W) x {d} (D) mm</b>",
    "dims_category": "🏷 Size category: <b>{category}</b>\n💶 Base price: <b>{price} €</b> (excl. 21% VAT)",
    "manual_notice": (
        "ℹ️ Your unit's dimensions are outside our standard size range:\n{problems}\n\n"
        "No problem — your order will be flagged for <b>Individual Manager Calculation</b>. "
        "You can continue; a manager will contact you with the exact price."
    ),
    "out_above": "{axis} {value} mm is above the maximum of {limit} mm",
    "out_below": "{axis} {value} mm is below the minimum of {limit} mm",
    "axis_height": "Height",
    "axis_width": "Width",
    "axis_depth": "Depth",
    # ------------------------------------------------------------------ photos
    "ask_photos": (
        "📸 Please upload 1–3 photos of your installed heat pump from different angles. "
        "This helps us verify pipe connections."
    ),
    "photos_status": "🖼 Photos received: <b>{count}/{max}</b>",
    "photos_more_hint": "You can add more photos, or tap “Done, Continue”.",
    "photos_max_hint": "Maximum reached. Tap “Done, Continue” or “Reset Photos”.",
    "photos_skipped": "⚠️ Only {max} photos can be attached; this one was skipped.",
    "photo_as_document": "Please send the picture as a <b>photo</b> (not as a file), so we can attach it to your order.",
    "photos_cleared": "Photos cleared",
    "photos_need_one": "Please upload at least 1 photo first.",
    "btn_photos_done": "✅ Done, Continue",
    "btn_photos_reset": "🔄 Reset Photos",
    # ------------------------------------------------------------------ colour
    "ask_color": "🎨 Please choose the enclosure colour:",
    "color_ral7016": "Anthracite RAL7016",
    "color_rr32": "Dark Brown RR32",
    "btn_custom_color": "Custom RAL / NCS Color (+{surcharge}€)",
    "ask_custom_color": "Please specify the color code or name according to RAL or NCS catalogs:",
    "color_custom_name": "Custom: {code}",
    "color_chosen": "🎨 Color: <b>{name}</b> {surcharge}",
    "surcharge_included": "(0 €, included)",
    "surcharge_custom": "(+{surcharge} €)",
    # ------------------------------------------------------------------ country / address
    "ask_country": "🌍 Please choose the destination country:",
    "ask_other_country": "Please type the name of the destination country:",
    "country_lv": "Latvia",
    "country_ee": "Estonia",
    "country_lt": "Lithuania",
    "country_other": "Other Country",
    "country_chosen": "🌍 Country: <b>{country}</b>",
    "ask_address": (
        "🏠 Please send the <b>postal code and exact delivery address</b> in one message.\n"
        "Example: <code>LV-1010, Riga, Brivibas iela 1-5</code>"
    ),
    "address_saved": "🏠 Postal code: <b>{zip}</b>\nAddress: <b>{address}</b>",
    # ------------------------------------------------------------------ contact
    "ask_email": "📧 Please enter your <b>e-mail address</b>, e.g. <code>john@example.com</code>",
    "ask_phone": (
        "📞 Please enter your <b>phone number</b> in the international format, e.g. <code>+37120000000</code>\n\n"
        "Or tap <b>📱 Share Contact</b> below."
    ),
    "btn_share_contact": "📱 Share Contact",
    "ask_name": "👤 Please enter your <b>first name</b>, e.g. <code>John</code>",
    # ------------------------------------------------------------------ payment
    "ask_payment": "💳 Please choose the payment method:",
    "payment_cash": "💵 Cash",
    "payment_transfer": "🏦 Bank transfer",
    "payment_chosen": "💳 Payment: <b>{payment}</b>",
    # ------------------------------------------------------------------ summary
    "summary_photos": "🖼 <b>Your photos ({count} pcs)</b> — they will be sent to Dabasbox with your order",
    "summary_title": "🧾 <b>ORDER SUMMARY</b>",
    "sum_dims": "📐 <b>Net dimensions:</b> {h} (H) x {w} (W) x {d} (D) mm",
    "sum_category": "🏷 <b>Category:</b> {category} (Base price: {price} €) [excl. 21% VAT]",
    "sum_category_manual": "🏷 <b>Category:</b> ⚠️ Individual Manager Calculation (dimensions outside the standard size range)",
    "sum_photos": "🖼 <b>Photos:</b> {count} pcs",
    "sum_color": "🎨 <b>Color:</b> {color} {surcharge}",
    "sum_country": "🌍 <b>Country:</b> {country}",
    "sum_address": "🏠 <b>Address:</b> {zip}, {address}",
    "sum_contact": "👤 <b>Name:</b> {name}",
    "sum_email": "📧 <b>E-mail:</b> {email}",
    "sum_phone": "📞 <b>Phone:</b> {phone}",
    "sum_payment": "💳 <b>Payment:</b> {payment}",
    "sum_total": "💰 <b>TOTAL PRICE:</b> {total} € (excl. 21% VAT)",
    "sum_breakdown": "   = {base} € base + {surcharge} € colour surcharge",
    "sum_total_manual": "💰 <b>TOTAL PRICE:</b> TO BE CALCULATED BY A MANAGER",
    "sum_total_manual_custom": (
        "💰 <b>TOTAL PRICE:</b> TO BE CALCULATED BY A MANAGER (+{surcharge} € custom colour surcharge applies)"
    ),
    "sum_shipping": "🚚 The shipping cost will be sent to the specified e-mail address: {email}",
    "sum_check": "Please check the details and confirm your order.",
    "btn_confirm": "✅ Confirm & Submit Order",
    "btn_cancel": "❌ Cancel",
    # ------------------------------------------------------------------ submission
    "already_submitted": "Your order has already been submitted.",
    "submit_failed_alert": "Submission failed, please try again.",
    "submit_failed": (
        "⚠️ Sorry, we couldn't submit your order right now. Please tap “Confirm & Submit Order” again "
        "in a moment. Your data has been kept."
    ),
    "order_submitted_alert": "Order submitted!",
    "order_submitted": (
        "✅ <b>Thank you! Your order #DABASBOX-{order_id} has been submitted.</b>\n\n"
        "Our manager will contact you shortly to confirm the details. "
        "Send /start to place another order."
    ),
    "order_cancelled_alert": "Order cancelled",
    # ------------------------------------------------------------------ hints for wrong input at each step
    "hint_instruction_ack": "Please tap “Proceed to Enter Dimensions” above to continue.",
    "hint_dimensions": "Please send the dimensions as text, e.g. <code>800x950x470</code>",
    "hint_photos": "Please send 1–3 photos of your installed heat pump, then tap “Done, Continue”.",
    "hint_color": "Please choose a colour using the buttons above.",
    "hint_custom_color": "Please type the RAL or NCS colour code, e.g. <code>RAL 9005</code>",
    "hint_country": "Please choose a country with the buttons above or type its name.",
    "hint_address": "Please send the postal code and delivery address as text.",
    "hint_email": "Please send your e-mail address as text, e.g. <code>john@example.com</code>",
    "hint_phone": "Please send your phone number as text, or tap “📱 Share Contact”.",
    "hint_name": "Please send your first name as text.",
    "hint_payment": "Please choose the payment method using the buttons above.",
    "hint_confirmation": "Please confirm or cancel the order using the buttons above.",
    # ------------------------------------------------------------------ validation errors
    "err_dims_format": (
        "I couldn't read these dimensions. Please send three whole numbers in millimetres "
        "in the format Height x Width x Depth, for example: 800x950x470"
    ),
    "err_dims_leading_zero": "Dimensions must not start with a zero. Example: 800x950x470",
    "err_color_short": "The colour code is too short. Example: RAL 9005 or NCS S 1080-Y50R",
    "err_color_long": "Please keep the colour code or name under 60 characters.",
    "err_ral": "This doesn't look like a valid RAL code. RAL Classic codes have 4 digits, e.g. RAL 9005.",
    "err_ncs": "This doesn't look like a valid NCS code. Example: NCS S 1080-Y50R",
    "err_color_name": "Please enter a RAL/NCS code (e.g. RAL 9005, NCS S 1080-Y50R) or a plain colour name.",
    "err_country": "Please enter the country name using letters only, e.g. Finland.",
    "err_address_short": (
        "The address is too short (minimum {min} characters). "
        "Please send postal code, city, street and house number, e.g. LV-1010, Riga, Brivibas iela 1"
    ),
    "err_address_long": "The address is too long (maximum {max} characters).",
    "err_address_no_digits": "The address must include a postal code (digits). Example: LV-1010, Riga, Brivibas iela 1",
    "err_postal_country": "I couldn't find a valid {country} postal code in the address. Please include it, e.g. {example}.",
    "err_postal_missing": "I couldn't find a postal code in the address. Please include it.",
    "err_address_rest": "Please add the city, street and house number after the postal code.",
    "err_phone": "The phone number is not valid. Please use the international format, e.g. +37120000000",
    "err_email": "This doesn't look like a valid e-mail address. Example: john@example.com",
    "err_email_typo": "Did you mean <b>{suggestion}</b>? Please check the part after @ and enter the full address again.",
    "err_email_domain": (
        "The domain <b>{domain}</b> can't receive e-mail. "
        "Please check the part after @ and enter the full address, e.g. name@gmail.com or name@inbox.lv"
    ),
    "err_name_chars": "The first name may contain letters, hyphens and apostrophes only.",
}
