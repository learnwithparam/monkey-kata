import { useState, useCallback } from 'react';
import { ChatMessage } from '@/components/demos/ChatMessages';

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
  timestamp: string;
}

interface UseStreamingChatOptions {
  apiEndpoint: string;
  sessionId: string;
  applicationId?: string;
  onApprovalCreated?: (approvalId: string) => void;
}

export function useStreamingChat({
  apiEndpoint,
  sessionId,
  applicationId,
  onApprovalCreated,
}: UseStreamingChatOptions) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [expandedToolCalls, setExpandedToolCalls] = useState<Set<string>>(new Set());

  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'> & { id?: string }) => {
    const newMessage: ChatMessage = {
      ...message,
      id: message.id || `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage.id;
  }, []);

  const toggleToolCall = useCallback((messageId: string) => {
    setExpandedToolCalls(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  }, []);

  const askQuestion = useCallback(async () => {
    if (!message.trim() || isAsking) {
      return;
    }

    const userMessage = message;
    setMessage('');
    setIsAsking(true);
    setCurrentAnswer('');

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
    });

    // Add typing indicator
    const typingMessageId = addMessage({
      type: 'assistant',
      content: '',
      isTyping: true,
    });

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
          application_id: applicationId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let done = false;
      let finalAnswer = '';
      let finalToolCalls: ToolCall[] = [];
      let approvalId: string | null = null;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value);
        
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                addMessage({
                  type: 'system',
                  content: `❌ Error: ${data.error}`,
                });
                setIsAsking(false);
                return;
              }

              if (data.tool_calls) {
                finalToolCalls = data.tool_calls;
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.tool_calls = data.tool_calls;
                  }
                  return newMessages;
                });
              }
              
              if (data.content) {
                finalAnswer += data.content;
                setCurrentAnswer(prev => prev + data.content);
                
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalAnswer;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
              }
              
              if (data.done) {
                const finalContent = data.response || finalAnswer;
                approvalId = data.approval_id || null;
                
                setMessages(prev => {
                  const newMessages = [...prev];
                  const typingMessage = newMessages.find(msg => msg.id === typingMessageId);
                  if (typingMessage) {
                    typingMessage.content = finalContent;
                    typingMessage.tool_calls = data.tool_calls || finalToolCalls;
                    typingMessage.isTyping = false;
                  }
                  return newMessages;
                });
                setCurrentAnswer('');
                setIsAsking(false);
                
                // Callback for approval creation
                if (approvalId && onApprovalCreated) {
                  onApprovalCreated(approvalId);
                }
              }
            } catch (e) {
              console.error('Error parsing streaming data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error asking question:', error);
      
      setMessages(prev => {
        return prev.filter(msg => msg.id !== typingMessageId);
      });
      
      addMessage({
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
      setIsAsking(false);
    }
  }, [message, isAsking, apiEndpoint, sessionId, addMessage, onApprovalCreated]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isAsking || !message.trim()) return;
      askQuestion();
    }
  }, [message, isAsking, askQuestion]);

  return {
    message,
    setMessage,
    messages,
    setMessages,
    isAsking,
    currentAnswer,
    setCurrentAnswer,
    expandedToolCalls,
    toggleToolCall,
    askQuestion,
    handleKeyPress,
    addMessage,
  };
}

