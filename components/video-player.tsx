"use client"

import { useRef, useEffect } from "react"

interface VideoPlayerProps {
  src: string
}

export function VideoPlayer({ src }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // In a real application, you would connect to the actual stream
    // For demo purposes, we're just setting up basic video properties
    video.muted = true
    video.autoplay = true

    // In a real implementation, you would handle RTSP/HLS/WebRTC streams
    // This is just a placeholder for demonstration

    return () => {
      if (video) {
        video.pause()
        video.src = ""
      }
    }
  }, [src])

  return (
    <div className="relative h-full w-full bg-gray-200">
      {/* Placeholder with camera icon */}
      <div className="absolute inset-0 flex items-center justify-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="64"
          height="64"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-gray-400"
        >
          <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
          <circle cx="12" cy="13" r="3" />
        </svg>
      </div>

      {/* Hidden video element - would be visible in a real implementation */}
      <video ref={videoRef} className="h-full w-full object-cover opacity-0" />
    </div>
  )
}
