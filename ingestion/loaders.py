import sqlite3
from datetime import datetime
from .cleaner import strip_html
from config import settings

def get_conn():
    return sqlite3.connect(settings.SQLITE_PATH)



# ── Each loader returns list of dicts ──────────────────────

def load_faqs() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT id, question, answer FROM faq_faq").fetchall()
    conn.close()
    chunks = []
    for id, question, answer in rows:
        # FAQ is already atomic — Q+A together as one chunk
        text = f"Question: {question}\nAnswer: {strip_html(answer)}"
        chunks.append({
            "text": text,
            "source_table": "faq",
            "source_id": id,
            "title": question,
            "category": "faq",
            "date": None,
            "url": None
        })
    return chunks


def load_members() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.id, m.full_name, m.position, m.email, 
               m.cell, m.phone_number, m.type,
               d.name as department, v.name as division
        FROM members_members m
        LEFT JOIN members_memberdepartment d ON m.department_id = d.id
        LEFT JOIN members_memberdivision v ON m.division_id = v.id
    """).fetchall()
    conn.close()
    chunks = []
    for row in rows:
        id, name, position, email, cell, phone, mtype, dept, div = row
        # Build natural language sentence — best for retrieval
        text = f"{name} is {position}"
        if dept: text += f" in the {dept} department"
        if div:  text += f", {div} division"
        if email: text += f". Email: {email}"
        if cell:  text += f". Cell: {cell}"
        if phone: text += f". Phone: {phone}"
        text += f". Type: {mtype}."
        chunks.append({
            "text": text,
            "source_table": "members",
            "source_id": id,
            "title": name,
            "category": "contact",
            "date": None,
            "url": None
        })
    return chunks


def load_admissions() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, is_open, start_date, end_date, link
        FROM admission_admissionopen
    """).fetchall()
    conn.close()
    chunks = []
    for id, title, is_open, start, end, link in rows:
        status = "currently open" if is_open else "closed"
        text = f"Admission: {title}. Status: {status}."
        if start: text += f" Start date: {start}."
        if end:   text += f" End date: {end}."
        if link:  text += f" Link: {link}"
        chunks.append({
            "text": text,
            "source_table": "admission",
            "source_id": id,
            "title": title,
            "category": "admission",
            "date": start,
            "url": link
        })
    return chunks


def load_notices() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, description, created_at
        FROM notice_management_notice
    """).fetchall()
    conn.close()
    chunks = []
    for id, title, desc, created in rows:
        text = f"Notice: {title}. {strip_html(desc)}"
        chunks.append({
            "text": text,
            "source_table": "notice",
            "source_id": id,
            "title": title,
            "category": "notice",
            "date": created,
            "url": None
        })
    return chunks


def load_events_news() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, description, created_at, event_date
        FROM event_or_news_management_event_or_news
    """).fetchall()
    conn.close()
    chunks = []
    for id, title, desc, created, event_date in rows:
        text = f"Event/News: {title}. {strip_html(desc)}"
        if event_date: text += f" Date: {event_date}."
        chunks.append({
            "text": text,
            "source_table": "event_news",
            "source_id": id,
            "title": title,
            "category": "event_news",
            "date": event_date or created,
            "url": None
        })
    return chunks


def load_cpd_resources() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, title, description, created_at
        FROM cpd_resources_cpdresource
    """).fetchall()
    conn.close()
    chunks = []
    for id, title, desc, created in rows:
        text = f"CPD Resource: {title}. {strip_html(desc)}"
        chunks.append({
            "text": text,
            "source_table": "cpd",
            "source_id": id,
            "title": title,
            "category": "cpd",
            "date": created,
            "url": None
        })
    return chunks


def load_all() -> list[dict]:
    """Master loader — add new loaders here as needed."""
    loaders = [
        load_faqs,
        load_members,
        load_admissions,
        load_notices,
        load_events_news,
        load_cpd_resources,
    ]
    all_chunks = []
    for loader in loaders:
        try:
            chunks = loader()
            all_chunks.extend(chunks)
            print(f" {loader.__name__}: {len(chunks)} chunks")
        except Exception as e:
            print(f" {loader.__name__} failed: {e}")
    print(f" Total chunks: {len(all_chunks)}")
    return all_chunks