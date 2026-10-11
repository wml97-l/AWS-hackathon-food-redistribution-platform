import { useState } from 'react';
import './GapAnalysis.css';

const API_BASE = 'http://localhost:5001';

const SAMPLE_PROMPTS = [
  // Original prompts
  "We have 50kg of dairy products expiring tomorrow in Dublin",
  "Find charities in Cork that need tinned goods",
  "What are the active requests for drinks in Dublin?",
  "Which Gold tier charities have capacity for 100kg orders?",
  "Show me charities in Galway that prefer SMD products",
  "We have surplus bread and bakery items in Dublin, who should receive them?",
  "Find the best match for 200kg of frozen vegetables in Cork",
  "Which charities have active requests right now?",
  "Recommend charities for a large donation of tinned food in Dublin",

  // Location-based queries
  "List all charities operating in Dublin",
  "Which Cork charities have the highest order capacity?",
  "Find Galway charities that accept frozen goods",
  "Show me Dublin charities with active requests",
  "What charities in Cork prefer dairy products?",
  "Are there any Gold tier charities in Galway?",
  "Compare charity capacity between Dublin and Cork",
  "Which location has the most active requests?",
  "Find charities near Dublin city centre",
  "Show all Bronze tier charities in Cork",

  // Food category queries
  "Who needs dairy products right now?",
  "Find charities that accept frozen meat",
  "Which charities prefer fresh produce?",
  "Show me charities that take ambient goods",
  "Who has requested tinned vegetables?",
  "Find matches for chilled ready meals",
  "Which charities accept drinks and beverages?",
  "Who wants bakery products in Dublin?",
  "Find charities that need breakfast cereals",
  "Show charities accepting fruit and vegetables",
  "Who takes pasta and rice donations?",
  "Find charities needing baby food",
  "Which charities accept confectionery?",
  "Who needs cooking oils and sauces?",
  "Find matches for sandwich platters",

  // Quantity-based queries
  "We have 500kg of mixed groceries to donate",
  "Find a charity that can handle 25kg of yoghurt",
  "Who can accept a small donation of 10kg?",
  "Match 150kg of frozen goods to the right charity",
  "We have 75kg of surplus bread",
  "Find charities for a 300kg pallet of tinned goods",
  "Who can handle bulk donations over 200kg?",
  "Small batch of 15kg dairy needs a home",
  "Match 1000kg of ambient products",
  "We have exactly 42kg of mixed chilled items",

  // Tier-based queries
  "Show all Gold tier charity profiles",
  "Which Silver tier charities are in Dublin?",
  "Compare Gold vs Bronze tier capacity",
  "Find the highest capacity Gold members",
  "Which tier has the most active requests?",
  "Show Bronze charities that need support",
  "List Silver tier charities with dairy preference",
  "Which Gold charities haven't ordered recently?",
  "Find top performing Bronze tier charities",
  "Show tier distribution across all locations",

  // Urgency and expiry queries
  "Dairy expiring today - who can collect in Dublin?",
  "Urgent: 100kg of chilled goods need redistribution",
  "Find fastest responders for perishable items",
  "Short shelf life products need immediate matching",
  "Who can accept same-day donations in Cork?",
  "Emergency surplus - 200kg fresh produce",
  "Expiring frozen goods need urgent placement",
  "Find charities for end-of-day bakery surplus",
  "Quick match needed for 50kg of sandwiches",
  "Perishable dairy - who's closest in Galway?",

  // Preference and history queries
  "Which charities consistently order dairy?",
  "Show charities with diverse food preferences",
  "Find charities that haven't received tinned goods lately",
  "Who has the longest history with FoodCloud?",
  "Which charities order most frequently?",
  "Show preference patterns for Dublin charities",
  "Find charities open to trying new categories",
  "Who typically accepts large orders?",
  "Which charities prefer variety in donations?",
  "Show ordering trends for Cork charities",

  // Matching and recommendation queries
  "Best match for mixed ambient groceries in Dublin",
  "Recommend top 5 charities for frozen goods",
  "Who's the ideal recipient for 80kg of drinks?",
  "Find optimal matches for dairy in Cork",
  "Suggest charities for weekly bread donations",
  "Best fit for regular small donations",
  "Match surplus Christmas goods to charities",
  "Recommend charities for cafe surplus",
  "Find matches for restaurant end-of-service food",
  "Best charities for supermarket write-offs",

  // Analytical queries
  "What's the total demand for dairy across all charities?",
  "Show supply vs demand for tinned goods",
  "Which food category has the most unmet requests?",
  "Analyse charity capacity utilisation",
  "What percentage of requests are being fulfilled?",
  "Show the most requested food categories",
  "Which charities are underserved?",
  "Identify gaps in current food distribution",
  "Compare request volumes by location",
  "What's the average order size by tier?",
];

function GapAnalysis() {
  const [query, setQuery] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [response, setResponse] = useState(null);
  const [clarificationInput, setClarificationInput] = useState('');
  const [error, setError] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const sendQuery = async (queryText, action = 'query') => {
    setIsQuerying(true);
    setError(null);
    setShowDetails(false);
    try {
      const res = await fetch(`${API_BASE}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          session_id: sessionId,
          action: action
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error || `Server error: ${res.status}`);
      }

      const data = await res.json();

      // Check for error in response body
      if (data.status === 'error') {
        throw new Error(data.error || 'Unknown error from agent');
      }

      // Store session ID for conversation continuity
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      setResponse(data);
    } catch (err) {
      let errorMessage = 'Error connecting to AI agent';
      if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
        errorMessage = 'Cannot connect to server. Is the Flask server running on port 5001?';
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setResponse(null);
    }
    setIsQuerying(false);
  };

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    await sendQuery(query, 'query');
  };

  const handleRefine = async () => {
    await sendQuery('Please provide more detail and analysis', 'refine');
  };

  const handleClarificationSubmit = async (e) => {
    e.preventDefault();
    if (!clarificationInput.trim()) return;
    await sendQuery(clarificationInput, 'clarify');
    setClarificationInput('');
  };

  const handleOptionClick = async (option) => {
    await sendQuery(option, 'clarify');
  };

  const handleNewConversation = () => {
    setSessionId(null);
    setResponse(null);
    setQuery('');
    setClarificationInput('');
    setShowDetails(false);
  };

  const handleGeneratePrompt = () => {
    const randomPrompt = SAMPLE_PROMPTS[Math.floor(Math.random() * SAMPLE_PROMPTS.length)];
    setQuery(randomPrompt);
  };

  const renderGenericResponse = (data) => {
    // Filter out internal/meta fields for details view
    const displayData = { ...data };
    delete displayData.session_id;
    delete displayData.status;

    // Extract summary - check common summary field names
    const summary = data.summary || data.message || data.response || data.answer || data.text || data.result;
    const hasSummary = typeof summary === 'string' && summary.length > 0;

    // Format JSON with syntax highlighting
    const formatJsonWithHighlighting = (obj) => {
      const jsonString = JSON.stringify(obj, null, 2);
      return jsonString
        .replace(/(".*?"):/g, '<span class="json-hl-key">$1</span>:')
        .replace(/: (".*?")/g, ': <span class="json-hl-string">$1</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span class="json-hl-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-hl-bool">$1</span>')
        .replace(/: (null)/g, ': <span class="json-hl-null">$1</span>');
    };

    return (
      <div className="ai-response-box complete">
        {hasSummary ? (
          <div className="summary-text">{summary}</div>
        ) : (
          <div className="summary-text fallback">Response received. Click "Show Details" to view the full data.</div>
        )}

        <button
          className="details-toggle"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>

        {showDetails && (
          <div className="details-panel">
            <pre
              className="json-viewer"
              dangerouslySetInnerHTML={{ __html: formatJsonWithHighlighting(displayData) }}
            />
          </div>
        )}

        <div className="response-actions">
          <button className="refine-btn" onClick={handleRefine} disabled={isQuerying}>
            {isQuerying ? 'Refining...' : 'Refine Answer'}
          </button>
          <button className="new-btn" onClick={handleNewConversation}>
            New Question
          </button>
        </div>
      </div>
    );
  };

  const renderResponse = () => {
    if (!response) return null;

    // Clarification needed
    if (response.status === 'needs_clarification') {
      return (
        <div className="ai-response-box clarification">
          <div className="clarification-header">
            <span className="clarification-icon">?</span>
            <strong>Clarification Needed</strong>
          </div>
          <p className="clarification-question">{response.question}</p>
          {response.context && (
            <p className="clarification-context">{response.context}</p>
          )}
          {response.options && response.options.length > 0 && (
            <div className="clarification-options">
              {response.options.map((option, idx) => (
                <button
                  key={idx}
                  className="option-btn"
                  onClick={() => handleOptionClick(option)}
                  disabled={isQuerying}
                >
                  {option}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={handleClarificationSubmit} className="clarification-form">
            <input
              type="text"
              placeholder="Or type your answer..."
              value={clarificationInput}
              onChange={(e) => setClarificationInput(e.target.value)}
              disabled={isQuerying}
            />
            <button type="submit" disabled={isQuerying || !clarificationInput.trim()}>
              Send
            </button>
          </form>
        </div>
      );
    }

    // Complete response with recommendations
    if (response.recommended_charities && response.recommended_charities.length > 0) {
      return (
        <div className="ai-response-box complete">
          {response.summary && (
            <p className="response-summary">{response.summary}</p>
          )}
          <div className="recommendations-list">
            {response.recommended_charities.map((charity, idx) => (
              <div key={idx} className={`recommendation-card tier-${charity.tier?.toLowerCase()}`}>
                <div className="recommendation-header">
                  <span className="charity-name">{charity.name}</span>
                  <span className={`tier-badge ${charity.tier?.toLowerCase()}`}>{charity.tier}</span>
                </div>
                <p className="recommendation-reason">{charity.reason}</p>
                {charity.score && (
                  <span className={`score-badge score-${charity.score?.toLowerCase()}`}>
                    {charity.score}
                  </span>
                )}
              </div>
            ))}
          </div>
          <div className="response-actions">
            <button className="refine-btn" onClick={handleRefine} disabled={isQuerying}>
              {isQuerying ? 'Refining...' : 'Refine Answer'}
            </button>
            <button className="new-btn" onClick={handleNewConversation}>
              New Question
            </button>
          </div>
        </div>
      );
    }

    // Text response fallback - check if it's JSON
    if (response.text_response) {
      // Try to parse as JSON
      let parsedJson = null;
      try {
        const trimmed = response.text_response.trim();
        if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
          parsedJson = JSON.parse(trimmed);
        }
      } catch (e) {
        // Not valid JSON, that's fine
      }

      // If it's JSON, use the generic renderer
      if (parsedJson) {
        return renderGenericResponse({ ...parsedJson, session_id: response.session_id });
      }

      // Otherwise show as plain text
      return (
        <div className="ai-response-box complete">
          <div className="summary-text">{response.text_response}</div>
          <div className="response-actions">
            <button className="refine-btn" onClick={handleRefine} disabled={isQuerying}>
              {isQuerying ? 'Refining...' : 'Refine Answer'}
            </button>
            <button className="new-btn" onClick={handleNewConversation}>
              New Question
            </button>
          </div>
        </div>
      );
    }

    // Generic fallback for any other JSON structure
    return renderGenericResponse(response);
  };

  return (
    <div className="gap-analysis-enhanced">
      <div className="gap-header-section">
        <div className="gap-header-title">
          <h2>MealMap Intelligence</h2>
          {sessionId && (
            <span className="session-indicator" title={`Session: ${sessionId}`}>
              Conversation active
            </span>
          )}
        </div>

        <div className="ai-input-section">
          <form onSubmit={handleQuerySubmit} className="ai-input-wrapper">
            <button
              type="button"
              className="ai-icon-btn"
              onClick={handleGeneratePrompt}
              disabled={isQuerying}
              title="Generate sample prompt"
            >
              ✨
            </button>
            <input
              type="text"
              className="ai-input"
              placeholder="Ask about shortages in Dublin, or find matches for expiring dairy..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isQuerying}
            />
            <button type="submit" className="ai-submit-btn" disabled={isQuerying || !query.trim()}>
              {isQuerying ? 'Thinking...' : 'Ask'}
            </button>
          </form>
          {error && (
            <div className="ai-error-box">
              <span className="error-icon">!</span>
              <span className="error-message">{error}</span>
              <button className="close-error" onClick={() => setError(null)}>x</button>
            </div>
          )}
          {renderResponse()}
        </div>
      </div>
    </div>
  );
}

export default GapAnalysis;
