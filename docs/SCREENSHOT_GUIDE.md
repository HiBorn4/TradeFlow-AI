# 📸 Screenshot & Recording Guide - TradeFlow AI

This guide tells you exactly what to capture, how, and where to save each asset.

---

## Prerequisites

- App running locally (see README Quick Start)
- Sample PDF: `logictic_ai_system/data/InfrabuildTest invoice-3.pdf`
- Screen: 1280×900 or 1440×900 recommended
- Recording tool: OBS Studio (free), Loom (free), or macOS Cmd+Shift+5

---

## Screenshots

### `01-main-upload.png` - Landing screen
**What**: Full browser window showing the TradeFlow AI homepage before any file is uploaded.  
**Shows**: Hero header, upload zone, sidebar with green "Backend connected" status, Quick Actions panel, Supported Document Types list.  
**Size**: ~1280×900  
**Tip**: Make sure the backend is running (green badge in sidebar).

### `02-processing-log.png` - Live pipeline log
**What**: Mid-processing view after uploading InfrabuildTest invoice-3.pdf.  
**Shows**: The "Processing Log" section with step-by-step classification lines visible:
```
✅ Page 01: Saved to 'Tax Invoice'
✅ Page 04: Saved to 'Certificate of Origin'
...
```
**Tip**: Screenshot around the 30-second mark when classification lines are streaming.

### `03-json-results.png` - Extraction output
**What**: The response panel after full processing completes.  
**Shows**: "🎉 Parallel Processing Complete!" summary, DocTypes extracted per class.  
**Tip**: Type "Show all extracted data" in the Command Interface after processing.

### `04-chat-commands.png` - Command interface
**What**: The bottom chat section after a quick-action query.  
**Shows**: Chat history with a user command + agent response showing JSON summary.  
**Tip**: Click "📊 View All Results" quick action and screenshot the response.

---

## Screen Recording (`assets/demo/tradeflow-demo.mp4`)

**Duration**: 90–120 seconds  
**Resolution**: 1280×720 minimum, 1920×1080 preferred  
**Format**: MP4 (H.264)

### Script

| Time | Action | What viewer sees |
|------|--------|-----------------|
| 0:00–0:05 | Open `http://localhost:8501` | Clean dark UI, green backend badge |
| 0:05–0:12 | Drag `InfrabuildTest invoice-3.pdf` onto the upload zone | File name + size appears |
| 0:12–0:16 | Click "🚀 Process Document" | Spinner starts |
| 0:16–0:45 | Let classification run (x1.5 speed in edit) | Live log lines appearing per page |
| 0:45–1:00 | Extraction phase (x2 speed) | "5 classes in parallel" messages |
| 1:00–1:15 | Final results | "🎉 Parallel Processing Complete!" |
| 1:15–1:30 | Click "📊 View All Results" quick action | Structured JSON summary |
| 1:30–end | Hover over sidebar tool list | All 7 MCP tools visible |

### Post-processing tips
- Add captions for each phase (OBS or DaVinci Resolve free)
- Export a GIF version (first 20 seconds) for the README hero
- Upload to YouTube/Loom and replace the badge link in README

---

## Where to save

```
assets/
├── architecture.svg          ← already generated ✅
├── screenshots/
│   ├── 01-main-upload.png
│   ├── 02-processing-log.png
│   ├── 03-json-results.png
│   └── 04-chat-commands.png
└── demo/
    └── tradeflow-demo.mp4
```

Then update README.md image paths accordingly - each `![...](assets/screenshots/XX.png)` block already points to the right location.
