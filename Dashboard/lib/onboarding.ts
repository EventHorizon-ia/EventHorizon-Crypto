// ============================================================
// LÓGICA DE RECOMENDAÇÃO DE PLANO
// Baseado nas respostas do onboarding, calcula o plano ideal.
// ============================================================

// ----- Tipos (definidos localmente para evitar erro de importação)
type RespostasOnboarding = {
  nivel_experiencia: "iniciante" | "intermediario" | "avancado" | "profissional"
  horas_dia: "1-2h" | "3-5h" | "6-8h" | "integral"
  apetite_risco: "conservador" | "moderado" | "agressivo" | "insano"
  qtd_moedas: "3" | "10" | "20+"
  alertas_tipo: "navegador" | "telegram" | "nenhum"
}

type Plano = "basico" | "pro" | "enterprise"

const PLANOS = {
  basico: {
    id: "basico" as const,
    nome: "Básico",
    preco: 97,
    moedas: 3,
    alertas: false,
    telegram: false,
    api_access: false,
  },
  pro: {
    id: "pro" as const,
    nome: "Pro",
    preco: 197,
    moedas: 10,
    alertas: true,
    telegram: true,
    api_access: false,
  },
  enterprise: {
    id: "enterprise" as const,
    nome: "Enterprise",
    preco: 497,
    moedas: 20,
    alertas: true,
    telegram: true,
    api_access: true,
  },
}

// Pontuação por resposta
const PONTUACAO: Record<string, number> = {
  // Nível de experiência
  iniciante: 1,
  intermediario: 2,
  avancado: 3,
  profissional: 4,

  // Horas por dia
  "1-2h": 1,
  "3-5h": 2,
  "6-8h": 3,
  integral: 4,

  // Apetite a risco
  conservador: 1,
  moderado: 2,
  agressivo: 3,
  insano: 4,

  // Quantidade de moedas
  "3": 1,
  "10": 2,
  "20+": 3,

  // Alertas
  nenhum: 1,
  navegador: 2,
  telegram: 3,
}

export interface ResultadoRecomendacao {
  plano: Plano
  pontuacao: number
  motivo: string
  beneficios: string[]
}

/**
 * Calcula o plano recomendado com base nas respostas do onboarding.
 * Regras:
 *   - Pontuação 5–8  → Básico
 *   - Pontuação 9–14 → Pro
 *   - Pontuação 15+  → Enterprise
 */
export function calcularPlanoRecomendado(
  respostas: RespostasOnboarding
): ResultadoRecomendacao {
  const pontuacao =
    PONTUACAO[respostas.nivel_experiencia] +
    PONTUACAO[respostas.horas_dia] +
    PONTUACAO[respostas.apetite_risco] +
    PONTUACAO[respostas.qtd_moedas] +
    PONTUACAO[respostas.alertas_tipo]

  let plano: Plano
  let motivo: string
  let beneficios: string[]

  // ----- Básico -----
  if (pontuacao <= 8) {
    plano = "basico"
    motivo = "Perfeito para quem está começando no trading com IA"
    beneficios = [
      "Previsões em tempo real para BTC, ETH e BNB",
      "Dashboard com acurácia e histórico",
      "Sem complexidade desnecessária para iniciantes",
    ]

  // ----- Pro -----
  } else if (pontuacao <= 14) {
    plano = "pro"
    motivo = "Ideal para traders ativos que querem diversificar"
    beneficios = [
      "10 moedas monitoradas simultaneamente",
      "Alertas automáticos no Telegram",
      "Análise de performance por horizonte",
      "Gestão de risco avançada",
    ]

  // ----- Enterprise -----
  } else {
    plano = "enterprise"
    motivo = "Para traders profissionais que precisam do máximo"
    beneficios = [
      "20+ moedas monitoradas sem limites",
      "Telegram prioritário com análises detalhadas",
      "Acesso à API para integração própria",
      "Suporte dedicado",
    ]
  }

  return { plano, pontuacao, motivo, beneficios }
}

// Rótulos amigáveis para exibir no resumo do onboarding
export const ROTULOS = {
  nivel_experiencia: {
    iniciante: "Iniciante",
    intermediario: "Intermediário",
    avancado: "Avançado",
    profissional: "Profissional",
  },
  horas_dia: {
    "1-2h": "1 a 2 horas por dia",
    "3-5h": "3 a 5 horas por dia",
    "6-8h": "6 a 8 horas por dia",
    integral: "Tempo integral",
  },
  apetite_risco: {
    conservador: "Conservador",
    moderado: "Moderado",
    agressivo: "Agressivo",
    insano: "Insano 🔥",
  },
  qtd_moedas: {
    "3": "3 moedas (Básico)",
    "10": "10 moedas (Pro)",
    "20+": "20+ moedas (Enterprise)",
  },
  alertas_tipo: {
    nenhum: "Sem alertas",
    navegador: "Alertas no navegador",
    telegram: "Alertas no Telegram",
  },
} as const