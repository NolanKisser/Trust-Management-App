import React, { useState } from 'react';

const LLMAnalysis = ({ selectedDevice }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * Helper function to clean the AI output.
   * If it's JSON, it renders a list. If it's text, it strips the quotes.
   */
  const formatAIResponse = (text) => {
    // 1. Remove triple quotes or markdown code blocks
    const cleanText = text.replace(/"""/g, "").replace(/```json/g, "").replace(/```/g, "").trim();

    try {
      // 2. Try to parse as JSON
      const parsed = JSON.parse(cleanText);
      
      // 3. If successful, render a structured list
      return (
        <div className="space-y-2">
          {Object.entries(parsed).map(([key, value]) => (
            <div key={key} className="border-l-2 border-blue-400 pl-3 py-1">
              <span className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter">
                {key.replace(/([A-Z])/g, ' $1')}
              </span>
              <div className="text-sm text-gray-800">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </div>
            </div>
          ))}
        </div>
      );
    } catch (e) {
      // 4. If not JSON, just return the text (with quotes removed)
      return <div className="whitespace-pre-wrap">{cleanText}</div>;
    }
  };

  const startAnalysis = async () => {
    if (!selectedDevice) return;
    setLoading(true);

    const friendlyInitMessage = { 
      role: 'user', 
      parts: `Initiating behavioral diagnostic for ${selectedDevice.id}...` 
    };

    try {
      const res = await fetch('http://localhost:8000/api/llm-analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          device_id: selectedDevice.id, 
          history: [] 
        })
      });
      
      const data = await res.json();

      setMessages([
        friendlyInitMessage, 
        { role: 'model', parts: data.response }
      ]);
    } catch (error) {
      console.error("Analysis Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userText = input;
    setInput("");
    setLoading(true);

    const userMsg = { role: 'user', parts: userText };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await fetch('http://localhost:8000/api/llm-analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          device_id: selectedDevice.id, 
          history: messages, 
          new_message: userText 
        })
      });
      
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'model', parts: data.response }]);
    } catch (error) {
      console.error("Message Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 bg-white shadow-inner">
      <div className="border-b pb-3 mb-4 flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-800">AI Behavioral Analysis</h2>
        {selectedDevice && (
          <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-mono font-bold">
            Target: {selectedDevice.id}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        {!messages.length ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 p-8">
            <div className="text-5xl animate-bounce">🧠</div>
            <h3 className="text-lg font-semibold text-gray-700">Ready for Analysis</h3>
            <p className="text-gray-500 max-w-xs text-sm">
              Click the button below to parse telemetry logs and generate a behavioral security report.
            </p>
            <button 
              onClick={startAnalysis}
              disabled={loading || !selectedDevice}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-md active:scale-95 disabled:opacity-50"
            >
              {loading ? "Crunching Logs..." : `Analyze ${selectedDevice?.id}`}
            </button>
          </div>
        ) : (
          messages.map((m, i) => (
            <div 
              key={i} 
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[90%] p-4 rounded-2xl shadow-sm ${
                m.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-gray-50 text-gray-800 border border-gray-100 rounded-bl-none'
              }`}>
                <div className={`font-bold mb-2 text-[10px] uppercase tracking-widest ${m.role === 'user' ? 'text-blue-100' : 'text-blue-500'}`}>
                  {m.role === 'user' ? 'Operator' : 'AI Analysis Engine'}
                </div>
                
                {/* 5. Dynamically format the content */}
                <div className="leading-relaxed">
                  {m.role === 'user' ? m.parts : formatAIResponse(m.parts)}
                </div>
              </div>
            </div>
          ))
        )}
        {loading && messages.length > 0 && (
          <div className="flex items-center space-x-2 text-xs text-blue-400 italic animate-pulse">
            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            <span>AI is interpreting device patterns...</span>
          </div>
        )}
      </div>

      {messages.length > 0 && (
        <div className="flex gap-2 border-t pt-4 bg-white">
          <input 
            value={input} 
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            className="flex-1 border border-gray-200 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm transition-all"
            placeholder="Ask about specific anomalies..."
            disabled={loading}
          />
          <button 
            onClick={sendMessage} 
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-xl font-bold transition-all shadow-sm"
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
};

export default LLMAnalysis;