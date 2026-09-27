# Screenshots — Proof Checklist

Capture these while the app runs (local or deployed). Professional filenames
keep the repo recruiter-ready. Store PNGs here with exactly these names.

| # | Filename | What to capture | What it proves |
|---|---|---|---|
| 01 | `01-project-folder-structure.png` | IDE/tree of the repo | modular, industry-style layout |
| 02 | `02-cloud-architecture-diagram.png` | `docs/architecture.md` diagram | system design skill |
| 03 | `03-registration-page.png` | register form empty | auth flow exists |
| 04 | `04-registration-success.png` | redirect to profile with welcome box | account creation works |
| 05 | `05-login-page.png` | login form (+ demo button) | credential access |
| 06 | `06-user-profile-form.png` | profile filled with choices | profile collection |
| 07 | `07-profile-saved-success.png` | success box after save | persistence via cloud DB |
| 08 | `08-diet-preference-selection.png` | diet/goal chips selected | personalization inputs |
| 09 | `09-plan-generation-page.png` | generate page before clicking | generation UX |
| 10 | `10-generated-diet-plan.png` | full plan card incl. engine badge + disclaimer | AI engine output + honest framing |
| 11 | `11-plan-saved-success.png` | "Saved to your cloud dashboard!" | save path works |
| 12 | `12-saved-plans-list.png` | saved-plans grid | retrieval of stored plans |
| 13 | `13-cloud-database-record.png` | Supabase Table Editor → diet_plans row | cloud database in action |
| 14 | `14-cloud-storage-object.png` | Supabase Storage → bucket object | object storage in action |
| 15 | `15-file-upload-page.png` | cloud-files page with picker | object storage UI |
| 16 | `16-file-upload-success.png` | success + table row | upload accepted after validation |
| 17 | `17-file-download-roundtrip.png` | downloaded file opens, bytes match | authorized download works |
| 18 | `18-user-dashboard.png` | full dashboard | aggregation + personalization |
| 19 | `19-api-swagger-docs.png` | /docs endpoint list | documented REST API |
| 20 | `20-health-probes-response.png` | the three /api/health* JSONs | monitoring readiness |
| 21 | `21-automated-tests-passing.png` | `pytest -v` green tail | quality discipline |
| 22 | `22-ci-pipeline-green.png` | GitHub Actions green check | CI/CD works |
| 23 | `23-deployed-app-live.png` | dashboard on the Vercel URL | real cloud deployment |

Tips: use the browser at 100% zoom, full-window (not tiny), and crop browser
chrome. For 13/14, blur any keys visible in the Supabase dashboard.
