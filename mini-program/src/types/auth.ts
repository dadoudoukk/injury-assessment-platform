export interface LoginResponse {
  access_token: string
  mustChangePassword?: boolean
  isPatient?: boolean
  isAgency?: boolean
}

export interface WxLoginBody {
  code: string
}

export interface PasswordLoginBody {
  username: string
  password: string
}
