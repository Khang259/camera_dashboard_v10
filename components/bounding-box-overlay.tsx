"use client"

import type { BoundingBox } from "@/lib/types"

interface BoundingBoxOverlayProps {
  boundingBoxes: BoundingBox[]
}

export function BoundingBoxOverlay({ boundingBoxes }: BoundingBoxOverlayProps) {
  return (
    <div className="absolute inset-0 pointer-events-none">
      {boundingBoxes.map((box, index) => (
        <div
          key={index}
          className="absolute border-2 border-red-500"
          style={{
            left: `${box.x}%`,
            top: `${box.y}%`,
            width: `${box.width}%`,
            height: `${box.height}%`,
          }}
        >
          <div className="absolute top-0 left-0 bg-red-500 text-white text-xs px-1 py-0.5 rounded-br">
            {box.label} {Math.round(box.confidence * 100)}%
          </div>
        </div>
      ))}
    </div>
  )
}
