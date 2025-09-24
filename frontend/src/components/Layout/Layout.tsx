import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  LightBulbIcon,
  CogIcon,
  BellIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, gradient: 'from-blue-500 to-blue-600' },
    { name: 'Sentiment', href: '/sentiment', icon: ChatBubbleLeftRightIcon, gradient: 'from-purple-500 to-purple-600' },
    { name: 'Engagement', href: '/engagement', icon: ChartBarIcon, gradient: 'from-green-500 to-green-600' },
    { name: 'PR Strategy', href: '/pr-strategy', icon: LightBulbIcon, gradient: 'from-amber-500 to-amber-600' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-72 bg-white/95 backdrop-blur-xl shadow-2xl border-r border-gray-200/50">
        {/* Header */}
        <div className="flex h-20 items-center justify-center border-b border-gray-200/50 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
              <ChartBarIcon className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">SportsPR Analytics</h1>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="mt-8 px-6">
          <div className="space-y-3">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group relative flex items-center gap-4 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-300 ${
                    isActive
                      ? `bg-gradient-to-r ${item.gradient} text-white shadow-lg shadow-${item.gradient.split('-')[1]}-500/25 transform scale-105`
                      : 'text-gray-700 hover:bg-gray-50 hover:shadow-md hover:transform hover:scale-102'
                  }`}
                >
                  <div className={`p-2 rounded-xl transition-all duration-300 ${
                    isActive 
                      ? 'bg-white/20' 
                      : 'bg-gray-100 group-hover:bg-gray-200'
                  }`}>
                    <Icon className={`h-5 w-5 transition-colors duration-300 ${
                      isActive ? 'text-white' : 'text-gray-600 group-hover:text-gray-700'
                    }`} />
                  </div>
                  <span className="font-semibold">{item.name}</span>
                  {isActive && (
                    <div className="absolute right-4 w-2 h-2 bg-white rounded-full animate-pulse" />
                  )}
                </Link>
              );
            })}
          </div>
        </nav>
        
        {/* Quick Stats */}
        <div className="mx-6 mt-8 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border border-gray-200/50">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Stats</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">Active Campaigns</span>
              <span className="text-xs font-bold text-blue-600">12</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">Sentiment Score</span>
              <span className="text-xs font-bold text-green-600">+0.82</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">Risk Level</span>
              <span className="text-xs font-bold text-amber-600">Medium</span>
            </div>
          </div>
        </div>
        
        {/* User section */}
        <div className="absolute bottom-0 w-full border-t border-gray-200/50 p-6 bg-white/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
                A
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900">Admin User</p>
              <p className="text-xs text-gray-500">admin@sportspr.com</p>
            </div>
            <CogIcon className="w-5 h-5 text-gray-400 hover:text-gray-600 cursor-pointer transition-colors" />
          </div>
        </div>
      </div>
      
      {/* Main content */}
      <div className="pl-72">
        {/* Top Bar */}
        <div className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search campaigns, metrics, insights..."
                  className="pl-10 pr-4 py-2 w-80 bg-gray-50/80 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all duration-300"
                />
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <BellIcon className="w-6 h-6 text-gray-600 hover:text-gray-800 cursor-pointer transition-colors" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
              </div>
              <div className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-lg">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                Live Monitoring
              </div>
            </div>
          </div>
        </div>
        
        <main className="min-h-screen p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;