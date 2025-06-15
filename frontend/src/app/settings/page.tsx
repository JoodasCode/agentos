'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Settings, 
  Key, 
  Shield, 
  Eye, 
  EyeOff, 
  Trash2, 
  Plus, 
  TestTube,
  ArrowLeft,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'

interface ApiKey {
  id: string
  service_name: string
  key_name: string
  masked_key: string
  status: 'active' | 'inactive' | 'expired'
  created_at: string
  last_used?: string
}

interface ServiceIntegration {
  id: string
  name: string
  description: string
  icon: string
  setup_url: string
  docs_url: string
  required_scopes: string[]
}

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [services, setServices] = useState<ServiceIntegration[]>([])
  const [loading, setLoading] = useState(true)
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())
  const [newKey, setNewKey] = useState({ service: '', name: '', key: '' })
  const [showAddForm, setShowAddForm] = useState(false)
  const [testingKey, setTestingKey] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load services
      const servicesResponse = await fetch('https://agentos-production-6348.up.railway.app/api/v1/settings/services', {
        headers: { 'Authorization': 'Bearer demo-token' }
      })
      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json()
        setServices(servicesData)
      }

      // Load API keys
      const keysResponse = await fetch('https://agentos-production-6348.up.railway.app/api/v1/settings/api-keys', {
        headers: { 'Authorization': 'Bearer demo-token' }
      })
      if (keysResponse.ok) {
        const keysData = await keysResponse.json()
        setApiKeys(keysData)
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleKeyVisibility = (keyId: string) => {
    const newVisible = new Set(visibleKeys)
    if (newVisible.has(keyId)) {
      newVisible.delete(keyId)
    } else {
      newVisible.add(keyId)
    }
    setVisibleKeys(newVisible)
  }

  const addApiKey = async () => {
    if (!newKey.service || !newKey.name || !newKey.key) return

    try {
      const response = await fetch('https://agentos-production-6348.up.railway.app/api/v1/settings/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token'
        },
        body: JSON.stringify({
          service_name: newKey.service,
          key_name: newKey.name,
          api_key: newKey.key
        })
      })

      if (response.ok) {
        setNewKey({ service: '', name: '', key: '' })
        setShowAddForm(false)
        loadData()
      }
    } catch (error) {
      console.error('Error adding API key:', error)
    }
  }

  const deleteApiKey = async (keyId: string) => {
    try {
      const response = await fetch(`https://agentos-production-6348.up.railway.app/api/v1/settings/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer demo-token' }
      })

      if (response.ok) {
        loadData()
      }
    } catch (error) {
      console.error('Error deleting API key:', error)
    }
  }

  const testApiKey = async (keyId: string) => {
    setTestingKey(keyId)
    try {
      const response = await fetch(`https://agentos-production-6348.up.railway.app/api/v1/settings/api-keys/${keyId}/test`, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer demo-token' }
      })

      const result = await response.json()
      // Handle test result (you could show a toast or update UI)
      console.log('Test result:', result)
    } catch (error) {
      console.error('Error testing API key:', error)
    } finally {
      setTestingKey(null)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'inactive':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'expired':
        return <Clock className="w-4 h-4 text-yellow-500" />
      default:
        return <XCircle className="w-4 h-4 text-gray-500" />
    }
  }

  const connectSlack = async () => {
    try {
      const sessionId = 'demo-session' // In production, use actual session ID
      const response = await fetch(`https://agentos-production-6348.up.railway.app/integrations/slack/oauth/authorize?session_id=${sessionId}`)
      const result = await response.json()
      
      if (result.success && result.auth_url) {
        // Open Slack OAuth in new window
        window.open(result.auth_url, 'slack-oauth', 'width=600,height=600')
      }
    } catch (error) {
      console.error('Error connecting to Slack:', error)
    }
  }

  const connectNotion = async () => {
    // For now, show manual setup instructions
    alert('Notion OAuth integration coming soon! For now, please add your Notion API key manually in the API Keys tab.')
  }

  const connectGoogleCalendar = async () => {
    // For now, show manual setup instructions
    alert('Google Calendar OAuth integration coming soon! For now, please add your Google Calendar API key manually in the API Keys tab.')
  }

  const connectGitHub = async () => {
    // For now, show manual setup instructions
    alert('GitHub OAuth integration coming soon! For now, please add your GitHub API key manually in the API Keys tab.')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm mb-6 p-6">
          <div className="flex items-center gap-4 mb-4">
            <Link 
              href="/" 
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Settings className="w-8 h-8" />
                Settings
              </h1>
              <p className="text-gray-600">Manage your API keys and service integrations</p>
            </div>
          </div>
        </div>

        {/* Settings Tabs */}
        <div className="bg-white rounded-lg shadow-sm">
          <Tabs defaultValue="api-keys" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="api-keys" className="flex items-center gap-2">
                <Key className="w-4 h-4" />
                API Keys
              </TabsTrigger>
              <TabsTrigger value="services" className="flex items-center gap-2">
                <ExternalLink className="w-4 h-4" />
                Services
              </TabsTrigger>
              <TabsTrigger value="security" className="flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Security
              </TabsTrigger>
            </TabsList>

            {/* API Keys Tab */}
            <TabsContent value="api-keys" className="p-6">
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-semibold">API Keys</h2>
                    <p className="text-gray-600">Manage your service API keys securely</p>
                  </div>
                  <Button 
                    onClick={() => setShowAddForm(true)}
                    className="flex items-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Add API Key
                  </Button>
                </div>

                {/* Add API Key Form */}
                {showAddForm && (
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <h3 className="font-medium mb-4">Add New API Key</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="service">Service</Label>
                        <select
                          id="service"
                          value={newKey.service}
                          onChange={(e) => setNewKey({ ...newKey, service: e.target.value })}
                          className="w-full mt-1 p-2 border border-gray-300 rounded-md"
                        >
                          <option value="">Select service</option>
                          {services.map(service => (
                            <option key={service.id} value={service.name}>
                              {service.name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <Label htmlFor="name">Key Name</Label>
                        <Input
                          id="name"
                          value={newKey.name}
                          onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                          placeholder="e.g., Production Key"
                        />
                      </div>
                      <div>
                        <Label htmlFor="key">API Key</Label>
                        <Input
                          id="key"
                          type="password"
                          value={newKey.key}
                          onChange={(e) => setNewKey({ ...newKey, key: e.target.value })}
                          placeholder="Enter your API key"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2 mt-4">
                      <Button onClick={addApiKey}>Add Key</Button>
                      <Button variant="outline" onClick={() => setShowAddForm(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {/* API Keys List */}
                <div className="space-y-4">
                  {apiKeys.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <Key className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No API keys configured yet</p>
                      <p className="text-sm">Add your first API key to get started</p>
                    </div>
                  ) : (
                    apiKeys.map((key) => (
                      <div key={key.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {getStatusIcon(key.status)}
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium">{key.key_name}</h3>
                                <Badge variant="outline">{key.service_name}</Badge>
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                                  {visibleKeys.has(key.id) ? key.masked_key : '••••••••••••••••'}
                                </code>
                                <button
                                  onClick={() => toggleKeyVisibility(key.id)}
                                  className="p-1 hover:bg-gray-100 rounded"
                                >
                                  {visibleKeys.has(key.id) ? (
                                    <EyeOff className="w-4 h-4" />
                                  ) : (
                                    <Eye className="w-4 h-4" />
                                  )}
                                </button>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => testApiKey(key.id)}
                              disabled={testingKey === key.id}
                              className="flex items-center gap-2"
                            >
                              <TestTube className="w-4 h-4" />
                              {testingKey === key.id ? 'Testing...' : 'Test'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => deleteApiKey(key.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-gray-500">
                          Created: {new Date(key.created_at).toLocaleDateString()}
                          {key.last_used && (
                            <span className="ml-4">
                              Last used: {new Date(key.last_used).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </TabsContent>

            {/* Services Tab */}
            <TabsContent value="services" className="p-6">
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold">Service Integrations</h2>
                  <p className="text-gray-600">Connect your favorite services with one click</p>
                </div>

                {/* Featured Integrations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Slack Integration */}
                  <div className="border border-gray-200 rounded-lg p-6 bg-gradient-to-br from-purple-50 to-pink-50">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">💬</div>
                        <div>
                          <h3 className="font-semibold text-lg">Slack</h3>
                          <p className="text-sm text-gray-600">Send messages and manage channels</p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="bg-green-100 text-green-800">
                        Popular
                      </Badge>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600">
                        <p className="font-medium mb-2">What you can do:</p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                          <li>Send messages to channels</li>
                          <li>Create and manage channels</li>
                          <li>Upload files and documents</li>
                          <li>Get workspace information</li>
                        </ul>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          className="flex-1 bg-purple-600 hover:bg-purple-700"
                          onClick={() => connectSlack()}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Connect Slack
                        </Button>
                        <Button variant="outline" size="sm" asChild>
                          <a href="https://api.slack.com/docs" target="_blank" rel="noopener noreferrer">
                            Docs
                          </a>
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Notion Integration */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">📝</div>
                        <div>
                          <h3 className="font-semibold text-lg">Notion</h3>
                          <p className="text-sm text-gray-600">Create pages and manage databases</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600">
                        <p className="font-medium mb-2">What you can do:</p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                          <li>Create and update pages</li>
                          <li>Manage database entries</li>
                          <li>Search and retrieve content</li>
                          <li>Organize your workspace</li>
                        </ul>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          className="flex-1"
                          onClick={() => connectNotion()}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Connect Notion
                        </Button>
                        <Button variant="outline" size="sm" asChild>
                          <a href="https://developers.notion.com" target="_blank" rel="noopener noreferrer">
                            Docs
                          </a>
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Google Calendar Integration */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">📅</div>
                        <div>
                          <h3 className="font-semibold text-lg">Google Calendar</h3>
                          <p className="text-sm text-gray-600">Schedule events and manage calendars</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600">
                        <p className="font-medium mb-2">What you can do:</p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                          <li>Create and update events</li>
                          <li>Schedule meetings</li>
                          <li>Manage multiple calendars</li>
                          <li>Send invitations</li>
                        </ul>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          className="flex-1"
                          onClick={() => connectGoogleCalendar()}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Connect Calendar
                        </Button>
                        <Button variant="outline" size="sm" asChild>
                          <a href="https://developers.google.com/calendar" target="_blank" rel="noopener noreferrer">
                            Docs
                          </a>
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* GitHub Integration */}
                  <div className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">🐙</div>
                        <div>
                          <h3 className="font-semibold text-lg">GitHub</h3>
                          <p className="text-sm text-gray-600">Manage repositories and issues</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600">
                        <p className="font-medium mb-2">What you can do:</p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                          <li>Create and manage repositories</li>
                          <li>Handle issues and pull requests</li>
                          <li>Monitor project activity</li>
                          <li>Automate workflows</li>
                        </ul>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          className="flex-1"
                          onClick={() => connectGitHub()}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Connect GitHub
                        </Button>
                        <Button variant="outline" size="sm" asChild>
                          <a href="https://docs.github.com/en/rest" target="_blank" rel="noopener noreferrer">
                            Docs
                          </a>
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Connection Status */}
                <div className="border-t pt-6">
                  <h3 className="font-medium mb-4">Connected Services</h3>
                  <div className="space-y-2">
                    {apiKeys.length === 0 ? (
                      <p className="text-gray-500 text-sm">No services connected yet. Connect your first service above!</p>
                    ) : (
                      apiKeys.map((key) => (
                        <div key={key.id} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                          <div className="flex items-center gap-3">
                            <CheckCircle className="w-5 h-5 text-green-600" />
                            <div>
                              <p className="font-medium text-green-900">{key.service_name}</p>
                              <p className="text-sm text-green-700">Connected • {key.key_name}</p>
                            </div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => deleteApiKey(key.id)}
                            className="text-red-600 hover:text-red-700 border-red-200"
                          >
                            Disconnect
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="p-6">
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold">Security Settings</h2>
                  <p className="text-gray-600">Manage your security preferences</p>
                </div>

                <div className="space-y-4">
                  <Alert>
                    <Shield className="h-4 w-4" />
                    <AlertDescription>
                      All API keys are encrypted using AES-256-GCM encryption and stored securely.
                      Keys are never stored in plain text and are only decrypted when needed for API calls.
                    </AlertDescription>
                  </Alert>

                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">Auto-rotate API keys</h3>
                        <p className="text-sm text-gray-600">Automatically rotate keys every 90 days</p>
                      </div>
                      <Switch />
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">Usage notifications</h3>
                        <p className="text-sm text-gray-600">Get notified when API keys are used</p>
                      </div>
                      <Switch />
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">Failed attempt alerts</h3>
                        <p className="text-sm text-gray-600">Alert on failed API authentication attempts</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
} 