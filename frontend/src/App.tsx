import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { FileUp, User, Search, Database } from 'lucide-react';
import DataIngestion from './components/DataIngestion';
import UserProfile from './components/UserProfile';
import Matching from './components/Matching';
import OpportunityDetail from './components/OpportunityDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-3">
                <Database className="h-8 w-8 text-indigo-600" />
                <h1 className="text-2xl font-bold text-gray-900">FundingMatch</h1>
              </div>
              <nav className="flex space-x-8">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <FileUp className="h-4 w-4" />
                  <span>Data Ingestion</span>
                </NavLink>
                <NavLink
                  to="/profile"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <User className="h-4 w-4" />
                  <span>User Profile</span>
                </NavLink>
                <NavLink
                  to="/matching"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-indigo-100 text-indigo-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <Search className="h-4 w-4" />
                  <span>Matching</span>
                </NavLink>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<DataIngestion />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/matching" element={<Matching />} />
            <Route path="/opportunity/:index" element={<OpportunityDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;