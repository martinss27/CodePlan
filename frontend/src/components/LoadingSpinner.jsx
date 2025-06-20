import React from 'react';

const LoadingSpinner = ({ 
  size = 'md', 
  color = 'indigo', 
  text = '', 
  fullScreen = false,
  overlay = false 
}) => {
  const sizeClasses = {
    xs: 'w-4 h-4',
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const colorClasses = {
    indigo: 'text-indigo-600',
    blue: 'text-blue-600',
    purple: 'text-purple-600',
    green: 'text-green-600',
    red: 'text-red-600',
    yellow: 'text-yellow-600',
    gray: 'text-gray-600',
    white: 'text-white'
  };

  const SpinnerContent = () => (
    <div className="flex flex-col items-center justify-center space-y-3">
      <div className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin`}>
        <svg className="w-full h-full" fill="none" viewBox="0 0 24 24">
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4"
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
      {text && (
        <p className={`text-sm font-medium ${colorClasses[color]}`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50">
        <SpinnerContent />
      </div>
    );
  }

  if (overlay) {
    return (
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
        <SpinnerContent />
      </div>
    );
  }

  return <SpinnerContent />;
};

// Pulse Loading Component
export const PulseLoader = ({ size = 'md', color = 'indigo' }) => {
  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8'
  };

  const colorClasses = {
    indigo: 'bg-indigo-600',
    blue: 'bg-blue-600',
    purple: 'bg-purple-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
    gray: 'bg-gray-600',
    white: 'bg-white'
  };

  return (
    <div className="flex space-x-1">
      <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-pulse`} style={{ animationDelay: '0ms' }}></div>
      <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-pulse`} style={{ animationDelay: '150ms' }}></div>
      <div className={`${sizeClasses[size]} ${colorClasses[color]} rounded-full animate-pulse`} style={{ animationDelay: '300ms' }}></div>
    </div>
  );
};

// Skeleton Loading Component
export const SkeletonLoader = ({ type = 'text', lines = 1, className = '' }) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return (
          <div className="space-y-2">
            {Array.from({ length: lines }).map((_, index) => (
              <div
                key={index}
                className={`h-4 bg-gray-200 rounded animate-pulse ${className}`}
                style={{ 
                  width: `${Math.random() * 40 + 60}%`,
                  animationDelay: `${index * 100}ms`
                }}
              />
            ))}
          </div>
        );
      
      case 'card':
        return (
          <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
            <div className="flex items-center space-x-4 mb-4">
              <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: '60%' }}></div>
                <div className="h-3 bg-gray-200 rounded animate-pulse" style={{ width: '40%' }}></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: '80%' }}></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: '70%' }}></div>
            </div>
          </div>
        );
      
      case 'avatar':
        return (
          <div className={`w-12 h-12 bg-gray-200 rounded-full animate-pulse ${className}`}></div>
        );
      
      case 'button':
        return (
          <div className={`h-10 bg-gray-200 rounded-lg animate-pulse ${className}`} style={{ width: '120px' }}></div>
        );
      
      default:
        return (
          <div className={`h-4 bg-gray-200 rounded animate-pulse ${className}`}></div>
        );
    }
  };

  return renderSkeleton();
};

// Page Loading Component
export const PageLoader = ({ message = 'Loading...' }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="text-center">
        <div className="w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
          <span className="text-white font-bold text-xl">C</span>
        </div>
        <LoadingSpinner size="lg" color="indigo" text={message} />
      </div>
    </div>
  );
};

export default LoadingSpinner; 