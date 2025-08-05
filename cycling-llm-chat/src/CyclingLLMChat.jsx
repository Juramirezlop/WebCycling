import React, { useState, useRef, useEffect } from 'react';
import { Send, Bike, ChevronDown, AlertCircle, CheckCircle } from 'lucide-react';

const CyclingLLMChat = () => {
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: 'Pregúntame sobre campeones, estadísticas y resultados del ciclismo Colombiano. 🚴‍♂️',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // API URL - cambiar según tu configuración
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Verificar conexión al cargar
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      setConnectionStatus(data.success ? 'connected' : 'error');
    } catch (error) {
      console.error('Error checking connection:', error);
      setConnectionStatus('error');
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userMessage.content })
      });

      const data = await response.json();

      const assistantMessage = {
        type: 'assistant',
        content: data.success ? data.data.answer : `Error: ${data.error}`,
        timestamp: new Date(),
        metadata: data.success ? {
          resultsCount: data.data.results_count,
          sqlQuery: data.data.sql_query
        } : null
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'assistant',
        content: 'Lo siento, hubo un error al procesar tu pregunta. Por favor, verifica que el servidor esté funcionando.',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('es-CO', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const ConnectionIndicator = () => {
    const getStatusInfo = () => {
      switch (connectionStatus) {
        case 'connected':
          return { icon: CheckCircle, color: 'text-green-400', text: 'Conectado' };
        case 'error':
          return { icon: AlertCircle, color: 'text-red-400', text: 'Sin conexión' };
        default:
          return { icon: AlertCircle, color: 'text-yellow-400', text: 'Verificando...' };
      }
    };

    const { icon: Icon, color, text } = getStatusInfo();

    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Icon className={`w-4 h-4 ${color}`} />
        <span>{text}</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-yellow-400 via-blue-500 to-red-500 p-2 rounded-lg">
                <Bike className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-yellow-400 via-blue-500 to-red-500 bg-clip-text text-transparent">
                  Cycling LLM Colombia
                </h1>
                <p className="text-sm text-gray-400">Asistente de Ciclismo Colombiano</p>
              </div>
            </div>
            <ConnectionIndicator />
          </div>
        </div>
      </header>

      {/* Messages Container */}
      <main className="flex-1 overflow-hidden flex flex-col max-w-4xl mx-auto w-full">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                    : message.isError
                    ? 'bg-red-900/20 border border-red-700/30 text-red-200'
                    : 'bg-gray-800/50 border border-gray-700/30 text-gray-100'
                }`}
              >
                <div className="whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </div>
                
                {/* Metadata para respuestas del asistente */}
                {message.metadata && (
                  <div className="mt-3 pt-3 border-t border-gray-600/30">
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <span>📊 {message.metadata.resultsCount} resultados</span>
                      <span>⏱️ {formatTime(message.timestamp)}</span>
                    </div>
                  </div>
                )}
                
                {/* Timestamp */}
                {!message.metadata && (
                  <div className="mt-2 text-xs opacity-60">
                    {formatTime(message.timestamp)}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800/50 border border-gray-700/30 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2 text-gray-400">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse delay-75"></div>
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse delay-150"></div>
                  </div>
                  <span>Buscando información...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-700/50 bg-gray-900/50 backdrop-blur-sm p-4">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Pregunta sobre ciclismo colombiano... (ej: ¿Quién tiene más podios en nacionales?)"
                className="w-full bg-gray-800/50 border border-gray-600/50 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 resize-none transition-all duration-200"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isLoading}
              />
              
              {/* Colombian flag accent */}
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="w-1 h-6 bg-gradient-to-b from-yellow-400 via-blue-500 to-red-500 rounded-full opacity-30"></div>
              </div>
            </div>
            
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-all duration-200 flex items-center justify-center min-w-[48px]"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          
          {/* Suggested questions */}
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              "¿Quién tiene más podios?",
              "Ganadores de 1950",
              "Podio nacional 1947",
              "Campeones por año"
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInput(suggestion)}
                className="text-xs px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 border border-gray-600/30 rounded-full text-gray-300 hover:text-white transition-all duration-200"
                disabled={isLoading}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default CyclingLLMChat;