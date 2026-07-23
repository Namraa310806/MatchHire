import * as React from "react"

interface KeyboardNavigationOptions {
  onEnter?: () => void
  onEscape?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  onHome?: () => void
  onEnd?: () => void
  enabled?: boolean
}

export function useKeyboardNavigation(options: KeyboardNavigationOptions = {}) {
  const {
    onEnter,
    onEscape,
    onArrowUp,
    onArrowDown,
    onArrowLeft,
    onArrowRight,
    onHome,
    onEnd,
    enabled = true,
  } = options

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent) => {
      if (!enabled) return

      switch (e.key) {
        case "Enter":
          onEnter?.()
          break
        case "Escape":
          onEscape?.()
          break
        case "ArrowUp":
          onArrowUp?.()
          e.preventDefault()
          break
        case "ArrowDown":
          onArrowDown?.()
          e.preventDefault()
          break
        case "ArrowLeft":
          onArrowLeft?.()
          e.preventDefault()
          break
        case "ArrowRight":
          onArrowRight?.()
          e.preventDefault()
          break
        case "Home":
          onHome?.()
          e.preventDefault()
          break
        case "End":
          onEnd?.()
          e.preventDefault()
          break
      }
    },
    [enabled, onEnter, onEscape, onArrowUp, onArrowDown, onArrowLeft, onArrowRight, onHome, onEnd]
  )

  return { handleKeyDown }
}
