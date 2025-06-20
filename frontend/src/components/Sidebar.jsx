import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function Sidebar({ isOpen, onClose }) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const menuItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: '📊',
      description: 'Overview of your projects'
    },
    {
      name: 'Projects',
      path: '/projects',
      icon: '📁',
      description: 'Manage your projects'
    },
    {
      name: 'Tasks',
      path: '/tasks',
      icon: '✅',
      description: 'Track your tasks'
    },
    {
      name: 'Team',
      path: '/team',
      icon: '👥',
      description: 'Team collaboration'
    },
    {
      name: 'Analytics',
      path: '/analytics',
      icon: '📈',
      description: 'Project analytics'
    },
    {
      name: 'Settings',
      path: '/settings',
      icon: '⚙️',
      description: 'Account settings'
    }
  ];

  const handleItemClick = (path) => {
    navigate(path);
    if (onClose) onClose();
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-white shadow-lg z-50 transition-all duration-300 ease-in-out
        ${collapsed ? 'w-16' : 'w-64'}
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
              <span className="text-xl font-bold text-gray-800">CodePlan</span>
            </div>
          )}
          
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-2">
          {menuItems.map((item, index) => (
            <button
              key={index}
              onClick={() => handleItemClick(item.path)}
              className={`
                w-full flex items-center space-x-3 p-3 rounded-lg transition-all duration-200 group
                ${isActive(item.path)
                  ? 'bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 border border-indigo-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }
              `}
              title={collapsed ? item.name : ''}
            >
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-lg transition-colors
                ${isActive(item.path)
                  ? 'bg-indigo-100 text-indigo-600'
                  : 'bg-gray-100 text-gray-500 group-hover:bg-indigo-100 group-hover:text-indigo-600'
                }
              `}>
                <span className="text-lg">{item.icon}</span>
              </div>
              
              {!collapsed && (
                <div className="flex-1 text-left">
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-gray-500">{item.description}</div>
                </div>
              )}
            </button>
          ))}
        </nav>

        {/* Bottom Section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          {!collapsed && (
            <div className="mb-4 p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
              <div className="text-sm font-medium text-indigo-700 mb-1">Pro Plan</div>
              <div className="text-xs text-indigo-600 mb-2">Unlock all features</div>
              <button className="w-full bg-indigo-600 text-white text-xs py-2 px-3 rounded-lg hover:bg-indigo-700 transition-colors">
                Upgrade
              </button>
            </div>
          )}
          
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">JD</span>
            </div>
            {!collapsed && (
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">John Doe</div>
                <div className="text-xs text-gray-500">john@example.com</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default Sidebar; 