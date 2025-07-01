import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message, conversation_id } = await request.json();

    // Generate a simple ID
    const generateId = () => Math.random().toString(36).substring(2) + Date.now().toString(36);

    // For now, return a simple response indicating the backend is ready
    const response = {
      conversation_id: conversation_id || generateId(),
      current_agent: "Triage Agent",
      messages: [
        {
          content: "¡Hola! Bienvenido a nuestro asistente de productos promocionales. Para comenzar, por favor selecciona tu unidad de negocio:",
          agent: "Triage Agent"
        }
      ],
      events: [
        {
          id: generateId(),
          type: "message",
          agent: "Triage Agent",
          content: "Agent initialized"
        }
      ],
      context: {
        business_unit: null,
        customer_name: null,
        selected_products: [],
        descripcion: null,
        precio: null
      },
      agents: [
        {
          name: "Triage Agent",
          description: "A triage agent that can delegate a customer's request to the appropriate business unit agent.",
          handoffs: ["Promoselect Agent", "SuitUp Agent"],
          tools: ["display_business_selector"],
          input_guardrails: ["Relevance Guardrail", "Jailbreak Guardrail"]
        },
        {
          name: "Promoselect Agent", 
          description: "A helpful agent that can search for individual promotional products from Promoselect.",
          handoffs: ["Triage Agent"],
          tools: ["save_product_description", "save_budget", "search_and_format_products"],
          input_guardrails: ["Relevance Guardrail", "Jailbreak Guardrail"]
        },
        {
          name: "SuitUp Agent",
          description: "A helpful agent that can search for promotional product kits from SuitUp.",
          handoffs: ["Triage Agent"],
          tools: ["save_product_description", "save_budget", "search_and_format_kits"],
          input_guardrails: ["Relevance Guardrail", "Jailbreak Guardrail"]
        }
      ],
      guardrails: []
    };

    // Check if we should display business selector
    if (!conversation_id || message.toLowerCase().includes('hola') || message.toLowerCase().includes('hello')) {
      response.messages = [
        {
          content: "DISPLAY_BUSINESS_SELECTOR",
          agent: "Triage Agent"
        }
      ];
    }

    return NextResponse.json(response, { status: 200 });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
} 