# URL Shortener API

A simple, thread-safe URL shortener service built with Flask using Python built-in data structures for in-memory storage.

## Features

* ✅ Shortens long URLs to 6-character codes
* 🔁 Redirects short codes to original URLs
* 📊 Tracks click counts and creation timestamps
* 🧠 Thread-safe using Python's `threading.RLock`
* 🔍 Prevents duplicate URLs (returns existing short code)
* 🛡️ Validates URLs with security checks
* ❌ Handles edge cases and invalid input gracefully

## API Endpoints

### 1. **Shorten URL**

```http
POST /api/shorten
Content-Type: application/json

{
  "url": "https://www.example.com"
}
```

**Success (201 Created):**

```json
{
  "short_code": "abc123",
  "original_url": "https://www.example.com",
  "created_at": "2024-01-01T10:00:00Z"
}
```

**Duplicate (200 OK):**

```json
{
  "short_code": "abc123",
  "original_url": "https://www.example.com",
  "message": "URL already exists"
}
```

---

### 2. **Redirect to Original URL**

```http
GET /<short_code>
```

* **302 Redirect** to original URL
* Increments click count
* **404** if code not found

---

### 3. **Get Analytics**

```http
GET /api/stats/<short_code>
```

**Success (200 OK):**

```json
{
  "short_code": "abc123",
  "original_url": "https://www.example.com",
  "click_count": 5,
  "created_at": "2024-01-01T10:00:00Z"
}
```

---

### 4. **Health Check**

```http
GET /
GET /api/health
```

---

### 5. **Global Statistics**

```http
GET /api/stats
```

```json
{
  "total_urls": 150,
  "total_clicks": 1250
}
```

---

## Setup Instructions

### Prerequisites

* Python 3.8+
* pip

### Installation

```bash
git clone https://github.com/<your-username>/url-shortener
cd url-shortener
pip install -r requirements.txt
```

### Run the Application

```bash
python -m flask --app app.main run
```

Visit the API at: [http://localhost:5000](http://localhost:5000)

---

## Run Tests

```bash
pytest
pytest -v                     # verbose output
pytest --cov=app tests/       # coverage report
```

---

## Project Structure

```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py      # API endpoints
│   ├── models.py    # Thread-safe in-memory store
│   └── utils.py     # URL validation, encoding
├── tests/           # Pytest test cases
├── requirements.txt
├── README.md
└── Notes.md         # (AI usage notes)
```

---

## Design Decisions

* **In-memory store**: Fast, no external dependencies
* **Base62 encoding**: Short, URL-safe, human-readable
* **Thread-safe RLock**: Ensures safety under concurrency
* **6-character code**: \~56 billion possible codes
* **Validation**: Rejects dangerous schemes (e.g., `javascript:`)

---

## Limitations

* No persistent storage (data lost on restart)
* No authentication (public API)
* No custom short codes (auto-generated only)
* Single-instance only (not clustered)

---

## Future Improvements

* Add persistent storage (e.g., SQLite, Redis)
* Support custom short codes
* Add rate limiting or API key protection
* Expiration for old links
* Web dashboard for analytics

---

## License

This project is provided for evaluation and educational purposes.
