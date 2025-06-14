'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

interface Message {
  id: string
  content: string
  sender: 'user' | 'agent'
  agentName?: string
  timestamp: string
  agentType?: 'lead' | 'followup'
  mentionedAgent?: string
}

interface ConversationState {
  ready_for_action: boolean
  lead_agent: string
  questions_asked: string[]
  answers_collected: Record<string, unknown>
}

const agentConfig = {
  Alex: { color: 'bg-blue-500', description: 'Strategic Planning' },
  Dana: { color: 'bg-purple-500', description: 'Creative Content' },
  Riley: { color: 'bg-green-500', description: 'Data Analysis' },
  Jamie: { color: 'bg-orange-500', description: 'Operations' }
}

export default function AgentOSChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversationState, setConversationState] = useState<ConversationState | null>(null)
  const [showAgentDropdown, setShowAgentDropdown] = useState(false)
  const [mentionedAgent, setMentionedAgent] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle @ mention detection
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value
    setInput(value)

    // Check for @ mention
    const atIndex = value.lastIndexOf('@')
    console.log('@ detection:', { value, atIndex, showDropdown: showAgentDropdown })
    
    if (atIndex !== -1 && atIndex === value.length - 1) {
      // Show dropdown when @ is typed at the end
      console.log('Showing dropdown for @')
      setShowAgentDropdown(true)
    } else if (atIndex !== -1) {
      // Check if typing agent name after @
      const afterAt = value.substring(atIndex + 1)
      const agents = Object.keys(agentConfig)
      const matchingAgent = agents.find(agent => 
        agent.toLowerCase().startsWith(afterAt.toLowerCase()) && afterAt.length > 0
      )
      
      console.log('After @:', { afterAt, matchingAgent })
      
      if (matchingAgent && afterAt.length > 0 && !afterAt.includes(' ')) {
        setShowAgentDropdown(true)
      } else if (afterAt.includes(' ') || afterAt.length === 0) {
        setShowAgentDropdown(false)
      }
    } else {
      setShowAgentDropdown(false)
    }

    // Extract mentioned agent from completed mention
    const mentionMatch = value.match(/@(\w+)/)
    if (mentionMatch && Object.keys(agentConfig).includes(mentionMatch[1])) {
      setMentionedAgent(mentionMatch[1])
      console.log('Mentioned agent:', mentionMatch[1])
    } else {
      setMentionedAgent(null)
    }
  }

  // Handle agent selection from dropdown
  const selectAgent = (agentName: string) => {
    const atIndex = input.lastIndexOf('@')
    if (atIndex !== -1) {
      const beforeAt = input.substring(0, atIndex)
      const afterAt = input.substring(atIndex + 1)
      const spaceIndex = afterAt.indexOf(' ')
      const afterMention = spaceIndex !== -1 ? afterAt.substring(spaceIndex) : ''
      
      setInput(`${beforeAt}@${agentName}${afterMention.startsWith(' ') ? afterMention : ' ' + afterMention}`)
      setMentionedAgent(agentName)
    }
    setShowAgentDropdown(false)
    inputRef.current?.focus()
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date().toISOString(),
      mentionedAgent: mentionedAgent || undefined
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setMentionedAgent(null)
    setIsLoading(true)

    try {
      const endpoint = conversationId 
        ? `/chat/continue/${conversationId}`
        : '/chat/start'
      
      const requestBody: { message: string; mentioned_agent?: string } = { message: input }
      if (mentionedAgent) {
        requestBody.mentioned_agent = mentionedAgent
      }
      
      const response = await fetch(`https://agentos-production-6348.up.railway.app${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      
      // Set conversation ID if this is the first message
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      // Update conversation state
      if (data.conversation_state) {
        setConversationState(data.conversation_state)
      }

      // Add agent responses
      if (data.agent_responses) {
        const agentMessages: Message[] = data.agent_responses.map((response: { content: string; agent_name: string; timestamp: string; agent_type: string }, index: number) => ({
          id: `${Date.now()}-${index}`,
          content: response.content,
          sender: 'agent' as const,
          agentName: response.agent_name,
          timestamp: response.timestamp,
          agentType: response.agent_type
        }))

        setMessages(prev => [...prev, ...agentMessages])
      }

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: 'Sorry, I encountered an error. Please make sure the backend server is running.',
        sender: 'agent',
        agentName: 'System',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (showAgentDropdown) {
        // Select first agent in dropdown
        const agents = Object.keys(agentConfig)
        if (agents.length > 0) {
          selectAgent(agents[0])
        }
      } else {
        sendMessage()
      }
    } else if (e.key === 'Escape') {
      setShowAgentDropdown(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm mb-6 p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent OS V2</h1>
              <p className="text-gray-600">Multi-Agent Conversational Platform</p>
            </div>
            <Link 
              href="/settings" 
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
            >
              Settings
            </Link>
          </div>
          
          {/* Agent Status */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(agentConfig).map(([name, config]) => (
              <div key={name} className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                <div className={`w-3 h-3 rounded-full ${config.color}`}></div>
                <div>
                  <p className="font-medium text-sm">{name}</p>
                  <p className="text-xs text-gray-500">{config.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Interface */}
        <div className="bg-white rounded-lg shadow-sm h-[600px] flex flex-col relative">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Conversation</h2>
              {conversationState && (
                <div className="flex gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    conversationState.ready_for_action 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {conversationState.ready_for_action ? "Ready for Action" : "Gathering Info"}
                  </span>
                  {conversationState.lead_agent && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Lead: {conversationState.lead_agent}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🤖</span>
                </div>
                <h3 className="text-lg font-medium mb-2">Welcome to Agent OS V2</h3>
                <p className="text-gray-600 mb-4">
                  Start a conversation with our AI agents. They&apos;ll help you with strategy, 
                  creative content, data analysis, and operations.
                </p>
                <div className="text-sm text-gray-500 bg-gray-50 rounded-lg p-3 max-w-md mx-auto">
                  <p className="font-medium mb-1">💡 Pro tip:</p>
                  <p>Type <span className="bg-white px-1 rounded">@Alex</span>, <span className="bg-white px-1 rounded">@Dana</span>, <span className="bg-white px-1 rounded">@Riley</span>, or <span className="bg-white px-1 rounded">@Jamie</span> to mention specific agents!</p>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.sender === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {message.sender === 'agent' && message.agentName && (
                    <div className="text-xs font-medium mb-1 opacity-75">
                      {message.agentName}
                    </div>
                  )}
                  {message.sender === 'user' && message.mentionedAgent && (
                    <div className="text-xs mb-1 opacity-75">
                      → @{message.mentionedAgent}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className="text-xs opacity-75 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* Agent Dropdown */}
          {showAgentDropdown && (
            <div 
              className="absolute bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-2 min-w-[200px]"
              style={{ 
                bottom: '80px',
                left: '20px'
              }}
            >
              <div className="px-3 py-1 text-xs text-gray-500 border-b border-gray-100 mb-1">
                Select an agent:
              </div>
              {Object.entries(agentConfig).map(([name, config]) => (
                <button
                  key={name}
                  onClick={() => selectAgent(name)}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 transition-colors"
                >
                  <div className={`w-3 h-3 rounded-full ${config.color}`}></div>
                  <div>
                    <div className="font-medium text-sm">{name}</div>
                    <div className="text-xs text-gray-500">{config.description}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
          
          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyPress}
                  placeholder={mentionedAgent ? `Message @${mentionedAgent}...` : "Type your message... (use @ to mention agents)"}
                  className={`w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:border-transparent ${
                    showAgentDropdown 
                      ? 'border-blue-500 ring-2 ring-blue-200' 
                      : 'border-gray-300 focus:ring-blue-500'
                  }`}
                  rows={2}
                  disabled={isLoading}
                />
                {mentionedAgent && (
                  <div className="absolute top-2 right-2">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                      @{mentionedAgent}
                    </span>
                  </div>
                )}
                {showAgentDropdown && (
                  <div className="absolute top-2 left-2">
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      @ typing...
                    </span>
                  </div>
                )}
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
