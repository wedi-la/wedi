
Object.defineProperty(exports, "__esModule", { value: true });

const {
  Decimal,
  objectEnumValues,
  makeStrictEnum,
  Public,
  getRuntime,
  skip
} = require('./runtime/index-browser.js')


const Prisma = {}

exports.Prisma = Prisma
exports.$Enums = {}

/**
 * Prisma Client JS version: 5.22.0
 * Query Engine version: 605197351a3c8bdd595af2d2a9bc3025bca48ea2
 */
Prisma.prismaVersion = {
  client: "5.22.0",
  engine: "605197351a3c8bdd595af2d2a9bc3025bca48ea2"
}

Prisma.PrismaClientKnownRequestError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`PrismaClientKnownRequestError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)};
Prisma.PrismaClientUnknownRequestError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`PrismaClientUnknownRequestError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.PrismaClientRustPanicError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`PrismaClientRustPanicError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.PrismaClientInitializationError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`PrismaClientInitializationError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.PrismaClientValidationError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`PrismaClientValidationError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.NotFoundError = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`NotFoundError is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.Decimal = Decimal

/**
 * Re-export of sql-template-tag
 */
Prisma.sql = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`sqltag is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.empty = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`empty is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.join = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`join is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.raw = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`raw is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.validator = Public.validator

/**
* Extensions
*/
Prisma.getExtensionContext = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`Extensions.getExtensionContext is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}
Prisma.defineExtension = () => {
  const runtimeName = getRuntime().prettyName;
  throw new Error(`Extensions.defineExtension is unable to run in this browser environment, or has been bundled for the browser (running in ${runtimeName}).
In case this error is unexpected for you, please report it in https://pris.ly/prisma-prisma-bug-report`,
)}

/**
 * Shorthand utilities for JSON filtering
 */
Prisma.DbNull = objectEnumValues.instances.DbNull
Prisma.JsonNull = objectEnumValues.instances.JsonNull
Prisma.AnyNull = objectEnumValues.instances.AnyNull

Prisma.NullTypes = {
  DbNull: objectEnumValues.classes.DbNull,
  JsonNull: objectEnumValues.classes.JsonNull,
  AnyNull: objectEnumValues.classes.AnyNull
}



/**
 * Enums
 */

exports.Prisma.TransactionIsolationLevel = makeStrictEnum({
  ReadUncommitted: 'ReadUncommitted',
  ReadCommitted: 'ReadCommitted',
  RepeatableRead: 'RepeatableRead',
  Serializable: 'Serializable'
});

exports.Prisma.OrganizationScalarFieldEnum = {
  id: 'id',
  name: 'name',
  slug: 'slug',
  description: 'description',
  billingEmail: 'billingEmail',
  taxId: 'taxId',
  country: 'country',
  complianceStatus: 'complianceStatus',
  kycVerifiedAt: 'kycVerifiedAt',
  settings: 'settings',
  features: 'features',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt',
  ownerId: 'ownerId'
};

exports.Prisma.UserScalarFieldEnum = {
  id: 'id',
  email: 'email',
  name: 'name',
  avatarUrl: 'avatarUrl',
  authProvider: 'authProvider',
  authProviderId: 'authProviderId',
  emailVerified: 'emailVerified',
  primaryWalletId: 'primaryWalletId',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt',
  lastLoginAt: 'lastLoginAt'
};

exports.Prisma.CustomerScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  email: 'email',
  name: 'name',
  phone: 'phone',
  billingAddress: 'billingAddress',
  shippingAddress: 'shippingAddress',
  walletAddress: 'walletAddress',
  preferredChainId: 'preferredChainId',
  isActive: 'isActive',
  emailVerified: 'emailVerified',
  metadata: 'metadata',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.CustomerPaymentMethodScalarFieldEnum = {
  id: 'id',
  customerId: 'customerId',
  type: 'type',
  provider: 'provider',
  externalId: 'externalId',
  last4: 'last4',
  brand: 'brand',
  expiryMonth: 'expiryMonth',
  expiryYear: 'expiryYear',
  bankName: 'bankName',
  accountLast4: 'accountLast4',
  walletAddress: 'walletAddress',
  chainId: 'chainId',
  isDefault: 'isDefault',
  isActive: 'isActive',
  metadata: 'metadata',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.SubscriptionScalarFieldEnum = {
  id: 'id',
  customerId: 'customerId',
  organizationId: 'organizationId',
  status: 'status',
  currentPeriodStart: 'currentPeriodStart',
  currentPeriodEnd: 'currentPeriodEnd',
  cancelAt: 'cancelAt',
  canceledAt: 'canceledAt',
  endedAt: 'endedAt',
  trialStart: 'trialStart',
  trialEnd: 'trialEnd',
  metadata: 'metadata',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.SubscriptionItemScalarFieldEnum = {
  id: 'id',
  subscriptionId: 'subscriptionId',
  priceId: 'priceId',
  quantity: 'quantity',
  metadata: 'metadata',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.WalletScalarFieldEnum = {
  id: 'id',
  address: 'address',
  chainId: 'chainId',
  type: 'type',
  userId: 'userId',
  organizationId: 'organizationId',
  smartWalletFactory: 'smartWalletFactory',
  smartWalletConfig: 'smartWalletConfig',
  isActive: 'isActive',
  allowlist: 'allowlist',
  blocklist: 'blocklist',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.BlockchainTransactionScalarFieldEnum = {
  id: 'id',
  hash: 'hash',
  chainId: 'chainId',
  fromAddress: 'fromAddress',
  toAddress: 'toAddress',
  value: 'value',
  data: 'data',
  gasLimit: 'gasLimit',
  gasPrice: 'gasPrice',
  nonce: 'nonce',
  status: 'status',
  blockNumber: 'blockNumber',
  confirmations: 'confirmations',
  isSponsored: 'isSponsored',
  sponsorshipId: 'sponsorshipId',
  walletId: 'walletId',
  paymentOrderId: 'paymentOrderId',
  createdAt: 'createdAt',
  minedAt: 'minedAt'
};

exports.Prisma.GasSponsorshipScalarFieldEnum = {
  id: 'id',
  sponsorWalletId: 'sponsorWalletId',
  maxGasAmount: 'maxGasAmount',
  usedGasAmount: 'usedGasAmount',
  maxTransactions: 'maxTransactions',
  usedTransactions: 'usedTransactions',
  expiresAt: 'expiresAt',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.ProductScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  name: 'name',
  description: 'description',
  type: 'type',
  isActive: 'isActive',
  metadata: 'metadata',
  images: 'images',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.PriceScalarFieldEnum = {
  id: 'id',
  productId: 'productId',
  amount: 'amount',
  currency: 'currency',
  type: 'type',
  interval: 'interval',
  intervalCount: 'intervalCount',
  trialPeriodDays: 'trialPeriodDays',
  isActive: 'isActive',
  metadata: 'metadata',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.PaymentLinkScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  createdById: 'createdById',
  executingAgentId: 'executingAgentId',
  integrationKeyId: 'integrationKeyId',
  title: 'title',
  description: 'description',
  referenceId: 'referenceId',
  shortCode: 'shortCode',
  qrCode: 'qrCode',
  priceId: 'priceId',
  amount: 'amount',
  currency: 'currency',
  targetAmount: 'targetAmount',
  targetCurrency: 'targetCurrency',
  smartContractAddress: 'smartContractAddress',
  smartContractChainId: 'smartContractChainId',
  tokenAddress: 'tokenAddress',
  status: 'status',
  allowMultiplePayments: 'allowMultiplePayments',
  requiresKyc: 'requiresKyc',
  expiresAt: 'expiresAt',
  redirectUrls: 'redirectUrls',
  metadata: 'metadata',
  theme: 'theme',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.PaymentOrderScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  paymentLinkId: 'paymentLinkId',
  customerId: 'customerId',
  orderNumber: 'orderNumber',
  status: 'status',
  requestedAmount: 'requestedAmount',
  requestedCurrency: 'requestedCurrency',
  settledAmount: 'settledAmount',
  settledCurrency: 'settledCurrency',
  exchangeRate: 'exchangeRate',
  exchangeRateLockedAt: 'exchangeRateLockedAt',
  exchangeRateSource: 'exchangeRateSource',
  platformFee: 'platformFee',
  providerFee: 'providerFee',
  networkFee: 'networkFee',
  totalFee: 'totalFee',
  customerEmail: 'customerEmail',
  customerName: 'customerName',
  customerWallet: 'customerWallet',
  customerIp: 'customerIp',
  customerCountry: 'customerCountry',
  riskScore: 'riskScore',
  riskFactors: 'riskFactors',
  kycStatus: 'kycStatus',
  kycVerifiedAt: 'kycVerifiedAt',
  selectedRoute: 'selectedRoute',
  failureReason: 'failureReason',
  failureCode: 'failureCode',
  retryCount: 'retryCount',
  createdAt: 'createdAt',
  startedAt: 'startedAt',
  completedAt: 'completedAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.ProviderScalarFieldEnum = {
  id: 'id',
  code: 'code',
  name: 'name',
  type: 'type',
  supportedCountries: 'supportedCountries',
  supportedCurrencies: 'supportedCurrencies',
  paymentMethods: 'paymentMethods',
  features: 'features',
  canCollect: 'canCollect',
  canPayout: 'canPayout',
  isActive: 'isActive',
  healthStatus: 'healthStatus',
  lastHealthCheck: 'lastHealthCheck',
  avgResponseTime: 'avgResponseTime',
  successRate: 'successRate'
};

exports.Prisma.ProviderConfigScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  providerId: 'providerId',
  environment: 'environment',
  credentials: 'credentials',
  webhookSecret: 'webhookSecret',
  settings: 'settings',
  isActive: 'isActive',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.ProviderRouteScalarFieldEnum = {
  id: 'id',
  providerId: 'providerId',
  name: 'name',
  fromCountry: 'fromCountry',
  toCountry: 'toCountry',
  fromCurrency: 'fromCurrency',
  toCurrency: 'toCurrency',
  paymentMethod: 'paymentMethod',
  fixedFee: 'fixedFee',
  percentageFee: 'percentageFee',
  minAmount: 'minAmount',
  maxAmount: 'maxAmount',
  estimatedTime: 'estimatedTime',
  cutoffTime: 'cutoffTime',
  workingDays: 'workingDays',
  isActive: 'isActive',
  priority: 'priority'
};

exports.Prisma.PaymentCorridorScalarFieldEnum = {
  id: 'id',
  code: 'code',
  name: 'name',
  fromCountry: 'fromCountry',
  toCountry: 'toCountry',
  fromCurrency: 'fromCurrency',
  toCurrency: 'toCurrency',
  collectProviders: 'collectProviders',
  payoutProviders: 'payoutProviders',
  avgTransferTime: 'avgTransferTime',
  minAmount: 'minAmount',
  maxAmount: 'maxAmount',
  isActive: 'isActive',
  isPopular: 'isPopular',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.ProviderTransactionScalarFieldEnum = {
  id: 'id',
  paymentOrderId: 'paymentOrderId',
  providerId: 'providerId',
  type: 'type',
  externalId: 'externalId',
  status: 'status',
  request: 'request',
  response: 'response',
  errorCode: 'errorCode',
  errorMessage: 'errorMessage',
  isRetryable: 'isRetryable',
  createdAt: 'createdAt',
  completedAt: 'completedAt'
};

exports.Prisma.AgentScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  name: 'name',
  type: 'type',
  version: 'version',
  model: 'model',
  agentWalletId: 'agentWalletId',
  graphDefinition: 'graphDefinition',
  tools: 'tools',
  systemPrompt: 'systemPrompt',
  supportedProviders: 'supportedProviders',
  supportedChains: 'supportedChains',
  capabilities: 'capabilities',
  isActive: 'isActive',
  totalExecutions: 'totalExecutions',
  avgExecutionTime: 'avgExecutionTime',
  successRate: 'successRate',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.AgentDecisionScalarFieldEnum = {
  id: 'id',
  agentId: 'agentId',
  paymentOrderId: 'paymentOrderId',
  decisionType: 'decisionType',
  input: 'input',
  reasoning: 'reasoning',
  decision: 'decision',
  confidence: 'confidence',
  executionTime: 'executionTime',
  tokensUsed: 'tokensUsed',
  wasOverridden: 'wasOverridden',
  overriddenBy: 'overriddenBy',
  overrideReason: 'overrideReason',
  createdAt: 'createdAt'
};

exports.Prisma.AgentCheckpointScalarFieldEnum = {
  id: 'id',
  agentId: 'agentId',
  threadId: 'threadId',
  checkpointId: 'checkpointId',
  state: 'state',
  metadata: 'metadata',
  createdAt: 'createdAt'
};

exports.Prisma.AgentInteractionScalarFieldEnum = {
  id: 'id',
  agentDecisionId: 'agentDecisionId',
  userId: 'userId',
  type: 'type',
  message: 'message',
  action: 'action',
  result: 'result',
  createdAt: 'createdAt'
};

exports.Prisma.WebhookScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  url: 'url',
  events: 'events',
  secret: 'secret',
  isActive: 'isActive',
  failureCount: 'failureCount',
  lastFailureAt: 'lastFailureAt',
  createdAt: 'createdAt',
  updatedAt: 'updatedAt'
};

exports.Prisma.WebhookDeliveryScalarFieldEnum = {
  id: 'id',
  webhookId: 'webhookId',
  eventType: 'eventType',
  eventId: 'eventId',
  payload: 'payload',
  statusCode: 'statusCode',
  response: 'response',
  error: 'error',
  attempts: 'attempts',
  nextRetryAt: 'nextRetryAt',
  createdAt: 'createdAt',
  deliveredAt: 'deliveredAt'
};

exports.Prisma.ManualProcessStepScalarFieldEnum = {
  id: 'id',
  paymentOrderId: 'paymentOrderId',
  type: 'type',
  reason: 'reason',
  instructions: 'instructions',
  assignedTo: 'assignedTo',
  assignedTeam: 'assignedTeam',
  priority: 'priority',
  status: 'status',
  resolution: 'resolution',
  createdAt: 'createdAt',
  startedAt: 'startedAt',
  completedAt: 'completedAt',
  dueAt: 'dueAt'
};

exports.Prisma.PaymentEventScalarFieldEnum = {
  id: 'id',
  paymentOrderId: 'paymentOrderId',
  sequenceNumber: 'sequenceNumber',
  eventType: 'eventType',
  eventVersion: 'eventVersion',
  data: 'data',
  metadata: 'metadata',
  kafkaTopic: 'kafkaTopic',
  kafkaPartition: 'kafkaPartition',
  kafkaOffset: 'kafkaOffset',
  occurredAt: 'occurredAt'
};

exports.Prisma.AuditLogScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  userId: 'userId',
  action: 'action',
  entityType: 'entityType',
  entityId: 'entityId',
  changes: 'changes',
  metadata: 'metadata',
  ipAddress: 'ipAddress',
  userAgent: 'userAgent',
  requestId: 'requestId',
  createdAt: 'createdAt'
};

exports.Prisma.ApiKeyScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  name: 'name',
  keyHash: 'keyHash',
  prefix: 'prefix',
  scopes: 'scopes',
  rateLimit: 'rateLimit',
  isActive: 'isActive',
  expiresAt: 'expiresAt',
  lastUsedAt: 'lastUsedAt',
  createdAt: 'createdAt',
  revokedAt: 'revokedAt'
};

exports.Prisma.IntegrationKeyScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  agentId: 'agentId',
  name: 'name',
  keyHash: 'keyHash',
  prefix: 'prefix',
  description: 'description',
  allowedCorridors: 'allowedCorridors',
  allowedProviders: 'allowedProviders',
  rateLimit: 'rateLimit',
  dailyLimit: 'dailyLimit',
  lastUsedAt: 'lastUsedAt',
  usageCount: 'usageCount',
  isActive: 'isActive',
  expiresAt: 'expiresAt',
  createdAt: 'createdAt',
  revokedAt: 'revokedAt'
};

exports.Prisma.OrganizationUserScalarFieldEnum = {
  id: 'id',
  organizationId: 'organizationId',
  userId: 'userId',
  role: 'role',
  permissions: 'permissions',
  invitedBy: 'invitedBy',
  invitedAt: 'invitedAt',
  acceptedAt: 'acceptedAt',
  isActive: 'isActive'
};

exports.Prisma.SortOrder = {
  asc: 'asc',
  desc: 'desc'
};

exports.Prisma.JsonNullValueInput = {
  JsonNull: Prisma.JsonNull
};

exports.Prisma.NullableJsonNullValueInput = {
  DbNull: Prisma.DbNull,
  JsonNull: Prisma.JsonNull
};

exports.Prisma.QueryMode = {
  default: 'default',
  insensitive: 'insensitive'
};

exports.Prisma.JsonNullValueFilter = {
  DbNull: Prisma.DbNull,
  JsonNull: Prisma.JsonNull,
  AnyNull: Prisma.AnyNull
};

exports.Prisma.NullsOrder = {
  first: 'first',
  last: 'last'
};
exports.ComplianceStatus = exports.$Enums.ComplianceStatus = {
  PENDING: 'PENDING',
  IN_REVIEW: 'IN_REVIEW',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
  SUSPENDED: 'SUSPENDED'
};

exports.AuthProvider = exports.$Enums.AuthProvider = {
  EMAIL: 'EMAIL',
  GOOGLE: 'GOOGLE',
  THIRDWEB: 'THIRDWEB',
  WALLET_CONNECT: 'WALLET_CONNECT'
};

exports.PaymentMethodType = exports.$Enums.PaymentMethodType = {
  CARD: 'CARD',
  BANK_ACCOUNT: 'BANK_ACCOUNT',
  WALLET: 'WALLET',
  CASH: 'CASH'
};

exports.SubscriptionStatus = exports.$Enums.SubscriptionStatus = {
  ACTIVE: 'ACTIVE',
  PAST_DUE: 'PAST_DUE',
  CANCELED: 'CANCELED',
  UNPAID: 'UNPAID',
  TRIALING: 'TRIALING'
};

exports.WalletType = exports.$Enums.WalletType = {
  EOA: 'EOA',
  SMART_WALLET: 'SMART_WALLET',
  MULTI_SIG: 'MULTI_SIG'
};

exports.BlockchainTxStatus = exports.$Enums.BlockchainTxStatus = {
  PENDING: 'PENDING',
  MINED: 'MINED',
  CONFIRMED: 'CONFIRMED',
  FAILED: 'FAILED',
  DROPPED: 'DROPPED'
};

exports.ProductType = exports.$Enums.ProductType = {
  SERVICE: 'SERVICE',
  GOOD: 'GOOD',
  SUBSCRIPTION: 'SUBSCRIPTION'
};

exports.PriceType = exports.$Enums.PriceType = {
  ONE_TIME: 'ONE_TIME',
  RECURRING: 'RECURRING'
};

exports.BillingInterval = exports.$Enums.BillingInterval = {
  DAY: 'DAY',
  WEEK: 'WEEK',
  MONTH: 'MONTH',
  YEAR: 'YEAR'
};

exports.PaymentLinkStatus = exports.$Enums.PaymentLinkStatus = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  PAUSED: 'PAUSED',
  EXPIRED: 'EXPIRED',
  ARCHIVED: 'ARCHIVED',
  COMPLETED: 'COMPLETED'
};

exports.PaymentOrderStatus = exports.$Enums.PaymentOrderStatus = {
  CREATED: 'CREATED',
  AWAITING_PAYMENT: 'AWAITING_PAYMENT',
  PROCESSING: 'PROCESSING',
  REQUIRES_ACTION: 'REQUIRES_ACTION',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  REFUNDED: 'REFUNDED',
  CANCELLED: 'CANCELLED'
};

exports.KycStatus = exports.$Enums.KycStatus = {
  NOT_REQUIRED: 'NOT_REQUIRED',
  PENDING: 'PENDING',
  IN_REVIEW: 'IN_REVIEW',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED'
};

exports.ProviderType = exports.$Enums.ProviderType = {
  BANKING_RAILS: 'BANKING_RAILS',
  CARD_PROCESSOR: 'CARD_PROCESSOR',
  CRYPTO_ONRAMP: 'CRYPTO_ONRAMP',
  CRYPTO_OFFRAMP: 'CRYPTO_OFFRAMP',
  OPEN_BANKING: 'OPEN_BANKING',
  WALLET: 'WALLET'
};

exports.ProviderHealth = exports.$Enums.ProviderHealth = {
  HEALTHY: 'HEALTHY',
  DEGRADED: 'DEGRADED',
  DOWN: 'DOWN',
  MAINTENANCE: 'MAINTENANCE'
};

exports.Environment = exports.$Enums.Environment = {
  PRODUCTION: 'PRODUCTION',
  SANDBOX: 'SANDBOX',
  TEST: 'TEST'
};

exports.ProviderTxType = exports.$Enums.ProviderTxType = {
  PAYMENT_INITIATION: 'PAYMENT_INITIATION',
  STATUS_CHECK: 'STATUS_CHECK',
  REFUND: 'REFUND',
  WEBHOOK_CALLBACK: 'WEBHOOK_CALLBACK',
  BALANCE_CHECK: 'BALANCE_CHECK',
  EXCHANGE_RATE: 'EXCHANGE_RATE'
};

exports.AgentType = exports.$Enums.AgentType = {
  PAYMENT_ORCHESTRATOR: 'PAYMENT_ORCHESTRATOR',
  RISK_ANALYZER: 'RISK_ANALYZER',
  ROUTE_OPTIMIZER: 'ROUTE_OPTIMIZER',
  FRAUD_DETECTOR: 'FRAUD_DETECTOR',
  CUSTOMER_SUPPORT: 'CUSTOMER_SUPPORT',
  RECONCILIATION: 'RECONCILIATION'
};

exports.InteractionType = exports.$Enums.InteractionType = {
  APPROVAL_REQUEST: 'APPROVAL_REQUEST',
  INFORMATION_REQUEST: 'INFORMATION_REQUEST',
  OVERRIDE: 'OVERRIDE',
  FEEDBACK: 'FEEDBACK'
};

exports.ManualStepType = exports.$Enums.ManualStepType = {
  KYC_REVIEW: 'KYC_REVIEW',
  FRAUD_REVIEW: 'FRAUD_REVIEW',
  EXCEPTION_HANDLING: 'EXCEPTION_HANDLING',
  RECONCILIATION: 'RECONCILIATION',
  CUSTOMER_SUPPORT: 'CUSTOMER_SUPPORT'
};

exports.Priority = exports.$Enums.Priority = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  URGENT: 'URGENT'
};

exports.ManualStepStatus = exports.$Enums.ManualStepStatus = {
  PENDING: 'PENDING',
  IN_PROGRESS: 'IN_PROGRESS',
  COMPLETED: 'COMPLETED',
  CANCELLED: 'CANCELLED'
};

exports.UserRole = exports.$Enums.UserRole = {
  OWNER: 'OWNER',
  ADMIN: 'ADMIN',
  DEVELOPER: 'DEVELOPER',
  FINANCE: 'FINANCE',
  SUPPORT: 'SUPPORT',
  VIEWER: 'VIEWER'
};

exports.Prisma.ModelName = {
  Organization: 'Organization',
  User: 'User',
  Customer: 'Customer',
  CustomerPaymentMethod: 'CustomerPaymentMethod',
  Subscription: 'Subscription',
  SubscriptionItem: 'SubscriptionItem',
  Wallet: 'Wallet',
  BlockchainTransaction: 'BlockchainTransaction',
  GasSponsorship: 'GasSponsorship',
  Product: 'Product',
  Price: 'Price',
  PaymentLink: 'PaymentLink',
  PaymentOrder: 'PaymentOrder',
  Provider: 'Provider',
  ProviderConfig: 'ProviderConfig',
  ProviderRoute: 'ProviderRoute',
  PaymentCorridor: 'PaymentCorridor',
  ProviderTransaction: 'ProviderTransaction',
  Agent: 'Agent',
  AgentDecision: 'AgentDecision',
  AgentCheckpoint: 'AgentCheckpoint',
  AgentInteraction: 'AgentInteraction',
  Webhook: 'Webhook',
  WebhookDelivery: 'WebhookDelivery',
  ManualProcessStep: 'ManualProcessStep',
  PaymentEvent: 'PaymentEvent',
  AuditLog: 'AuditLog',
  ApiKey: 'ApiKey',
  IntegrationKey: 'IntegrationKey',
  OrganizationUser: 'OrganizationUser'
};

/**
 * This is a stub Prisma Client that will error at runtime if called.
 */
class PrismaClient {
  constructor() {
    return new Proxy(this, {
      get(target, prop) {
        let message
        const runtime = getRuntime()
        if (runtime.isEdge) {
          message = `PrismaClient is not configured to run in ${runtime.prettyName}. In order to run Prisma Client on edge runtime, either:
- Use Prisma Accelerate: https://pris.ly/d/accelerate
- Use Driver Adapters: https://pris.ly/d/driver-adapters
`;
        } else {
          message = 'PrismaClient is unable to run in this browser environment, or has been bundled for the browser (running in `' + runtime.prettyName + '`).'
        }
        
        message += `
If this is unexpected, please open an issue: https://pris.ly/prisma-prisma-bug-report`

        throw new Error(message)
      }
    })
  }
}

exports.PrismaClient = PrismaClient

Object.assign(exports, Prisma)
