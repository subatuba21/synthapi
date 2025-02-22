const { useState } = React;

function ApiForm() {
  const [endpoints, setEndpoints] = useState([{
    name: '',
    method: 'GET',
    path: '',
    parameters: [{
      name: '',
      type: 'string',
      required: false,
      description: '',
      constraints: {
        min: '',
        max: '',
        enum: []
      }
    }]
  }]);

  const addEndpoint = () => {
    setEndpoints([...endpoints, {
      name: '',
      method: 'GET',
      path: '',
      parameters: [{
        name: '',
        type: 'string',
        required: false,
        description: '',
        constraints: {
          min: '',
          max: '',
          enum: []
        }
      }]
    }]);
  };

  const removeEndpoint = (index) => {
    setEndpoints(endpoints.filter((_, i) => i !== index));
  };

  const addParameter = (endpointIndex) => {
    const newEndpoints = [...endpoints];
    newEndpoints[endpointIndex].parameters.push({
      name: '',
      type: 'string',
      required: false,
      description: '',
      constraints: {
        min: '',
        max: '',
        enum: []
      }
    });
    setEndpoints(newEndpoints);
  };

  const removeParameter = (endpointIndex, paramIndex) => {
    const newEndpoints = [...endpoints];
    newEndpoints[endpointIndex].parameters = 
      newEndpoints[endpointIndex].parameters.filter((_, i) => i !== paramIndex);
    setEndpoints(newEndpoints);
  };

  const handleEndpointChange = (index, field, value) => {
    const newEndpoints = [...endpoints];
    newEndpoints[index][field] = value;
    setEndpoints(newEndpoints);
  };

  const handleParameterChange = (endpointIndex, paramIndex, field, value) => {
    const newEndpoints = [...endpoints];
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      newEndpoints[endpointIndex].parameters[paramIndex][parent][child] = value;
    } else {
      newEndpoints[endpointIndex].parameters[paramIndex][field] = value;
    }
    setEndpoints(newEndpoints);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const openApiSpec = {
      openapi: '3.0.0',
      info: {
        title: 'Generated API Spec',
        version: '1.0.0'
      },
      paths: {}
    };

    endpoints.forEach(endpoint => {
      const parameters = endpoint.parameters.map(param => ({
        name: param.name,
        in: 'query',
        required: param.required,
        schema: {
          type: param.type,
          ...(param.constraints.min && { minimum: Number(param.constraints.min) }),
          ...(param.constraints.max && { maximum: Number(param.constraints.max) }),
          ...(param.constraints.enum.length && { enum: param.constraints.enum })
        },
        description: param.description
      }));

      openApiSpec.paths[endpoint.path] = {
        [endpoint.method.toLowerCase()]: {
          summary: endpoint.name,
          parameters
        }
      };
    });

    try {
      const response = await fetch('/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(openApiSpec)
      });
      
      if (response.ok) {
        alert('OpenAPI specification saved successfully!');
        window.close();  // Attempt to close the window
      } else {
        alert('Failed to save specification');
      }
    } catch (error) {
      alert('Error saving specification: ' + error.message);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">API Definition Form</h1>
          <button
            type="button"
            onClick={addEndpoint}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Add Endpoint
          </button>
        </div>

        {endpoints.map((endpoint, endpointIndex) => (
          <div key={endpointIndex} className="border rounded-lg p-4 space-y-4 bg-white">
            <div className="flex justify-between items-start">
              <h2 className="text-xl font-semibold">Endpoint {endpointIndex + 1}</h2>
              <button
                type="button"
                onClick={() => removeEndpoint(endpointIndex)}
                className="text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={endpoint.name}
                  onChange={(e) => handleEndpointChange(endpointIndex, 'name', e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="Search Businesses"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Method</label>
                <select
                  value={endpoint.method}
                  onChange={(e) => handleEndpointChange(endpointIndex, 'method', e.target.value)}
                  className="w-full p-2 border rounded"
                >
                  <option>GET</option>
                  <option>POST</option>
                  <option>PUT</option>
                  <option>DELETE</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Path</label>
                <input
                  type="text"
                  value={endpoint.path}
                  onChange={(e) => handleEndpointChange(endpointIndex, 'path', e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="/v3/businesses/search"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Parameters</h3>
                <button
                  type="button"
                  onClick={() => addParameter(endpointIndex)}
                  className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Add Parameter
                </button>
              </div>

              {endpoint.parameters.map((param, paramIndex) => (
                <div key={paramIndex} className="border rounded p-4 space-y-4">
                  <div className="flex justify-between items-start">
                    <h4 className="font-medium">Parameter {paramIndex + 1}</h4>
                    <button
                      type="button"
                      onClick={() => removeParameter(endpointIndex, paramIndex)}
                      className="text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={param.name}
                        onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'name', e.target.value)}
                        className="w-full p-2 border rounded"
                        placeholder="location"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Type</label>
                      <select
                        value={param.type}
                        onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'type', e.target.value)}
                        className="w-full p-2 border rounded"
                      >
                        <option>string</option>
                        <option>number</option>
                        <option>integer</option>
                        <option>boolean</option>
                        <option>array</option>
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium mb-1">Description</label>
                      <textarea
                        value={param.description}
                        onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'description', e.target.value)}
                        className="w-full p-2 border rounded"
                        rows="2"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Required</label>
                      <input
                        type="checkbox"
                        checked={param.required}
                        onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'required', e.target.checked)}
                        className="h-4 w-4"
                      />
                    </div>

                    {(param.type === 'number' || param.type === 'integer') && (
                      <>
                        <div>
                          <label className="block text-sm font-medium mb-1">Minimum</label>
                          <input
                            type="number"
                            value={param.constraints.min}
                            onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'constraints.min', e.target.value)}
                            className="w-full p-2 border rounded"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">Maximum</label>
                          <input
                            type="number"
                            value={param.constraints.max}
                            onChange={(e) => handleParameterChange(endpointIndex, paramIndex, 'constraints.max', e.target.value)}
                            className="w-full p-2 border rounded"
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Generate OpenAPI Spec
          </button>
        </div>
      </form>
    </div>
  );
}

ReactDOM.render(<ApiForm />, document.getElementById('root'));