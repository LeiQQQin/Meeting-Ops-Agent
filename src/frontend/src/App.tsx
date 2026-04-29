import React, { useState } from "react";
import { BrowserRouter, Route, Routes, Link, useLocation } from "react-router-dom";
import MeetingList from "./pages/MeetingList";
import MeetingDetail from "./pages/MeetingDetail";
import NewMeeting from "./pages/NewMeeting";
import Dashboard from "./pages/Dashboard";

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const active = location.pathname === to || location.pathname.startsWith(to + "/");
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        active
          ? "bg-blue-700 text-white"
          : "text-blue-100 hover:bg-blue-600 hover:text-white"
      }`}
    >
      {children}
    </Link>
  );
}

function Navigation() {
  return (
    <nav className="bg-blue-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🤖</span>
            <Link to="/" className="text-white font-bold text-lg">
              Meeting Ops Agent
            </Link>
          </div>
          <div className="flex items-center space-x-2">
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/meetings">Meetings</NavLink>
            <NavLink to="/new-meeting">+ New Meeting</NavLink>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/meetings" element={<MeetingList />} />
            <Route path="/meetings/:id" element={<MeetingDetail />} />
            <Route path="/new-meeting" element={<NewMeeting />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
