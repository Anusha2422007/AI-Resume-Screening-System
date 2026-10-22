from flask import Flask, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from pathlib import Path
import sqlite3, re, json, io, csv, os

ROOT=Path(__file__).resolve().parent
UPLOADS=ROOT/'uploads'; UPLOADS.mkdir(exist_ok=True)
DB=ROOT/'screening.db'
app=Flask(__name__,static_folder=None)
app.config['MAX_CONTENT_LENGTH']=10*1024*1024*10
SKILLS=['Python','Java','JavaScript','TypeScript','React','Angular','Vue','HTML','CSS','SQL','MySQL','PostgreSQL','MongoDB','Node.js','Express','Flask','Django','FastAPI','AWS','Azure','Docker','Kubernetes','Linux','Git','Machine Learning','Data Analysis','Excel','Pandas','NumPy','Power BI','Tableau','TensorFlow','PyTorch','REST API','Communication','Problem Solving','Spring Boot','C++','C#','Figma']
ALIASES={'Node.js':r'node\.?js','REST API':r'rest(?:ful)?\s+api','C++':r'c\+\+','C#':r'c#','SQL':r'(?<![a-z])sql(?![a-z])'}
def extract_skills(text):
    return [s for s in SKILLS if re.search(ALIASES.get(s,r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])'),text,re.I)]
def connect():
    db=sqlite3.connect(DB);db.row_factory=sqlite3.Row;return db
def init():
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, role TEXT, score INTEGER, skills TEXT, missing TEXT, location TEXT, experience TEXT, filename TEXT, original_name TEXT, summary TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
        db.execute('CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
init()
def serialize(r):
    d=dict(r);d['skills']=json.loads(d['skills']);d['missing']=json.loads(d['missing']);return d
@app.get('/')
def home():return send_from_directory(ROOT,'index.html')
@app.get('/<path:path>')
def assets(path):
    if path in ('script.js','style.css'):return send_from_directory(ROOT,path)
    return ('Not found',404)
@app.get('/api/candidates')
def candidates():
    with connect() as db: return jsonify([serialize(r) for r in db.execute('SELECT * FROM candidates ORDER BY id DESC')])
@app.post('/api/screen')
def screen():
    title=request.form.get('title','').strip();desc=request.form.get('description','').strip()
    files=request.files.getlist('resumes')
    if not title or not desc or not files:return jsonify(error='Job title, description, and PDF files are required.'),400
    if len(files)>20:return jsonify(error='Maximum 20 PDFs per batch.'),400
    required=extract_skills(desc)
    created=[]
    with connect() as db:
        db.execute('INSERT INTO jobs(title,description) VALUES (?,?)',(title,desc))
        for f in files:
            original=secure_filename(f.filename or '')
            if not original.lower().endswith('.pdf'):return jsonify(error='PDF files only.'),400
            data=f.read()
            if len(data)>10*1024*1024:return jsonify(error='Each PDF must be under 10 MB.'),400
            if not data.startswith(b'%PDF'):return jsonify(error='Invalid PDF file.'),400
            try:
                reader=PdfReader(io.BytesIO(data));text='\n'.join(page.extract_text() or '' for page in reader.pages[:30])
            except Exception:return jsonify(error=f'Could not read {original}.'),400
            if not text.strip():return jsonify(error=f'{original} contains no extractable text (scanned PDFs require OCR).'),400
            found=extract_skills(text);matched=[s for s in required if s in found];missing=[s for s in required if s not in found]
            score=round(100*len(matched)/len(required)) if required else 0
            name=Path(original).stem.replace('_',' ').replace('-',' ').strip()
            # Deterministic keyword overlap, not a trained AI model or hiring recommendation.
            summary=f'Matched {len(matched)} of {len(required)} recognized job-description skills. Keyword matching only; manually review every resume.' if required else 'No recognized skills in the job description; score is unavailable (shown as 0).'
            cur=db.execute('INSERT INTO candidates(name,role,score,skills,missing,location,experience,filename,original_name,summary) VALUES (?,?,?,?,?,?,?,?,?,?)',(name,title,score,json.dumps(found),json.dumps(missing),'Not provided','Not verified','',original,summary))
            ident=cur.lastrowid;stored=f'{ident}.pdf';(UPLOADS/stored).write_bytes(data)
            db.execute('UPDATE candidates SET filename=? WHERE id=?',(stored,ident));created.append(ident)
    return jsonify(created=created,count=len(created),method='transparent keyword skill matching')
@app.get('/api/resumes/<int:ident>')
def resume(ident):
    with connect() as db:r=db.execute('SELECT filename,original_name FROM candidates WHERE id=?',(ident,)).fetchone()
    if not r:return jsonify(error='Not found'),404
    return send_from_directory(UPLOADS,r['filename'],as_attachment=True,download_name=r['original_name'])
@app.get('/api/export')
def export():
    output=io.StringIO();w=csv.writer(output);w.writerow(['Name','Role','Score','Skills','Missing Skills','Summary'])
    with connect() as db:
        for r in db.execute('SELECT * FROM candidates ORDER BY id DESC'):
            c=serialize(r);w.writerow([c['name'],c['role'],c['score'],'; '.join(c['skills']),'; '.join(c['missing']),c['summary']])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=candidates.csv'})
if __name__=='__main__':app.run(debug=True,port=5000)
