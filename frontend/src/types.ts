export type Company = {
  id: string
  legal_name: string
  contact_name: string
  email: string
  phone: string
  status: "active" | "inactive" | "suspended"
  notes: string | null
  created_at: string
  updated_at: string
}

export type PhoneNumber = {
  id: string
  company_id: string
  label: string
  phone_e164: string
  provider: string
  uazapi_base_url: string
  connection_status: string
  webhook_url: string | null
  webhook_url_prefix: string
  created_at: string
  updated_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
}

export type WebhookUrlResponse = {
  phone_number_id: string
  company_id: string
  webhook_url: string | null
  webhook_url_prefix: string
  message: string | null
}

export type WebhookRegenerateResponse = {
  phone_number_id: string
  company_id: string
  webhook_url: string
  message: string
}
