import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import * as monaco from 'monaco-editor'
import { loader } from '@monaco-editor/react'

// Configure Monaco Editor to load local copy offline instead of hitting CDN
loader.config({ monaco });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

