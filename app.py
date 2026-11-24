"""
GLOBAL CHEMICAL SOLUTION — SINGLE FILE FLASK WEBSITE
----------------------------------------------------
A one-file starter website with enquiry cart, SQLite persistence,
and a password-protected Admin Dashboard.

Run:
    pip install Flask
    python app.py

Then open:
    Website:         http://127.0.0.1:5000
    Admin Dashboard: http://127.0.0.1:5000/admin

IMPORTANT:
- This demo intentionally displays only a limited lawful catalogue:
  Isopropyl Alcohol (IPA), HDPE Industrial Bottle, Ethylhexanoic Acid.
- Confirm product classification, local law, destination-country rules,
  transport requirements, intended use, and current SDS before supply.
- Enquiries are saved locally to enquiries.db.
- Replace FLASK_SECRET_KEY and ADMIN_PASSWORD before public deployment.
- Images are remote Unsplash images and require an internet connection.
"""

from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from datetime import datetime, timezone
from functools import wraps
import os
import sqlite3
import json

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "replace-this-development-key-before-deployment",
)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DB_PATH = "enquiries.db"

# ---------------------------------------------------------------------
# COMPANY PROFILE
# ---------------------------------------------------------------------

COMPANY = {
    "name": "Global Chemical Solution",
    "short_name": "GCS",
    "email": "Bestgblonine.uk@gmail.com",
    "phone": "+44 7983 259218",
    "address": "22 Parks Vw Rd, Inverness IV2 6JJ, United Kingdom",
    "country": "United Kingdom",
    "tagline": "Professional service. Responsible supply.",
}

# ---------------------------------------------------------------------
# SAFE STARTER CATALOGUE
# ---------------------------------------------------------------------

PRODUCTS = [
    {
        "id": 1,
        "slug": "isopropyl-alcohol",
        "name": "Isopropyl Alcohol (IPA)",
        "category": "Solvents",
        "short": "Industrial and professional-use solvent enquiry.",
        "description": (
            "Isopropyl alcohol is used in a range of legitimate industrial "
            "and cleaning applications. Exact concentration, grade, "
            "packaging, availability and supply eligibility must be "
            "confirmed before any quotation or supply decision."
        ),
        "image": (
            "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6"
            "?auto=format&fit=crop&w=1200&q=85"
        ),
        "badge": "Solvent",
        "specifications": [
            ("Product", "Isopropyl Alcohol (IPA)"),
            ("Grade", "Confirm on enquiry"),
            ("Concentration", "Confirm on enquiry"),
            ("Packaging", "Subject to availability"),
            ("Documentation", "Current SDS on request"),
        ],
        "applications": [
            "Professional cleaning applications",
            "Industrial process enquiries",
            "Laboratory and maintenance supply enquiries",
        ],
        "notice": (
            "Use only in accordance with the current SDS and applicable "
            "workplace safety procedures."
        ),
    },
    {
        "id": 2,
        "slug": "hdpe-industrial-bottle",
        "name": "HDPE Industrial Bottle",
        "category": "Packaging",
        "short": "Durable packaging for compatible industrial materials.",
        "description": (
            "High-density polyethylene (HDPE) containers are used for "
            "packaging a variety of compatible materials. Container "
            "compatibility must be checked against the exact chemical, "
            "concentration, temperature and storage conditions."
        ),
        "image": (
            "https://images.unsplash.com/photo-1602143407151-7111542de6e8"
            "?auto=format&fit=crop&w=1200&q=85"
        ),
        "badge": "Packaging",
        "specifications": [
            ("Material", "HDPE"),
            ("Capacity", "Confirm on enquiry"),
            ("Closure", "Confirm on enquiry"),
            ("Compatibility", "Must be verified for each substance"),
            ("Documentation", "Product information on request"),
        ],
        "applications": [
            "Compatible industrial packaging",
            "Storage of approved compatible materials",
            "Packaging procurement enquiries",
        ],
        "notice": (
            "Never assume a container is compatible. Obtain a documented "
            "compatibility confirmation before filling or storing chemicals."
        ),
    },
    {
        "id": 3,
        "slug": "ethylhexanoic-acid",
        "name": "Ethylhexanoic Acid",
        "category": "Industrial Chemicals",
        "short": "Industrial chemical specification enquiry.",
        "description": (
            "Ethylhexanoic acid is used in certain industrial chemical "
            "applications. Grade, specification, packaging and supply "
            "eligibility must be confirmed through a formal enquiry and "
            "applicable regulatory review."
        ),
        "image": (
            "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69"
            "?auto=format&fit=crop&w=1200&q=85"
        ),
        "badge": "Industrial",
        "specifications": [
            ("Product", "Ethylhexanoic Acid"),
            ("Grade", "Confirm on enquiry"),
            ("Specification", "Confirm on enquiry"),
            ("Packaging", "Subject to availability"),
            ("Documentation", "Current SDS on request"),
        ],
        "applications": [
            "Industrial chemical enquiries",
            "Specification and documentation review",
            "Approved professional applications",
        ],
        "notice": (
            "Review the current SDS and applicable local requirements before "
            "handling, storage, transport or use."
        ),
    },
]

CATEGORIES = ["All", "Solvents", "Packaging", "Industrial Chemicals"]

# ---------------------------------------------------------------------
# DATABASE HELPERS
# ---------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            subject TEXT NOT NULL,
            selected_products TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapped

# ---------------------------------------------------------------------
# SINGLE-PAGE HTML TEMPLATE
# ---------------------------------------------------------------------

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Global Chemical Solution — professional industrial product and packaging enquiries.">
<meta name="theme-color" content="#10243b">
<title>{{ company.name }} | Professional Chemical Solutions</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
:root {
    --navy: #10243b;
    --navy-dark: #091827;
    --navy-soft: #173b59;
    --blue: #1768a5;
    --blue-light: #278fc0;
    --cyan: #36b9c7;
    --cyan-soft: #e8f8f9;
    --ink: #1c2b3a;
    --muted: #687887;
    --muted-light: #91a0aa;
    --white: #ffffff;
    --pale: #f3f7fa;
    --pale-blue: #eaf2f7;
    --line: #e3ebf0;
    --success: #16794a;
    --danger: #a52d36;
    --shadow: 0 18px 55px rgba(16, 36, 59, 0.10);
    --radius: 12px;
    --radius-small: 6px;
    --container: 1160px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 90px; }
body { color: var(--ink); background: var(--white); font-family: "DM Sans", sans-serif; line-height: 1.65; overflow-x: hidden; }
body.modal-open { overflow: hidden; }
img { display: block; max-width: 100%; }
button, input, textarea, select { font: inherit; }
button { cursor: pointer; }
a { color: inherit; }

.container { width: min(var(--container), 90%); margin-inline: auto; }
.section { padding: 92px 0; }
.section-soft { background: var(--pale); }

h1, h2, h3, h4, h5 { font-family: "Manrope", sans-serif; line-height: 1.18; color: inherit; }
h1 { font-size: clamp(2.6rem, 5vw, 4.7rem); font-weight: 800; letter-spacing: -2.4px; }
h2 { font-size: clamp(2rem, 3.5vw, 3.15rem); font-weight: 800; letter-spacing: -1.4px; }
h3 { font-size: 1.22rem; font-weight: 800; }
p { color: var(--muted); }

.eyebrow { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; color: var(--blue); font-size: 0.69rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
.eyebrow::before { content: ""; width: 27px; height: 2px; background: var(--cyan); }
.eyebrow-light { color: #c0dce9; }

.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 25px; margin-bottom: 36px; }
.section-heading h2 { margin-bottom: 0; }
.section-intro { max-width: 650px; margin-top: 15px; font-size: 0.96rem; }

.btn { display: inline-flex; min-height: 48px; align-items: center; justify-content: center; gap: 13px; padding: 13px 21px; border: 1px solid transparent; border-radius: var(--radius-small); text-decoration: none; font-size: 0.83rem; font-weight: 800; transition: transform 0.2s ease, background 0.2s ease; }
.btn:hover { transform: translateY(-2px); }
.btn-primary { color: var(--white); background: linear-gradient(105deg, var(--blue), #1599b1); }
.btn-dark { color: var(--white); background: var(--navy); }
.btn-outline { color: var(--white); border-color: rgba(255, 255, 255, 0.55); background: rgba(255, 255, 255, 0.07); }
.btn-outline-dark { color: var(--navy); border-color: #cbd8e0; background: transparent; }

.text-link { color: var(--blue); text-decoration: none; font-size: 0.83rem; font-weight: 800; }
.text-link:hover { color: var(--cyan); }
.pill { display: inline-flex; align-items: center; padding: 6px 11px; border-radius: 99px; color: var(--blue); background: #e9f5fa; font-size: 0.68rem; font-weight: 800; }
.hidden { display: none !important; }

.topbar { color: #c6d6e1; background: var(--navy-dark); font-size: 0.72rem; }
.topbar-inner { display: flex; justify-content: space-between; gap: 20px; padding: 9px 0; }
.topbar a { color: #dce9ef; text-decoration: none; }
.topbar a:hover { color: var(--cyan); }

.site-header { position: sticky; top: 0; z-index: 50; background: rgba(255, 255, 255, 0.97); border-bottom: 1px solid var(--line); backdrop-filter: blur(14px); }
.navbar { display: flex; min-height: 84px; align-items: center; justify-content: space-between; gap: 25px; }
.brand { display: inline-flex; align-items: center; gap: 11px; color: var(--navy); text-decoration: none; font-family: "Manrope", sans-serif; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px; line-height: 1.12; }
.brand-mark { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 12px; color: white; background: linear-gradient(135deg, var(--blue), var(--cyan)); box-shadow: 0 8px 18px rgba(23, 104, 165, 0.18); font-size: 0.95rem; letter-spacing: 0; }
.brand small { display: block; margin-top: 4px; color: #718294; font-size: 0.57rem; letter-spacing: 3px; }

.nav-links { display: flex; align-items: center; gap: 24px; }
.nav-links a { color: #34485a; text-decoration: none; font-size: 0.79rem; font-weight: 800; transition: color 0.2s ease; }
.nav-links a:hover, .nav-links a.active { color: var(--blue); }
.nav-links .nav-cta { padding: 13px 17px; border-radius: 5px; color: white; background: var(--navy); }
.menu-button { display: none; width: 42px; height: 42px; border: 1px solid var(--line); border-radius: 7px; color: var(--navy); background: white; font-size: 1.35rem; }

.hero {
    position: relative; display: flex; min-height: 630px; align-items: center; overflow: hidden; color: white;
    background:
        linear-gradient(90deg, rgba(7, 24, 43, 0.97) 0%, rgba(9, 38, 61, 0.84) 48%, rgba(8, 37, 58, 0.36) 100%),
        url("https://images.unsplash.com/photo-1581093458791-9d42e3c4a3d8?auto=format&fit=crop&w=2100&q=90") center / cover;
}
.hero::after { position: absolute; right: -120px; bottom: -240px; width: 580px; height: 580px; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 50%; content: ""; }
.hero-content { position: relative; z-index: 2; padding: 95px 0; }
.hero h1 { max-width: 790px; margin-bottom: 24px; }
.hero h1 span { color: #68d8dc; }
.hero-copy { max-width: 650px; color: #d0dce5; font-size: 1.04rem; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 13px; margin-top: 31px; }
.hero-proof { display: flex; flex-wrap: wrap; gap: 25px; margin-top: 35px; color: #d5e2e9; font-size: 0.75rem; }
.hero-proof span::before { margin-right: 8px; color: #6ce0d9; content: "✓"; font-weight: 900; }

.hero-stamp { position: absolute; right: 8%; bottom: 55px; z-index: 2; display: flex; min-width: 210px; flex-direction: column; padding: 23px 25px; border: 1px solid rgba(255, 255, 255, 0.4); color: white; background: rgba(255, 255, 255, 0.11); backdrop-filter: blur(12px); }
.hero-stamp strong { font-family: "Manrope", sans-serif; font-size: 2.5rem; letter-spacing: 3px; }
.hero-stamp span { font-size: 0.65rem; letter-spacing: 2px; }
.hero-stamp small { margin-top: 10px; color: #c8d9e5; font-size: 0.55rem; letter-spacing: 1.5px; }

.value-strip { border-bottom: 1px solid var(--line); background: #f4f8fa; }
.value-grid { display: grid; grid-template-columns: repeat(4, 1fr); padding: 27px 0; }
.value-item { display: flex; align-items: center; gap: 15px; padding: 5px 22px; border-right: 1px solid #dce6eb; }
.value-item:first-child { padding-left: 0; }
.value-item:last-child { border: 0; }
.value-number { color: #1a9caf; font-family: "Manrope", sans-serif; font-size: 1.65rem; font-weight: 800; }
.value-item span:last-child { color: #43586a; font-size: 0.73rem; font-weight: 800; line-height: 1.35; }

.catalogue-tools { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 25px; }
.search-box { display: flex; width: min(360px, 100%); align-items: center; gap: 10px; padding: 11px 14px; border: 1px solid var(--line); border-radius: 7px; background: white; }
.search-box span { color: var(--muted-light); }
.search-box input { width: 100%; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 0.82rem; }

.filter-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.filter-button { padding: 9px 14px; border: 1px solid var(--line); border-radius: 99px; color: #536575; background: white; font-size: 0.72rem; font-weight: 800; transition: all 0.2s ease; }
.filter-button:hover, .filter-button.active { border-color: var(--blue); color: white; background: var(--blue); }

.product-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; }
.product-card { overflow: hidden; border: 1px solid var(--line); border-radius: var(--radius); background: white; transition: transform 0.25s ease, box-shadow 0.25s ease; }
.product-card:hover { transform: translateY(-6px); box-shadow: var(--shadow); }
.product-image { position: relative; height: 235px; overflow: hidden; background: var(--pale-blue); }
.product-image img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s ease; }
.product-card:hover .product-image img { transform: scale(1.06); }
.product-badge { position: absolute; top: 16px; left: 16px; padding: 6px 11px; border-radius: 4px; color: var(--blue); background: white; font-size: 0.65rem; font-weight: 800; }
.product-content { padding: 23px; }
.product-content h3 { margin: 12px 0 10px; }
.product-content p { min-height: 66px; font-size: 0.81rem; }
.product-bottom { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 17px; padding-top: 15px; border-top: 1px solid var(--line); flex-wrap: wrap; }
.action-btn { padding: 0; border: 0; color: var(--blue); background: transparent; font-size: 0.76rem; font-weight: 800; }
.action-btn:hover { color: var(--navy); }
.product-bottom > span { color: var(--muted-light); font-size: 0.65rem; }
.no-results { display: none; padding: 45px 20px; border: 1px dashed #cbd8e0; border-radius: var(--radius); color: var(--muted); text-align: center; }

.split-feature { display: grid; grid-template-columns: 1fr 1fr; background: var(--pale); }
.split-photo { min-height: 530px; background: url("https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=1400&q=85") center / cover; }
.split-copy { align-self: center; padding: 80px clamp(35px, 8vw, 120px); }
.split-copy h2 { max-width: 520px; margin-bottom: 20px; }
.split-copy > p { max-width: 550px; }
.check-list { margin: 27px 0; list-style: none; }
.check-list li { position: relative; padding: 9px 0 9px 29px; color: #45596a; font-size: 0.82rem; }
.check-list li::before { position: absolute; left: 0; color: #159eaa; content: "✓"; font-weight: 900; }

.process-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 23px; margin-top: 36px; }
.process-card { padding: 30px; border: 1px solid var(--line); border-radius: var(--radius); background: white; }
.process-card .step { display: grid; width: 48px; height: 48px; place-items: center; margin-bottom: 22px; border-radius: 12px; color: white; background: linear-gradient(135deg, var(--blue), var(--cyan)); font-family: "Manrope", sans-serif; font-weight: 800; }
.process-card h3 { margin-bottom: 11px; }
.process-card p { font-size: 0.81rem; }

.safety-panel {
    position: relative; overflow: hidden; padding: 70px; border-radius: 15px; color: white;
    background: linear-gradient(110deg, rgba(12, 36, 57, 0.97), rgba(19, 91, 119, 0.88)), url("https://images.unsplash.com/photo-1581093588401-fbb62a02f120?auto=format&fit=crop&w=1600&q=85") center / cover;
}
.safety-panel h2 { max-width: 700px; }
.safety-panel p { max-width: 680px; color: #d0dce5; }
.safety-points { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin: 30px 0; }
.safety-point { padding: 17px; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 7px; color: #e3edf2; background: rgba(255, 255, 255, 0.07); font-size: 0.76rem; }

.cta-band { padding: 57px 0; color: white; background: linear-gradient(110deg, #10243b, #174b6c); }
.cta-inner { display: flex; align-items: center; justify-content: space-between; gap: 25px; }
.cta-inner h2 { margin-bottom: 8px; font-size: clamp(1.8rem, 3vw, 2.5rem); }
.cta-inner p { color: #c5d6e0; }

.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.info-card { padding: 29px; border: 1px solid var(--line); border-radius: var(--radius); background: white; }
.info-card .info-number { color: var(--cyan); font-family: "Manrope", sans-serif; font-size: 1.9rem; font-weight: 800; }
.info-card h3 { margin: 12px 0; }
.info-card p { font-size: 0.82rem; }

.contact-layout { display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 75px; }
.contact-details { margin-top: 28px; }
.contact-line { display: flex; flex-direction: column; gap: 4px; padding: 17px 0; border-top: 1px solid var(--line); }
.contact-line small { color: #8494a0; font-size: 0.63rem; font-weight: 800; letter-spacing: 1.5px; }
.contact-line strong { overflow-wrap: anywhere; font-size: 0.88rem; }

.contact-form { padding: 34px; border: 1px solid var(--line); border-radius: var(--radius); background: #f7fafb; }
.contact-form h3 { margin-bottom: 23px; font-size: 1.45rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.form-field { margin-bottom: 16px; }
.form-field label { display: block; margin-bottom: 7px; color: #42586a; font-size: 0.73rem; font-weight: 800; }
.form-field input, .form-field textarea, .form-field select { width: 100%; padding: 13px 14px; border: 1px solid #dce5ea; border-radius: 5px; outline: none; color: var(--ink); background: white; font-size: 0.82rem; transition: border 0.2s ease, box-shadow 0.2s ease; }
.form-field input:focus, .form-field textarea:focus, .form-field select:focus { border-color: var(--blue-light); box-shadow: 0 0 0 3px rgba(39, 143, 192, 0.10); }
.form-field textarea { min-height: 130px; resize: vertical; }
.form-note { display: block; margin-top: 14px; color: #8796a0; font-size: 0.65rem; }

.flash { margin-bottom: 17px; padding: 12px 14px; border-radius: 5px; font-size: 0.77rem; }
.flash.success { color: var(--success); background: #e5f6ec; }
.flash.error { color: var(--danger); background: #fff0f0; }

.footer { padding-top: 62px; color: #d8e3e9; background: var(--navy-dark); }
.footer-grid { display: grid; grid-template-columns: 1.35fr 0.7fr 1fr; gap: 55px; padding-bottom: 47px; }
.footer-brand { color: white; }
.footer-brand p { max-width: 350px; margin-top: 20px; color: #aebfca; font-size: 0.78rem; }
.footer h4 { margin-bottom: 18px; color: white; font-size: 0.85rem; }
.footer-links a { display: block; margin: 10px 0; color: #afc0cb; text-decoration: none; font-size: 0.76rem; }
.footer-links a:hover { color: var(--cyan); }
.footer-contact p { margin: 9px 0; color: #afc0cb; font-size: 0.75rem; overflow-wrap: anywhere; }
.footer-bottom { padding: 18px 0; border-top: 1px solid rgba(255, 255, 255, 0.12); color: #9fb0bc; font-size: 0.68rem; }
.footer-bottom-inner { display: flex; justify-content: space-between; gap: 20px; }

.modal-backdrop { position: fixed; inset: 0; z-index: 100; display: none; overflow-y: auto; padding: 35px 15px; background: rgba(5, 17, 29, 0.75); }
.modal-backdrop.open { display: grid; place-items: center; }
.product-modal { position: relative; width: min(900px, 100%); overflow: hidden; border-radius: 12px; background: white; box-shadow: 0 25px 90px rgba(0, 0, 0, 0.25); }
.modal-close { position: absolute; top: 13px; right: 13px; z-index: 2; display: grid; width: 38px; height: 38px; place-items: center; border: 0; border-radius: 50%; color: var(--navy); background: white; font-size: 1.3rem; }
.modal-content { display: grid; grid-template-columns: 0.9fr 1.1fr; }
.modal-image { min-height: 440px; background: var(--pale-blue); }
.modal-image img { width: 100%; height: 100%; object-fit: cover; }
.modal-info { padding: 43px 37px; }
.modal-info h2 { margin: 13px 0; font-size: 2rem; }
.modal-info p { font-size: 0.84rem; }
.modal-specs { margin: 22px 0; list-style: none; }
.modal-specs li { padding: 9px 0; border-bottom: 1px solid var(--line); color: #536575; font-size: 0.76rem; }
.modal-notice { margin: 20px 0; padding: 13px; border-left: 3px solid var(--cyan); color: #496170; background: var(--cyan-soft); font-size: 0.72rem; }

.back-to-top { position: fixed; right: 22px; bottom: 22px; z-index: 40; display: none; width: 43px; height: 43px; border: 0; border-radius: 50%; color: white; background: var(--blue); box-shadow: var(--shadow); font-size: 1.2rem; }
.back-to-top.visible { display: block; }
:focus-visible { outline: 3px solid rgba(54, 185, 199, 0.65); outline-offset: 3px; }

@media (max-width: 900px) {
    .nav-links { gap: 15px; }
    .nav-links a { font-size: 0.72rem; }
    .hero-stamp { right: 5%; }
    .product-grid { grid-template-columns: repeat(2, 1fr); }
    .value-item { padding-inline: 12px; }
    .split-copy { padding: 60px 7%; }
    .footer-grid { gap: 30px; }
}

@media (max-width: 700px) {
    .topbar-inner { justify-content: center; text-align: center; }
    .topbar-inner span:last-child { display: none; }
    .navbar { min-height: 72px; }
    .menu-button { display: block; }
    .nav-links { position: absolute; top: 72px; right: 0; left: 0; display: none; align-items: stretch; flex-direction: column; gap: 0; padding: 12px 5% 20px; border-bottom: 1px solid var(--line); background: white; box-shadow: 0 12px 25px rgba(0, 0, 0, 0.08); }
    .nav-links.open { display: flex; }
    .nav-links a { padding: 12px 0; font-size: 0.82rem; }
    .nav-links .nav-cta { padding: 13px 15px; }
    .hero { min-height: 600px; background-position: 60% center; }
    .hero-content { padding: 75px 0; }
    .hero-stamp { display: none; }
    .hero-proof { gap: 12px 20px; }
    .value-grid { grid-template-columns: repeat(2, 1fr); gap: 18px 10px; }
    .value-item { border: 0; padding: 4px 0; }
    .section { padding: 65px 0; }
    .section-heading { display: block; }
    .section-heading .text-link { display: inline-block; margin-top: 15px; }
    .catalogue-tools { align-items: stretch; flex-direction: column; }
    .search-box { width: 100%; }
    .product-grid { grid-template-columns: 1fr; }
    .product-image { height: 230px; }
    .split-feature { grid-template-columns: 1fr; }
    .split-photo { min-height: 310px; }
    .split-copy { padding: 55px 6%; }
    .process-grid { grid-template-columns: 1fr; }
    .safety-panel { padding: 40px 25px; }
    .safety-points { grid-template-columns: 1fr; }
    .cta-inner { align-items: flex-start; flex-direction: column; }
    .contact-layout { grid-template-columns: 1fr; gap: 35px; }
    .info-grid { grid-template-columns: 1fr; }
    .footer-grid { grid-template-columns: 1fr; gap: 28px; }
    .footer-bottom-inner { flex-direction: column; }
    .modal-content { grid-template-columns: 1fr; }
    .modal-image { min-height: 230px; max-height: 260px; }
    .modal-info { padding: 28px 23px; }
}

@media (max-width: 420px) {
    h1 { letter-spacing: -1.5px; }
    .hero-actions { align-items: stretch; flex-direction: column; }
    .hero-actions .btn { width: 100%; }
    .form-row { grid-template-columns: 1fr; gap: 0; }
    .contact-form { padding: 23px 18px; }
    .brand { font-size: 0.75rem; }
    .brand-mark { width: 42px; height: 42px; }
}
</style>
</head>

<body>

<div class="topbar">
    <div class="container topbar-inner">
        <span>Professional industrial product enquiries</span>
        <span>
            <a href="mailto:{{ company.email }}">{{ company.email }}</a>
            &nbsp; | &nbsp;
            <a href="tel:{{ company.phone }}">{{ company.phone }}</a>
        </span>
    </div>
</div>

<header class="site-header">
    <div class="container navbar">
        <a class="brand" href="#home" aria-label="Global Chemical Solution home">
            <span class="brand-mark">GCS</span>
            <span>
                GLOBAL CHEMICAL
                <small>SOLUTION</small>
            </span>
        </a>

        <button class="menu-button" id="menuButton" aria-label="Open navigation" aria-expanded="false">☰</button>

        <nav class="nav-links" id="navLinks">
            <a class="active" href="#home">Home</a>
            <a href="#products">Products</a>
            <a href="#about">About</a>
            <a href="#process">Our Process</a>
            <a href="#cart">Cart</a>
            <a href="{{ url_for('admin_dashboard') }}">Admin</a>
            <a href="#contact" class="nav-cta">Request an Enquiry ↗</a>
        </nav>
    </div>
</header>

<main id="home">
<section class="hero">
    <div class="container hero-content">
        <div class="eyebrow eyebrow-light">INDUSTRIAL SUPPLY • RESPONSIBLE SERVICE</div>
        <h1>Reliable chemical solutions. <span>Professional service.</span></h1>
        <p class="hero-copy">
            Explore selected industrial product and packaging enquiries.
            We focus on clear specifications, responsible communication
            and safety documentation.
        </p>
        <div class="hero-actions">
            <a class="btn btn-primary" href="#products">Explore Catalogue <span>→</span></a>
            <a class="btn btn-outline" href="#contact">Contact Our Team</a>
        </div>
        <div class="hero-proof">
            <span>Specification-led enquiries</span>
            <span>Documentation on request</span>
            <span>Safety-first approach</span>
        </div>
    </div>

    <div class="hero-stamp">
        <strong>GCS</strong>
        <span>GLOBAL CHEMICAL</span>
        <span>SOLUTION</span>
        <small>INDUSTRIAL • PACKAGING • SUPPORT</small>
    </div>
</section>

<section class="value-strip">
    <div class="container value-grid">
        <div class="value-item"><span class="value-number">01</span><span>Clear product<br>information</span></div>
        <div class="value-item"><span class="value-number">02</span><span>Safety-first<br>approach</span></div>
        <div class="value-item"><span class="value-number">03</span><span>Documentation<br>support</span></div>
        <div class="value-item"><span class="value-number">04</span><span>Professional<br>enquiries</span></div>
    </div>
</section>

<section class="section container" id="products">
    <div class="section-heading">
        <div>
            <div class="eyebrow">OUR CATALOGUE</div>
            <h2>Products & solutions</h2>
            <p class="section-intro">
                Browse the starter catalogue. Final product specifications,
                packaging and availability are confirmed individually.
            </p>
        </div>
        <a class="text-link" href="#contact">Ask about a product →</a>
    </div>

    <div class="catalogue-tools">
        <div class="search-box">
            <span>⌕</span>
            <input type="search" id="productSearch" placeholder="Search catalogue..." aria-label="Search products">
        </div>
        <span class="pill">{{ products|length }} catalogue items</span>
    </div>

    <div class="filter-row" id="filterRow">
        {% for category in categories %}
        <button class="filter-button {% if loop.first %}active{% endif %}" data-category="{{ category }}" type="button">{{ category }}</button>
        {% endfor %}
    </div>

    <div class="product-grid" id="productGrid">
        {% for product in products %}
        <article class="product-card" data-name="{{ product.name|lower }}" data-category="{{ product.category }}">
            <div class="product-image">
                <img src="{{ product.image }}" alt="{{ product.name }}" loading="lazy">
                <span class="product-badge">{{ product.badge }}</span>
            </div>

            <div class="product-content">
                <span class="pill">{{ product.category }}</span>
                <h3>{{ product.name }}</h3>
                <p>{{ product.short }}</p>

                <div class="product-bottom">
                    <span>Specification on enquiry</span>
                    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
                        <button type="button" class="action-btn details-button" data-product-id="{{ product.id }}">View details ↗</button>
                        <button type="button" class="action-btn add-cart-button" data-product-id="{{ product.id }}">Add to enquiry cart +</button>
                    </div>
                </div>
            </div>
        </article>
        {% endfor %}
    </div>

    <div class="no-results" id="noResults">No matching catalogue items found. Try another search.</div>

    <div class="catalogue-note" style="margin-top:30px;padding:17px 19px;border-left:3px solid var(--cyan);color:#496170;background:#edf7f8;font-size:.78rem;">
        <strong>Important:</strong>
        Product supply is subject to applicable laws, intended-use review,
        transport requirements, destination checks and documentation.
    </div>
</section>

<section class="split-feature" id="about">
    <div class="split-photo" role="img" aria-label="Modern laboratory workspace"></div>
    <div class="split-copy">
        <div class="eyebrow">ABOUT GLOBAL CHEMICAL SOLUTION</div>
        <h2>Good supply starts with the right information.</h2>
        <p>
            Global Chemical Solution provides a professional point of
            contact for enquiries relating to selected industrial products
            and compatible packaging solutions.
        </p>
        <ul class="check-list">
            <li>Clear product and specification discussions</li>
            <li>Safety Data Sheet information on request</li>
            <li>Destination and transport requirements reviewed</li>
            <li>Professional communication throughout the enquiry</li>
        </ul>
        <a class="btn btn-dark" href="#contact">Speak With Our Team →</a>
    </div>
</section>

<section class="section container" id="process">
    <div class="section-heading">
        <div>
            <div class="eyebrow">HOW WE WORK</div>
            <h2>A clear enquiry process</h2>
            <p class="section-intro">
                Product discussions should be based on accurate information,
                appropriate documentation and relevant legal checks.
            </p>
        </div>
    </div>

    <div class="process-grid">
        <article class="process-card">
            <div class="step">01</div>
            <h3>Share your enquiry</h3>
            <p>Tell us which catalogue item you are asking about, the intended professional application and the destination.</p>
        </article>
        <article class="process-card">
            <div class="step">02</div>
            <h3>Review specifications</h3>
            <p>Confirm the exact specification, grade, packaging and documentation needed for your enquiry.</p>
        </article>
        <article class="process-card">
            <div class="step">03</div>
            <h3>Compliance review</h3>
            <p>Any supply decision requires applicable legal, safety, transport and destination-country checks.</p>
        </article>
    </div>
</section>

<section class="section section-soft" id="safety">
    <div class="container">
        <div class="safety-panel">
            <div class="eyebrow eyebrow-light">RESPONSIBLE HANDLING</div>
            <h2>Safety information is part of every chemical conversation.</h2>
            <p>
                Always obtain and review the current Safety Data Sheet (SDS)
                for the exact product and grade. Website content is not a
                substitute for professional safety advice or official
                product documentation.
            </p>
            <div class="safety-points">
                <div class="safety-point"><strong>01 — SDS</strong><br>Request current product documentation.</div>
                <div class="safety-point"><strong>02 — Compatibility</strong><br>Verify container and material compatibility.</div>
                <div class="safety-point"><strong>03 — Regulations</strong><br>Check laws and transport rules for each destination.</div>
            </div>
            <a class="btn btn-primary" href="#contact">Request Documentation Information ↗</a>
        </div>
    </div>
</section>

<section class="section container">
    <div class="section-heading">
        <div>
            <div class="eyebrow">OUR COMMITMENT</div>
            <h2>Professional standards</h2>
        </div>
    </div>

    <div class="info-grid">
        <article class="info-card"><div class="info-number">01</div><h3>Clear communication</h3><p>We aim to make product enquiries and documentation discussions clear and straightforward.</p></article>
        <article class="info-card"><div class="info-number">02</div><h3>Accurate information</h3><p>Product details must be checked against the exact specification and supplier documentation.</p></article>
        <article class="info-card"><div class="info-number">03</div><h3>Responsible handling</h3><p>Safe handling, storage and transport require current product-specific information and trained personnel.</p></article>
        <article class="info-card"><div class="info-number">04</div><h3>Regulatory awareness</h3><p>Any product supply must meet applicable requirements in the origin, transit and destination jurisdictions.</p></article>
    </div>
</section>

<section class="section container" id="cart">
    <div class="section-heading">
        <div>
            <div class="eyebrow">YOUR SELECTION</div>
            <h2>Enquiry cart</h2>
            <p class="section-intro">Add permitted catalogue items and submit your requirements for a quotation. Prices are confirmed individually; no prices are invented here.</p>
        </div>
    </div>
    <div style="background:#f3f7fa;border:1px solid #e3ebf0;border-radius:12px;padding:22px">
        <div id="cartItems"><p>Your enquiry cart is empty.</p></div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-top:15px">
            <strong id="cartCount">0 items selected</strong>
            <button type="button" class="btn btn-outline-dark" id="clearCart">Clear cart</button>
        </div>
    </div>
</section>

<section class="section section-soft" id="contact">
    <div class="container contact-layout">
        <div>
            <div class="eyebrow">GET IN TOUCH</div>
            <h2>Let's discuss your requirements.</h2>
            <p class="section-intro">
                Send a product, specification or documentation enquiry.
                For an accurate response, include the intended application
                and destination country.
            </p>

            <div class="contact-details">
                <div class="contact-line"><small>EMAIL ADDRESS</small><strong>{{ company.email }}</strong></div>
                <div class="contact-line"><small>PHONE / WHATSAPP</small><strong>{{ company.phone }}</strong></div>
                <div class="contact-line"><small>BUSINESS ADDRESS</small><strong>{{ company.address }}</strong></div>
            </div>

            <a class="btn btn-outline-dark" href="https://wa.me/447983259218" target="_blank" rel="noopener">Open WhatsApp ↗</a>
        </div>

        <form class="contact-form" method="POST" action="{{ url_for('home') }}#contact">
            <h3>Send an enquiry</h3>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}

            <div class="form-row">
                <div class="form-field">
                    <label for="name">Your name *</label>
                    <input id="name" name="name" required maxlength="100" placeholder="Full name">
                </div>
                <div class="form-field">
                    <label for="email">Email address *</label>
                    <input id="email" name="email" type="email" required maxlength="150" placeholder="you@example.com">
                </div>
            </div>

            <div class="form-field">
                <label for="subject">Subject *</label>
                <select id="subject" name="subject" required>
                    <option value="">Select enquiry type</option>
                    <option>Product specification</option>
                    <option>Safety Data Sheet</option>
                    <option>Packaging information</option>
                    <option>General business enquiry</option>
                </select>
            </div>

            <div class="form-row">
                <div class="form-field"><label for="phone">Phone / WhatsApp *</label><input id="phone" name="phone" required maxlength="40" placeholder="Your contact number"></div>
                <div class="form-field"><label for="city">City *</label><input id="city" name="city" required maxlength="100" placeholder="City"></div>
            </div>
            <div class="form-field"><label for="address">Delivery / Business Address *</label><input id="address" name="address" required maxlength="300" placeholder="Street, building, postcode"></div>
            <div class="form-field"><label for="country">Country *</label><input id="country" name="country" required maxlength="100" placeholder="Country"></div>
            <input type="hidden" id="selectedProducts" name="selected_products" value="[]">

            <div class="form-field">
                <label for="message">Message / Intended application *</label>
                <textarea id="message" name="message" required maxlength="3000" placeholder="Tell us about your enquiry, intended application and destination country."></textarea>
            </div>

            <button class="btn btn-primary" type="submit">Submit Enquiry ↗</button>

            <small class="form-note">Your enquiry is saved to the website database for the site owner to review. A quotation and supply eligibility are subject to product, destination and regulatory checks. Do not submit sensitive personal information.</small>
        </form>
    </div>
</section>

<section class="cta-band">
    <div class="container cta-inner">
        <div>
            <div class="eyebrow eyebrow-light">GLOBAL CHEMICAL SOLUTION</div>
            <h2>Need product information?</h2>
            <p>Our contact details are available for professional enquiries.</p>
        </div>
        <a class="btn btn-primary" href="#contact">Contact Our Team ↗</a>
    </div>
</section>
</main>

<footer class="footer">
    <div class="container footer-grid">
        <div class="footer-brand">
            <a class="brand footer-brand" href="#home">
                <span class="brand-mark">GCS</span>
                <span>GLOBAL CHEMICAL<small>SOLUTION</small></span>
            </a>
            <p>Professional enquiries for selected industrial products and compatible packaging solutions. Responsible information and safety documentation matter.</p>
        </div>

        <div class="footer-links">
            <h4>Explore Website</h4>
            <a href="#home">Home</a>
            <a href="#products">Product catalogue</a>
            <a href="#about">About us</a>
            <a href="#process">Our process</a>
            <a href="#contact">Contact</a>
            <a href="{{ url_for('admin_dashboard') }}">Admin Dashboard</a>
        </div>

        <div class="footer-contact">
            <h4>Contact Information</h4>
            <p>{{ company.email }}</p>
            <p>{{ company.phone }}</p>
            <p>{{ company.address }}</p>
        </div>
    </div>

    <div class="footer-bottom">
        <div class="container footer-bottom-inner">
            <span>© {{ year }} Global Chemical Solution. All rights reserved.</span>
            <span>Supply is subject to legal, safety and destination checks.</span>
        </div>
    </div>
</footer>

<div class="modal-backdrop" id="productModal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="product-modal">
        <button class="modal-close" id="modalClose" aria-label="Close dialog">×</button>
        <div class="modal-content">
            <div class="modal-image"><img id="modalImage" src="" alt=""></div>
            <div class="modal-info">
                <span class="pill" id="modalCategory"></span>
                <h2 id="modalTitle">Product details</h2>
                <p id="modalDescription"></p>
                <h3>Product information</h3>
                <ul class="modal-specs" id="modalSpecs"></ul>
                <div class="modal-notice" id="modalNotice"></div>
                <a class="btn btn-primary" href="#contact" id="modalEnquiry">Enquire about this product ↗</a>
            </div>
        </div>
    </div>
</div>

<button class="back-to-top" id="backToTop" aria-label="Back to top">↑</button>

<script>
const PRODUCTS = {{ products|tojson }};

const menuButton = document.getElementById("menuButton");
const navLinks = document.getElementById("navLinks");

menuButton.addEventListener("click", function () {
    const isOpen = navLinks.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.textContent = isOpen ? "×" : "☰";
});

navLinks.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
        navLinks.classList.remove("open");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.textContent = "☰";
    });
});

const searchInput = document.getElementById("productSearch");
const filterButtons = document.querySelectorAll(".filter-button");
const productCards = document.querySelectorAll(".product-card");
const noResults = document.getElementById("noResults");
let activeCategory = "All";

function filterProducts() {
    const searchTerm = searchInput.value.trim().toLowerCase();
    let visibleCount = 0;

    productCards.forEach(function (card) {
        const productName = card.dataset.name || "";
        const productCategory = card.dataset.category || "";
        const matchesSearch = productName.includes(searchTerm);
        const matchesCategory = activeCategory === "All" || productCategory === activeCategory;
        const shouldShow = matchesSearch && matchesCategory;

        card.classList.toggle("hidden", !shouldShow);
        if (shouldShow) visibleCount += 1;
    });

    noResults.style.display = visibleCount === 0 ? "block" : "none";
}

searchInput.addEventListener("input", filterProducts);

filterButtons.forEach(function (button) {
    button.addEventListener("click", function () {
        filterButtons.forEach(function (item) { item.classList.remove("active"); });
        button.classList.add("active");
        activeCategory = button.dataset.category;
        filterProducts();
    });
});

const modal = document.getElementById("productModal");
const modalClose = document.getElementById("modalClose");
const modalImage = document.getElementById("modalImage");
const modalCategory = document.getElementById("modalCategory");
const modalTitle = document.getElementById("modalTitle");
const modalDescription = document.getElementById("modalDescription");
const modalSpecs = document.getElementById("modalSpecs");
const modalNotice = document.getElementById("modalNotice");
const modalEnquiry = document.getElementById("modalEnquiry");

function openProductModal(productId) {
    const product = PRODUCTS.find(function (item) { return Number(item.id) === Number(productId); });
    if (!product) return;

    modalImage.src = product.image;
    modalImage.alt = product.name;
    modalCategory.textContent = product.category;
    modalTitle.textContent = product.name;
    modalDescription.textContent = product.description;
    modalNotice.textContent = product.notice;
    modalSpecs.innerHTML = "";

    product.specifications.forEach(function (specification) {
        const item = document.createElement("li");
        const label = document.createElement("strong");
        label.textContent = specification[0] + ": ";
        item.appendChild(label);
        item.appendChild(document.createTextNode(specification[1]));
        modalSpecs.appendChild(item);
    });

    modalEnquiry.dataset.productName = product.name;
    modal.classList.add("open");
    document.body.classList.add("modal-open");
    modalClose.focus();
}

function closeProductModal() {
    modal.classList.remove("open");
    document.body.classList.remove("modal-open");
}

document.querySelectorAll(".details-button").forEach(function (button) {
    button.addEventListener("click", function () { openProductModal(button.dataset.productId); });
});

modalClose.addEventListener("click", closeProductModal);
modal.addEventListener("click", function (event) { if (event.target === modal) closeProductModal(); });
document.addEventListener("keydown", function (event) { if (event.key === "Escape" && modal.classList.contains("open")) closeProductModal(); });

modalEnquiry.addEventListener("click", function () {
    const productName = modalEnquiry.dataset.productName;
    if (productName) {
        document.getElementById("subject").value = "Product specification";
        const msgBox = document.getElementById("message");
        if (!msgBox.value.includes(productName)) {
            msgBox.value = "Enquiry regarding: " + productName + "\n" + msgBox.value;
        }
    }
    closeProductModal();
});

const backToTop = document.getElementById("backToTop");
window.addEventListener("scroll", function () {
    backToTop.classList.toggle("visible", window.scrollY > 450);
});
backToTop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

const pageSections = document.querySelectorAll("main section[id]");
const navAnchors = document.querySelectorAll(".nav-links a[href^='#']");
const sectionObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
        if (entry.isIntersecting) {
            navAnchors.forEach(function (anchor) {
                anchor.classList.toggle("active", anchor.getAttribute("href") === "#" + entry.target.id);
            });
        }
    });
}, { rootMargin: "-35% 0px -55% 0px" });
pageSections.forEach(function (section) { sectionObserver.observe(section); });

document.querySelectorAll("img").forEach(function (imageElement) {
    imageElement.addEventListener("error", function () {
        imageElement.style.opacity = "0.25";
        imageElement.alt = "Image unavailable — check internet connection";
    });
});

const enquiryCart = {};
const cartItemsBox = document.getElementById("cartItems");
const cartCountLabel = document.getElementById("cartCount");
const selectedProductsInput = document.getElementById("selectedProducts");

function renderCart() {
    const ids = Object.keys(enquiryCart);
    cartItemsBox.innerHTML = "";
    if (!ids.length) { cartItemsBox.innerHTML = "<p>Your enquiry cart is empty.</p>"; }
    ids.forEach(function(id) {
        const row = document.createElement("div");
        row.style.cssText = "display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid #dce6ec;align-items:center;flex-wrap:wrap";
        const title = document.createElement("strong"); title.textContent = enquiryCart[id].name;
        const qty = document.createElement("span"); qty.textContent = "Quantity: " + enquiryCart[id].quantity;
        const controls = document.createElement("div"); controls.style.cssText = "display:flex;gap:8px;align-items:center";
        [["−", -1], ["+", 1], ["Remove", 0]].forEach(function(pair) {
            const b = document.createElement("button");
            b.type = "button";
            b.textContent = pair[0];
            b.className = "action-btn";
            b.addEventListener("click", function() {
                if (pair[1] === 0 || enquiryCart[id].quantity + pair[1] < 1) delete enquiryCart[id];
                else enquiryCart[id].quantity += pair[1];
                renderCart();
            });
            controls.appendChild(b);
        });
        row.append(title, qty, controls);
        cartItemsBox.appendChild(row);
    });
    const total = ids.reduce((sum, id) => sum + enquiryCart[id].quantity, 0);
    cartCountLabel.textContent = total + (total === 1 ? " item selected" : " items selected");
    selectedProductsInput.value = JSON.stringify(ids.map(id => ({ id: Number(id), name: enquiryCart[id].name, quantity: enquiryCart[id].quantity })));
}

document.querySelectorAll(".add-cart-button").forEach(function(button) {
    button.addEventListener("click", function() {
        const item = PRODUCTS.find(p => Number(p.id) === Number(button.dataset.productId));
        if (!item) return;
        if (!enquiryCart[item.id]) enquiryCart[item.id] = { name: item.name, quantity: 0 };
        enquiryCart[item.id].quantity++;
        renderCart();
        document.getElementById("cart").scrollIntoView({ behavior: "smooth" });
    });
});

document.getElementById("clearCart").addEventListener("click", function() {
    Object.keys(enquiryCart).forEach(k => delete enquiryCart[k]);
    renderCart();
});
renderCart();

const contactForm = document.querySelector(".contact-form");
contactForm.addEventListener("submit", function (event) {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const message = document.getElementById("message").value.trim();
    if (!name || !email || !message) {
        event.preventDefault();
        alert("Please complete all required fields.");
    }
});

document.addEventListener("DOMContentLoaded", function () { filterProducts(); });
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------
# ADMIN DASHBOARD HTML TEMPLATES
# ---------------------------------------------------------------------

ADMIN_LOGIN_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin Login | {{ company.name }}</title>
<style>
    body { font-family: Arial, sans-serif; background: #f3f7fa; color: #1c2b3a; display: grid; place-items: center; min-height: 100vh; margin: 0; padding: 16px; }
    .box { background: #fff; border: 1px solid #dce6ec; border-radius: 10px; padding: 28px; width: min(400px, 100%); box-shadow: 0 12px 30px rgba(16,36,59,0.08); }
    h1 { margin: 0 0 8px; font-size: 1.4rem; color: #10243b; }
    p { margin: 0 0 18px; color: #687887; font-size: 0.9rem; }
    label { display: block; font-weight: bold; font-size: 0.85rem; margin-bottom: 6px; }
    input[type="password"] { width: 100%; padding: 11px; border: 1px solid #cbd8e0; border-radius: 6px; box-sizing: border-box; margin-bottom: 14px; }
    button { width: 100%; padding: 11px; border: 0; border-radius: 6px; background: #1768a5; color: #fff; font-weight: bold; cursor: pointer; }
    .flash { padding: 10px 12px; border-radius: 6px; margin-bottom: 14px; font-size: 0.85rem; }
    .flash.error { background: #fff0f0; color: #a52d36; }
    .flash.success { background: #e5f6ec; color: #16794a; }
    .back { display: inline-block; margin-top: 14px; font-size: 0.85rem; color: #1768a5; text-decoration: none; }
</style>
</head>
<body>
    <div class="box">
        <h1>Admin Login</h1>
        <p>{{ company.name }} — Enquiry Management</p>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <label for="password">Admin Password</label>
            <input type="password" id="password" name="password" required autofocus>
            <button type="submit">Sign In</button>
        </form>
        <a class="back" href="{{ url_for('home') }}">← Back to Website</a>
    </div>
</body>
</html>
"""

ADMIN_DASHBOARD_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin Dashboard | {{ company.name }}</title>
<style>
    body { font-family: Arial, sans-serif; background: #f3f7fa; color: #1c2b3a; margin: 0; padding: 24px; }
    .wrap { max-width: 1160px; margin: 0 auto; }
    .top { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; background: #10243b; color: #fff; padding: 18px 22px; border-radius: 10px; margin-bottom: 20px; }
    .top h1 { margin: 0; font-size: 1.35rem; }
    .top-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .btn { display: inline-block; padding: 9px 14px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: bold; border: 0; cursor: pointer; }
    .btn-light { background: #fff; color: #10243b; }
    .btn-danger { background: #a52d36; color: #fff; padding: 6px 10px; font-size: 0.78rem; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 20px; }
    .stat { background: #fff; border: 1px solid #dce6ec; border-radius: 8px; padding: 16px; }
    .stat strong { display: block; font-size: 1.6rem; color: #1768a5; }
    .stat span { font-size: 0.82rem; color: #687887; }
    .card { background: #fff; border: 1px solid #dce6ec; border-radius: 10px; padding: 18px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid #e3ebf0; vertical-align: top; }
    th { background: #f8fbfd; color: #10243b; }
    .items-list { margin: 0; padding-left: 16px; }
    .flash { padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 0.88rem; }
    .flash.success { background: #e5f6ec; color: #16794a; }
</style>
</head>
<body>
<div class="wrap">
    <div class="top">
        <div>
            <h1>{{ company.name }} — Admin Dashboard</h1>
        </div>
        <div class="top-actions">
            <a class="btn btn-light" href="{{ url_for('home') }}">View Website</a>
            <a class="btn btn-light" href="{{ url_for('admin_logout') }}">Logout</a>
        </div>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
    {% endwith %}

    <div class="stats">
        <div class="stat"><strong>{{ enquiries|length }}</strong><span>Total Saved Enquiries</span></div>
        <div class="stat"><strong>{{ products|length }}</strong><span>Catalogue Items</span></div>
    </div>

    <div class="card">
        {% if enquiries %}
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Date (UTC)</th>
                    <th>Customer</th>
                    <th>Contact & Location</th>
                    <th>Subject</th>
                    <th>Selected Items</th>
                    <th>Message</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for row in enquiries %}
                <tr>
                    <td>#{{ row.id }}</td>
                    <td>{{ row.created_at[:19].replace("T", " ") }}</td>
                    <td>
                        <strong>{{ row.name }}</strong><br>
                        {{ row.email }}
                    </td>
                    <td>
                        {{ row.phone }}<br>
                        {{ row.address }}, {{ row.city }}, {{ row.country }}
                    </td>
                    <td>{{ row.subject }}</td>
                    <td>
                        {% if row.parsed_items %}
                            <ul class="items-list">
                                {% for item in row.parsed_items %}
                                    <li>{{ item.name }} (Qty: {{ item.quantity }})</li>
                                {% endfor %}
                            </ul>
                        {% else %}
                            <em>None</em>
                        {% endif %}
                    </td>
                    <td style="max-width:260px;white-space:pre-wrap">{{ row.message }}</td>
                    <td>
                        <form method="POST" action="{{ url_for('delete_enquiry', enquiry_id=row.id) }}" onsubmit="return confirm('Delete this enquiry?');">
                            <button class="btn btn-danger" type="submit">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <p>No enquiries saved yet.</p>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

# ---------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        fields = {
            key: request.form.get(key, "").strip()
            for key in ["name", "email", "phone", "address", "city", "country", "subject", "message"]
        }
        selected_raw = request.form.get("selected_products", "[]")
        try:
            selected = json.loads(selected_raw)
            if not isinstance(selected, list):
                raise ValueError
        except (ValueError, TypeError):
            selected = []

        valid_ids = {int(p["id"]) for p in PRODUCTS}
        clean_items = []
        for item in selected:
            try:
                pid, qty = int(item.get("id")), int(item.get("quantity"))
                if pid in valid_ids and 1 <= qty <= 1000:
                    product = next(p for p in PRODUCTS if int(p["id"]) == pid)
                    clean_items.append({"id": pid, "name": product["name"], "quantity": qty})
            except (AttributeError, TypeError, ValueError):
                continue

        if not all(fields.values()):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("home") + "#contact")

        if (
            len(fields["name"]) > 100
            or len(fields["email"]) > 150
            or len(fields["message"]) > 3000
            or len(fields["address"]) > 300
        ):
            flash("One or more fields are too long.", "error")
            return redirect(url_for("home") + "#contact")

        db = get_db()
        db.execute(
            """
            INSERT INTO enquiries
            (created_at, name, email, phone, address, city, country, subject, selected_products, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                fields["name"],
                fields["email"],
                fields["phone"],
                fields["address"],
                fields["city"],
                fields["country"],
                fields["subject"],
                json.dumps(clean_items),
                fields["message"],
            ),
        )
        db.commit()
        db.close()

        flash("Thank you. Your enquiry has been saved successfully. The team can review it and contact you.", "success")
        return redirect(url_for("home") + "#contact")

    return render_template_string(
        PAGE,
        company=COMPANY,
        products=PRODUCTS,
        categories=CATEGORIES,
        year=datetime.now().year,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Logged in to Admin Dashboard.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid password.", "error")
    return render_template_string(ADMIN_LOGIN_PAGE, company=COMPANY)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM enquiries ORDER BY id DESC").fetchall()
    db.close()

    enquiries = []
    for r in rows:
        item_dict = dict(r)
        try:
            parsed = json.loads(item_dict.get("selected_products") or "[]")
            item_dict["parsed_items"] = parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            item_dict["parsed_items"] = []
        enquiries.append(item_dict)

    return render_template_string(
        ADMIN_DASHBOARD_PAGE,
        company=COMPANY,
        products=PRODUCTS,
        enquiries=enquiries,
    )


@app.route("/admin/delete/<int:enquiry_id>", methods=["POST"])
@admin_required
def delete_enquiry(enquiry_id):
    db = get_db()
    db.execute("DELETE FROM enquiries WHERE id = ?", (enquiry_id,))
    db.commit()
    db.close()
    flash(f"Enquiry #{enquiry_id} deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/health")
def health():
    return {
        "status": "ok",
        "website": COMPANY["name"],
        "catalogue_items": len(PRODUCTS),
    }


@app.errorhandler(404)
def page_not_found(error):
    return (
        "<h1>Page not found</h1>"
        "<p>The page you requested does not exist.</p>"
        '<p><a href="/">Return to website</a></p>',
        404,
    )


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
