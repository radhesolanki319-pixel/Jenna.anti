'use client';

import React, { createContext, useContext } from 'react';
import { useWebSocket, type UseWebSocketReturn } from '@/hooks/useWebSocket';

const WebSocketContext = createContext<UseWebSocketReturn | undefined>(undefined);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const ws = useWebSocket('/api/v1/ws');

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext(): UseWebSocketReturn {
  const ctx = useContext(WebSocketContext);
  if (!ctx) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return ctx;
}
