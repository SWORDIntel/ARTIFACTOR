// ARTIFACTOR Chrome Extension - Popup Entry Point
import React from 'react';
import { createRoot } from 'react-dom/client';
import PopupApp from './PopupApp';
import '../../styles/dark-theme.css';

const container = document.getElementById('popup-root');
if (!container) {
  throw new Error('Popup root element not found');
}

const root = createRoot(container);
root.render(<PopupApp />);