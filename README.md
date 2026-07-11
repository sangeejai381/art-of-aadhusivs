# Art of Aadhusivs

A Flask-powered art store: browse products, DM/inquire to buy (no online checkout),
and manage everything yourself from a simple admin dashboard.

## 1. Run it locally

```bash
cd art_of_aadhusivs
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**

## 2. Set your details

Open `app.py` and edit the settings block near the top:

```python
SITE_NAME = "Art of Aadhusivs"
INSTAGRAM_HANDLE = "aadhusivs_art"     # your real Instagram username, no @
WHATSAPP_NUMBER  = "917020858864"      # your real number: countrycode+number, no + or spaces
ADMIN_USERNAME   = "aadhusiv"
```

To change the admin password, either set environment variables before running:

```bash
export ADMIN_USERNAME="yourname"
export ADMIN_PASSWORD="a-strong-password"
python app.py
```

...or edit the default `"changeme123"` directly in `app.py`. **Change this before
putting the site anywhere public.**

## 3. Add your products

Go to **/admin/login**, sign in, and use the **+ Add Product** tab: name, price,
description, category, photo. Products appear on the homepage instantly.

## 4. How "buying" works here

There's no payment gateway. Every product has two ways for someone to reach you:

- **DM to Buy** → opens your Instagram profile in a new tab so the buyer sends you
  a DM directly. *(Instagram does not allow a website to pre-fill DM text or pipe
  DMs into a custom inbox unless you're approved for Meta's Business Messaging API
  — that's a formal business verification process, separate from this site.)*
- **Quick Inquiry** → a form on the site itself. It's saved straight into your own
  database and shows up under the **Inquiries** tab in your admin dashboard, so you
  always have a backup even if someone doesn't/can't DM. Also useful since WhatsApp
  (unlike Instagram) *does* support pre-filled messages — there's a "Chat on
  WhatsApp" button on every product page for that reason.

If later on you want DMs to land automatically in a CRM/dashboard, that requires
applying for Instagram's Business Messaging API through Meta — happy to help you
wire that up once you have that approval.

## 5. Project structure

```
app.py                     Flask app: routes, models, admin logic
templates/                 Jinja templates (home, product page, admin, etc.)
static/css/style.css       All styling
static/js/main.js          Mobile nav, inquiry modal, admin tab logic
static/uploads/            Product photos uploaded via the admin panel
instance/store.db          SQLite database (products + inquiries)
```

## 6. Deploying

For real traffic, don't use `python app.py` (that's the dev server). Use gunicorn:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

...and put it behind Nginx or deploy on Render / Railway / PythonAnywhere, all of
which support Flask out of the box.
