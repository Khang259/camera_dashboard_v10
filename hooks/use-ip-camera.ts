import { useEffect, useState, useCallback } from 'react'
import type { Camera } from '@/lib/types'


// 
interface IPCameraStreamState {
  isConnected: boolean // Trạng thái kết nối cameraIP dạng bool
  error: string | null //Lỗi
  streamUrl: string | null //URL của camera
}

export function useIPCamera(camera: Camera) {
  const [state, setState] = useState<IPCameraStreamState>({
    isConnected: false,
    error: null,
    streamUrl: null,
  })

  const connect = useCallback(async () => {
    try {
      // Lấy stream URL từ server
      const response = await fetch(`http://192.168.1.108:8000/api/cameras/${camera.id}/stream`)
      if (!response.ok) {
        throw new Error('Failed to get camera stream')
      }
      
      const data = await response.json() //trả thông tin dạng JSON từ response của URL
      setState({
        isConnected: true,
        error: null,
        streamUrl: data.streamUrl,
      })
    } catch (err) {
      setState({
        isConnected: false,
        error: err instanceof Error ? err.message : 'Failed to connect to camera',
        streamUrl: null,
      })
    }
  }, [camera.id])

  const disconnect = useCallback(() => {
    setState({
      isConnected: false,
      error: null,
      streamUrl: null,
    })
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    ...state,
    connect,
    disconnect,
  }
} 