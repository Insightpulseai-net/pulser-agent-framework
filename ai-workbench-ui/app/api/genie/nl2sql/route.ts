import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const { prompt } = await request.json()

    const litellmUrl = process.env.NEXT_PUBLIC_LITELLM_URL || 'https://litellm.insightpulseai.net/v1'
    const apiKey = process.env.LITELLM_API_KEY || ''

    const response = await fetch(`${litellmUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4.5',
        messages: [
          {
            role: 'system',
            content: 'You are a SQL expert. Convert natural language questions to SQL queries. Only respond with the SQL query, no explanations.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 2000,
      }),
    })

    const data = await response.json()
    const sql = data.choices?.[0]?.message?.content || 'Error generating SQL'

    return NextResponse.json({ sql, usage: data.usage })
  } catch (error: any) {
    console.error('Error calling LiteLLM:', error)
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
