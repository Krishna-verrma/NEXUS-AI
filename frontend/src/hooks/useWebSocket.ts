import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  task_id?: string;
  step_id?: string;
  agent_id?: string;
  status?: string;
  operation?: string;
  preview?: string;
  output?: any;
  final_result?: string;
  steps?: any[];
  message?: string;
  error?: string;
  duration_seconds?: number;
  report_id?: string;
}

export function useTaskWebSocket(
  taskId: string | null,
  onMessage: (msg: WebSocketMessage) => void
) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!taskId) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    const wsUrl = `ws://127.0.0.1:8000/ws/tasks/${taskId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (err) => {
      console.warn('WebSocket connection warning:', err);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  return { isConnected };
}
