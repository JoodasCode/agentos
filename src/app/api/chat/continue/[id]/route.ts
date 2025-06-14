import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    const conversationId = params.id
    
    const response = await fetch(`https://agentos-production-6348.up.railway.app/chat/continue/${conversationId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Railway API responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error proxying to Railway:', error)
    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    )
  }
} 