# The Pizza Cone Co. — Website & Staff Dashboard

A Django site for a takeaway pizza-cone shop: a public menu/info site (no
online ordering — order at the counter), plus a staff-only dashboard for
managing the menu, tracking ingredient inventory, and logging sales.

## What's included

- **Public site**: Home, full Menu (grouped by category), item detail pages,
  About, and a **Find Us** page showing where the shop is today and its
  upcoming schedule (this is a rotating/mobile setup — no fixed address).
  A banner also appears on the homepage when there's a stop today or coming up.
- **Staff dashboard** (`/staff/`, login required, staff accounts only):
  - **Overview** — today's revenue, sales count, low-stock alerts, recent sales/items
  - **Record Sale** — a simple point-of-sale style screen: enter quantities
    sold per item and submit. This automatically deducts the ingredients
    used from inventory.
  - **Sales History** — a log of every recorded sale.
  - **Reports** — revenue and best-sellers for Today / This Week / This Month / All Time.
  - **Location Schedule** — add/edit/remove upcoming stops (date, time,
    address, notes, map link). The public site automatically shows today's
    stop and the upcoming list from this.
  - **Inventory** — ingredient stock levels, restock, low-stock warnings.
  - **Menu Items** — add/edit/delete items, upload photos, mark items
    unavailable ("86" them), and define each item's **recipe** (which
    ingredients + how much it uses) so inventory tracks automatically.
  - **Categories** — manage menu groupings.
- Django admin (`/admin/`) is also available for power-user editing.

## Requirements

- Python 3.11+ (3.12 recommended)
- pip

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Load the starter menu, ingredients, and recipes
python manage.py seed_menu

# 4b. (Optional) Load a few sample location stops (today + upcoming)
python manage.py seed_schedule

# 5. Create a staff/admin login
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Visit:
- **http://127.0.0.1:8000/** — the public site
- **http://127.0.0.1:8000/staff/login/** — staff dashboard login
- **http://127.0.0.1:8000/admin/** — Django admin

A demo database is included in this project (already migrated + seeded) with
a default staff login:

- **Username:** `admin`
- **Password:** `pizzacone123`

**Change this password (or delete `db.sqlite3` and start fresh with your own
`createsuperuser`) before putting this anywhere public.**

## How the location schedule works

Since this shop moves around, there's no fixed address on the site. Instead:

1. Staff go to **Location Schedule** in the dashboard and **Add a Stop** —
   date, start/end time, a name (e.g. "Downtown Farmers Market"), optional
   address, an optional **photo** (event flyer, venue shot, the truck at
   that spot, etc.), an optional **map pin** (latitude/longitude — this
   powers an embedded map and precise directions), notes, and an optional
   plain map link as a fallback if you don't have coordinates.
2. The public **Find Us** page automatically shows:
   - Today's stop (highlighted, with its photo, an embedded map if
     coordinates were set, and a directions link) if one is scheduled
   - The list of upcoming stops (with photos where uploaded)
3. The homepage shows a banner: "We're here today!" (with today's stop) or
   "Next stop: ..." (if nothing's scheduled today but something's coming up).
4. Mark a stop `is_cancelled` (edit it) if plans change — it'll stop showing
   on the public site without needing to delete the history.

Directions links use, in order of preference: the lat/long pin, then the
manual map link, then a text search on the address.

## How inventory + sales work

1. Go to **Menu Items → Edit** on any item and scroll to **Recipe**. Add each
   ingredient it uses and how much (e.g. Pepperoni Cone uses 4 oz Mozzarella,
   2 oz Pepperoni, 1 Cone Shell, 2 oz Pizza Sauce).
2. Go to **Inventory** to see stock levels and to add new ingredients, adjust
   thresholds, or restock (e.g. after a delivery).
3. When staff ring up a customer, they go to **Record Sale**, enter the
   quantity sold for each item, choose a payment method, and submit. This:
   - Creates a sale record
   - Deducts the recipe ingredients from stock automatically
   - Shows up immediately in **Sales History** and **Reports**
4. If an ingredient runs low (at or below its reorder threshold), it shows up
   as a **Low Stock** alert on the dashboard Overview and Inventory pages.
5. On the public menu, an item automatically shows a **Sold Out** badge if
   it doesn't have enough of any required ingredient in stock — no manual
   toggling needed (staff can still manually hide/"86" an item any time from
   Menu Items regardless of stock).

## Staff workflow: update menu, prices, and photos

1. Log in at **/staff/login/** with a staff account.
2. Open **Menu Items** from the left sidebar.
3. Click **+ Add Menu Item** to create a new item, or **Edit** on an existing one.
4. Set or change the **Price** field, then upload an image using the **Image** field.
5. Click **Save** to publish changes to the public menu.

Notes:
- Staff users (`is_staff=True`) can add, edit, and delete menu items from the dashboard.
- Superusers can create additional staff accounts from **Staff Accounts**.
- Uploaded images are validated for size/type and stored under `media/menu_items/`.

## Project structure

```
pizzacone_project/   Django project settings & root URLs
core/                 Home, About, Visit Us pages
menu/                 Category, MenuItem, Ingredient, MenuItemIngredient (recipes)
sales/                Sale, SaleLineItem + inventory deduction logic
dashboard/            Staff-only views: menu mgmt, inventory, sales/reports
templates/            All HTML templates (base.html + per-app folders)
static/                CSS, JS, and brand images (logo, hero banner, etc.)
media/                 Uploaded menu item photos (created at runtime)
```

## Notes on payment

This is a takeaway shop — there's no online payment or checkout. `Sale`
records simply note how the customer paid (Cash / Card / Other) for your own
bookkeping; no payment processor is integrated.

## Customizing the look

- Colors, fonts, and layout live in `static/css/style.css` (CSS variables at
  the top: `--pc-red`, `--pc-gold`, `--pc-black`, etc.)
- Swap logo/hero images in `static/images/` (same filenames, or update the
  `{% static %}` references in `templates/base.html` and `templates/core/home.html`).
- Business info (phone, address, hours) is set in
  `pizzacone_project/settings.py` under `STORE_NAME`, `STORE_PHONE`,
  `STORE_ADDRESS`, `STORE_HOURS`.

## Deploying

Before deploying anywhere public:
- Set `DEBUG = False` in `settings.py`
- Set a real, secret `SECRET_KEY` (use an environment variable)
- Set `ALLOWED_HOSTS`
- Switch from SQLite to Postgres/MySQL for production use
- Serve static/media files properly (e.g. WhiteNoise, S3, or your host's static file handling)
