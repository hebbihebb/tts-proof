# Phase 11 PR-2: Report Display + Diff Viewer

## Summary

Implements human-readable report display and visual diff viewer for pipeline results in the web UI. Users can now review processing stats and see exact changes made to their files through an intuitive modal interface.

## Changes

### Backend (4 new endpoints)
- **GET `/api/runs/{run_id}/report`** - Returns formatted report + JSON path
- **GET `/api/runs/{run_id}/diff`** - Returns unified diff (server-side truncation)
- **GET `/api/runs/{run_id}/result`** - Returns exit code + artifact paths
- **GET `/api/artifact`** - Downloads specific artifacts by name

**Key Implementation**:
- Reuses existing `report.pretty.render_pretty()` formatter
- Python stdlib `difflib.unified_diff()` for diff generation
- Fallback to `output.rejected.md` when validation fails (exit code 3)
- Updated `run_pipeline_job()` to send `run_id` in WebSocket completion

### Frontend (2 new components)
- **`ReportDisplay.tsx`** - Modal showing formatted stats with copy/download
- **`DiffViewer.tsx`** - Unified diff display with syntax highlighting

**Features**:
- Color-coded diff lines (red=removed, green=added, blue=headers)
- Collapsible modals with dark mode support
- Download buttons for JSON report and full output
- "No differences" message for unchanged files
- Rejected state indicator (yellow banner)

### Configuration
- **Blessed Models** expanded to include:
  - Detector: `qwen2.5-1.5b-instruct`, `qwen3-4b-instruct-2507`, `qwen3-8b`
  - Fixer: `qwen2.5-1.5b-instruct`, `qwen3-4b-instruct-2507`, `qwen3-8b`

## Testing

### Automated Tests ✅
- **4/4 integration tests passing** (0.12s)
- Tests for report rendering, diff generation, truncation, artifact creation

### Manual UI Testing ✅
- **Smoke test** with `detector_smoke_test.md`
- **Model**: qwen3-4b-instruct-2507 (4B shows better accuracy)
- **Steps**: prepass-basic, prepass-advanced, detect, apply
- **Result**: All 3 test cases fixed correctly
  - "F l a s h" → "Flash" (prepass-basic)
  - "U-N-I-T-E-D" → "UNITED" (detector)
  - "Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!" (detector)
- **Output hash**: `1B7C4259066B136FB696A59F1A6A34D27D2BCCCDBDADAE436391737130F0BF98`

## Files Changed

**Backend**:
- `backend/app.py` (+184 lines) - 4 endpoints, 3 Pydantic models

**Frontend**:
- `frontend/src/components/ReportDisplay.tsx` (+152 lines)
- `frontend/src/components/DiffViewer.tsx` (+175 lines)
- `frontend/src/App.tsx` (+72 lines) - Results section integration
- `frontend/src/services/api.ts` (+53 lines) - 4 new API methods

**Config**:
- `mdp/config.py` (+8 lines) - Blessed models expansion

**Tests**:
- `testing/test_web_report.py` (+142 lines) - Integration tests

**Docs**:
- `docs/PHASE11_PR2_TEST_RESULTS.md` (+148 lines)
- `.gitignore` (+4 lines)

## Acceptance Criteria

- ✅ Report display matches CLI `--report-pretty` format
- ✅ Diff viewer shows unified diff with color coding
- ✅ Artifact download buttons functional
- ✅ Results section appears after processing completes
- ✅ Multiple blessed models available in dropdowns
- ✅ Dark mode support
- ✅ Zero regressions in existing tests

## Known Limitations

- Rejection workflow (exit code 3) not tested yet
- Large file handling (>1MB) not tested yet
- Performance with many changes not tested yet

## Screenshots

*(Add screenshots here if desired)*

1. Report modal with formatted stats
2. Diff viewer showing changes with color coding
3. Model selection dropdowns with 3 options

## Migration Notes

**Breaking Changes**: None

**Required Actions**:
- Restart backend server to load new blessed models
- Frontend auto-updates via hot reload

## Related Issues

Closes Phase 11 PR-2 milestone. Follows PR-1 (step toggles + model pickers).

Next: PR-3 (Artifact Management & Run History)
