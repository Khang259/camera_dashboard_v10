import { useEffect, useState, useCallback, useRef } from 'react'

interface CameraStreamData {
  frame: string
  fingerCounts: number[]
  totalFingers: number
}

const MAX_RETRIES = 5
const RETRY_DELAY = 2000 // 2 seconds
const WS_URL = 'ws://192.168.1.108:8000/ws/camera'
const HEARTBEAT_INTERVAL = 30000 // 30 seconds

export function useCameraStream() {
  const [streamData, setStreamData] = useState<CameraStreamData | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }
  }, [])

  const startHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
    }

    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
        startHeartbeat()
      }
    }, HEARTBEAT_INTERVAL)
  }, [])

  const connectWebSocket = useCallback(() => {
    // Cleanup existing connection
    cleanup()

    try {
      console.log('Attempting to connect to WebSocket...')
      const newWs = new WebSocket(WS_URL)

      newWs.onopen = () => {
        console.log('WebSocket connected successfully')
        setIsConnected(true)
        setError(null)
        setRetryCount(0)
        startHeartbeat()
      }

      newWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'pong') {
            // Handle heartbeat response
            return
          }
          setStreamData(data)
        } catch (err) {
          console.error('Error parsing stream data:', err)
          setError('Error parsing stream data')
        }
      }

      newWs.onerror = (event) => {
        console.error('WebSocket error:', event)
        const errorMessage = 'Failed to connect to camera server. '
        if (event.type === 'error' && (event as any).message?.includes('Insufficient resources')) {
          setError(errorMessage + 'Server is busy. Please try again later.')
        } else {
          setError(errorMessage + 'Please check if the server is running.')
        }
        setIsConnected(false)
      }

      newWs.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        setIsConnected(false)
        
        // Chỉ thử kết nối lại nếu không phải là đóng có chủ ý
        if (event.code !== 1000 && retryCount < MAX_RETRIES) {
          console.log(`Retrying connection... (${retryCount + 1}/${MAX_RETRIES})`)
          reconnectTimeoutRef.current = setTimeout(() => {
            setRetryCount(prev => prev + 1)
            connectWebSocket()
          }, RETRY_DELAY * (retryCount + 1)) // Tăng delay theo số lần retry
        } else if (retryCount >= MAX_RETRIES) {
          setError('Failed to connect after multiple attempts. Please check if the server is running.')
        }
      }

      wsRef.current = newWs
      return newWs
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      setError('Failed to create WebSocket connection')
      return null
    }
  }, [cleanup, retryCount, startHeartbeat])

  // Hàm để thử kết nối lại thủ công
  const reconnect = useCallback(() => {
    cleanup() // Cleanup trước khi kết nối lại
    setRetryCount(0)
    setError(null)
    connectWebSocket()
  }, [cleanup, connectWebSocket])

  useEffect(() => {
    connectWebSocket()

    return () => {
      cleanup()
    }
  }, [connectWebSocket, cleanup])

  return {
    streamData,
    isConnected,
    error,
    retryCount,
    reconnect
  }
} 