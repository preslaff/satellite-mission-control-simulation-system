# Known Issues

## Recently Resolved Issues

### WebSocket Dictionary Iteration Error (RESOLVED - 2025-10-24)

**Status:** ✅ Fixed
**Priority:** High
**Fix Date:** 2025-10-24

**Description:**
WebSocket broadcast loop was crashing with "dictionary changed size during iteration" error when clients disconnected during broadcast.

**Solution:**
Modified `backend/app/services/websocket_manager.py` to create a snapshot of connections before iteration:
```python
# Fixed in broadcast() and _broadcast_loop() methods
connections_snapshot = list(self.active_connections.items())
for connection_id, websocket in connections_snapshot:
    # ... send messages safely
```

**Impact:** WebSocket connections are now stable and can handle client disconnections gracefully.

---

### CelesTrak API Abuse Risk (RESOLVED - 2025-10-24)

**Status:** ✅ Fixed
**Priority:** Critical
**Fix Date:** 2025-10-24

**Description:**
Frontend high-frequency polling caused `fetch_by_norad_id()` to hit CelesTrak API directly for every request, bypassing the 2-hour group cache. This resulted in ~18,000 API calls/hour, risking IP blocking (threshold: 10,000 errors/day).

**Solution:**
Modified `backend/app/services/satellite_fetcher.py` to implement cache-first lookups:
- Searches all group caches (stations, starlink, weather, GPS) before calling CelesTrak
- Only fetches from CelesTrak if satellite not found in any cache
- Reduces API calls from ~18,000/hour to ~1 call every 2 hours

**Impact:** Prevents CelesTrak IP blocking while maintaining fast response times through cached data.

---

### Database Connection SQLAlchemy 2.0 Compatibility (RESOLVED - 2025-10-24)

**Status:** ✅ Fixed
**Priority:** Medium
**Fix Date:** 2025-10-24

**Description:**
Database health checks failing with: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`

**Solution:**
Updated `backend/app/core/database.py` to wrap raw SQL in `text()`:
```python
from sqlalchemy import text
db.execute(text('SELECT 1'))
```

**Impact:** Database connection tests now work correctly with SQLAlchemy 2.0.

---

### TimescaleDB Hypertable Setup (RESOLVED - 2025-10-24)

**Status:** ✅ Documented
**Priority:** Medium
**Fix Date:** 2025-10-24

**Description:**
TimescaleDB hypertable conversion required composite primary key including timestamp column. Initial schema only had `id` as primary key.

**Solution:**
- Updated `backend/app/models/telemetry.py` with composite primary key: `(id, satellite_id, timestamp)`
- Documented complete setup process in `backend/DATABASE_SETUP.md`
- Added troubleshooting for common TimescaleDB errors

**Impact:** TimescaleDB hypertables work correctly for time-series telemetry data optimization.

---

## Active Issues

## WebSocket Real-Time Updates (403 Forbidden)

**Status:** May Be Resolved - Needs Verification
**Priority:** Low
**Date:** 2025-10-23
**Last Update:** 2025-10-24

**Note:** Recent logs (2025-10-24) show WebSocket connections working successfully:
- Connections being accepted
- Satellite tracking working
- Position updates broadcasting
- Only issues were dictionary iteration bug (now fixed) and keepalive timeouts (client-side)

This issue may have been resolved or is environment-specific. Further testing recommended.

### Description
WebSocket connections to `/ws/tracking` endpoint are rejected with 403 Forbidden error, even after removing CORS middleware.

### Implementation Details
The following components have been implemented and are ready to use once the 403 issue is resolved:

**Backend:**
- `backend/app/services/websocket_manager.py` - Connection manager with broadcast loop
- `backend/app/api/routes/websocket.py` - WebSocket endpoint at `/ws/tracking`
- Automatic satellite position updates every 1 second
- Support for selective satellite tracking per client

**Frontend:**
- `frontend/src/lib/services/websocket.js` - WebSocket service with auto-reconnect
- Integration with `satellitePositions` store
- Connection lifecycle management

### Error Logs
```
INFO: 127.0.0.1:XXXXX - "WebSocket /ws/tracking" 403
INFO: connection rejected (403 Forbidden)
INFO: connection closed
```

### Attempted Fixes
1. ✗ Removed CORS middleware entirely
2. ✗ Custom CORS middleware to bypass WebSocket paths
3. ✗ Wildcard CORS origins with `allow_credentials=False`

### Potential Causes
- FastAPI/Starlette version compatibility
- Uvicorn WebSocket handshake configuration
- Windows-specific WebSocket handling
- Missing server-side authentication/authorization logic

### Workaround
Current implementation uses 15-second HTTP polling, which is adequate for demonstration purposes.

### Next Steps
- Test on Linux/Mac environment
- Check FastAPI/Starlette versions
- Review Uvicorn WebSocket documentation
- Consider alternative WebSocket library (e.g., `websockets`)

---
