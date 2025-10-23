interface AlertMessageProps {
  type: 'warning' | 'info' | 'error' | 'success';
  message: string;
}

export default function AlertMessage({ type, message }: AlertMessageProps) {
  const getAlertClasses = () => {
    switch (type) {
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-700';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <div className={`px-4 py-3 rounded-lg text-sm font-medium border ${getAlertClasses()}`}>
      {message}
    </div>
  );
}
