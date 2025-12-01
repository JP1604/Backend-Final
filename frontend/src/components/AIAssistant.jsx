import { useState } from 'react';
import { Sparkles, Loader, Check, X, RefreshCw, Play, AlertCircle } from 'lucide-react';
import './AIAssistant.css';

const AIAssistant = ({ onApplySuggestion, currentChallenge }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState('');
  const [language, setLanguage] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState('');
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  
  // Validation state
  const [showValidation, setShowValidation] = useState(false);
  const [solutionCode, setSolutionCode] = useState('');
  const [validating, setValidating] = useState(false);
  const [validationResults, setValidationResults] = useState(null);
  const [validationError, setValidationError] = useState('');

  // API configuration - now uses backend endpoint
  const API_BASE_URL = 'http://localhost:8008';

  const generateSuggestions = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic or category');
      return;
    }

    setLoading(true);
    setError('');
    setSuggestions([]);

    try {
      console.log('Generating challenge via backend for:', topic);
      const result = await generateWithBackend(topic, language);

      if (result) {
        setSuggestions([result]);
        setSelectedSuggestion(0);
      } else {
        setError('The AI did not return any suggestions.');
      }
    } catch (err) {
      console.error('AI Generation Error:', err);
      setError(err.message || 'Error generating challenge suggestion');
    } finally {
      setLoading(false);
    }
  };

  const generateWithBackend = async (topic, language) => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('You must be logged in to use the AI Assistant');
    }

    try {
      const requestBody = { topic };
      if (language && language.trim()) {
        requestBody.language = language.toLowerCase();
      }

      const response = await fetch(`${API_BASE_URL}/ai/generate-challenge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        
        if (response.status === 403) {
          throw new Error('Only professors and administrators can use the AI Assistant');
        }

        if (response.status === 400) {
          throw new Error(errorData.detail || 'Invalid request parameters');
        }

        throw new Error(
          errorData.detail || `Server error: ${response.status}`
        );
      }

      const data = await response.json();
      console.log('✅ Backend generated suggestion:', data);

      return data;
    } catch (err) {
      if (err instanceof TypeError && err.message.includes('fetch')) {
        throw new Error('Could not connect to server. Please make sure the backend is running.');
      }
      throw err;
    }
  };

  const applySuggestion = () => {
    if (selectedSuggestion === null || !suggestions[selectedSuggestion]) return;
    const suggestion = suggestions[selectedSuggestion];
    onApplySuggestion(suggestion);
    setIsOpen(false);
    setSuggestions([]);
    setTopic('');
    setShowValidation(false);
    setValidationResults(null);
  };

  const regenerateSuggestion = () => {
    generateSuggestions();
  };

  const validateTestCases = async () => {
    if (!solutionCode.trim()) {
      setValidationError('Please enter solution code to validate');
      return;
    }

    if (selectedSuggestion === null || !suggestions[selectedSuggestion]) {
      setValidationError('No suggestion selected');
      return;
    }

    const suggestion = suggestions[selectedSuggestion];

    setValidating(true);
    setValidationError('');
    setValidationResults(null);

    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('You must be logged in to validate test cases');
      }

      // Determine language from suggestion or default
      const validationLanguage = suggestion.language || language || 'python';

      // Transform test cases to match backend DTO format
      const formattedTestCases = (suggestion.testCases || suggestion.test_cases || []).map(tc => ({
        input: tc.input || null,  // Input is optional, send null if empty
        expected_output: tc.expected_output || tc.expectedOutput,
        is_hidden: tc.is_hidden !== undefined ? tc.is_hidden : tc.isHidden,
        order_index: tc.order_index || tc.orderIndex
      }));

      const response = await fetch(`${API_BASE_URL}/ai/validate-test-cases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          solution_code: solutionCode,
          language: validationLanguage.toLowerCase(),
          test_cases: formattedTestCases,
          time_limit_ms: suggestion.limits?.time_limit_ms || 5000
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        }
        
        if (response.status === 403) {
          throw new Error('Only professors and administrators can validate test cases');
        }

        throw new Error(
          errorData.detail || `Validation failed: ${response.status}`
        );
      }

      const results = await response.json();
      console.log('✅ Validation results:', results);
      setValidationResults(results);

    } catch (err) {
      console.error('Validation Error:', err);
      setValidationError(err.message || 'Error validating test cases');
    } finally {
      setValidating(false);
    }
  };

  return (
    <>
      {/* Botón para abrir/cerrar el asistente */}
      <button
        type="button"
        className="ai-assistant-toggle"
        onClick={() => setIsOpen(!isOpen)}
        title="Open AI Assistant"
      >
        <Sparkles size={20} />
        AI Assistant
      </button>

      {isOpen && (
        <div className="modal-overlay" onClick={() => setIsOpen(false)}>
          <div
            className="modal-content ai-assistant-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div className="ai-header-title">
                <Sparkles size={24} className="ai-icon" />
                <h3>AI Challenge Assistant</h3>
              </div>
              <button className="btn-close" onClick={() => setIsOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="ai-assistant-content">
              {/* Input de tema */}
              <div className="ai-input-section">
                <label>What topic or category do you want to create a challenge about?</label>
                <div className="ai-input-group">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g., Binary Trees, Sorting Algorithms, Dynamic Programming..."
                    className="ai-topic-input"
                    onKeyDown={(e) => e.key === 'Enter' && generateSuggestions()}
                  />
                </div>
                
                <label style={{ marginTop: '1rem' }}>Preferred language (optional):</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="ai-language-select"
                  style={{ 
                    width: '100%', 
                    padding: '0.5rem', 
                    borderRadius: '8px', 
                    border: '1px solid #ddd',
                    marginBottom: '1rem'
                  }}
                >
                  <option value="">Any language</option>
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                  <option value="nodejs">Node.js</option>
                  <option value="cpp">C++</option>
                </select>

                <button
                  type="button"
                  onClick={generateSuggestions}
                  disabled={loading || !topic.trim()}
                  className="btn-generate"
                  style={{ width: '100%' }}
                >
                  {loading ? <Loader size={18} className="spin" /> : <Sparkles size={18} />}
                  {loading ? 'Generating...' : 'Generate Challenge'}
                </button>
                {error && <div className="ai-error">{error}</div>}
              </div>

              {/* Resultado de la IA */}
              {suggestions.length > 0 && (
                <div className="ai-suggestions">
                  <div className="ai-suggestion-header">
                    <h4>Generated Suggestion</h4>
                    <button
                      type="button"
                      onClick={regenerateSuggestion}
                      className="btn-regenerate"
                      title="Generate another suggestion"
                    >
                      <RefreshCw size={16} />
                      Regenerate
                    </button>
                  </div>

                  {suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className={`ai-suggestion-card ${
                        selectedSuggestion === index ? 'selected' : ''
                      }`}
                      onClick={() => setSelectedSuggestion(index)}
                    >
                      <div className="suggestion-title">
                        <h5>{suggestion.title}</h5>
                        <span className={`difficulty-badge ${suggestion.difficulty}`}>
                          {suggestion.difficulty}
                        </span>
                      </div>

                      <div className="suggestion-description">{suggestion.description}</div>

                      <div className="suggestion-tags">
                        {suggestion.tags?.map((tag, i) => (
                          <span key={i} className="tag">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div className="ai-actions">
                    <button
                      type="button"
                      onClick={applySuggestion}
                      className="btn-apply"
                      disabled={selectedSuggestion === null}
                    >
                      <Check size={18} />
                      Apply Suggestion
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowValidation(!showValidation)}
                      className="btn-validate"
                      disabled={selectedSuggestion === null}
                      style={{ 
                        backgroundColor: showValidation ? '#6c757d' : '#17a2b8',
                        marginLeft: '0.5rem' 
                      }}
                    >
                      <Play size={18} />
                      {showValidation ? 'Hide Validation' : 'Validate Test Cases'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSuggestions([]);
                        setSelectedSuggestion(null);
                        setShowValidation(false);
                        setValidationResults(null);
                      }}
                      className="btn-discard"
                    >
                      <X size={18} />
                      Discard
                    </button>
                  </div>

                  {/* Validation Section */}
                  {showValidation && (
                    <div className="ai-validation-section" style={{
                      marginTop: '1.5rem',
                      padding: '1rem',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '8px',
                      border: '1px solid #dee2e6'
                    }}>
                      <h5 style={{ marginBottom: '1rem', color: '#495057' }}>
                        <AlertCircle size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                        Validate Test Cases
                      </h5>
                      <p style={{ fontSize: '0.9rem', color: '#6c757d', marginBottom: '1rem' }}>
                        Paste your solution code below to verify that the AI-generated test cases produce the correct outputs.
                      </p>

                      <textarea
                        value={solutionCode}
                        onChange={(e) => setSolutionCode(e.target.value)}
                        placeholder={`# Example solution code for: ${suggestions[selectedSuggestion]?.title || 'challenge'}\n\n# Write your solution here...`}
                        style={{
                          width: '100%',
                          minHeight: '200px',
                          fontFamily: 'monospace',
                          fontSize: '0.9rem',
                          padding: '0.75rem',
                          border: '1px solid #ced4da',
                          borderRadius: '4px',
                          marginBottom: '1rem',
                          resize: 'vertical'
                        }}
                      />

                      <button
                        type="button"
                        onClick={validateTestCases}
                        disabled={validating || !solutionCode.trim()}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          backgroundColor: validating ? '#6c757d' : '#28a745',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: validating ? 'not-allowed' : 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          fontSize: '1rem',
                          fontWeight: '500'
                        }}
                      >
                        {validating ? (
                          <>
                            <Loader size={18} className="spin" />
                            Validating...
                          </>
                        ) : (
                          <>
                            <Play size={18} />
                            Run Validation
                          </>
                        )}
                      </button>

                      {validationError && (
                        <div style={{
                          marginTop: '1rem',
                          padding: '0.75rem',
                          backgroundColor: '#f8d7da',
                          color: '#721c24',
                          borderRadius: '4px',
                          border: '1px solid #f5c6cb'
                        }}>
                          {validationError}
                        </div>
                      )}

                      {/* Validation Results */}
                      {validationResults && (
                        <div style={{ marginTop: '1rem' }}>
                          <div style={{
                            padding: '1rem',
                            backgroundColor: validationResults.all_passed ? '#d4edda' : '#fff3cd',
                            border: `1px solid ${validationResults.all_passed ? '#c3e6cb' : '#ffeaa7'}`,
                            borderRadius: '4px',
                            marginBottom: '1rem'
                          }}>
                            <h6 style={{ 
                              margin: '0 0 0.5rem 0',
                              color: validationResults.all_passed ? '#155724' : '#856404'
                            }}>
                              {validationResults.all_passed ? '✅ All Tests Passed!' : '⚠️ Some Tests Failed'}
                            </h6>
                            <p style={{ 
                              margin: 0,
                              fontSize: '0.9rem',
                              color: validationResults.all_passed ? '#155724' : '#856404'
                            }}>
                              {validationResults.passed_count} / {validationResults.total_test_cases} test cases passed
                            </p>
                            <p style={{
                              marginTop: '0.75rem',
                              marginBottom: 0,
                              fontSize: '0.9rem',
                              color: '#495057'
                            }}>
                              {validationResults.recommendation}
                            </p>
                          </div>

                          {/* Detailed Results */}
                          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            {validationResults.validation_results.map((result, idx) => (
                              <div
                                key={idx}
                                style={{
                                  padding: '0.75rem',
                                  marginBottom: '0.5rem',
                                  backgroundColor: 'white',
                                  border: `2px solid ${result.passed ? '#28a745' : '#dc3545'}`,
                                  borderRadius: '4px'
                                }}
                              >
                                <div style={{ 
                                  display: 'flex', 
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  marginBottom: '0.5rem'
                                }}>
                                  <strong style={{ color: '#495057' }}>
                                    Test Case #{result.order_index}
                                  </strong>
                                  <span style={{
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    fontSize: '0.85rem',
                                    fontWeight: 'bold',
                                    backgroundColor: result.passed ? '#d4edda' : '#f8d7da',
                                    color: result.passed ? '#155724' : '#721c24'
                                  }}>
                                    {result.passed ? '✓ PASSED' : '✗ FAILED'}
                                  </span>
                                </div>

                                <div style={{ fontSize: '0.85rem', color: '#6c757d' }}>
                                  <div style={{ marginBottom: '0.25rem' }}>
                                    <strong>Input:</strong> <code>{result.input && result.input.trim() ? result.input : '(no input)'}</code>
                                  </div>
                                  <div style={{ marginBottom: '0.25rem' }}>
                                    <strong>Expected:</strong> <code>{result.expected_output}</code>
                                  </div>
                                  <div style={{ marginBottom: '0.25rem' }}>
                                    <strong>Actual:</strong> <code style={{ 
                                      color: result.passed ? '#28a745' : '#dc3545' 
                                    }}>
                                      {result.actual_output || '(no output)'}
                                    </code>
                                  </div>
                                  {result.execution_time_ms && (
                                    <div style={{ marginTop: '0.25rem', fontSize: '0.8rem', color: '#6c757d' }}>
                                      ⏱️ Execution time: {result.execution_time_ms}ms
                                    </div>
                                  )}
                                  {result.error && (
                                    <div style={{
                                      marginTop: '0.5rem',
                                      padding: '0.5rem',
                                      backgroundColor: '#f8d7da',
                                      color: '#721c24',
                                      borderRadius: '4px',
                                      fontSize: '0.8rem'
                                    }}>
                                      <strong>Error:</strong> {result.error}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Mensaje inicial */}
              {suggestions.length === 0 && !loading && (
                <div className="ai-info">
                  <Sparkles size={48} className="ai-info-icon" />
                  <h4>How the AI Assistant helps you:</h4>
                  <ul>
                    <li>🎯 Generate challenge ideas based on topics</li>
                    <li>📝 Create problem descriptions and constraints</li>
                    <li>✅ Propose example test cases with input/output</li>
                    <li>🏷️ Suggest relevant tags and difficulty levels</li>
                  </ul>
                  <p className="ai-disclaimer">
                    <strong>Note:</strong> AI suggestions should be reviewed and validated by the
                    instructor before publishing.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistant;
