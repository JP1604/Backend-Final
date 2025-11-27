import { useState, useEffect } from 'react';
import { Plus, Trash2, Eye, EyeOff, Save, X } from 'lucide-react';
import './TestCaseManager.css';

/**
 * Test Case Manager Component
 * Manages test cases for a challenge (create, edit, delete, toggle visibility)
 */
const TestCaseManager = ({ challengeId, initialTestCases = [], onSave, onClose }) => {
  const [testCases, setTestCases] = useState(initialTestCases);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setTestCases(initialTestCases);
  }, [initialTestCases]);

  const addTestCase = () => {
    setTestCases([
      ...testCases,
      {
        input: '',
        expected_output: '',
        is_hidden: false,
        order_index: testCases.length
      }
    ]);
  };

  const updateTestCase = (index, field, value) => {
    const updated = [...testCases];
    updated[index] = { ...updated[index], [field]: value };
    setTestCases(updated);
  };

  const deleteTestCase = (index) => {
    const updated = testCases.filter((_, i) => i !== index);
    // Update order indices
    updated.forEach((tc, i) => tc.order_index = i);
    setTestCases(updated);
  };

  const toggleVisibility = (index) => {
    const updated = [...testCases];
    updated[index] = { ...updated[index], is_hidden: !updated[index].is_hidden };
    setTestCases(updated);
  };

  const handleSave = async () => {
    setError('');

    // Validation
    if (testCases.length === 0) {
      setError('At least one test case is required');
      return;
    }

    for (let i = 0; i < testCases.length; i++) {
      if (!testCases[i].expected_output.trim()) {
        setError(`Test case ${i + 1}: Expected output is required`);
        return;
      }
    }

    setSaving(true);
    try {
      await onSave(testCases);
    } catch (err) {
      setError(err.message || 'Failed to save test cases');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="testcase-manager">
      <div className="testcase-header">
        <h3>Manage Test Cases</h3>
        <button className="btn-close" onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      <div className="testcase-content">
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <div className="testcase-info">
          <p>
            <strong>Public test cases</strong> are visible to students and help them understand the problem.
            <strong> Hidden test cases</strong> are used for evaluation but not shown to students.
          </p>
        </div>

        <div className="testcases-list">
          {testCases.map((testCase, index) => (
            <div key={index} className={`testcase-item ${testCase.is_hidden ? 'hidden-case' : 'public-case'}`}>
              <div className="testcase-header-row">
                <span className="testcase-number">Test Case {index + 1}</span>
                <div className="testcase-actions">
                  <button
                    type="button"
                    onClick={() => toggleVisibility(index)}
                    className="btn-icon"
                    title={testCase.is_hidden ? 'Make Public' : 'Make Hidden'}
                  >
                    {testCase.is_hidden ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteTestCase(index)}
                    className="btn-icon btn-danger"
                    title="Delete Test Case"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="testcase-fields">
                <div className="form-group">
                  <label>Input {testCase.is_hidden && <span className="badge-hidden">HIDDEN</span>}</label>
                  <textarea
                    value={testCase.input || ''}
                    onChange={(e) => updateTestCase(index, 'input', e.target.value)}
                    placeholder="Input data for this test case (optional if no input needed)"
                    rows={3}
                  />
                  <small>Leave empty if the challenge doesn't require input</small>
                </div>

                <div className="form-group">
                  <label>Expected Output * {testCase.is_hidden && <span className="badge-hidden">HIDDEN</span>}</label>
                  <textarea
                    value={testCase.expected_output}
                    onChange={(e) => updateTestCase(index, 'expected_output', e.target.value)}
                    placeholder="Expected output for this test case"
                    rows={3}
                    required
                  />
                </div>
              </div>
            </div>
          ))}

          {testCases.length === 0 && (
            <div className="empty-testcases">
              <p>No test cases yet. Add at least one to validate solutions.</p>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={addTestCase}
          className="btn-add-testcase"
        >
          <Plus size={18} />
          Add Test Case
        </button>

        <div className="testcase-footer">
          <div className="testcase-summary">
            <span>
              Total: {testCases.length} test case{testCases.length !== 1 ? 's' : ''}
            </span>
            <span>
              Public: {testCases.filter(tc => !tc.is_hidden).length}
            </span>
            <span>
              Hidden: {testCases.filter(tc => tc.is_hidden).length}
            </span>
          </div>

          <div className="testcase-actions-footer">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || testCases.length === 0}
              className="btn-save"
            >
              <Save size={18} />
              {saving ? 'Saving...' : 'Save Test Cases'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn-cancel"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestCaseManager;
