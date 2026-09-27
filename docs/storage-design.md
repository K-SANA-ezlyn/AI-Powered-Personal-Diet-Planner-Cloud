# Cloud Storage Design

## Cloud Database vs Cloud Object Storage — the distinction the project demonstrates

| | Cloud **Database** (Postgres/SQLite) | Cloud **Object Storage** (Supabase Storage / S3-like) |
|---|---|---|
| Data shape | structured rows, typed columns | unstructured blobs (bytes) |
| Access pattern | queries, joins, filters, aggregations | put/get/delete by key |
| Scaling model | vertical + read replicas | horizontal to petabytes, essentially unlimited |
| Cost profile | pricier per GB | very cheap per GB |
| Served via | SQL over a connection | HTTPS object URLs / signed URLs / CDNs |
| In this project | users, profiles, diet_plans, file metadata | meal photos, food-log CSVs, exports |

**Why the split matters:** storing blobs in the DB bloats backups, slows
queries, and costs more. Storing structured relationships in files loses
transactions, indexing and concurrent access. Correct separation is a
first-class learning outcome of this project.

## Bucket layout

```text
meals/
└── {user_id}/
    └── {uuid8}_{safe_filename}
        e.g. meals/9f3c…ab/4d1e7f02_meal_photo.png
```

* **user-scoped prefix** mirrors the DB ownership model and makes per-user
  lifecycle rules (exports, cleanup) trivial.
* **UUID segment** prevents collisions and overwrites between uploads.
* **`safe_filename`** strips path components (`../../etc/passwd` becomes a
  flat name) — blocks path traversal at the key-construction layer.
* Local provider additionally re-validates the resolved path against its
  root (`_full()` defence-in-depth).

## Providers (same interface, chosen by env)

```python
StorageProvider (ABC)
├── LocalStorageProvider     # STORAGE_PROVIDER=local    -> uploads/ folder
└── SupabaseStorageProvider  # STORAGE_PROVIDER=supabase -> private bucket
```

| Operation | Local mode | Cloud mode (Supabase) |
|---|---|---|
| Upload | write bytes under `UPLOAD_DIR` | `POST /object/{bucket}/{path}` with service key |
| Download | read file | `GET /object/{bucket}/{path}` — or a **300-second signed URL** issued only after authorization |
| Delete | unlink file | `DELETE /object/{bucket}/{path}` |
| Health probe | write+remove `.health` file | upload+delete a probe object |

## Security properties

1. **Private bucket.** The cloud bucket allows no public reads or writes.
   The backend uploads with the service-role key; users never receive
   storage credentials.
2. **Authorized downloads only.** `GET /api/files/{id}/download` first checks
   the metadata row's owner against the JWT; only then are bytes streamed
   (or a short-lived signed URL minted in cloud mode).
3. **No object keys from clients.** Keys are constructed server-side from the
   authenticated user id + UUID; client input contributes only a sanitized
   filename.
4. **Upload validation before storage.** Extension whitelist → size limit →
   magic-byte sniffing; a `.exe` renamed `meal.jpg` is rejected with 415.
5. **Orphan prevention.** If the metadata insert fails after the object was
   stored, the route deletes the just-uploaded object (storage-first with
   compensating cleanup — see `failure-handling.md`).

## What is stored where — quick answer

```text
POST /api/files/upload (meal.png, 800 KB)
  ├── 800 KB  -> object storage:  meals/{user_id}/{uuid}_meal.png
  └── ~150 B  -> cloud database:  user_files row (id, user_id, filename,
                                    storage_path, content_type, size, time)
```

Listing files = one indexed DB query (fast). Downloading = one DB row + one
object GET. Deleting = both, object first (best effort) then the row.
