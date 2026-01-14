import React from 'react';
import MacWindow from './layouts/MacWindow';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <MacWindow>
      <Dashboard />
    </MacWindow>
  );
}

export default App;
