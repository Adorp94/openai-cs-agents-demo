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

// Vector store management
let promoVectorStoreId: string | null = null;
let suitupVectorStoreId: string | null = null;

async function setupVectorStores() {
  if (promoVectorStoreId && suitupVectorStoreId) {
    return { promoVectorStoreId, suitupVectorStoreId };
  }

  try {
    console.log('Setting up vector stores...');
    
    // Convert CSV to JSONL and create vector stores
    const promoJsonl = await csvToJsonl('airtable/promo.csv', 'promo');
    const suitupJsonl = await csvToJsonl('airtable/suitup.csv', 'suitup');
    
    // Create vector stores
    promoVectorStoreId = await createVectorStore('Promotional Products', promoJsonl);
    suitupVectorStoreId = await createVectorStore('Promotional Kits', suitupJsonl);
    
    console.log(`Vector stores created - Promo: ${promoVectorStoreId}, SuitUp: ${suitupVectorStoreId}`);
    
    return { promoVectorStoreId, suitupVectorStoreId };
  } catch (error) {
    console.error('Failed to setup vector stores:', error);
    return { promoVectorStoreId: null, suitupVectorStoreId: null };
  }
}

async function csvToJsonl(csvPath: string, productType: 'promo' | 'suitup'): Promise<any[]> {
  const fullPath = path.join(process.cwd(), csvPath);
  const csvData = fs.readFileSync(fullPath, 'utf-8');
  const lines = csvData.split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  
  const jsonlData = [];
  
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    
    // Better CSV parsing for complex fields with quotes
    const values: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let char of line) {
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());
    
    const row: any = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    
    if (!row.nombre) continue;
    
    let doc;
    if (productType === 'promo') {
      doc = {
        text: `Producto: ${row.nombre} - ${row.descripcion} - Categoría: ${row.categorias} - Precio: ${row.precio} - SKU: ${row.sku}`,
        metadata: {
          sku: row.sku || '',
          nombre: row.nombre || '',
          descripcion: row.descripcion || '',
          categorias: row.categorias || '',
          precio: row.precio || '',
          imagenes_url: row.imagenes_url || '',
          type: 'promotional_product'
        }
      };
    } else {
      doc = {
        text: `Kit: ${row.nombre} - ${row.descripcion} - Productos incluidos: ${row.productos} - Precio: ${row.precio}`,
        metadata: {
          nombre: row.nombre || '',
          descripcion: row.descripcion || '',
          productos: row.productos || '',
          precio: row.precio || '',
          imagen: row.imagen || '',
          type: 'promotional_kit'
        }
      };
    }
    
    jsonlData.push(doc);
  }
  
  return jsonlData;
}

async function createVectorStore(name: string, jsonlData: any[]): Promise<string> {
  try {
    // For now, return a placeholder since vector stores need proper API setup
    // In production, you'd use the OpenAI API directly with HTTP calls
    console.log(`Mock vector store created for ${name} with ${jsonlData.length} documents`);
    return `vs_mock_${Math.random().toString(36).substring(7)}`;
  } catch (error) {
    console.error(`Failed to create vector store ${name}:`, error);
    throw error;
  }
}

// Precise search functions (first tier)
function searchPromoProductsPrecise(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    const csvPath = path.join(process.cwd(), 'airtable', 'promo.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const products = [];
    for (let i = 1; i < Math.min(lines.length, 200); i++) {
      const line = lines[i];
      if (!line.trim()) continue;
      
      // Better CSV parsing for complex fields with quotes
      const values: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let char of line) {
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());
      
      const product: any = {};
      headers.forEach((header, index) => {
        product[header] = values[index] || '';
      });
      
      // Filter by keyword (search in name and description)
      const matchesKeyword = !keyword || 
        product.nombre?.toLowerCase().includes(keyword.toLowerCase()) ||
        product.descripcion?.toLowerCase().includes(keyword.toLowerCase()) ||
        product.categorias?.toLowerCase().includes(keyword.toLowerCase());
        
      // Extract price (remove currency symbols and convert to number)
      const priceText = product.precio || '';
      const price = parseFloat(priceText.replace(/[$,\s]/g, ''));
      const withinBudget = !maxPrice || (price > 0 && price <= maxPrice);
      
      if (matchesKeyword && withinBudget && product.nombre) {
        products.push({
          sku: product.sku,
          nombre: product.nombre,
          precio: product.precio,
          descripcion: product.descripcion,
          categorias: product.categorias,
          imagenes_url: product.imagenes_url
        });
      }
      
      if (products.length >= limit) break;
    }
    
    console.log(`Precise search for "${keyword}" with max price ${maxPrice} found ${products.length} products`);
    return products;
  } catch (error) {
    console.error('Error in precise promo search:', error);
    return [];
  }
}

function searchSuitUpKitsPrecise(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    const csvPath = path.join(process.cwd(), 'airtable', 'suitup.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const kits = [];
    for (let i = 1; i < Math.min(lines.length, 100); i++) {
      const line = lines[i];
      if (!line.trim()) continue;
      
      // Better CSV parsing for complex fields with quotes
      const values: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let char of line) {
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());
      
      const kit: any = {};
      headers.forEach((header, index) => {
        kit[header] = values[index] || '';
      });
      
      // Filter by keyword and price
      const matchesKeyword = !keyword || 
        kit.nombre?.toLowerCase().includes(keyword.toLowerCase()) ||
        kit.descripcion?.toLowerCase().includes(keyword.toLowerCase()) ||
        kit.productos?.toLowerCase().includes(keyword.toLowerCase());
        
      const priceText = kit.precio || '';
      const price = parseFloat(priceText.replace(/[$,\s]/g, ''));
      const withinBudget = !maxPrice || (price > 0 && price <= maxPrice);
      
      if (matchesKeyword && withinBudget && kit.nombre) {
        kits.push({
          nombre: kit.nombre,
          precio: kit.precio,
          descripcion: kit.descripcion,
          productos: kit.productos,
          imagen: kit.imagen
        });
      }
      
      if (kits.length >= limit) break;
    }
    
    console.log(`Precise search for "${keyword}" with max price ${maxPrice} found ${kits.length} kits`);
    return kits;
  } catch (error) {
    console.error('Error in precise suitup search:', error);
    return [];
  }
}

// Vector search functions (second tier - semantic search using OpenAI)
async function searchPromoProductsVector(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    // Use OpenAI directly for semantic search on product descriptions
    const csvPath = path.join(process.cwd(), 'airtable', 'promo.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
         // Get product descriptions for semantic analysis
     const productDescriptions: Array<{text: string, product: any}> = [];
    for (let i = 1; i < Math.min(lines.length, 50); i++) { // Limit for API efficiency
      const line = lines[i];
      if (!line.trim()) continue;
      
      const values: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let char of line) {
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());
      
      const product: any = {};
      headers.forEach((header, index) => {
        product[header] = values[index] || '';
      });
      
      if (product.nombre) {
        productDescriptions.push({
          text: `${product.nombre} - ${product.descripcion} - ${product.categorias}`,
          product: product
        });
      }
    }
    
    // Use OpenAI to find semantic matches
    const prompt = `Find the ${limit} most semantically similar products to "${keyword}" from this list:
    
${productDescriptions.map((p, i) => `${i}: ${p.text}`).join('\n')}

${maxPrice ? `Only include products under ${maxPrice} pesos.` : ''}

Respond with just the numbers of the matching products, separated by commas (e.g. "1,3,5").`;

    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      temperature: 0
    });
    
    const matches = response.choices[0].message.content?.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) || [];
    
    const results = matches.map(index => {
      const productDesc = productDescriptions[index];
      if (!productDesc) return null;
      
      const product = productDesc.product;
      // Apply price filter
      if (maxPrice) {
        const priceText = product.precio || '';
        const price = parseFloat(priceText.replace(/[$,\s]/g, ''));
        if (price > 0 && price > maxPrice) return null;
      }
      
      return {
        sku: product.sku,
        nombre: product.nombre,
        precio: product.precio,
        descripcion: product.descripcion,
        categorias: product.categorias,
        imagenes_url: product.imagenes_url
      };
    }).filter(Boolean);
    
    console.log(`Vector search for "${keyword}" found ${results.length} results`);
    return results;
  } catch (error) {
    console.error('Error in vector promo search:', error);
    return [];
  }
}

async function searchSuitUpKitsVector(keyword: string, maxPrice?: number, limit: number = 3) {
  try {
    // Use OpenAI directly for semantic search on kit descriptions
    const csvPath = path.join(process.cwd(), 'airtable', 'suitup.csv');
    const csvData = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvData.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    // Get kit descriptions for semantic analysis
    const kitDescriptions: Array<{text: string, kit: any}> = [];
    for (let i = 1; i < Math.min(lines.length, 30); i++) { // Limit for API efficiency
      const line = lines[i];
      if (!line.trim()) continue;
      
      const values: string[] = [];
      let current = '';
      let inQuotes = false;
      
      for (let char of line) {
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      values.push(current.trim());
      
      const kit: any = {};
      headers.forEach((header, index) => {
        kit[header] = values[index] || '';
      });
      
      if (kit.nombre) {
        kitDescriptions.push({
          text: `${kit.nombre} - ${kit.descripcion} - ${kit.productos}`,
          kit: kit
        });
      }
    }
    
    // Use OpenAI to find semantic matches
    const prompt = `Find the ${limit} most semantically similar promotional kits to "${keyword}" from this list:
    
${kitDescriptions.map((k, i) => `${i}: ${k.text}`).join('\n')}

${maxPrice ? `Only include kits under ${maxPrice} pesos.` : ''}

Respond with just the numbers of the matching kits, separated by commas (e.g. "1,3,5").`;

    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      temperature: 0
    });
    
    const matches = response.choices[0].message.content?.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) || [];
    
    const results = matches.map(index => {
      const kitDesc = kitDescriptions[index];
      if (!kitDesc) return null;
      
      const kit = kitDesc.kit;
      // Apply price filter
      if (maxPrice) {
        const priceText = kit.precio || '';
        const price = parseFloat(priceText.replace(/[$,\s]/g, ''));
        if (price > 0 && price > maxPrice) return null;
      }
      
      return {
        nombre: kit.nombre,
        precio: kit.precio,
        descripcion: kit.descripcion,
        productos: kit.productos,
        imagen: kit.imagen
      };
    }).filter(Boolean);
    
    console.log(`Vector search for "${keyword}" found ${results.length} kit results`);
    return results;
  } catch (error) {
    console.error('Error in vector suitup search:', error);
    return [];
  }
}

function parseVectorSearchResults(content: string, type: 'products' | 'kits', limit: number) {
  // Try to extract product/kit information from the assistant's response
  // This is a simplified parser - in production you'd want more robust parsing
  const results = [];
  
  try {
    // Look for JSON-like structures or formatted product information
    const lines = content.split('\n');
    for (const line of lines) {
      if (line.includes('nombre') || line.includes('Producto:') || line.includes('Kit:')) {
        // Extract basic product info (simplified)
        if (type === 'products') {
          results.push({
            sku: '',
            nombre: line.substring(0, 50),
            precio: 'Ver precio',
            descripcion: 'Producto encontrado mediante búsqueda semántica',
            categorias: '',
            imagenes_url: ''
          });
        } else {
          results.push({
            nombre: line.substring(0, 50),
            precio: 'Ver precio',
            descripcion: 'Kit encontrado mediante búsqueda semántica',
            productos: '',
            imagen: ''
          });
        }
        
        if (results.length >= limit) break;
      }
    }
  } catch (error) {
    console.error('Error parsing vector search results:', error);
  }
  
  return results;
}

// Comprehensive search functions (precise + vector fallback)
async function searchAndFormatProducts(keyword: string, maxPrice?: number, limit: number = 3): Promise<string> {
  console.log(`Comprehensive search for: '${keyword}', max_price: ${maxPrice}`);
  
  // STEP 1: Try precise search first
  const preciseResults = searchPromoProductsPrecise(keyword, maxPrice, limit);
  console.log(`Precise search returned ${preciseResults.length} results`);
  
  // STEP 2: If precise search found results, return them
  if (preciseResults.length > 0) {
    return formatProductResults(preciseResults);
  }
  
  // STEP 3: Try semantic/vector search as fallback
  console.log('Precise search found no results, trying semantic search...');
  const vectorResults = await searchPromoProductsVector(keyword, maxPrice, limit);
  console.log(`Vector search returned ${vectorResults.length} results`);
  
  // STEP 4: Return results or no-results message
  if (vectorResults.length > 0) {
    return formatProductResults(vectorResults);
  } else {
    return "No se encontraron productos que coincidan con los criterios de búsqueda.";
  }
}

async function searchAndFormatKits(keyword: string, maxPrice?: number, limit: number = 3): Promise<string> {
  console.log(`Comprehensive kit search for: '${keyword}', max_price: ${maxPrice}`);
  
  // STEP 1: Try precise search first
  const preciseResults = searchSuitUpKitsPrecise(keyword, maxPrice, limit);
  console.log(`Precise kit search returned ${preciseResults.length} results`);
  
  // STEP 2: If precise search found results, return them
  if (preciseResults.length > 0) {
    return formatKitResults(preciseResults);
  }
  
  // STEP 3: Try semantic/vector search as fallback
  console.log('Precise search found no results, trying semantic search...');
  const vectorResults = await searchSuitUpKitsVector(keyword, maxPrice, limit);
  console.log(`Vector search returned ${vectorResults.length} results`);
  
  // STEP 4: Return results or no-results message
  if (vectorResults.length > 0) {
    return formatKitResults(vectorResults);
  } else {
    return "No se encontraron kits que coincidan con los criterios de búsqueda.";
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
            responseMessage = await searchAndFormatProducts(conversation.context.descripcion, maxPrice);
          } else if (conversation.context.business_unit === 'suitup') {
            responseMessage = await searchAndFormatKits(conversation.context.descripcion, maxPrice);
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