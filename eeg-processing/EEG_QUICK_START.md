# EEG Frontend Integration - Quick Reference

## 🚀 Fastest Way to Add EEG to Your App

### 1. Minimal Setup (3 lines)

```tsx
import { EEGDashboard } from '@/modules/eeg'

<EEGDashboard sessionId="your-session-uuid" />
```

Done! Real-time EEG visualization dengan waveforms, metrics, dan connection status.

---

## 📊 Component Options

### Full Dashboard
```tsx
import { EEGDashboard } from '@/modules/eeg'

<EEGDashboard 
  sessionId={sessionId}
  backendUrl="ws://localhost:8000"
  showWaveforms={true}
  onStateChange={(state) => console.log('State:', state)}
/>
```

### Metrics Only
```tsx
import { EEGMetricsDisplay } from '@/modules/eeg'

// Otomatis connect via WebSocket
<EEGMetricsDisplay />
```

### Waveforms Only
```tsx
import { EEGWaveformDisplay } from '@/modules/eeg'

<div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
  <EEGWaveformDisplay channel="AF7" width={400} height={120} />
  <EEGWaveformDisplay channel="AF8" width={400} height={120} />
  <EEGWaveformDisplay channel="TP9" width={400} height={120} />
  <EEGWaveformDisplay channel="TP10" width={400} height={120} />
</div>
```

### Manual Control
```tsx
import { useEEGWebSocket, useEEGStore } from '@/modules/eeg'

function MyComponent() {
  const { isConnected, connectionError } = useEEGWebSocket({
    sessionId,
    enabled: true
  })
  
  const metrics = useEEGStore(s => s.currentMetrics)
  const history = useEEGStore(s => s.dataHistory)
  
  return (
    <div>
      {isConnected ? '✓' : '✗'}
      {metrics?.eegFatigueScore}%
    </div>
  )
}
```

---

## 🎯 Common Use Cases

### Floating Widget di Game

```tsx
function GamePage() {
  const sessionId = useUserStore(s => s.sessionId)
  
  return (
    <div>
      <GameCanvas />
      <div style={{
        position: 'fixed',
        top: 20, right: 20,
        width: 320,
        background: 'white',
        padding: 12,
        borderRadius: 8,
        zIndex: 100,
        boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
      }}>
        <EEGMetricsDisplay />
      </div>
    </div>
  )
}
```

### Alert untuk Fatigue

```tsx
import { useEEGStore } from '@/modules/eeg'
import { useEffect } from 'react'

function FatigueAlert() {
  const metrics = useEEGStore(s => s.currentMetrics)
  
  useEffect(() => {
    if (metrics?.cognitiveState === 'fatigued') {
      alert('⚠️ Fatigue detected! Please rest.')
    }
  }, [metrics?.cognitiveState])
  
  return null
}
```

### Real-time Statistics

```tsx
function Stats() {
  const metrics = useEEGStore(s => s.currentMetrics)
  const average = useEEGStore(s => s.getAverageMetrics(2000))
  
  return (
    <div>
      <div>Current: {metrics?.eegFatigueScore}%</div>
      <div>Last 2s: {average?.eegFatigueScore}%</div>
    </div>
  )
}
```

### Responsive Dashboard (Mobile-friendly)

```tsx
function Dashboard() {
  const sessionId = useUserStore(s => s.sessionId)
  
  return (
    <div style={{
      maxWidth: 1200,
      margin: '0 auto',
      padding: 16,
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
      gap: 16
    }}>
      <EEGMetricsDisplay />
      <EEGDashboard 
        sessionId={sessionId} 
        showWaveforms={window.innerWidth > 768}
      />
    </div>
  )
}
```

---

## 📈 Data Structure

```typescript
interface EEGMetrics {
  timestamp: string                      // ISO timestamp
  rawChannels: {
    TP9: number   // µV
    AF7: number
    AF8: number
    TP10: number
  }
  
  // Frequency bands (power)
  deltapower?: number      // 1-4 Hz
  thetaPower?: number      // 4-8 Hz (drowsiness)
  alphaPower?: number      // 8-13 Hz (relaxation)
  betaPower?: number       // 13-30 Hz (alertness)
  gammaPower?: number      // 30-45 Hz
  
  // Indicators
  thetaAlphaRatio?: number      // drowsiness (high = drowsy)
  betaAlphaRatio?: number       // engagement (high = engaged)
  signalQuality?: number        // 0-1 confidence
  
  // State
  cognitiveState?: 'alert' | 'drowsy' | 'fatigued'
  eegFatigueScore?: number      // 0-100 percentage
}
```

---

## 🔧 Configuration

### Hook Options

```tsx
useEEGWebSocket({
  sessionId: string              // Required
  backendUrl?: string            // Default: ws://localhost:8000
  onMetricsReceived?: (metrics) => void
  onError?: (error) => void
  enabled?: boolean              // Default: true
})
```

### Component Props

**EEGWaveformDisplay**:
- `channel`: 'TP9' | 'AF7' | 'AF8' | 'TP10'
- `height`: number (px)
- `width`: number (px)
- `updateInterval`: number (ms)

**EEGDashboard**:
- `sessionId`: string
- `backendUrl`: string
- `showWaveforms`: boolean
- `onStateChange`: (state) => void

---

## ✅ Checklist Sebelum Launch

- [ ] Backend running (`python main.py`)
- [ ] EEG server running (`python server.py --session-id <UUID>`)
- [ ] Muse 2 paired via Bluetooth
- [ ] LSL stream aktif (`python -m muselsl stream`)
- [ ] Environment variables set (`.env.local`)
- [ ] Session UUID dari backend tersedia
- [ ] WebSocket endpoint accessible
- [ ] No CORS errors di DevTools

---

## 🐛 Quick Troubleshooting

| Issue | Quick Fix |
|-------|----------|
| "Waiting for EEG data..." | Check if `eeg-processing/server.py` running |
| WebSocket disconnected | Verify backend WebSocket endpoint |
| High CPU usage | Set `updateInterval={100}` di waveform |
| Missing data | Check browser console untuk errors |
| All channels 0 | Muse2 tidak streaming atau bad signal |

---

## 📁 File Structure

```
frontend/src/
├── stores/eegStore.ts           # State management
├── hooks/useEEGWebSocket.ts      # WebSocket connection
├── modules/eeg/index.ts          # Barrel exports
├── components/
│   ├── EEGDashboard.tsx          # Main component
│   └── EEG/
│       ├── EEGMetricsDisplay.tsx
│       ├── EEGWaveformDisplay.tsx
│       └── README.md
└── components/page/
    ├── EEGMonitoringPage.tsx     # Dedicated page
    └── EEGMonitoringPage.css
```

---

## 🚀 Performance Tips

1. **Reduce rendering**:
   ```tsx
   <EEGWaveformDisplay updateInterval={100} />  // 10 FPS vs 20 FPS
   ```

2. **Disable waveforms on mobile**:
   ```tsx
   showWaveforms={window.innerWidth > 768}
   ```

3. **Memoize callbacks**:
   ```tsx
   const handleStateChange = useCallback((state) => {
     // ...
   }, [])
   ```

4. **Use selector memoization**:
   ```tsx
   const metrics = useEEGStore(
     (state) => state.currentMetrics,
     (a, b) => a?.timestamp === b?.timestamp  // Custom compare
   )
   ```

---

## 📚 Learn More

- Full docs: `frontend/src/components/EEG/README.md`
- Setup guide: `EEG_SETUP_GUIDE.md`
- Backend API: http://localhost:8000/api/docs

---

**Version**: 1.0.0 | **Last Updated**: Feb 5, 2026
