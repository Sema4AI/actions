export const API_BASE_URL = '';

const resolveWebsocketProtocol = (): 'ws:' | 'wss:' => {
  return window.location.protocol === 'https:' ? 'wss:' : 'ws:';
};

export const WEBSOCKET_BASE_URL = `${resolveWebsocketProtocol()}//${window.location.host}`;
