# AI Resume Screening System — Frontend + Backend

## Requirements
Python 3.10+ and a browser.

## Run (Windows VS Code terminal)
```powershell
cd AI_Resume_Fullstack
py -m pip install -r requirements.txt
py app.py
```
Open http://127.0.0.1:5000 in Chrome. **Do not open index.html directly**; the backend must be running.

## Included
- Frontend: `index.html`, `style.css`, `script.js` (same visual theme as supplied reference)
- Backend: Flask `app.py`, SQLite `screening.db` created on first run
- Uploaded PDFs stored in `uploads/` (created on first run)
- PDF text extraction via pypdf; job-description vs resume recognized skill-keyword matching
- Dashboard, job setup, upload, candidates, candidate details, reports, CSV export, previous/next and dashboard navigation

## Important limitations
This is an **educational prototype**, not a production-ready hiring platform. It does **not** use a trained AI model. Scores are transparent keyword-overlap percentages and are not reliable hiring assessments. No authentication, authorization, malware scanning, privacy safeguards, or production deployment configuration are included. Do not upload real candidates' personal data or use it for employment decisions. Text-only PDFs are supported; scanned PDFs need OCR. If no skill is recognized in the job description, the score shows 0 (unavailable).
