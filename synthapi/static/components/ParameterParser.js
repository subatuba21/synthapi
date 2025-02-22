// ParameterParser.js
import React, { useState } from 'react';

const ParameterParser = ({ onParametersGenerated }) => {
  const [rawText, setRawText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const parseParameters = () => {
    // This is where we'll implement the parsing logic
    const lines = rawText.split('\n').filter(line => line.trim());
    const parameters = [];
    
    for (let i = 0; i < lines.length; i += 4) {
      if (i + 3 >= lines.length) break;
      
      const name = lines[i].trim();
      const type = lines[i + 1].trim();
      const constraints = lines[i + 2].trim();
      const description = lines[i + 3].trim();
      
      const parameter = {
        name,
        type: type.toLowerCase(),
        required: description.toLowerCase().includes('required'),
        description,
        constraints: {
          min: '',
          max: '',
          enum: []
        }
      };
      
      // Parse constraints
      if (type === 'number' || type === 'integer') {
        const rangeMatch = constraints.match(/([-\d.]+)\s*to\s*([-\d.]+)/);
        if (rangeMatch) {
          parameter.constraints.min = rangeMatch[1];
          parameter.constraints.max = rangeMatch[2];
        }
      } else if (type === 'array') {
        parameter.type = 'array';
        // Could expand this to handle array types better
      }
      
      parameters.push(parameter);
    }
    
    onParametersGenerated(parameters);
    setRawText('');
  };

  return (
    <div className="border rounded-lg p-4 space-y-4 bg-white">
      <h3 className="text-lg font-medium">Bulk Parameter Parser</h3>
      <div className="space-y-2">
        <textarea
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          className="w-full p-2 border rounded h-48"
          placeholder="Paste parameter descriptions here...
Example format:
location
string
length between 1 and 250
Required if either latitude or longitude is not provided..."
        />
        <div className="flex justify-end">
          <button
            type="button"
            onClick={parseParameters}
            disabled={isLoading || !rawText.trim()}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
          >
            {isLoading ? 'Parsing...' : 'Parse Parameters'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ParameterParser;