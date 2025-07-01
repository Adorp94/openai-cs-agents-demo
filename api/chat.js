// Node.js serverless function for chat API
export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow POST requests for chat
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { message, conversation_id } = req.body;

    // For now, return a simple response indicating the backend is ready
    // This can be expanded to include the actual OpenAI API calls
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

    res.status(200).json(response);

  } catch (error) {
    console.error('Chat API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
}

function generateId() {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
} 