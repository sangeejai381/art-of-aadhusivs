import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
load_dotenv()  # reads a local .env file if present (never commit this file)

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-this")
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    # Render/Neon/Heroku-style URLs sometimes start with postgres:// —
    # SQLAlchemy 2.x requires the postgresql:// scheme.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Local development fallback — plain SQLite file, no setup needed.
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "store.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB

db = SQLAlchemy(app)

# Make sure the folders SQLite and file uploads depend on actually exist.
# Git/GitHub never uploads empty folders, so on a fresh host (Render, etc.)
# these are missing unless we create them ourselves at startup.
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# OPTIONAL: Cloudinary for persistent image storage.
# On free hosts like Render, local disk storage gets wiped on every restart.
# If CLOUDINARY_URL is set, uploaded product photos are stored there instead
# and survive restarts/redeploys. If it's not set, images save locally as
# before (fine for local development, NOT reliable on Render's free tier).
# ---------------------------------------------------------------------------
CLOUDINARY_ENABLED = bool(os.environ.get("CLOUDINARY_URL"))
if CLOUDINARY_ENABLED:
    import cloudinary
    import cloudinary.uploader
    # cloudinary reads CLOUDINARY_URL from the environment automatically


# ---------------------------------------------------------------------------
# SITE / OWNER SETTINGS  -- edit these to match your details
# ---------------------------------------------------------------------------
SITE_NAME = "Art of AadhuSivs"
INSTAGRAM_HANDLE = os.environ.get("INSTAGRAM_HANDLE", "your_handle_here")   # <-- set as env var, no @
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "910000000000")        # <-- set as env var, country code, no +/spaces
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "aadhusiv")
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    generate_password_hash(os.environ.get("ADMIN_PASSWORD", "changeme123"))
)

CATEGORIES = [
    ("paintings", "Paintings 🎨"),
    ("sketches", "Sketches ✏️"),
    ("digital-art", "Digital Art 💻"),
    ("resin-art", "Resin Art ✨"),
    ("customs", "Custom Portraits 🖼️"),
    ("prints", "Prints 🖨️"),
]

# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Integer, nullable=False, default=0)
    original_price = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(60), default="paintings")
    image_filename = db.Column(db.String(255), default="")
    is_new = db.Column(db.Boolean, default=False)
    is_sold = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def category_label(self):
        for slug, label in CATEGORIES:
            if slug == self.category:
                return label
        return self.category

    def image_url(self):
        if not self.image_filename:
            return None
        if self.image_filename.startswith("http"):
            return self.image_filename  # Cloudinary (or any external) URL
        return url_for("static", filename="uploads/" + self.image_filename)


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    buyer_name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(160), nullable=False)  # phone / insta handle / email
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="new")  # new / replied / closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")


# ---------------------------------------------------------------------------
# AUTH HELPERS
# ---------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------------------------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return dict(
        site_name=SITE_NAME,
        ig_handle=INSTAGRAM_HANDLE,
        ig_url=f"https://instagram.com/{INSTAGRAM_HANDLE}",
        ig_dm_url=f"https://ig.me/m/{INSTAGRAM_HANDLE}",
        wa_number=WHATSAPP_NUMBER,
        categories=CATEGORIES,
        category_dict=dict(CATEGORIES),
    )


@app.route("/")
def index():
    category = request.args.get("category", "")
    query = Product.query
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()
    featured = Product.query.filter_by(is_featured=True).limit(6).all()
    new_arrivals = Product.query.filter_by(is_new=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template(
        "index.html",
        products=products,
        featured=featured,
        new_arrivals=new_arrivals,
        active_category=category,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related = (
        Product.query.filter(Product.category == product.category, Product.id != product.id)
        .limit(4)
        .all()
    )
    return render_template("product_detail.html", product=product, related=related)


@app.route("/inquire", methods=["POST"])
def inquire():
    name = request.form.get("name", "").strip()
    contact = request.form.get("contact", "").strip()
    message = request.form.get("message", "").strip()
    product_id = request.form.get("product_id") or None

    if not name or not contact:
        return jsonify({"ok": False, "error": "Please fill in your name and a way to reach you."}), 400

    inquiry = Inquiry(
        buyer_name=name,
        contact=contact,
        message=message,
        product_id=int(product_id) if product_id else None,
    )
    db.session.add(inquiry)
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# ADMIN ROUTES
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["is_admin"] = True
            flash("Welcome back!", "success")
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(50).all()
    return render_template("admin_dashboard.html", products=products, inquiries=inquiries)


@app.route("/admin/product/new", methods=["POST"])
@admin_required
def admin_product_new():
    _save_product(Product())
    flash("Product added.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/product/<int:product_id>/edit", methods=["POST"])
@admin_required
def admin_product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    _save_product(product)
    flash("Product updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/inquiry/<int:inquiry_id>/status", methods=["POST"])
@admin_required
def admin_inquiry_status(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    inquiry.status = request.form.get("status", "new")
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


def _save_product(product: Product):
    product.name = request.form.get("name", "").strip()
    product.description = request.form.get("description", "").strip()
    product.price = int(request.form.get("price") or 0)
    original_price = request.form.get("original_price")
    product.original_price = int(original_price) if original_price else None
    product.category = request.form.get("category", "paintings")
    product.is_new = bool(request.form.get("is_new"))
    product.is_sold = bool(request.form.get("is_sold"))
    product.is_featured = bool(request.form.get("is_featured"))

    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        if CLOUDINARY_ENABLED:
            result = cloudinary.uploader.upload(file, folder="art_of_aadhusivs")
            product.image_filename = result["secure_url"]  # full URL, stored as-is
        else:
            filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            product.image_filename = filename

    if not product.id:
        db.session.add(product)
    db.session.commit()


# ---------------------------------------------------------------------------
# Make sure tables exist whether this runs via `python app.py` or a
# production server like gunicorn (which never hits the __main__ block below).
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
