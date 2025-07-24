# NOTES.md

## Brief Notes About My Approach & Implementation Choices

I followed a pragmatic, engineering-first approach: understand the problem, design around the constraints, implement with correctness, and keep things simple and testable.

### 🔹 1. Design Approach

I started by mapping out the three core features:
- Shortening and storing a URL
- Redirecting via short code
- Retrieving analytics (clicks + timestamp)

I designed the service to be minimal, thread-safe, and fully in-memory, in line with the constraints. This helped avoid unnecessary complexity while ensuring functional correctness.

### 🔹 2. Data Structures & Logic (and Why)

- **Python `dict`** for storage: Chosen for its simplicity and constant-time performance. Suitable for small-scale, in-memory apps.
- **`threading.RLock`**: Used to safely handle concurrent read/write without corrupting shared state. `RLock` was preferred over `Lock` because it supports reentrant locking within the same thread.
- **Base62 short codes**: Picked for being compact, URL-safe, and collision-resistant. A retry mechanism handles potential code collisions.
- **Idempotent shortening**: The same URL returns the same code. This avoids duplicate entries and improves predictability for the user.

### 🔹 3. Tech Stack (and Why)

- **Flask**: Chosen for its lightweight nature and simplicity in creating REST APIs. Easy to set up and understand.
- **Pytest**: Used for its concise syntax and flexibility in writing functional and edge-case tests.
- **No external DB or libraries**: As required, the solution remains minimal and dependency-free.

### 🔹 4. Code Organization (and Why)

- `main.py`: Handles routing and JSON responses
- `models.py`: Manages the in-memory store and encapsulates business logic
- `utils.py`: Contains helpers for validation, encoding, normalization

This separation keeps the code organized and makes it easier to maintain or extend (e.g., replacing dicts with Redis in the future).

### 🔹 5. Input Validation & Error Handling

- URLs are normalized (adding `http://` if missing) and validated using `urlparse`.
- Unsafe URLs like `localhost`, `127.0.0.1`, or `javascript:` are rejected to avoid SSRF or injection risks.
- All error responses are returned as JSON with consistent formatting and status codes (e.g., 400 for bad input, 404 for unknown codes).

### 🔹 6. Timestamps & Output Formatting

- Timestamps are stored in UTC and formatted using the ISO 8601 standard.
- This ensures consistent, human-readable output and avoids timezone ambiguity across systems.

### 🔹 7. Testing & Debugging

- Wrote functional tests covering:
  - Valid shortening and redirection
  - Edge cases (invalid URLs, unknown codes)
  - Stats tracking
  - Concurrent access behavior

- Some test cases were drafted using AI tools and refined manually to match spec and real-world usage.

### 🔹 8. Final Checks & Optimization

- Cleaned up redundant logic
- Reviewed all response formats for consistency
- Ensured test coverage matched core feature set

**Summary**:  
Every decision — from using `dict` to choosing Flask — was made based on the problem's constraints, keeping the solution clean, correct, and ready for future extension if needed.
 
------

## AI Usage Disclosure

**Tools Used**:
- ChatGPT (OpenAI)
- Claude (Anthropic)
- Gemini (Google)

**Usage Summary**:

AI tools were used as assistants during development — similar to how a developer would use online documentation or StackOverflow:

- **ChatGPT** was used early on to help brainstorm the overall plan, choose appropriate data structures (e.g., thread-safe in-memory store), and review the final implementation against the requirements.
- **Claude** was used to discuss and refine the initial code structure (e.g., Flask routes, short code generation logic), and to help with some edge-case handling and error responses.
- **Gemini** assisted with testing ideas — helping identify missing test cases and ensuring all expected constraints were covered.

All code was reviewed, edited, and completed manually. Several tests, logic improvements, and error-handling cases were added independently after understanding the problem deeply.

The final implementation — including structure, concurrency design, and test reliability — reflects my own work, using AI tools as supportive reference points.