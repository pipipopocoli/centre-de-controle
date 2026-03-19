import { useEffect } from 'react'
import { useCockpitStore } from '../store/index.js'

/**
 * Handles clock tick, viewport sampling RAF loop, and media cleanup on unmount.
 */
export function usePolling({
  containerRef,
  panRef,
  mediaRecorderRef,
  mediaStreamRef,
}: {
  containerRef: React.RefObject<HTMLDivElement | null>
  panRef: React.RefObject<{ x: number; y: number }>
  mediaRecorderRef: React.RefObject<MediaRecorder | null>
  mediaStreamRef: React.RefObject<MediaStream | null>
}) {
  const setClockNow = useCockpitStore((s) => s.setClockNow)
  const setOverlayViewport = useCockpitStore((s) => s.setOverlayViewport)

  // Clock tick - update every second
  useEffect(() => {
    const timer = window.setInterval(() => setClockNow(new Date()), 1000)
    return () => window.clearInterval(timer)
  }, [setClockNow])

  // Media cleanup on unmount
  useEffect(() => {
    const recorderRef = mediaRecorderRef
    const streamRef = mediaStreamRef
    return () => {
      recorderRef.current?.stop()
      if (streamRef.current) {
        for (const track of streamRef.current.getTracks()) {
          track.stop()
        }
      }
    }
  }, [mediaRecorderRef, mediaStreamRef])

  // Viewport sampling RAF loop
  useEffect(() => {
    let rafId = 0

    const sampleViewport = () => {
      const container = containerRef.current
      if (container) {
        const dpr = window.devicePixelRatio || 1
        const rect = container.getBoundingClientRect()
        const next = {
          viewportWidth: Math.round(rect.width * dpr),
          viewportHeight: Math.round(rect.height * dpr),
          panX: panRef.current.x,
          panY: panRef.current.y,
          dpr,
        }

        setOverlayViewport((previous) => {
          const sameSize =
            previous.viewportWidth === next.viewportWidth &&
            previous.viewportHeight === next.viewportHeight &&
            previous.dpr === next.dpr
          const samePan =
            Math.abs(previous.panX - next.panX) < 0.5 &&
            Math.abs(previous.panY - next.panY) < 0.5
          if (sameSize && samePan) {
            return previous
          }
          return next
        })
      }

      rafId = window.requestAnimationFrame(sampleViewport)
    }

    rafId = window.requestAnimationFrame(sampleViewport)
    return () => {
      window.cancelAnimationFrame(rafId)
    }
  }, [containerRef, panRef, setOverlayViewport])
}
