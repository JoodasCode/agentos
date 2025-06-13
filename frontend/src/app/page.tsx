'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Bot, User, Zap, Target, Palette, BarChart3, Settings } from 'lucide-react'

interface Message {
  id: string
  content: string
  sender: 'user' | 'agent'
  agentName?: string
  timestamp: string
  agentType?: 'lead' | 'followup'
}

interface ConversationState {
  ready_for_action: boolean
  lead_agent: string
  questions_asked: string[]
  answers_collected: Record<string, unknown>
}

const agentConfig = {
  Alex: { icon: Target, color: 'bg-blue-500', description: 'Strategic Planning' },
  Dana: { icon: Palette, color: 'bg-purple-500', description: 'Creative Content' },
  Riley: { icon: BarChart3, color: 'bg-green-500', description: 'Data Analysis' },
  Jamie: { icon: Settings, color: 'bg-orange-500', description: 'Operations' }
}

export default function AgentOSChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversationState, setConversationState] = useState<ConversationState | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const endpoint = conversationId 
        ? `/api/chat/continue/${conversationId}`
        : '/api/chat/start'
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
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
        content: 'Sorry, I encountered an error. Please make sure the backend server is running on localhost:8000.',
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
      sendMessage()
    }
  }

  const getAgentAvatar = (agentName?: string) => {
    if (!agentName || !agentConfig[agentName as keyof typeof agentConfig]) {
      return { icon: Bot, color: 'bg-gray-500', description: 'AI Assistant' }
    }
    return agentConfig[agentName as keyof typeof agentConfig]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Agent OS V2</h1>
                <p className="text-sm text-muted-foreground">Multi-Agent Conversational Platform</p>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(agentConfig).map(([name, config]) => (
                <div key={name} className="flex items-center gap-2 p-2 rounded-lg bg-slate-50">
                  <div className={`p-1.5 rounded-full ${config.color}`}>
                    <config.icon className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{name}</p>
                    <p className="text-xs text-muted-foreground">{config.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Chat Interface */}
        <Card className="h-[600px] flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Conversation</CardTitle>
              {conversationState && (
                <div className="flex gap-2">
                  <Badge variant={conversationState.ready_for_action ? "default" : "secondary"}>
                    {conversationState.ready_for_action ? "Ready for Action" : "Gathering Info"}
                  </Badge>
                  {conversationState.lead_agent && (
                    <Badge variant="outline">
                      Lead: {conversationState.lead_agent}
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          
          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages */}
            <ScrollArea className="flex-1 px-6" ref={scrollAreaRef}>
              <div className="space-y-4 pb-4">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">Welcome to Agent OS V2</h3>
                                         <p className="text-muted-foreground">
                       Start a conversation with our AI agents. They&apos;ll help you with strategy, 
                       creative content, data analysis, and operations.
                     </p>
                  </div>
                )}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.sender === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.sender === 'agent' && (
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className={getAgentAvatar(message.agentName).color}>
                          {React.createElement(getAgentAvatar(message.agentName).icon, {
                            className: "h-4 w-4 text-white"
                          })}
                        </AvatarFallback>
                      </Avatar>
                    )}
                    
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.sender === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-white border shadow-sm'
                      }`}
                    >
                      {message.sender === 'agent' && message.agentName && (
                        <p className="text-xs font-medium text-muted-foreground mb-1">
                          {message.agentName}
                        </p>
                      )}
                      <p className="text-sm">{message.content}</p>
                    </div>
                    
                    {message.sender === 'user' && (
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-blue-500">
                          <User className="h-4 w-4 text-white" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex gap-3 justify-start">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-gray-500">
                        <Bot className="h-4 w-4 text-white" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="bg-white border shadow-sm rounded-lg px-4 py-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask the agents anything..."
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={!input.trim() || isLoading}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Press Enter to send • The agents will collaborate to help you
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Action Panel */}
        {conversationState?.ready_for_action && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Ready for Automation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                The agents have gathered enough information and are ready to execute automation workflows.
              </p>
              <div className="flex gap-2">
                <Button>
                  <Zap className="h-4 w-4 mr-2" />
                  Execute Workflow
                </Button>
                <Button variant="outline">View Automation Options</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
