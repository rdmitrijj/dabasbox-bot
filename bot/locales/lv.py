"""Latvian texts. Same keys and {placeholders} as en.py."""

NAME = "🇱🇻 Latviešu"

TEXTS: dict[str, str] = {
    # ------------------------------------------------------------------ language
    "language_set": "✅ Valoda: latviešu",
    # ------------------------------------------------------------------ start / commands
    "welcome": (
        "👋 <b>Laipni lūdzam Dabasbox!</b>\n"
        "Šeit varat pasūtīt aizsargkorpusu sava siltumsūkņa āra blokam.\n\n"
        "📏 <b>Kā izmērīt iekārtu</b>\n"
        "Mēriet siltumsūkni <b>uzstādītu un pieslēgtu</b>, milimetros (mm):\n\n"
        "• <b>Augstums</b> — no montāžas statīva pamatnes līdz siltumsūkņa augšai.\n"
        "• <b>Platums</b> — ieskaitot visus izvirzītos cauruļu pieslēgumus un savienojumus.\n"
        "• <b>Dziļums</b> — no siltumsūkņa ārējā priekšējā paneļa līdz ēkas fasādei "
        "(ieskaitot atstarpi līdz sienai).\n\n"
        "Norādiet tikai <b>faktiskos neto izmērus</b>. Ražošanā mēs automātiski pievienojam 3–4 cm atstarpi "
        "katrā pusē, lai montāža būtu vienkārša.\n\n"
        "Pasūtījumu jebkurā brīdī var atcelt ar /cancel."
    ),
    "tap_when_measured": "Kad iekārta ir izmērīta, nospiediet pogu zemāk.",
    "btn_proceed": "Ievadīt izmērus ➡️",
    "help": (
        "Šis bots pieņem pasūtījumus Dabasbox siltumsūkņu korpusiem.\n\n"
        "/start — sākt jaunu pasūtījumu\n"
        "/cancel — atcelt pašreizējo pasūtījumu\n"
        "/language — mainīt valodu\n"
        "/help — parādīt šo ziņu"
    ),
    "cancelled": "❌ Pasūtījums atcelts. Sūtiet /start, kad vēlaties veikt jaunu pasūtījumu.",
    "nothing_to_cancel": "Aktīva pasūtījuma nav. Sūtiet /start, lai to izveidotu.",
    "stale_button": "Šī poga vairs nav aktīva.",
    "use_start": "Sūtiet /start, lai veiktu jaunu Dabasbox pasūtījumu.",
    "restart_required": "⚠️ Pasūtījuma sesija ir beigusies vai nepilnīga. Lūdzu, sūtiet /start, lai sāktu no jauna.",
    # ------------------------------------------------------------------ dimensions
    "ask_dimensions": (
        "⚠️ <b>SVARĪGI:</b> Ievadiet siltumsūkņa <b>faktiskos NETO izmērus milimetros (mm)</b> "
        "bez papildu rezerves. 3-4 cm ražošanas pielaidi pievienosim mēs.\n\n"
        "Ievadiet izmērus formātā: <code>Augstums x Platums x Dziļums</code> (piem., <code>800x950x470</code>)."
    ),
    "dims_line": "📐 Neto izmēri: <b>{h} (A) x {w} (P) x {d} (Dz) mm</b>",
    "dims_category": "🏷 Izmēru kategorija: <b>{category}</b>\n💶 Bāzes cena: <b>{price} €</b> (bez 21% PVN)",
    "manual_notice": (
        "ℹ️ Jūsu iekārtas izmēri ir ārpus mūsu standarta izmēru diapazona:\n{problems}\n\n"
        "Nekas — pasūtījums tiks atzīmēts <b>individuālam menedžera aprēķinam</b>. "
        "Varat turpināt; menedžeris sazināsies ar jums, lai paziņotu precīzu cenu."
    ),
    "out_above": "{axis} {value} mm pārsniedz maksimālo {limit} mm",
    "out_below": "{axis} {value} mm ir mazāks par minimālo {limit} mm",
    "axis_height": "Augstums",
    "axis_width": "Platums",
    "axis_depth": "Dziļums",
    # ------------------------------------------------------------------ photos
    "ask_photos": (
        "📸 Lūdzu, augšupielādējiet 1–3 fotoattēlus ar uzstādīto siltumsūkni no dažādiem leņķiem. "
        "Tas palīdz mums pārbaudīt cauruļu pieslēgumus."
    ),
    "photos_status": "🖼 Saņemti foto: <b>{count}/{max}</b>",
    "photos_more_hint": "Varat pievienot vēl foto vai nospiest “Gatavs, turpināt”.",
    "photos_max_hint": "Maksimums sasniegts. Nospiediet “Gatavs, turpināt” vai “Dzēst foto”.",
    "photos_skipped": "⚠️ Var pievienot ne vairāk kā {max} foto; šis netika pievienots.",
    "photo_as_document": "Lūdzu, sūtiet attēlu kā <b>foto</b> (nevis kā failu), lai varam to pievienot pasūtījumam.",
    "photos_cleared": "Foto dzēsti",
    "photos_need_one": "Lūdzu, vispirms augšupielādējiet vismaz 1 foto.",
    "btn_photos_done": "✅ Gatavs, turpināt",
    "btn_photos_reset": "🔄 Dzēst foto",
    # ------------------------------------------------------------------ colour
    "ask_color": "🎨 Lūdzu, izvēlieties korpusa krāsu:",
    "color_ral7016": "Antracīts RAL7016",
    "color_rr32": "Tumši brūns RR32",
    "btn_custom_color": "Cita RAL / NCS krāsa (+{surcharge}€)",
    "ask_custom_color": "Lūdzu, norādiet krāsas kodu vai nosaukumu pēc RAL vai NCS kataloga:",
    "color_custom_name": "Individuāla: {code}",
    "color_chosen": "🎨 Krāsa: <b>{name}</b> {surcharge}",
    "surcharge_included": "(0 €, iekļauts)",
    "surcharge_custom": "(+{surcharge} €)",
    # ------------------------------------------------------------------ country / address
    "ask_country": "🌍 Lūdzu, izvēlieties piegādes valsti:",
    "ask_other_country": "Lūdzu, ierakstiet piegādes valsts nosaukumu:",
    "country_lv": "Latvija",
    "country_ee": "Igaunija",
    "country_lt": "Lietuva",
    "country_other": "Cita valsts",
    "country_chosen": "🌍 Valsts: <b>{country}</b>",
    "ask_address": (
        "🏠 Lūdzu, vienā ziņā nosūtiet <b>pasta indeksu un precīzu piegādes adresi</b>.\n"
        "Piemērs: <code>LV-1010, Rīga, Brīvības iela 1-5</code>"
    ),
    "address_saved": "🏠 Pasta indekss: <b>{zip}</b>\nAdrese: <b>{address}</b>",
    # ------------------------------------------------------------------ contact
    "ask_email": "📧 Lūdzu, ievadiet savu <b>e-pasta adresi</b>, piem. <code>janis@example.com</code>",
    "ask_phone": (
        "📞 Lūdzu, ievadiet savu <b>tālruņa numuru</b> starptautiskajā formātā, piem. <code>+37120000000</code>\n\n"
        "Vai nospiediet <b>📱 Dalīties ar kontaktu</b> zemāk."
    ),
    "btn_share_contact": "📱 Dalīties ar kontaktu",
    "ask_name": "👤 Lūdzu, ievadiet savu <b>vārdu</b>, piem. <code>Jānis</code>",
    # ------------------------------------------------------------------ payment
    "ask_payment": "💳 Lūdzu, izvēlieties apmaksas veidu:",
    "payment_cash": "💵 Skaidrā naudā",
    "payment_transfer": "🏦 Ar bankas pārskaitījumu",
    "payment_chosen": "💳 Apmaksa: <b>{payment}</b>",
    # ------------------------------------------------------------------ summary
    "summary_photos": "🖼 <b>Jūsu foto ({count} gab.)</b> — tie tiks nosūtīti Dabasbox kopā ar pasūtījumu",
    "summary_title": "🧾 <b>PASŪTĪJUMA KOPSAVILKUMS</b>",
    "sum_dims": "📐 <b>Neto izmēri:</b> {h} (A) x {w} (P) x {d} (Dz) mm",
    "sum_category": "🏷 <b>Kategorija:</b> {category} (bāzes cena: {price} €) [bez 21% PVN]",
    "sum_category_manual": "🏷 <b>Kategorija:</b> ⚠️ Individuāls menedžera aprēķins (izmēri ārpus standarta diapazona)",
    "sum_photos": "🖼 <b>Foto:</b> {count} gab.",
    "sum_color": "🎨 <b>Krāsa:</b> {color} {surcharge}",
    "sum_country": "🌍 <b>Valsts:</b> {country}",
    "sum_address": "🏠 <b>Adrese:</b> {zip}, {address}",
    "sum_contact": "👤 <b>Vārds:</b> {name}",
    "sum_email": "📧 <b>E-pasts:</b> {email}",
    "sum_phone": "📞 <b>Tālrunis:</b> {phone}",
    "sum_payment": "💳 <b>Apmaksa:</b> {payment}",
    "sum_total": "💰 <b>KOPĀ:</b> {total} € (bez 21% PVN)",
    "sum_breakdown": "   = {base} € bāzes cena + {surcharge} € krāsas piemaksa",
    "sum_total_manual": "💰 <b>KOPĀ:</b> APRĒĶINĀS MENEDŽERIS",
    "sum_total_manual_custom": "💰 <b>KOPĀ:</b> APRĒĶINĀS MENEDŽERIS (+{surcharge} € piemaksa par individuālu krāsu)",
    "sum_check": "Lūdzu, pārbaudiet datus un apstipriniet pasūtījumu.",
    "btn_confirm": "✅ Apstiprināt un nosūtīt",
    "btn_cancel": "❌ Atcelt",
    # ------------------------------------------------------------------ submission
    "already_submitted": "Jūsu pasūtījums jau ir nosūtīts.",
    "submit_failed_alert": "Neizdevās nosūtīt, lūdzu, mēģiniet vēlreiz.",
    "submit_failed": (
        "⚠️ Atvainojiet, pašlaik neizdevās nosūtīt pasūtījumu. Lūdzu, pēc brīža vēlreiz nospiediet "
        "“Apstiprināt un nosūtīt”. Jūsu dati ir saglabāti."
    ),
    "order_submitted_alert": "Pasūtījums nosūtīts!",
    "order_submitted": (
        "✅ <b>Paldies! Jūsu pasūtījums #DABASBOX-{order_id} ir nosūtīts.</b>\n\n"
        "Mūsu menedžeris drīzumā sazināsies ar jums, lai precizētu detaļas. "
        "Sūtiet /start, lai veiktu vēl vienu pasūtījumu."
    ),
    "order_cancelled_alert": "Pasūtījums atcelts",
    # ------------------------------------------------------------------ hints for wrong input at each step
    "hint_instruction_ack": "Lūdzu, nospiediet pogu “Ievadīt izmērus” augstāk, lai turpinātu.",
    "hint_dimensions": "Lūdzu, nosūtiet izmērus kā tekstu, piem. <code>800x950x470</code>",
    "hint_photos": "Lūdzu, nosūtiet 1–3 foto ar uzstādīto siltumsūkni un pēc tam nospiediet “Gatavs, turpināt”.",
    "hint_color": "Lūdzu, izvēlieties krāsu ar pogām augstāk.",
    "hint_custom_color": "Lūdzu, ierakstiet RAL vai NCS krāsas kodu, piem. <code>RAL 9005</code>",
    "hint_country": "Lūdzu, izvēlieties valsti ar pogām augstāk vai ierakstiet tās nosaukumu.",
    "hint_address": "Lūdzu, nosūtiet pasta indeksu un piegādes adresi kā tekstu.",
    "hint_email": "Lūdzu, nosūtiet e-pasta adresi kā tekstu, piem. <code>janis@example.com</code>",
    "hint_phone": "Lūdzu, nosūtiet tālruņa numuru kā tekstu vai nospiediet “📱 Dalīties ar kontaktu”.",
    "hint_name": "Lūdzu, nosūtiet savu vārdu kā tekstu.",
    "hint_payment": "Lūdzu, izvēlieties apmaksas veidu ar pogām augstāk.",
    "hint_confirmation": "Lūdzu, apstipriniet vai atceliet pasūtījumu ar pogām augstāk.",
    # ------------------------------------------------------------------ validation errors
    "err_dims_format": (
        "Neizdevās nolasīt izmērus. Lūdzu, nosūtiet trīs veselus skaitļus milimetros "
        "formātā Augstums x Platums x Dziļums, piemēram: 800x950x470"
    ),
    "err_dims_leading_zero": "Izmēri nedrīkst sākties ar nulli. Piemērs: 800x950x470",
    "err_color_short": "Krāsas kods ir pārāk īss. Piemērs: RAL 9005 vai NCS S 1080-Y50R",
    "err_color_long": "Lūdzu, krāsas kodam vai nosaukumam izmantojiet mazāk par 60 rakstzīmēm.",
    "err_ral": "Tas neizskatās pēc derīga RAL koda. RAL Classic kodiem ir 4 cipari, piem. RAL 9005.",
    "err_ncs": "Tas neizskatās pēc derīga NCS koda. Piemērs: NCS S 1080-Y50R",
    "err_color_name": "Lūdzu, ievadiet RAL/NCS kodu (piem. RAL 9005, NCS S 1080-Y50R) vai krāsas nosaukumu.",
    "err_country": "Lūdzu, ievadiet valsts nosaukumu tikai ar burtiem, piem. Somija.",
    "err_address_short": (
        "Adrese ir pārāk īsa (vismaz {min} rakstzīmes). "
        "Lūdzu, nosūtiet pasta indeksu, pilsētu, ielu un mājas numuru, piem. LV-1010, Rīga, Brīvības iela 1"
    ),
    "err_address_long": "Adrese ir pārāk gara (ne vairāk kā {max} rakstzīmes).",
    "err_address_no_digits": "Adresē jābūt pasta indeksam (cipariem). Piemērs: LV-1010, Rīga, Brīvības iela 1",
    "err_postal_country": "Adresē neatradu derīgu pasta indeksu ({country}). Lūdzu, norādiet to, piem. {example}.",
    "err_postal_missing": "Adresē neatradu pasta indeksu. Lūdzu, norādiet to.",
    "err_address_rest": "Lūdzu, pēc pasta indeksa norādiet pilsētu, ielu un mājas numuru.",
    "err_phone": "Tālruņa numurs nav derīgs. Lūdzu, izmantojiet starptautisko formātu, piem. +37120000000",
    "err_email": "Tas neizskatās pēc derīgas e-pasta adreses. Piemērs: janis@example.com",
    "err_email_typo": "Vai domājāt <b>{suggestion}</b>? Lūdzu, pārbaudiet daļu pēc @ un ievadiet pilnu adresi vēlreiz.",
    "err_email_domain": (
        "Domēns <b>{domain}</b> nevar saņemt e-pastu. "
        "Lūdzu, pārbaudiet daļu pēc @ un ievadiet pilnu adresi, piem. vards@gmail.com vai vards@inbox.lv"
    ),
    "err_name_chars": "Vārds var saturēt tikai burtus, defises un apostrofus.",
}
