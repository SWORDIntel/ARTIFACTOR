// ARTIFACTOR Chrome Extension - Options Entry Point
import React from 'react';
import { createRoot } from 'react-dom/client';
import OptionsApp from './OptionsApp';
import '../../styles/dark-theme.css';

const container = document.getElementById('options-root');
if (!container) {
  throw new Error('Options root element not found');
}

const root = createRoot(container);
root.render(<OptionsApp />);