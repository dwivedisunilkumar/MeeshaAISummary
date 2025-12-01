import streamlit as st
import pdfplumber
import re
from jinja2 import Environment, BaseLoader
import os
import pdfkit
from pypdf import PdfWriter, PdfReader
import tempfile
from datetime import datetime
import pandas as pd
import numpy as np
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Meesha Diagnostics AI", page_icon="🩺", layout="wide")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DB_FILENAME = "test_and_values.csv"

# --- HELPER: IMAGE TO BASE64 ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- VISUALLY STUNNING HTML TEMPLATE (PREMIUM EDITION) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Meesha Health Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            /* REFINED PALETTE */
            --brand: #00BBD4; 
            --brand-dark: #00838f;
            --brand-soft: #e0f7fa;
            
            --dark: #1e293b; 
            --text: #334155; 
            --text-light: #64748b;
            
            --bg-page: #f8fafc;
            --card-bg: #ffffff;
            
            --danger: #ef4444; --danger-soft: #fef2f2;
            --warning: #f59e0b; --warning-soft: #fffbeb;
            --success: #10b981; --success-soft: #f0fdf4;
        }

        body { font-family: 'Outfit', sans-serif; margin: 0; padding: 0; background: var(--bg-page); color: var(--text); }
        .page { width: 210mm; min-height: 297mm; padding: 12mm 15mm; margin: 0 auto; background: white; position: relative; overflow: hidden; box-sizing: border-box; }

        /* HEADER - CLEAN & PREMIUM */
        .header { 
            display: flex; justify-content: space-between; align-items: center; 
            padding-bottom: 25px; border-bottom: 2px solid #f1f5f9; margin-bottom: 35px; 
        }
        
        .logo-container { display: flex; align-items: center; gap: 15px; }
        .logo-img { height: 65px; width: auto; object-fit: contain; } /* Optimized for new logo */
        
        .header-meta { text-align: right; }
        .report-title { font-size: 10px; font-weight: 800; color: var(--brand); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }
        .report-date { font-size: 12px; font-weight: 600; color: var(--text-light); }

        /* MAIN LAYOUT GRID */
        .main-grid { display: grid; grid-template-columns: 1.8fr 1.2fr; gap: 30px; }
        .left-col { display: flex; flex-direction: column; gap: 25px; }
        .right-col { display: flex; flex-direction: column; gap: 25px; }

        /* CARD COMPONENT */
        .card { 
            background: white; border-radius: 16px; padding: 24px; 
            box-shadow: 0 10px 30px -5px rgba(0,0,0,0.04); border: 1px solid #f1f5f9;
            position: relative; overflow: hidden;
        }
        
        .card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
        .card-title { font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .card-icon { color: var(--brand); font-size: 14px; }

        /* PATIENT PROFILE - ELEGANT GRID */
        .profile-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .profile-item { }
        .pi-label { font-size: 9px; color: var(--text-light); font-weight: 600; text-transform: uppercase; margin-bottom: 3px; }
        .pi-value { font-size: 14px; font-weight: 700; color: var(--dark); }

        /* AI SUMMARY - HIGHLIGHT BOX */
        .summary-card { 
            background: linear-gradient(135deg, #ffffff 0%, #f8fdfe 100%); 
            border: 1px solid #e0f2fe; position: relative;
        }
        .summary-card::before {
            content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; 
            background: var(--brand); border-radius: 4px 0 0 4px;
        }
        .summary-text { font-size: 13px; line-height: 1.7; color: var(--text); font-weight: 400; }
        
        /* Text Highlights */
        .hl-crit { color: var(--danger); font-weight: 700; }
        .hl-brand { color: var(--brand-dark); font-weight: 700; }

        /* IMPACT ZONES - MODERN CARDS */
        .zone-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .zone-box { 
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; 
            padding: 12px; display: flex; align-items: center; gap: 12px; transition: 0.2s;
        }
        .zone-box.active { 
            background: #fff5f5; border-color: #fecaca; 
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.08); 
        }
        
        .z-icon { 
            width: 36px; height: 36px; background: white; border-radius: 10px; 
            display: flex; align-items: center; justify-content: center; font-size: 18px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03); filter: grayscale(100%); opacity: 0.5;
        }
        .zone-box.active .z-icon { filter: grayscale(0%); opacity: 1; background: #fee2e2; }
        
        .z-label { font-size: 11px; font-weight: 700; color: var(--text-light); }
        .zone-box.active .z-label { color: var(--danger); }

        /* CRITICAL METRICS - GAUGES */
        .alert-card { 
            background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px; 
            border: 1px solid #f1f5f9; border-left: 4px solid transparent;
        }
        .alert-card.crit { border-left-color: var(--danger); background: var(--danger-soft); }
        .alert-card.warn { border-left-color: var(--warning); background: var(--warning-soft); }
        
        .ac-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .ac-name { font-size: 12px; font-weight: 700; color: var(--dark); }
        .ac-pill { font-size: 9px; font-weight: 800; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; background: white; }
        .crit .ac-pill { color: var(--danger); box-shadow: 0 2px 4px rgba(239, 68, 68, 0.1); }
        .warn .ac-pill { color: #b45309; box-shadow: 0 2px 4px rgba(245, 158, 11, 0.1); }
        
        .ac-data { display: flex; align-items: baseline; gap: 6px; }
        .ac-val { font-size: 18px; font-weight: 800; color: var(--dark); }
        .ac-ref { font-size: 10px; color: var(--text-light); }
        
        /* TABLE - CLEAN DESIGN */
        .table-wrap { margin-top: 15px; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { text-align: left; padding: 12px 16px; background: #f8fafc; color: var(--text-light); font-weight: 700; text-transform: uppercase; font-size: 10px; border-bottom: 1px solid #e2e8f0; }
        td { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; color: var(--dark); font-weight: 500; }
        tr:last-child td { border-bottom: none; }
        
        .row-crit { background: #fffbfb; }
        
        .status-dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
        .s-crit { background: var(--danger); }
        .s-warn { background: var(--warning); }
        .s-norm { background: var(--success); }

        .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #f1f5f9; text-align: center; font-size: 10px; color: #cbd5e1; font-weight: 500; letter-spacing: 0.5px; }
    </style>
</head>
<body>

<div class="page">
    
    <!-- HEADER -->
    <div class="header">
        <div class="logo-container">
            {% if logo_b64 %}
                <img src="data:image/png;base64,{{ logo_b64 }}" class="logo-img" alt="Meesha Logo">
            {% else %}
                <h1 style="color:var(--brand); margin:0;">MEESHA</h1>
            {% endif %}
        </div>
        <div class="header-meta">
            <div class="report-title">AI Clinical Analysis</div>
            <div class="report-date">{{ report_date }}</div>
        </div>
    </div>

    <!-- MAIN GRID -->
    <div class="main-grid">
        
        <!-- LEFT COLUMN -->
        <div class="left-col">
            
            <!-- 1. PATIENT PROFILE -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">👤</span>
                    <span class="card-title">Patient Profile</span>
                </div>
                <div class="profile-grid">
                    <div class="profile-item">
                        <div class="pi-label">Patient Name</div>
                        <div class="pi-value">{{ patient_name }}</div>
                    </div>
                    <div class="profile-item">
                        <div class="pi-label">Patient ID</div>
                        <div class="pi-value">{{ patient_id }}</div>
                    </div>
                    <div class="profile-item">
                        <div class="pi-label">Age / Gender</div>
                        <div class="pi-value">{{ patient_age_gender }}</div>
                    </div>
                    <div class="profile-item">
                        <div class="pi-label">Referred By</div>
                        <div class="pi-value">{{ doctor_name }}</div>
                    </div>
                </div>
            </div>

            <!-- 2. AI SUMMARY -->
            <div class="card summary-card">
                <div class="card-header">
                    <span class="card-icon">🤖</span>
                    <span class="card-title" style="color:var(--brand-dark);">Clinical Insight</span>
                </div>
                <div class="summary-text">
                    {{ narrative }}
                </div>
            </div>

            <!-- 3. COMPREHENSIVE TABLE -->
            <div style="margin-top:10px;">
                <div class="card-title" style="margin-bottom:10px; padding-left:5px;">📊 Comprehensive Test List</div>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th width="45%">Test Name</th>
                                <th width="25%">Result</th>
                                <th width="30%">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for test in full_results %}
                            <tr class="{% if 'Crit' in test.status %}row-crit{% endif %}">
                                <td>{{ test.name }}</td>
                                <td>
                                    <strong>{{ test.value }}</strong> 
                                    <span style="font-size:9px; color:#94a3b8; margin-left:4px;">(Ref: {{ test.range }})</span>
                                </td>
                                <td>
                                    {% if 'Crit' in test.status %}
                                        <span style="color:var(--danger); font-weight:700; font-size:10px;"><span class="status-dot s-crit"></span>CRITICAL</span>
                                    {% elif 'Normal' in test.status %}
                                        <span style="color:var(--success); font-weight:700; font-size:10px;"><span class="status-dot s-norm"></span>NORMAL</span>
                                    {% else %}
                                        <span style="color:var(--warning); font-weight:700; font-size:10px;"><span class="status-dot s-warn"></span>ABNORMAL</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <!-- RIGHT COLUMN -->
        <div class="right-col">
            
            <!-- 4. IMPACT ZONES -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">⚡</span>
                    <span class="card-title">Impact Zones</span>
                </div>
                <div class="zone-grid">
                    <div class="zone-box {% if 'heart' in body_flags %}active{% endif %}">
                        <div class="z-icon">🫀</div>
                        <div class="z-label">Heart</div>
                    </div>
                    <div class="zone-box {% if 'liver' in body_flags %}active{% endif %}">
                        <div class="z-icon">🧪</div>
                        <div class="z-label">Liver</div>
                    </div>
                    <div class="zone-box {% if 'kidney' in body_flags %}active{% endif %}">
                        <div class="z-icon">💧</div>
                        <div class="z-label">Kidney</div>
                    </div>
                    <div class="zone-box {% if 'blood' in body_flags %}active{% endif %}">
                        <div class="z-icon">🩸</div>
                        <div class="z-label">Blood</div>
                    </div>
                    <div class="zone-box {% if 'bone' in body_flags %}active{% endif %}">
                        <div class="z-icon">🦴</div>
                        <div class="z-label">Bone</div>
                    </div>
                    <div class="zone-box {% if 'neuro' in body_flags %}active{% endif %}">
                        <div class="z-icon">🧠</div>
                        <div class="z-label">Neuro</div>
                    </div>
                </div>
            </div>

            <!-- 5. CRITICAL FINDINGS -->
            {% if critical_tests %}
            <div class="card" style="border-color: var(--danger-soft);">
                <div class="card-header">
                    <span class="card-icon" style="color:var(--danger);">⚠️</span>
                    <span class="card-title" style="color:var(--danger);">Action Required</span>
                </div>
                
                {% for test in critical_tests %}
                <div class="alert-card {% if 'Crit' in test.status %}crit{% else %}warn{% endif %}">
                    <div class="ac-head">
                        <span class="ac-name">{{ test.name }}</span>
                        <span class="ac-pill">{{ test.status }}</span>
                    </div>
                    <div class="ac-data">
                        <span class="ac-val">{{ test.value }}</span>
                        <span class="ac-ref">Ref: {{ test.range }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

        </div>
    </div>

    <div class="footer">
        Generated by Meesha Diagnostics AI • This summary is for informational support only.
    </div>
</div>

</body>
</html>
"""

# --- UTILITY FUNCTIONS ---

def get_wkhtmltopdf_config():
    """Locates the PDF engine."""
    possible_paths = [
        r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
        r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return pdfkit.configuration(wkhtmltopdf=path)
    return None

def load_reference_db(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.lower().str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading CSV database: {e}")
        return None

def determine_age_gender_nums(age_gender_str):
    try:
        age = 30; sex = 'Both'
        age_match = re.search(r"(\d{1,3})", age_gender_str)
        if age_match: age = int(age_match.group(1))
        if 'female' in age_gender_str.lower() or ' f ' in age_gender_str.lower(): sex = 'Female'
        elif 'male' in age_gender_str.lower() or ' m ' in age_gender_str.lower(): sex = 'Male'
        return age, sex
    except: return 30, 'Both'

def get_status(value, low, high):
    try:
        val = float(value); l = float(low); h = float(high)
        if val < l:
            if val < (l * 0.7): return "Crit Low", "crit"
            return "Low", "warn"
        elif val > h:
            if val > (h * 1.3): return "Crit High", "crit"
            return "High", "warn"
        return "Normal", "norm"
    except: return "Normal", "norm"

def map_body_impact(abnormal_tests):
    flags = []
    mappings = {
        'liver': ['liver', 'sgot', 'sgpt', 'bilirubin', 'alkaline', 'ggt'],
        'kidney': ['kidney', 'creatinine', 'urea', 'uric', 'bun', 'protein'],
        'heart': ['cholesterol', 'triglyceride', 'hdl', 'ldl', 'lipid', 'cardio'],
        'blood': ['haemoglobin', 'hemoglobin', 'rbc', 'wbc', 'platelet', 'mcv', 'mch'],
        'bone': ['calcium', 'vitamin d', 'vit d', 'phosphate', 'rheumatoid'],
        'neuro': ['b12', 'thyroid', 'tsh', 't3', 't4']
    }
    for test in abnormal_tests:
        name = test['name'].lower()
        for zone, keywords in mappings.items():
            if any(k in name for k in keywords):
                if zone not in flags: flags.append(zone)
    return flags

def extract_comprehensive_data(pdf_path, csv_path):
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt: full_text += txt + "\n"
    except: pass
    
    if not full_text.strip():
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        except: pass

    info = {"patient_name": "Unknown", "patient_id": "Unknown", "age_gender": "Unknown", "doctor": "Unknown", "date": "Unknown"}
    
    # Regex Extractions
    name_match = re.search(r"(?:Patient\s*Name|Name)\s*[:\-\.]?\s*(Mrs\.|Mr\.|Ms\.)?\s*([A-Za-z\s\.]+)", full_text, re.IGNORECASE)
    if name_match: info["patient_name"] = name_match.group(0).replace("Patient Name", "").replace(":","").strip()
    
    id_match = re.search(r"(?:Patient\s*Id|Id|ID|Treatment\s*id)\s*[:\-\.]?\s*(\d+)", full_text, re.IGNORECASE)
    if id_match: info["patient_id"] = id_match.group(1)
    
    age_match = re.search(r"(\d{1,3})\s*[Yy]?\w*\s*[\/\-]\s*(Male|Female|M|F)", full_text, re.IGNORECASE)
    if age_match: info["age_gender"] = f"{age_match.group(1)} Y / {age_match.group(2)}"
    
    doc_match = re.search(r"(?:Ref\.?\s*By|Referred\s*By|Dr)\s*[:\-\.]?\s*(Dr\.?[A-Za-z\s\.]+)", full_text, re.IGNORECASE)
    if doc_match: info["doctor"] = doc_match.group(1).strip()
    
    date_match = re.search(r"(?:Registered|Reported|Date)\s*(?:On)?\s*[:\-\.]?\s*(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{2,4})", full_text, re.IGNORECASE)
    if date_match: info["date"] = date_match.group(1)

    df = load_reference_db(csv_path)
    if df is None: return info, []

    p_age, p_sex = determine_age_gender_nums(info["age_gender"])
    found_tests = []
    unique_tests = df['testname'].unique()
    
    for test_name in unique_tests:
        safe_name = re.escape(test_name)
        pattern = rf"{safe_name}[^0-9\n]*?(\d+\.?\d*)"
        
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                val_str = match.group(1)
                value = float(val_str)
                
                if ("Haemoglobin" in test_name or "Hemoglobin" in test_name) and value < 3.0:
                     continue 

                test_rows = df[df['testname'] == test_name]
                ref_row = test_rows.iloc[0] 
                for _, row in test_rows.iterrows():
                    if row['fromage'] <= p_age <= row['toage']:
                        if row['sextype'] == 'Both' or row['sextype'].lower() == p_sex.lower():
                            ref_row = row
                            break
                
                low = ref_row['lowvalue']; high = ref_row['uppervalue']
                status_txt, css = get_status(value, low, high)
                
                found_tests.append({
                    "name": test_name, "value": value, "range": f"{low} - {high}",
                    "status": status_txt, "css_class": css
                })
            except: continue

    return info, found_tests

def generate_safe_summary(info, results):
    """Generates a summary WITHOUT specific numeric values to avoid errors."""
    abnormal_tests = [t for t in results if t['status'] != "Normal"]
    
    if not abnormal_tests:
        return "✅ <span class='hl-brand'>All Systems Stable.</span> Comprehensive review shows all extracted biomarkers are within optimal ranges."
    
    crit = [t for t in abnormal_tests if "Crit" in t['status']]
    warn = [t for t in abnormal_tests if "Crit" not in t['status']]
    
    lines = []
    if crit:
        names = ", ".join([f"<b>{t['name']}</b>" for t in crit])
        lines.append(f"<span class='hl-crit'>CRITICAL ALERT:</span> Severe deviations found in {names}. Immediate clinical review is strongly recommended.")
    
    if warn:
        names = ", ".join([t['name'] for t in warn[:4]])
        count_rest = len(warn) - 4
        suffix = f" and {count_rest} others" if count_rest > 0 else ""
        lines.append(f"<b>Observation:</b> Mild variations detected in {names}{suffix}. These may require routine monitoring or lifestyle adjustments.")
        
    return "<br><br>".join(lines)

# --- MAIN APP ---
def main():
    st.title("🩺 Meesha Diagnostics")
    st.subheader("AI Report Generator (Premium Edition)")
    
    db_path = os.path.join(SCRIPT_DIR, CSV_DB_FILENAME)
    if not os.path.exists(db_path):
        st.error(f"❌ Database not found: {CSV_DB_FILENAME}")
        st.stop()

    # UPDATED LOGO LOOKUP: Priority to 'image_0e9cfc.png'
    logo_candidates = ["image_0e9cfc.png", "meesha_logo.jpg", "jpeg meesha.jpeg", "image_0ff9db.png"]
    logo_b64 = None
    for cand in logo_candidates:
        cand_path = os.path.join(SCRIPT_DIR, cand)
        if os.path.exists(cand_path):
            logo_b64 = get_base64_image(cand_path)
            break

    uploaded_file = st.file_uploader("Upload Patient Report (PDF)", type="pdf")

    if uploaded_file is not None:
        config = get_wkhtmltopdf_config()
        if not config:
            st.error("❌ 'wkhtmltopdf' not found.")
            st.stop()
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(uploaded_file.getvalue())
            temp_pdf_path = tmp_pdf.name

        st.info("🔍 Analyzing biomarkers...")
        
        try:
            info, full_results = extract_comprehensive_data(temp_pdf_path, db_path)
            if info['date'] == "Unknown": info['report_date'] = datetime.now().strftime("%d-%m-%Y")
            else: info['report_date'] = info['date']

            narrative = generate_safe_summary(info, full_results)
            abnormal_tests = [t for t in full_results if t['status'] != "Normal"]
            body_flags = map_body_impact(abnormal_tests)
            
            st.success(f"✅ Analysis Complete: {len(full_results)} tests found.")
            
            with st.expander("📄 View Summary Preview"):
                st.markdown(narrative, unsafe_allow_html=True)

            env = Environment(loader=BaseLoader())
            template = env.from_string(HTML_TEMPLATE)
            
            html_output = template.render(
                patient_name=info["patient_name"],
                patient_id=info["patient_id"],
                patient_age_gender=info["age_gender"],
                doctor_name=info["doctor"],
                report_date=info["report_date"],
                narrative=narrative,
                full_results=full_results,
                critical_tests=abnormal_tests,
                body_flags=body_flags,
                logo_b64=logo_b64
            )
            
            temp_summary_path = temp_pdf_path.replace(".pdf", "_summary.pdf")
            options = {
                'page-size': 'A4', 'margin-top': '0mm', 'margin-right': '0mm', 
                'margin-bottom': '0mm', 'margin-left': '0mm', 'enable-local-file-access': None
            }
            pdfkit.from_string(html_output, temp_summary_path, configuration=config, options=options)

            final_output_path = temp_pdf_path.replace(".pdf", "_final.pdf")
            merger = PdfWriter()
            merger.append(temp_summary_path)
            merger.append(temp_pdf_path)
            merger.write(final_output_path)
            merger.close()

            with open(final_output_path, "rb") as f:
                final_pdf_bytes = f.read()

            file_label = f"Meesha_Analysis_{info['patient_name'].replace(' ', '_')}.pdf"
            st.download_button("📥 Download Report", final_pdf_bytes, file_name=file_label, mime="application/pdf")

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.text(traceback.format_exc())
            
        finally:
            try:
                if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)
                if os.path.exists(temp_summary_path): os.remove(temp_summary_path)
                if os.path.exists(final_output_path): os.remove(final_output_path)
            except: pass

if __name__ == "__main__":
    main()
