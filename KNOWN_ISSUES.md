# Known Issues

## WebSocket Real-Time Updates (403 Forbidden)

**Status:** Blocked - Needs Investigation
**Priority:** Medium
**Date:** 2025-10-23

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
