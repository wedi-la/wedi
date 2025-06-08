// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
  metadata?: {
    timestamp: string
    requestId: string
  }
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

// Pagination Types
export interface PaginationParams {
  page?: number
  limit?: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

// Event Types for Kafka/Event Bus
export interface PaymentEvent {
  eventType: string
  eventVersion: string
  orderId: string
  organizationId: string
  timestamp: string
  data: Record<string, any>
  metadata?: Record<string, any>
}

// Common Status Types
export type PaymentStatus = 
  | 'CREATED'
  | 'AWAITING_PAYMENT'
  | 'PROCESSING'
  | 'REQUIRES_ACTION'
  | 'COMPLETED'
  | 'FAILED'
  | 'REFUNDED'
  | 'CANCELLED'

// Provider Types
export interface ProviderWebhookPayload {
  provider: string
  event: string
  data: Record<string, any>
  signature?: string
}

// Auth Types
export interface JwtPayload {
  sub: string  // user ID
  org: string  // organization ID
  role: string
  iat: number
  exp: number
}

// Export sub-modules as they are created
// export * from './api'
// export * from './events'
// export * from './providers'
// export * from './webhooks' 