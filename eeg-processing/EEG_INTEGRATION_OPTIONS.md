# 🧠 EEG Monitoring Integration Guide

## Current Architecture

### Face Recognition (CameraFatigueMonitor)
```
Session.tsx (Game Page)
├─ GameCanvas (Main game)
├─ CameraFatigueMonitor (Floating widget - top-left)
│  ├─ Video feed (webcam)
│  ├─ Real-time metrics (eye blink, yawn, PERCLOS)
│  ├─ Fatigue score display
│  └─ Draggable position
└─ Other HUD elements (Speedometer, Steering, etc)
```

### Current Flow
- CameraFatigueMonitor adalah **floating widget** di dalam game
- Tampilannya: webcam + metrics + fatigue score
- Bisa di-drag, minimize, dan toggle on/off
- Terintegrasi langsung ke Session page

---

## 🧠 EEG Monitoring - Design Options

Kita punya beberapa pilihan untuk integrasi EEG:

### **Option 1: Floating Widget (Recommended) ✅ BEST**

**Lokasi**: Fixed floating panel di game (seperti CameraFatigueMonitor)  
**Tampilan**: Compact metrics + mini waveforms  
**Keuntungan**: Tidak mengganggu game, real-time monitoring

```tsx
// Session.tsx
<div className="app">
  <GameCanvas />
  <CameraFatigueMonitor />
  <EEGMonitoringWidget />  // ← Tambah ini
  <DebugOverlay />
  {/* Other HUD elements */}
</div>
```

**Lokasi**:
- Default: Top-right (agar tidak overlap dengan face monitor)
- Draggable & resizable
- Collapse/expand

**Tampilan**:
```
┌─────────────────┐
│ 🧠 EEG Live    │ ← Header
│ 🟢 Connected   │
├─────────────────┤
│ State: Alert    │
│ Fatigue: 25%    │
├─────────────────┤
│ TP9: 2.34 µV   │ ← Raw channels
│ AF7: -1.23 µV  │ (compact)
│ AF8: 0.89 µV   │
│ TP10: 1.56 µV  │
├─────────────────┤
│ Quality: 95%   │ ← Signal quality
└─────────────────┘
```

---

### **Option 2: Side Panel (Alternative)**

**Lokasi**: Right side panel  
**Tampilan**: Full metrics + 4 waveforms stacked  
**Keuntungan**: More space for details

```
Game Canvas                Side Panel (500px)
┌──────────────────┐   ┌──────────────────┐
│                  │   │   EEG Monitor    │
│                  │   │ ┌────────────┐   │
│   Game Scene     │   │ │  Metrics   │   │
│                  │   │ └────────────┘   │
│                  │   │ ┌────────────┐   │
│                  │   │ │ Waveforms  │   │
│                  │   │ │ (4 chan)   │   │
└──────────────────┘   └──────────────────┘
```

---

### **Option 3: Bottom HUD Bar**

**Lokasi**: Bottom of screen (like other HUD elements)  
**Tampilan**: Horizontal compact display  
**Keuntungan**: Native to game HUD design

```
┌────────────────────────────────────────────┐
│  Game Canvas                               │
└────────────────────────────────────────────┘
┌─ 🧠 EEG Live ─┬─ State: Alert ─┬─ 25% ─┬─ 95% Quality ─┐
│ TP9 AF7 AF8   │                │       │               │
│ TP10 Metrics  │ θ/α β/α        │ Info  │               │
└───────────────┴────────────────┴───────┴───────────────┘
```

---

### **Option 4: Dedicated Tab/Button**

**Lokasi**: Toggle button → opens modal/panel  
**Tampilan**: Full dashboard di overlay

```
Game Canvas + Button Toggle
        │
        ├─ Click "📊 EEG"
        │
        └─ Opens Modal
           ├─ Full metrics
           ├─ 4 waveforms
           ├─ Timeline
           └─ Session info
```

---

## 🎯 Recommendation: Option 1 + Option 3 Hybrid

**Best approach untuk UX Fumorive:**

```
┌─ Top-Left ────────────┐         ┌─ Top-Right ────────────────────┐
│ 📹 Face Monitor      │         │ 🧠 EEG Monitor               │
│ • Video feed         │         │ • Cognitive state            │
│ • Eye blink rate     │         │ • Fatigue score              │
│ • PERCLOS score      │         │ • Signal quality             │
│ • Fatigue alert      │         │ • Raw channels (compact)     │
└──────────────────────┘         └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Game Canvas (Main Driving Simulator)                            │
│                                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌───────┬────────────────────────────────────────────────┬────────┐
│Speed │ EEG Status: Alert | Fatigue: 25% | Quality: 95% │ RPM   │
│ 60   │ Channels: TP9▁ AF7▂ AF8▁ TP10▂ | θ/α: 0.57    │ 4.5K  │
└───────┴────────────────────────────────────────────────┴────────┘
```

---

## 📋 Implementation Plan

### File yang akan dibuat/modified:

1. **EEGMonitoringWidget.tsx** (NEW)
   - Floating widget version
   - Draggable & collapsible
   - Compact display

2. **EEGBottomHUD.tsx** (NEW)
   - Bottom status bar
   - Live metrics strip

3. **Session.tsx** (MODIFY)
   - Import & use EEGMonitoringWidget
   - Add EEGBottomHUD
   - Session ID integration

4. **gameStore.ts** (MODIFY)
   - Add EEG monitoring state
   - Position/visibility tracking
   - Integration with game state

---

## 🔗 Integration Points

### 1. Session ID Management
```tsx
// Get session ID for EEG connection
const sessionId = useUserStore(s => s.sessionId)

// Pass to EEG components
<EEGMonitoringWidget sessionId={sessionId} />
<EEGBottomHUD sessionId={sessionId} />
```

### 2. Cognitive State Integration
```tsx
// React to EEG state changes
const cognitiveState = useEEGStore(s => s.currentMetrics?.cognitiveState)

// Affect game logic
if (cognitiveState === 'fatigued') {
  adjustGameDifficulty('easy')
  showInGameWarning()
}
```

### 3. Combined Monitoring
```tsx
// Use both face + EEG for better accuracy
const faceFatigue = cameraFatigueScore
const eegFatigue = useEEGStore(s => s.currentMetrics?.eegFatigueScore)

// Combine them
const overallFatigue = (faceFatigue + eegFatigue) / 2
```

---

## 💾 Code Structure

```
frontend/src/components/
├─ EEG/
│  ├─ EEGWaveformDisplay.tsx      (Existing)
│  ├─ EEGMetricsDisplay.tsx       (Existing)
│  └─ README.md
│
├─ EEGMonitoringWidget.tsx         (NEW)
│  • Floating draggable widget
│  • Compact metrics + mini waveforms
│  • Toggle on/off
│  └─ EEGMonitoringWidget.css
│
├─ EEGBottomHUD.tsx               (NEW)
│  • Bottom status bar
│  • Real-time metrics strip
│  └─ EEGBottomHUD.css
│
├─ CameraFatigueMonitor.tsx       (Existing)
├─ Session.tsx                    (Modify)
└─ GameCanvas.tsx                 (Potentially modify)
```

---

## 🎨 Design Mockups

### EEGMonitoringWidget (Floating)
```
┌─────────────────────────────┐
│ ⋮ 🧠 EEG Live         [-][+]│  ← Header + drag bar
├─────────────────────────────┤
│                             │
│ 🟢 Connected (256Hz)        │
│                             │
│ COGNITIVE STATE             │
│ ╔═══════════════════════╗   │
│ ║ ⚡ ALERT - 25% ⚡     ║   │  ← Color coded badge
│ ╚═══════════════════════╝   │
│                             │
│ CHANNELS (µV)               │
│ TP9: 2.34  │ AF7: -1.23   │
│ AF8: 0.89  │ TP10: 1.56   │
│                             │
│ INDICATORS                  │
│ θ/α: 0.578 | β/α: 0.297   │
│ Quality: 95% ████████░     │
│                             │
└─────────────────────────────┘
```

### EEGBottomHUD (Status Bar)
```
┌──────────────────────────────────────────────────────────┐
│ 🧠 Live │ Alert │ 25% │ TP9:2.34 AF7:-1.23 AF8:0.89 TP10:1.56 │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Checklist

- [ ] Decide on Option (1 = floating, 2 = side, 3 = bottom, or hybrid)
- [ ] Create EEGMonitoringWidget component
- [ ] Create EEGBottomHUD component
- [ ] Integrate session ID
- [ ] Add to Session.tsx
- [ ] Style & position tweaks
- [ ] Test with real EEG data
- [ ] Optimize performance
- [ ] Mobile responsive
- [ ] Final polish

---

## 📌 Current Status

### ✅ Already Ready
- EEG data streaming working
- Zustand store set up
- Components created (Dashboard, Metrics, Waveforms)
- WebSocket connection stable

### 👉 TODO
- Create widget versions for in-game display
- Integrate with Session page
- Connect session ID
- Styling for game UI

---

## 🎯 Next Steps

**Mana yang kamu prefer?**

1. **Option 1** (Floating widget di top-right)
2. **Option 2** (Side panel)
3. **Option 3** (Bottom HUD bar)
4. **Hybrid** (Widget + bottom strip)

Atau kamu punya ide lain? 

Setelah memilih, saya bisa langsung bikin component yang siap di-integrate ke Session page Anda!

---

Gimana pendapatmu? Mana yang paling cocok untuk UX game kamu? 🎮
