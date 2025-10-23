interface ChallengeHeaderProps {
  title: string;
  difficulty?: 'Easy' | 'Medium' | 'Hard';
  estimatedTime?: string;
  tags?: string[];
}

export default function ChallengeHeader({ title, difficulty, estimatedTime, tags }: ChallengeHeaderProps) {
  const getDifficultyColor = (level?: string) => {
    switch (level) {
      case 'Easy':
        return 'bg-green-100 text-green-800';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'Hard':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{title}</h1>
      
      <div className="flex flex-wrap items-center gap-4 mb-4">
        {difficulty && (
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(difficulty)}`}>
            {difficulty}
          </span>
        )}
        
        {estimatedTime && (
          <span className="text-sm text-gray-600">
            ⏱️ {estimatedTime}
          </span>
        )}
      </div>

      {tags && tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, index) => (
            <span 
              key={index}
              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-md"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
