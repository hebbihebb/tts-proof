# Phase 11 PR-2: Next Steps Guide

**Current Status**: PR-1 merged ✅, ready to start PR-2  
**Goal**: Pretty Report Display & Diff Viewer  
**Estimated Time**: 10-14 hours

---

## 🎯 Quick Start

```bash
# 1. Create PR-2 branch
git checkout -b feat/phase11-pr2-report-display

# 2. Start development
python launch.py  # Starts both servers
```

---

## 📋 Implementation Checklist

### Part A: Report Display (4-6 hours)

**Backend** (`backend/app.py`):
- [ ] Add `GET /api/runs/{run_id}/report` endpoint
  - Read `stats.json` from `~/.mdp/runs/{run_id}/`
  - Transform into human-readable format
  - Return structured response
- [ ] Add Pydantic model: `ReportResponse`
- [ ] Test endpoint with existing runs

**Frontend** (`frontend/src/components/ReportDisplay.tsx`):
- [ ] Create component with props: `runId`, `stats`, `onClose`
- [ ] Header section: Run ID, timestamp, status
- [ ] Stats grid: Per-step breakdown with icons
- [ ] Collapsible sections for detailed stats
- [ ] Success/warning/error indicators
- [ ] Download button for JSON
- [ ] Responsive layout (Tailwind)
- [ ] Dark mode support

**Integration**:
- [ ] Add to `App.tsx` after pipeline completion
- [ ] Store `run_id` from WebSocket `completed` message
- [ ] Show report in modal or dedicated section
- [ ] Add "View Report" button to re-open

**Testing**:
- [ ] Integration test for `/api/runs/{run_id}/report`
- [ ] Test with various step combinations
- [ ] Test with errors and warnings
- [ ] Test with empty stats

### Part B: Diff Viewer (6-8 hours)

**Backend** (`backend/app.py`):
- [ ] Add `GET /api/runs/{run_id}/diff` endpoint
  - Read `input.txt` and `output.txt`
  - Compute line-by-line diff
  - Return structured diff data
- [ ] Add Pydantic model: `DiffResponse`
- [ ] Consider using `difflib` for algorithm
- [ ] Handle large files (pagination/streaming)

**Frontend** (`frontend/src/components/DiffViewer.tsx`):
- [ ] Create component with props: `runId`, `onClose`
- [ ] Side-by-side view option
- [ ] Unified view option
- [ ] Line numbers
- [ ] Color coding (green=added, red=removed, yellow=changed)
- [ ] Syntax highlighting for Markdown (optional)
- [ ] Search/filter functionality
- [ ] Jump to next/prev change
- [ ] Download diff as file
- [ ] Virtualization for large files

**Integration**:
- [ ] Add "View Diff" button next to "View Report"
- [ ] Toggle between report and diff views
- [ ] Share same modal/container

**Testing**:
- [ ] Integration test for `/api/runs/{run_id}/diff`
- [ ] Test with no changes
- [ ] Test with small/large changes
- [ ] Test with large files (>1MB)
- [ ] Performance testing

---

## 🔧 Technical Details

### Backend Implementation Pattern

```python
# backend/app.py

from pathlib import Path
from typing import Dict, Any, List

class ReportResponse(BaseModel):
    run_id: str
    timestamp: str
    status: str
    steps: List[str]
    stats: Dict[str, Any]
    summary: str

class DiffLine(BaseModel):
    line_num_old: Optional[int]
    line_num_new: Optional[int]
    type: str  # 'unchanged', 'added', 'removed', 'modified'
    content: str

class DiffResponse(BaseModel):
    run_id: str
    total_lines_old: int
    total_lines_new: int
    changes: int
    diff_lines: List[DiffLine]

@app.get("/api/runs/{run_id}/report", response_model=ReportResponse)
async def get_run_report(run_id: str):
    run_dir = Path.home() / '.mdp' / 'runs' / run_id
    stats_file = run_dir / 'stats.json'
    
    if not stats_file.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    # Transform stats into human-readable format
    summary = generate_summary(stats)
    
    return ReportResponse(
        run_id=run_id,
        timestamp=stats.get('timestamp', 'unknown'),
        status='completed',  # or extract from stats
        steps=list(stats.keys()),
        stats=stats,
        summary=summary
    )

@app.get("/api/runs/{run_id}/diff", response_model=DiffResponse)
async def get_run_diff(run_id: str):
    run_dir = Path.home() / '.mdp' / 'runs' / run_id
    input_file = run_dir / 'input.txt'
    output_file = run_dir / 'output.txt'
    
    if not input_file.exists() or not output_file.exists():
        raise HTTPException(status_code=404, detail="Run files not found")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        input_lines = f.readlines()
    with open(output_file, 'r', encoding='utf-8') as f:
        output_lines = f.readlines()
    
    # Compute diff using difflib
    import difflib
    diff = difflib.unified_diff(input_lines, output_lines, lineterm='')
    
    # Transform into structured format
    diff_lines = parse_diff(diff, input_lines, output_lines)
    
    return DiffResponse(
        run_id=run_id,
        total_lines_old=len(input_lines),
        total_lines_new=len(output_lines),
        changes=count_changes(diff_lines),
        diff_lines=diff_lines
    )
```

### Frontend Component Pattern

```typescript
// frontend/src/components/ReportDisplay.tsx

import React from 'react';
import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface ReportDisplayProps {
  runId: string;
  stats: Record<string, any>;
  onClose: () => void;
}

export const ReportDisplay: React.FC<ReportDisplayProps> = ({ runId, stats, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">Pipeline Report</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Summary section */}
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="text-green-600 dark:text-green-400 mt-1" size={20} />
              <div>
                <h3 className="font-semibold text-green-800 dark:text-green-200">Pipeline Completed</h3>
                <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                  {Object.keys(stats).length} steps executed successfully
                </p>
              </div>
            </div>
          </div>
          
          {/* Per-step stats */}
          {Object.entries(stats).map(([step, stepStats]) => (
            <StepStatsSection key={step} step={step} stats={stepStats} />
          ))}
        </div>
      </div>
    </div>
  );
};
```

```typescript
// frontend/src/components/DiffViewer.tsx

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface DiffViewerProps {
  runId: string;
  onClose: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ runId, onClose }) => {
  const [diffData, setDiffData] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'side-by-side' | 'unified'>('side-by-side');
  
  useEffect(() => {
    apiService.getRunDiff(runId).then(setDiffData);
  }, [runId]);
  
  if (!diffData) return <div>Loading diff...</div>;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        <div className="border-b p-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold">Changes</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('side-by-side')}
                className={`px-3 py-1 rounded ${viewMode === 'side-by-side' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              >
                Side-by-Side
              </button>
              <button
                onClick={() => setViewMode('unified')}
                className={`px-3 py-1 rounded ${viewMode === 'unified' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              >
                Unified
              </button>
            </div>
          </div>
          <button onClick={onClose}>Close</button>
        </div>
        
        <div className="flex-1 overflow-auto font-mono text-sm">
          {viewMode === 'side-by-side' ? (
            <SideBySideDiff lines={diffData.diff_lines} />
          ) : (
            <UnifiedDiff lines={diffData.diff_lines} />
          )}
        </div>
      </div>
    </div>
  );
};
```

---

## 🧪 Testing Strategy

### Integration Tests

```python
# testing/test_web_runner.py (add to existing file)

@pytest.mark.integration
def test_get_run_report():
    """Test report endpoint returns formatted stats"""
    # Create a run with known stats
    run_id = "test-run-123"
    stats = {...}  # Known test data
    
    response = client.get(f"/api/runs/{run_id}/report")
    assert response.status_code == 200
    data = response.json()
    assert data['run_id'] == run_id
    assert 'summary' in data

@pytest.mark.integration
def test_get_run_diff():
    """Test diff endpoint computes changes correctly"""
    run_id = "test-run-123"
    
    response = client.get(f"/api/runs/{run_id}/diff")
    assert response.status_code == 200
    data = response.json()
    assert 'diff_lines' in data
    assert data['changes'] >= 0
```

### Manual Testing

1. **Report Display**:
   - Run pipeline with all steps
   - Click "View Report" button
   - Verify all stats shown
   - Test collapsible sections
   - Test download button

2. **Diff Viewer**:
   - Run pipeline with known changes
   - Click "View Diff" button
   - Toggle between view modes
   - Search for specific changes
   - Test with large files

---

## 📚 Libraries to Consider

### Diff Algorithm
- **Built-in**: `difflib` (Python standard library) ✅ Recommended
- **Alternative**: `diff-match-patch` (more features, external dependency)

### Frontend Diff Display
- **react-diff-view**: Pre-built diff viewer component
- **react-syntax-highlighter**: Markdown syntax highlighting
- **react-virtualized**: For large file virtualization
- **Or**: Build custom (more control, fits existing UI)

---

## 🎯 Success Criteria

**PR-2 is complete when**:
- [ ] Report endpoint returns human-readable stats
- [ ] Diff endpoint computes changes correctly
- [ ] Report displays in modal with all step stats
- [ ] Diff viewer shows side-by-side comparison
- [ ] Both components have download buttons
- [ ] Integration tests passing (2+ new tests)
- [ ] Fast tests still passing (no regressions)
- [ ] Documentation updated
- [ ] PR created and merged into dev

---

## 💡 Pro Tips

1. **Start with backend endpoints** - easier to test independently
2. **Use existing run artifacts** - create runs via CLI for test data
3. **Reuse UI patterns** - match StepToggles/ModelPickers styling
4. **Test with edge cases** - no changes, huge changes, errors
5. **Consider performance** - large files need virtualization
6. **Mobile-first** - ensure responsive on small screens
7. **Accessibility** - keyboard navigation, ARIA labels

---

## 🚀 When You're Ready

```bash
# Create branch
git checkout -b feat/phase11-pr2-report-display

# Start coding!
code backend/app.py
code frontend/src/components/ReportDisplay.tsx

# Test as you go
pytest -m "integration" -v
npm run dev  # Frontend hot reload

# Commit frequently
git add .
git commit -m "feat(phase11-pr2): Add report display endpoint"

# Push when ready
git push -u origin feat/phase11-pr2-report-display
```

**Good luck! You've got this! 🎊**
