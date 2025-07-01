import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import fs from 'fs';
import path from 'path';

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Types for our conversation system
interface ConversationContext {
  business_unit: string | null;
  customer_name: string | null;
  selected_products: any[];
  descripcion: string | null;
  precio: string | null;
}

interface ConversationState {
  conversation_id: string;
  current_agent: string;
  context: ConversationContext;
  messages: Array<{content: string, agent: string}>;
  events: Array<{id: string, type: string, agent: string, content: string}>;
}

// In-memory conversation storage (in production, use a database)
const conversations = new Map<string, ConversationState>();

// Product search functions
function searchPromoProducts(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    const csvPath = path.join(process.cwd(), 'airtable', 'promo.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',');
    
    const products = [];
    for (let i = 1; i < Math.min(lines.length, 100); i++) { // Limit for performance
      const line = lines[i];
      if (!line.trim()) continue;
      
      const values = line.split(',');
      const product: any = {};
      headers.forEach((header, index) => {
        product[header.trim()] = values[index]?.trim() || '';
      });
      
      // Filter by keyword and price
      const matchesKeyword = !keyword || 
        product.nombre?.toLowerCase().includes(keyword.toLowerCase()) ||
        product.descripcion?.toLowerCase().includes(keyword.toLowerCase());
        
      const price = parseFloat(product.precio?.replace(/[^\d.]/g, '') || '0');
      const withinBudget = !maxPrice || price <= maxPrice;
      
      if (matchesKeyword && withinBudget) {
        products.push(product);
      }
      
      if (products.length >= limit) break;
    }
    
    return products;
  } catch (error) {
    console.error('Error searching promo products:', error);
    return [];
  }
}

function searchSuitUpKits(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    const csvPath = path.join(process.cwd(), 'airtable', 'suitup.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',');
    
    const kits = [];
    for (let i = 1; i < Math.min(lines.length, 50); i++) { // Limit for performance
      const line = lines[i];
      if (!line.trim()) continue;
      
      const values = line.split(',');
      const kit: any = {};
      headers.forEach((header, index) => {
        kit[header.trim()] = values[index]?.trim() || '';
      });
      
      // Filter by keyword and price
      const matchesKeyword = !keyword || 
        kit.nombre?.toLowerCase().includes(keyword.toLowerCase()) ||
        kit.descripcion?.toLowerCase().includes(keyword.toLowerCase()) ||
        kit.productos?.toLowerCase().includes(keyword.toLowerCase());
        
      const price = parseFloat(kit.precio?.replace(/[^\d.]/g, '') || '0');
      const withinBudget = !maxPrice || price <= maxPrice;
      
      if (matchesKeyword && withinBudget) {
        kits.push(kit);
      }
      
      if (kits.length >= limit) break;
    }
    
    return kits;
  } catch (error) {
    console.error('Error searching SuitUp kits:', error);
    return [];
  }
}

function formatProductResults(products: any[]) {
  if (products.length === 0) {
    return "No encontré productos que coincidan con tu búsqueda. ¿Podrías describir lo que necesitas de manera diferente?";
  }
  
  let result = `Encontré ${products.length} productos que podrían interesarte:\n\n`;
  
  products.forEach((product, index) => {
    result += `${index + 1}. **${product.nombre}**\n`;
    result += `   • Precio: ${product.precio}\n`;
    result += `   • Descripción: ${product.descripcion}\n`;
    if (product.categorias) result += `   • Categoría: ${product.categorias}\n`;
    result += '\n';
  });
  
  result += "¿Te interesa alguno de estos productos? ¿O prefieres que busque algo más específico?";
  return result;
}

function formatKitResults(kits: any[]) {
  if (kits.length === 0) {
    return "No encontré kits que coincidan con tu búsqueda. ¿Podrías describir lo que necesitas de manera diferente?";
  }
  
  let result = `Encontré ${kits.length} kits que podrían interesarte:\n\n`;
  
  kits.forEach((kit, index) => {
    result += `${index + 1}. **${kit.nombre}**\n`;
    result += `   • Precio: ${kit.precio}\n`;
    result += `   • Descripción: ${kit.descripcion}\n`;
    if (kit.productos) result += `   • Incluye: ${kit.productos}\n`;
    result += '\n';
  });
  
  result += "¿Te interesa alguno de estos kits? ¿O prefieres que busque algo más específico?";
  return result;
}

export async function POST(request: NextRequest) {
  try {
    const { message, conversation_id } = await request.json();
    const generateId = () => Math.random().toString(36).substring(2) + Date.now().toString(36);
    
    let convId = conversation_id || generateId();
    let conversation = conversations.get(convId);
    
    // Initialize new conversation
    if (!conversation) {
      conversation = {
        conversation_id: convId,
        current_agent: "Triage Agent",
        context: {
          business_unit: null,
          customer_name: null,
          selected_products: [],
          descripcion: null,
          precio: null
        },
        messages: [],
        events: [{
          id: generateId(),
          type: "message",
          agent: "Triage Agent",
          content: "Agent initialized"
        }]
      };
      
      // Initial greeting - show business selector
      if (!message || message.toLowerCase().includes('hola') || message.toLowerCase().includes('hello')) {
        conversation.messages.push({
          content: "DISPLAY_BUSINESS_SELECTOR",
          agent: "Triage Agent"
        });
        
        conversations.set(convId, conversation);
        
        return NextResponse.json({
          conversation_id: convId,
          current_agent: conversation.current_agent,
          messages: conversation.messages,
          events: conversation.events,
          context: conversation.context,
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
        });
      }
    }

    // Handle business unit selection
    if (message.toLowerCase().includes('promoselect')) {
      conversation.context.business_unit = 'promoselect';
      conversation.current_agent = 'Promoselect Agent';
      
      const responseMessage = "¡Perfecto! Ahora te ayudo a encontrar productos promocionales individuales. ¿Qué tipo de producto estás buscando? Por ejemplo: camisetas, bolígrafos, tazas, etc.";
      
      conversation.messages.push({
        content: responseMessage,
        agent: "Promoselect Agent"
      });
      
      conversation.events.push({
        id: generateId(),
        type: "handoff",
        agent: "Promoselect Agent",
        content: "Switched to Promoselect Agent"
      });
      
    } else if (message.toLowerCase().includes('suitup')) {
      conversation.context.business_unit = 'suitup';
      conversation.current_agent = 'SuitUp Agent';
      
      const responseMessage = "¡Excelente! Te ayudo a encontrar kits de productos promocionales. ¿Qué tipo de kit necesitas? Por ejemplo: kit ejecutivo, kit de bienvenida, kit de eventos, etc.";
      
      conversation.messages.push({
        content: responseMessage,
        agent: "SuitUp Agent"
      });
      
      conversation.events.push({
        id: generateId(),
        type: "handoff",
        agent: "SuitUp Agent",
        content: "Switched to SuitUp Agent"
      });
      
    } else {
      // Use OpenAI for conversation logic
      const systemPrompt = conversation.current_agent === 'Promoselect Agent' 
        ? `You are a friendly sales specialist at Promoselect, helping customers find promotional products. 
           Current context: ${JSON.stringify(conversation.context)}
           
           Strategy:
           1. If they haven't described what they want, ask for product description
           2. If they haven't mentioned budget, ask for price range
           3. If you have both description and budget, search for products
           4. Be conversational and helpful in Spanish`
        : conversation.current_agent === 'SuitUp Agent'
        ? `You are a friendly sales specialist at SuitUp, helping customers find promotional kits.
           Current context: ${JSON.stringify(conversation.context)}
           
           Strategy:
           1. If they haven't described what they want, ask for kit description  
           2. If they haven't mentioned budget, ask for price range
           3. If you have both description and budget, search for kits
           4. Be conversational and helpful in Spanish`
        : `You are a triage agent for promotional products. Guide customers to select Promoselect (individual products) or SuitUp (product kits).`;

      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: message }
        ],
        temperature: 0.7,
        max_tokens: 500
      });

      let responseMessage = completion.choices[0]?.message?.content || "Lo siento, no pude procesar tu mensaje.";
      
      // Check if we should perform a search
      if (conversation.context.business_unit && conversation.context.descripcion && conversation.context.precio) {
        const maxPrice = parseFloat(conversation.context.precio.replace(/[^\d]/g, ''));
        
        if (conversation.context.business_unit === 'promoselect') {
          const products = searchPromoProducts(conversation.context.descripcion, maxPrice);
          responseMessage = formatProductResults(products);
        } else if (conversation.context.business_unit === 'suitup') {
          const kits = searchSuitUpKits(conversation.context.descripcion, maxPrice);
          responseMessage = formatKitResults(kits);
        }
      } else {
        // Try to extract description and budget from the message
        if (!conversation.context.descripcion && message.length > 3) {
          conversation.context.descripcion = message;
        }
        
        const priceMatch = message.match(/(\d+)/);
        if (!conversation.context.precio && priceMatch) {
          conversation.context.precio = priceMatch[0];
        }
      }
      
      conversation.messages.push({
        content: responseMessage,
        agent: conversation.current_agent
      });
    }

    conversations.set(convId, conversation);

    return NextResponse.json({
      conversation_id: convId,
      current_agent: conversation.current_agent,
      messages: conversation.messages,
      events: conversation.events,
      context: conversation.context,
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
    });

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