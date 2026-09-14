import { WS_BASE_URL } from './api';

export type WebSocketListener = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<WebSocketListener>> = new Map();
  private isConnected = false;
  private reconnectTimer: any = null;

  constructor() {
    this.connect();
  }

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.ws = new WebSocket(WS_BASE_URL);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.notify('status', { connected: true });
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const type = payload.type || 'message';
          this.notify(type, payload);
          this.notify('*', payload);
        } catch {
          // ignore non-json messages
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.notify('status', { connected: false });
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.isConnected = false;
        this.notify('status', { connected: false });
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }

  public subscribe(eventType: string, listener: WebSocketListener): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(listener);

    return () => {
      this.listeners.get(eventType)?.delete(listener);
    };
  }

  private notify(eventType: string, data: any) {
    const handlers = this.listeners.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  public send(action: string, payload: Record<string, any> = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action, ...payload }));
    }
  }

  public getConnected(): boolean {
    return this.isConnected;
  }
}

export const wsService = new WebSocketService();
